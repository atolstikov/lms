import logging

from django_rq import job

from django.conf import settings

from code_reviews.api.gerrit import Gerrit
from code_reviews.api.ldap import ldap_client
from code_reviews.gerrit import get_or_create_change, list_change_files, \
    get_ldap_username
from code_reviews.gerrit.ldap import get_ldap_password_hash, user_to_ldap_entry
from learning.models import AssignmentComment, AssignmentSubmissionTypes
from users.models import User

logger = logging.getLogger(__name__)


@job('high')
def create_account_in_gerrit(*, user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"User with id={user_id} not found")
        return
    uid = get_ldap_username(user)
    with ldap_client() as client:
        results = client.search_users(uid)
        if results:
            logger.info(f"User with id={user_id} already has an account")
            return
        else:
            entry = user_to_ldap_entry(user)
            client.add_entry(entry)


@job('high')
def update_password_in_gerrit(*, user_id: int):
    """
    Update LDAP password hash in review.compscicenter.ru when user
    successfully changed his password with reset or change form.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"User with id={user_id} not found")
        return
    password_hash = get_ldap_password_hash(user.password)
    if not password_hash:
        logger.info(f"Empty hash for user_id={user_id}")
        return
    username = get_ldap_username(user)
    # TODO: What if connection fail when code review system is not available?
    with ldap_client() as client:
        changed = client.set_password_hash(username, password_hash)
        if not changed:
            logger.error(f"Password hash for user {user_id} wasn't changed")


@job('default')
def upload_attachment_to_gerrit(assignment_comment_id):
    assignment_solution = (AssignmentComment.objects
                           .select_related('student_assignment')
                           .get(type=AssignmentSubmissionTypes.SOLUTION,
                                pk=assignment_comment_id))
    student_assignment = assignment_solution.student_assignment
    attached_file = assignment_solution.attached_file

    client = Gerrit(settings.GERRIT_API_URI,
                    auth=(settings.GERRIT_CLIENT_USERNAME,
                          settings.GERRIT_CLIENT_HTTP_PASSWORD))

    change = get_or_create_change(client, student_assignment)
    if not change:
        logger.info('Failed to get or create a change')
        return

    response = client.get_change_edit(change.change_id)
    if not response.no_content:
        logger.info('Found previous change edit')
        response = client.delete_change_edit(change.change_id)
        if not response.no_content:
            logger.error('Failed to delete previous change edit')

    # Save extension to enable syntax highlighting in the UI
    extension = attached_file.name.split('.')[-1]
    solution_filename = f"solution.{extension}"

    # Delete other existing files
    change_files = list_change_files(client, change)
    for file in change_files:
        if file != solution_filename:
            client.delete_file(change.change_id, file)

    # Upload new solution as a Change Edit
    response = client.upload_file(change.change_id, solution_filename,
                                  attached_file)
    if not response.no_content:
        logger.info('Failed to upload the solution')

    # Publish Change Edit with all modifications
    response = client.publish_change_edit(change.change_id)
    if not response.no_content:
        logger.info('Failed to publish change edit')
        return
