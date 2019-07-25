# -*- coding: utf-8 -*-

import datetime

import factory
from django.utils import timezone

from courses.tests.factories import *
from learning.models import StudentAssignment, \
    AssignmentComment, Enrollment, AssignmentNotification, \
    CourseNewsNotification, Event, Branch, GraduateProfile
from learning.settings import Branches
from users.constants import Roles
from users.tests.factories import UserFactory, StudentFactory

__all__ = ('StudentAssignmentFactory',
           'AssignmentCommentFactory', 'EnrollmentFactory',
           'AssignmentNotificationFactory', 'BranchFactory',
           'CourseNewsNotificationFactory', 'EventFactory',
           'StudentAssignment', 'Enrollment', 'AssignmentComment', 'Branch',
           'GraduateProfileFactory')


class BranchFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Branch %03d" % n)
    code = factory.Iterator(x for x, _ in Branches.choices)

    class Meta:
        model = Branch
        django_get_or_create = ('code',)


# FIXME: create enrollment
class StudentAssignmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = StudentAssignment

    assignment = factory.SubFactory(AssignmentFactory)
    student = factory.SubFactory(StudentFactory)


class AssignmentCommentFactory(factory.DjangoModelFactory):
    """
    Make sure to call refresh_from_db if logic depends on
    `first_student_comment_at` or `last_comment_from`.
    """
    class Meta:
        model = AssignmentComment

    student_assignment = factory.SubFactory(StudentAssignmentFactory)
    text = factory.Sequence(lambda n: "Test comment %03d" % n)
    author = factory.SubFactory(UserFactory)
    attached_file = factory.django.FileField()


class EnrollmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Enrollment

    student = factory.SubFactory(StudentFactory)
    course = factory.SubFactory(CourseFactory)


class AssignmentNotificationFactory(factory.DjangoModelFactory):
    class Meta:
        model = AssignmentNotification

    user = factory.SubFactory(UserFactory)
    student_assignment = factory.SubFactory(StudentAssignmentFactory)


class CourseNewsNotificationFactory(factory.DjangoModelFactory):
    class Meta:
        model = CourseNewsNotification

    user = factory.SubFactory(UserFactory)
    course_offering_news = factory.SubFactory(CourseNewsFactory)


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = Event

    venue = factory.SubFactory(VenueFactory)
    name = factory.Sequence(lambda n: "Test event %03d" % n)
    description = factory.Sequence(lambda n: "Test event description %03d" % n)
    date = (datetime.datetime.now().replace(tzinfo=timezone.utc)
            + datetime.timedelta(days=3)).date()
    starts_at = "13:00"
    ends_at = "13:45"


class GraduateFactory(UserFactory):
    branch = factory.SubFactory('learning.tests.factories.BranchFactory',
                                code='spb')

    graduate_profile = factory.RelatedFactory(
        'learning.tests.factories.GraduateProfileFactory',
        'student'
    )

    @factory.post_generation
    def required_groups(self, create, extracted, **kwargs):
        if not create:
            return
        site_id = kwargs.pop("site_id", None)
        self.add_group(role=Roles.GRADUATE, site_id=site_id)


class GraduateProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = GraduateProfile

    student = factory.SubFactory(GraduateFactory, graduate_profile=None)
    graduated_on = factory.Faker('future_date', end_date="+10d", tzinfo=None)
