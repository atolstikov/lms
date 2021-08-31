import datetime
from decimal import Decimal

import factory
import pytest
import pytz
from bs4 import BeautifulSoup

from django.utils.encoding import smart_bytes
from django.utils.timezone import now
from django.utils.translation import gettext as _

from auth.mixins import PermissionRequiredMixin
from core.tests.factories import BranchFactory
from core.timezone.constants import DATE_FORMAT_RU, TIME_FORMAT_RU
from core.urls import reverse
from courses.models import Assignment, AssignmentAttachment, AssignmentSubmissionFormats
from courses.tests.factories import (
    AssignmentAttachmentFactory, AssignmentFactory, CourseFactory, SemesterFactory
)
from learning.models import StudentAssignment
from learning.permissions import ViewAssignmentAttachment
from learning.services import is_course_failed_by_student, get_student_profile
from learning.settings import Branches, GradeTypes, StudentStatuses
from learning.tests.factories import (
    AssignmentCommentFactory, EnrollmentFactory, StudentAssignmentFactory
)
from projects.tests.factories import ProjectReviewerFactory
from users.tests.factories import (
    CuratorFactory, StudentFactory, TeacherFactory, VolunteerFactory
)

# TODO: assignment submission page - comments localisation, assignment created localization


@pytest.mark.django_db
def test_security_course_detail(client):
    """Student can't watch news from completed course which they failed"""
    teacher = TeacherFactory()
    student = StudentFactory()
    past_year = datetime.datetime.now().year - 3
    co = CourseFactory(teachers=[teacher], semester__year=past_year)
    enrollment = EnrollmentFactory(student=student, course=co,
                                   grade=GradeTypes.UNSATISFACTORY)
    a = AssignmentFactory(course=co)
    co.refresh_from_db()
    assert is_course_failed_by_student(co, student)
    client.login(student)
    url = co.get_absolute_url()
    response = client.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.find(text=_("News")) is None
    # Change student co mark
    enrollment.grade = GradeTypes.EXCELLENT
    enrollment.save()
    response = client.get(url)
    assert not is_course_failed_by_student(co, student)
    # Change course offering state to not completed
    co.completed_at = now().date() + datetime.timedelta(days=1)
    co.save()
    response = client.get(url)
    assert not is_course_failed_by_student(co, student)


@pytest.mark.django_db
def test_student_assignment_last_comment_from():
    teacher = TeacherFactory.create()
    student = StudentFactory.create()
    s = SemesterFactory.create_current(for_branch=Branches.SPB)
    course = CourseFactory.create(semester=s, teachers=[teacher])
    EnrollmentFactory.create(student=student, course=course)
    assignment = AssignmentFactory.create(course=course)
    sa = StudentAssignment.objects.get(assignment=assignment)
    # Nobody comments yet
    assert sa.last_comment_from == StudentAssignment.CommentAuthorTypes.NOBODY
    AssignmentCommentFactory.create(student_assignment=sa, author=student)
    sa.refresh_from_db()
    assert sa.last_comment_from == StudentAssignment.CommentAuthorTypes.STUDENT
    AssignmentCommentFactory.create(student_assignment=sa, author=teacher)
    sa.refresh_from_db()
    assert sa.last_comment_from == StudentAssignment.CommentAuthorTypes.TEACHER


@pytest.mark.django_db
def test_student_assignment_model_weight_score():
    assignment = AssignmentFactory(weight=1, maximum_score=10, passing_score=2)
    student_assignment = StudentAssignment(assignment=assignment, score=2)
    assert student_assignment.weight_score == 2
    assignment.weight = Decimal('.5')
    assert student_assignment.weight_score == 1
    assignment.weight = Decimal('0.00')
    assert student_assignment.weight_score == 0
    assignment.weight = Decimal('0.01')
    assert student_assignment.weight_score == Decimal('0.02')


@pytest.mark.django_db
def test_student_assignment_first_student_comment_at(curator):
    teacher = TeacherFactory.create()
    student = StudentFactory.create()
    co = CourseFactory.create(teachers=[teacher])
    EnrollmentFactory.create(student=student, course=co)
    assignment = AssignmentFactory.create(course=co)
    sa = StudentAssignment.objects.get(assignment=assignment)
    assert sa.first_student_comment_at is None
    AssignmentCommentFactory.create(student_assignment=sa, author=teacher)
    sa.refresh_from_db()
    assert sa.first_student_comment_at is None
    AssignmentCommentFactory.create(student_assignment=sa, author=curator)
    sa.refresh_from_db()
    assert sa.first_student_comment_at is None
    AssignmentCommentFactory.create(student_assignment=sa, author=student)
    sa.refresh_from_db()
    assert sa.first_student_comment_at is not None
    first_student_comment_at = sa.first_student_comment_at
    # Make sure it doesn't changed
    AssignmentCommentFactory.create(student_assignment=sa, author=teacher)
    sa.refresh_from_db()
    assert sa.first_student_comment_at == first_student_comment_at
    # Second comment from student shouldn't change time
    AssignmentCommentFactory.create(student_assignment=sa, author=student)
    sa.refresh_from_db()
    assert sa.first_student_comment_at == first_student_comment_at


@pytest.mark.django_db
def test_first_comment_after_deadline(client):
    dt = datetime.datetime(2017, 1, 1, 23, 58, 0, 0, tzinfo=pytz.UTC)
    branch_spb = BranchFactory(code=Branches.SPB)
    assignment = AssignmentFactory(deadline_at=dt,
                                   course__main_branch=branch_spb)
    sa = StudentAssignmentFactory(assignment=assignment,
                                  student__branch=branch_spb)
    student = sa.student
    comment = AssignmentCommentFactory.create(student_assignment=sa,
                                              author=student,
                                              created=dt)
    client.login(student)
    response = client.get(sa.get_student_url())
    assert response.status_code == 200
    # Consider last min in favor of student
    assert response.context['first_comment_after_deadline'] is None
    assert smart_bytes('<hr class="deadline">') not in response.content
    comment.created = dt + datetime.timedelta(minutes=1)
    comment.save()
    response = client.get(sa.get_student_url())
    assert response.context['first_comment_after_deadline'] == comment
    assert smart_bytes('<hr class="deadline">') in response.content


@pytest.mark.django_db
def test_assignment_attachment_permissions(curator, client, tmpdir):
    teacher = TeacherFactory()
    client.login(teacher)
    term = SemesterFactory.create_current()
    course = CourseFactory(semester=term, teachers=[teacher])
    form = factory.build(dict, FACTORY_CLASS=AssignmentFactory)
    deadline_date = form['deadline_at'].strftime(DATE_FORMAT_RU)
    deadline_time = form['deadline_at'].strftime(TIME_FORMAT_RU)
    tmp_file = tmpdir.mkdir("attachment").join("attachment.txt")
    tmp_file.write("content")
    form.update({
        'course': course.pk,
        'attachments': tmp_file.open(),
        'time_zone': 'Europe/Moscow',
        'deadline_at_0': deadline_date,
        'deadline_at_1': deadline_time
    })
    url = course.get_create_assignment_url()
    client.post(url, form)
    assert Assignment.objects.count() == 1
    assert AssignmentAttachment.objects.count() == 1
    a_attachment = AssignmentAttachment.objects.first()
    assert a_attachment.attachment.read() == b"content"
    client.logout()
    task_attachment_url = a_attachment.get_download_url()
    response = client.get(task_attachment_url)
    assert response.status_code == 302  # redirect to login view
    student_spb = StudentFactory(branch__code=Branches.SPB)
    client.login(student_spb)
    response = client.get(task_attachment_url)
    assert response.status_code == 403  # not enrolled in
    EnrollmentFactory(student=student_spb, course=course)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    # Should be the same for volunteer
    volunteer_spb = VolunteerFactory(branch__code=Branches.SPB)
    client.login(volunteer_spb)
    response = client.get(task_attachment_url)
    assert response.status_code == 403
    EnrollmentFactory(student=volunteer_spb, course=course)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    # Check not actual teacher access
    other_teacher = TeacherFactory()
    client.login(other_teacher)
    response = client.get(task_attachment_url)
    assert response.status_code == 403  # not a course teacher (among all terms)
    client.login(teacher)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    client.login(curator)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    project_reviewer = ProjectReviewerFactory()
    # Reviewers and others have no access
    client.login(project_reviewer)
    response = client.get(task_attachment_url)
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("inactive_status", StudentStatuses.inactive_statuses)
def test_assignment_attachment_inactive_student(inactive_status, client,
                                                settings):
    """Inactive student can't view assignment attachments"""
    course = CourseFactory(semester=SemesterFactory.create_current())
    student_spb = StudentFactory(branch__code=Branches.SPB)
    a_attachment = AssignmentAttachmentFactory(assignment__course=course)
    EnrollmentFactory(course=course, student=student_spb)
    task_attachment_url = a_attachment.get_download_url()
    client.login(student_spb)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    student_profile = get_student_profile(student_spb, settings.SITE_ID)
    student_profile.status = inactive_status
    student_profile.save()
    response = client.get(task_attachment_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_assignment_admin_form(client):
    """
    Student assignments should be generated after creating assignment.
    """
    client.login(CuratorFactory())
    enrollment = EnrollmentFactory()
    course = enrollment.course
    a = AssignmentFactory.build()
    post_data = {
        'course': course.pk,
        'title': a.title,
        'submission_type': AssignmentSubmissionFormats.ONLINE,
        'text': a.text,
        'passing_score': 0,
        'maximum_score': 5,
        'weight': 1,
        'time_zone': 'Europe/Moscow',
        'deadline_at_0': str(a.deadline_at.date()),
        'deadline_at_1': '00:00'
    }
    assert StudentAssignment.objects.count() == 0
    response = client.post(reverse('admin:courses_assignment_add'), post_data)
    assert (Assignment.objects.count() == 1)
    assert StudentAssignment.objects.count() == 1


@pytest.mark.django_db
def test_download_assignment_attachment(lms_resolver):
    url = reverse('study:download_assignment_attachment',
                  kwargs={"sid": "wrongsid", "file_name": "filename.txt"})
    resolver = lms_resolver(url)
    assert issubclass(resolver.func.view_class, PermissionRequiredMixin)
    assert resolver.func.view_class.permission_required == ViewAssignmentAttachment.name
