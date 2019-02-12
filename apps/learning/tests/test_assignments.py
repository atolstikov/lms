import datetime
from decimal import Decimal

import factory
import pytest
import pytz
from bs4 import BeautifulSoup
from core.tests.utils import CSCTestCase
from django.utils import timezone, formats
from django.utils.encoding import smart_bytes
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from core.constants import DATE_FORMAT_RU, TIME_FORMAT_RU
from core.urls import reverse
from courses.models import Assignment, AssignmentAttachment
from courses.tests.factories import SemesterFactory, CourseFactory, \
    CourseTeacherFactory, AssignmentFactory
from courses.utils import get_current_term_pair
from learning.enrollment import course_failed_by_student
from learning.models import StudentAssignment
from learning.settings import StudentStatuses, GradeTypes
from learning.tests.factories import EnrollmentFactory, \
    AssignmentCommentFactory, \
    StudentAssignmentFactory
from learning.tests.mixins import MyUtilitiesMixin
from learning.tests.test_views import GroupSecurityCheckMixin
from users.constants import AcademicRoles
from users.tests.factories import UserFactory, TeacherCenterFactory, \
    StudentFactory, \
    StudentCenterFactory, VolunteerFactory, ProjectReviewerFactory


# TODO: assignment submission page - comments localisation, assignment created localization
# TODO: Преподавание -> Задания, добавить тест для deadline_local


class StudentAssignmentListTests(GroupSecurityCheckMixin,
                                 MyUtilitiesMixin, CSCTestCase):
    url_name = 'study:assignment_list'
    groups_allowed = [AcademicRoles.STUDENT_CENTER]

    def test_list(self):
        u = StudentCenterFactory()
        now_year, now_season = get_current_term_pair('spb')
        s = SemesterFactory.create(year=now_year, type=now_season)
        co = CourseFactory.create(semester=s)
        as1 = AssignmentFactory.create_batch(2, course=co)
        self.doLogin(u)
        # no assignments yet
        resp = self.client.get(reverse(self.url_name))
        self.assertEqual(0, len(resp.context['assignment_list_open']))
        self.assertEqual(0, len(resp.context['assignment_list_archive']))
        # enroll at course offering, assignments are shown
        EnrollmentFactory.create(student=u, course=co)
        resp = self.client.get(reverse(self.url_name))
        self.assertEqual(2, len(resp.context['assignment_list_open']))
        self.assertEqual(0, len(resp.context['assignment_list_archive']))
        # add a few assignments, they should show up
        as2 = AssignmentFactory.create_batch(3, course=co)
        resp = self.client.get(reverse(self.url_name))
        self.assertSameObjects([(StudentAssignment.objects
                                 .get(assignment=a, student=u))
                                for a in (as1 + as2)],
                               resp.context['assignment_list_open'])
        # Add few old assignments from current semester with expired deadline
        deadline_at = (datetime.datetime.now().replace(tzinfo=timezone.utc)
                       - datetime.timedelta(days=1))
        as_olds = AssignmentFactory.create_batch(2, course=co,
                                             deadline_at=deadline_at)
        resp = self.client.get(reverse(self.url_name))
        for a in as1 + as2 + as_olds:
            self.assertContains(resp, a.title)
        for a in as_olds:
            self.assertContains(resp, a.title)
        self.assertSameObjects([(StudentAssignment.objects
                                 .get(assignment=a, student=u))
                                for a in (as1 + as2)],
                               resp.context['assignment_list_open'])
        self.assertSameObjects([(StudentAssignment.objects
                                 .get(assignment=a, student=u)) for a in as_olds],
                                resp.context['assignment_list_archive'])
        # Now add assignment from old semester
        old_s = SemesterFactory.create(year=now_year - 1, type=now_season)
        old_co = CourseFactory.create(semester=old_s)
        as_past = AssignmentFactory(course=old_co)
        resp = self.client.get(reverse(self.url_name))
        self.assertNotIn(as_past, resp.context['assignment_list_archive'])

    def test_assignments_from_unenrolled_course(self):
        """Move to archive active assignments from course offerings
        which student already leave
        """
        u = StudentCenterFactory()
        now_year, now_season = get_current_term_pair('spb')
        s = SemesterFactory.create(year=now_year, type=now_season)
        # Create open co to pass enrollment limit
        co = CourseFactory.create(semester=s, is_open=True)
        as1 = AssignmentFactory.create_batch(2, course=co)
        self.doLogin(u)
        # enroll at course offering, assignments are shown
        EnrollmentFactory.create(student=u, course=co)
        resp = self.client.get(reverse(self.url_name))
        self.assertEqual(2, len(resp.context['assignment_list_open']))
        self.assertEqual(0, len(resp.context['assignment_list_archive']))
        # Now unenroll from the course
        form = {'course_pk': co.pk}
        response = self.client.post(co.get_unenroll_url(), form)
        resp = self.client.get(reverse(self.url_name))
        self.assertEqual(0, len(resp.context['assignment_list_open']))
        self.assertEqual(2, len(resp.context['assignment_list_archive']))


@pytest.mark.django_db
def test_security_assignmentstudent_detail(client, assert_login_redirect):
    """
    Students can't see assignments from completed course, which they failed
    """
    teacher = TeacherCenterFactory()
    student = StudentCenterFactory()
    past_year = datetime.datetime.now().year - 3
    past_semester = SemesterFactory.create(year=past_year)
    co = CourseFactory(teachers=[teacher], semester=past_semester)
    enrollment = EnrollmentFactory(student=student, course=co,
                                   grade=GradeTypes.UNSATISFACTORY)
    a = AssignmentFactory(course=co)
    a_s = StudentAssignment.objects.get(student=student, assignment=a)
    url = a_s.get_student_url()
    client.login(student)
    assert_login_redirect(url, method='get')
    # Teacher still can view student assignment
    client.login(teacher)
    response = client.get(a_s.get_teacher_url())
    assert response.status_code == 200


@pytest.mark.django_db
def test_security_course_detail(client):
    """Student can't watch news from completed course which they failed"""
    teacher = TeacherCenterFactory()
    student = StudentFactory()
    past_year = datetime.datetime.now().year - 3
    co = CourseFactory(teachers=[teacher], semester__year=past_year)
    enrollment = EnrollmentFactory(student=student, course=co,
                                   grade=GradeTypes.UNSATISFACTORY)
    a = AssignmentFactory(course=co)
    co.refresh_from_db()
    assert course_failed_by_student(co, student)
    client.login(student)
    url = co.get_absolute_url()
    response = client.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.find(text=_("News")) is None
    # Change student co mark
    enrollment.grade = GradeTypes.EXCELLENT
    enrollment.save()
    response = client.get(url)
    assert not course_failed_by_student(co, student)
    # Change course offering state to not completed
    co.completed_at = now().date() + datetime.timedelta(days=1)
    co.save()
    response = client.get(url)
    assert not course_failed_by_student(co, student)


@pytest.mark.django_db
def test_assignment_contents(client):
    teacher = TeacherCenterFactory()
    student = StudentCenterFactory()
    co = CourseFactory.create(teachers=[teacher])
    EnrollmentFactory.create(student=student, course=co)
    a = AssignmentFactory.create(course=co)
    a_s = (StudentAssignment.objects
           .get(assignment=a, student=student))
    client.login(teacher)
    assert smart_bytes(a.text) in client.get(a_s.get_teacher_url()).content


@pytest.mark.django_db
def test_studentassignment_last_comment_from():
    """`last_comment_from` attribute is updated by signal"""
    teacher = TeacherCenterFactory.create()
    student = StudentCenterFactory.create()
    now_year, now_season = get_current_term_pair('spb')
    s = SemesterFactory.create(year=now_year, type=now_season)
    co = CourseFactory.create(city_id='spb', semester=s,
                              teachers=[teacher])
    EnrollmentFactory.create(student=student, course=co)
    assignment = AssignmentFactory.create(course=co)
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
def test_studentassignment_first_student_comment_at(curator):
    """`first_student_comment_at` attribute is updated by signal"""
    teacher = TeacherCenterFactory.create()
    student = StudentCenterFactory.create()
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


class AssignmentTeacherDetailsTest(MyUtilitiesMixin, CSCTestCase):
    def test_security(self):
        teacher = TeacherCenterFactory()
        a = AssignmentFactory.create(course__teachers=[teacher])
        url = a.get_teacher_url()
        self.assertLoginRedirect(url)
        test_groups = [
            [],
            [AcademicRoles.TEACHER_CENTER],
            [AcademicRoles.STUDENT_CENTER],
        ]
        for groups in test_groups:
            self.doLogin(UserFactory.create(groups=groups, city_id='spb'))
            if groups == [AcademicRoles.TEACHER_CENTER]:
                self.assertEqual(403, self.client.get(url).status_code)
            else:
                self.assertLoginRedirect(url)
            self.doLogout()
        self.doLogin(teacher)
        self.assertEqual(200, self.client.get(url).status_code)

    def test_details(self):
        teacher = TeacherCenterFactory()
        student = StudentCenterFactory()
        now_year, now_season = get_current_term_pair('spb')
        s = SemesterFactory.create(year=now_year, type=now_season)
        co = CourseFactory.create(city='spb', semester=s,
                                  teachers=[teacher])
        a = AssignmentFactory.create(course=co)
        self.doLogin(teacher)
        url = a.get_teacher_url()
        resp = self.client.get(url)
        self.assertEqual(a, resp.context['assignment'])
        self.assertEqual(0, len(resp.context['a_s_list']))
        EnrollmentFactory.create(student=student, course=co)
        a_s = StudentAssignment.objects.get(student=student, assignment=a)
        resp = self.client.get(url)
        self.assertEqual(a, resp.context['assignment'])
        self.assertSameObjects([a_s], resp.context['a_s_list'])


class AssignmentTeacherListTests(MyUtilitiesMixin, CSCTestCase):
    url_name = 'teaching:assignment_list'
    groups_allowed = [AcademicRoles.TEACHER_CENTER]

    def test_group_security(self):
        """Custom logic instead of GroupSecurityCheckMixin.
        Teacher can get 302 if no CO yet"""
        self.assertLoginRedirect(reverse(self.url_name))
        all_test_groups = [
            [],
            [AcademicRoles.TEACHER_CENTER],
            [AcademicRoles.STUDENT_CENTER],
            [AcademicRoles.GRADUATE_CENTER]
        ]
        for groups in all_test_groups:
            user = UserFactory.create(groups=groups, city_id='spb')
            self.doLogin(user)
            if any(group in self.groups_allowed for group in groups):
                co = CourseFactory.create(teachers=[user])
                # Create co for teacher to prevent 404 error
                self.assertStatusCode(200, self.url_name)
            else:
                self.assertLoginRedirect(reverse(self.url_name))
            self.client.logout()
        self.doLogin(UserFactory.create(is_superuser=True, is_staff=True))
        self.assertStatusCode(302, self.url_name)

    def test_list(self):
        # Default filter for grade - `no_grade`
        TEACHER_ASSIGNMENTS_PAGE = reverse(self.url_name)
        teacher = TeacherCenterFactory()
        students = UserFactory.create_batch(3, groups=['Student [CENTER]'])
        now_year, now_season = get_current_term_pair('spb')
        s = SemesterFactory.create(year=now_year, type=now_season)
        # some other teacher's course offering
        co_other = CourseFactory.create(city='spb', semester=s)
        AssignmentFactory.create_batch(2, course=co_other)
        self.doLogin(teacher)
        # no course offerings yet, return 302
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE)
        self.assertEqual(302, resp.status_code)
        # Create co, assignments and enroll students
        co = CourseFactory.create(city='spb', semester=s,
                                  teachers=[teacher])
        for student1 in students:
            EnrollmentFactory.create(student=student1, course=co)
        assignment = AssignmentFactory.create(course=co)
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE)
        # TODO: add wrong term type and check redirect.
        # By default we show all submissions without grades
        self.assertEqual(3, len(resp.context['student_assignment_list']))
        # Show submissions without comments
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=empty")
        self.assertEqual(3, len(resp.context['student_assignment_list']))
        # TODO: add test which assignment selected by default.
        sas = ((StudentAssignment.objects.get(student=student,
                                              assignment=assignment))
               for student in students)
        self.assertSameObjects(sas, resp.context['student_assignment_list'])
        # Let's check assignments with last comment from student only
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=student")
        self.assertEqual(0, len(resp.context['student_assignment_list']))
        # Teacher commented on student1 assignment
        student1, student2, student3 = students
        sa1: StudentAssignment = StudentAssignment.objects.get(
            student=student1, assignment=assignment)
        sa2 = StudentAssignment.objects.get(student=student2,
                                            assignment=assignment)
        AssignmentCommentFactory.create(student_assignment=sa1, author=teacher)
        assert sa1.last_comment_from == sa1.CommentAuthorTypes.TEACHER
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=any")
        self.assertEqual(3, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=student")
        self.assertEqual(0, len(resp.context['student_assignment_list']))
        resp = self.client.get(reverse(self.url_name) + "?comment=teacher")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=empty")
        self.assertEqual(2, len(resp.context['student_assignment_list']))
        # Student2 commented on assignment
        AssignmentCommentFactory.create_batch(2, student_assignment=sa2,
                                              author=student2)
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=any")
        self.assertEqual(3, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=student")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        self.assertSameObjects([sa2], resp.context['student_assignment_list'])
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=teacher")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=empty")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        # Teacher answered on the student2 assignment
        AssignmentCommentFactory.create(student_assignment=sa2, author=teacher)
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=any")
        self.assertEqual(3, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=student")
        self.assertEqual(0, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=teacher")
        self.assertEqual(2, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=empty")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        # Student 3 add comment on assignment
        sa3 = StudentAssignment.objects.get(student=student3,
                                            assignment=assignment)
        AssignmentCommentFactory.create_batch(3, student_assignment=sa3,
                                              author=student3)
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=any")
        self.assertEqual(3, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=student")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=teacher")
        self.assertEqual(2, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE + "?comment=empty")
        self.assertEqual(0, len(resp.context['student_assignment_list']))
        # teacher has set a grade
        sa3.score = 3
        sa3.save()
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE +
                               "?comment=student&score=no")
        self.assertEqual(0, len(resp.context['student_assignment_list']))
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE +
                               "?comment=student&score=any")
        self.assertEqual(1, len(resp.context['student_assignment_list']))
        sa3.refresh_from_db()
        sa1.score = 3
        sa1.save()
        resp = self.client.get(TEACHER_ASSIGNMENTS_PAGE +
                               "?comment=student&score=yes")
        self.assertEqual(1, len(resp.context['student_assignment_list']))


@pytest.mark.django_db
def test_assignment_public_form_for_teachers(settings, client):
    settings.LANGUAGE_CODE = 'ru'  # formatting depends on locale
    teacher = TeacherCenterFactory()
    co_in_spb = CourseFactory(city='spb', teachers=[teacher])
    client.login(teacher)
    form_data = {
        "title": "title",
        "text": "text",
        "deadline_at_0": "29.06.2017",
        "deadline_at_1": "00:00",
        "passing_score": "3",
        "maximum_score": "5",
    }
    add_url = co_in_spb.get_create_assignment_url()
    response = client.post(add_url, form_data, follow=True)
    assert response.status_code == 200
    assert Assignment.objects.count() == 1
    assignment = Assignment.objects.first()
    # In DB we store datetime values in UTC
    assert assignment.deadline_at.day == 28
    assert assignment.deadline_at.hour == 21
    assert assignment.deadline_at.minute == 0
    assert assignment.course_id == co_in_spb.pk
    tz_diff = datetime.timedelta(hours=3)  # UTC+3 for msk timezone
    assert assignment.deadline_at_local().utcoffset() == tz_diff
    # Check widget shows local time
    response = client.get(assignment.get_update_url())
    widget_html = response.context['form']['deadline_at'].as_widget()
    widget = BeautifulSoup(widget_html, "html.parser")
    time_input = widget.find('input', {"name": 'deadline_at_1'})
    assert time_input.get('value') == '00:00'
    # Clone CO from msk
    co_in_nsk = CourseFactory(city_id='nsk',
                              meta_course=co_in_spb.meta_course,
                              teachers=[teacher])
    add_url = co_in_nsk.get_create_assignment_url()
    response = client.post(add_url, form_data, follow=True)
    assert response.status_code == 200
    assert Assignment.objects.count() == 2
    assignment_last = Assignment.objects.order_by("pk").last()
    assert assignment_last.course_id == co_in_nsk.pk
    tz_diff = datetime.timedelta(hours=7)  # UTC+7 for nsk timezone
    assert assignment_last.deadline_at_local().utcoffset() == tz_diff
    assert assignment_last.deadline_at.hour == 17


@pytest.mark.django_db
def test_assignment_deadline_display_for_teacher(settings, client):
    settings.LANGUAGE_CODE = 'ru'  # formatting depends on locale
    dt = datetime.datetime(2017, 1, 1, 15, 0, 0, 0, tzinfo=pytz.UTC)
    teacher = TeacherCenterFactory()
    assignment = AssignmentFactory(deadline_at=dt,
                                   course__city_id='spb',
                                   course__teachers=[teacher])
    url_for_teacher = assignment.get_teacher_url()
    client.login(teacher)
    response = client.get(url_for_teacher)
    html = BeautifulSoup(response.content, "html.parser")
    # Note: On this page used `naturalday` filter, so use passed datetime
    deadline_str = formats.date_format(assignment.deadline_at_local(),
                                       'd E Y H:i')
    assert deadline_str == "01 января 2017 18:00"
    assert any(deadline_str in s.string for s in html.find_all('p'))
    # Test student submission page
    sa = StudentAssignmentFactory(assignment=assignment)
    response = client.get(sa.get_teacher_url())
    html = BeautifulSoup(response.content, "html.parser")
    # Note: On this page used `naturalday` filter, so use passed datetime
    deadline_str = formats.date_format(assignment.deadline_at_local(),
                                       'd E Y H:i')
    assert deadline_str == "01 января 2017 18:00"
    assert any(deadline_str in s.string for s in
               html.find_all('span', {"class": "nowrap"}))


@pytest.mark.django_db
def test_deadline_l10n_on_student_assignments_page(settings, client):
    settings.LANGUAGE_CODE = 'ru'  # formatting depends on locale
    FORMAT_DATE_PART = 'd E Y'
    FORMAT_TIME_PART = 'H:i'
    # This day will be in archive block (1 jan 2017 15:00)
    dt = datetime.datetime(2017, 1, 1, 15, 0, 0, 0, tzinfo=pytz.UTC)
    # Assignment will be created with the past date, but we will see it on
    # assignments page since course offering semester set to current
    current_term = SemesterFactory.create_current()
    assignment = AssignmentFactory(deadline_at=dt,
                                   course__city_id='spb',
                                   course__is_correspondence=False,
                                   course__semester_id=current_term.pk)
    student = StudentCenterFactory(city_id='spb')
    sa = StudentAssignmentFactory(assignment=assignment, student=student)
    client.login(student)
    url_learning_assignments = reverse('study:assignment_list')
    response = client.get(url_learning_assignments)
    html = BeautifulSoup(response.content, "html.parser")
    # Note: On this page used `naturalday` filter, so use passed datetime
    year_part = formats.date_format(assignment.deadline_at_local(),
                                    FORMAT_DATE_PART)
    assert year_part == "01 января 2017"
    time_part = formats.date_format(assignment.deadline_at_local(),
                                    FORMAT_TIME_PART)
    assert time_part == "18:00"
    assert any(year_part in s.text and time_part in s.text for s in
               html.find_all('div', {'class': 'assignment-date'}))
    # Test `upcoming` block
    now_year, _ = get_current_term_pair('spb')
    dt = dt.replace(year=now_year + 1, month=2, hour=14)
    assignment.deadline_at = dt
    assignment.save()
    year_part = formats.date_format(assignment.deadline_at_local(),
                                    FORMAT_DATE_PART)
    assert year_part == "01 февраля {}".format(now_year + 1)
    time_part = formats.date_format(assignment.deadline_at_local(),
                                    FORMAT_TIME_PART)
    assert time_part == "17:00"
    response = client.get(url_learning_assignments)
    html = BeautifulSoup(response.content, "html.parser")
    assert any(year_part in s.text and time_part in s.text for s in
               html.find_all('div', {'class': 'assignment-date'}))
    # Make course online, now deadlines depends on user timezone for
    # center students
    dt = datetime.datetime(2017, 1, 1, 15, 0, 0, 0, tzinfo=pytz.UTC)
    assignment_nsk = AssignmentFactory(deadline_at=dt,
                                       course__city_id='nsk',
                                       course__is_correspondence=True,
                                       course__semester=current_term)
    StudentAssignmentFactory(assignment=assignment_nsk, student=student)
    client.login(student)
    response = client.get(url_learning_assignments)
    assert len(response.context["assignment_list"]) == 2
    assert response.context["tz_override"] == settings.TIME_ZONES['spb']
    year_part = formats.date_format(assignment_nsk.deadline_at_local(),
                                    FORMAT_DATE_PART)
    assert year_part == "01 января 2017"
    time_part = formats.date_format(
        assignment_nsk.deadline_at_local(tz=settings.TIME_ZONES['spb']),
        FORMAT_TIME_PART)
    assert time_part == "18:00"
    html = BeautifulSoup(response.content, "html.parser")
    assert any(year_part in s.text and time_part in s.text for s in
               html.find_all('div', {'class': 'assignment-date'}))
    # Make student as a volunteer, should be the same
    student.groups.remove(AcademicRoles.STUDENT_CENTER)
    student.groups.add(AcademicRoles.VOLUNTEER)
    response = client.get(url_learning_assignments)
    assert response.status_code == 200
    html = BeautifulSoup(response.content, "html.parser")
    assert any(year_part in s.text and time_part in s.text for s in
               html.find_all('div', {'class': 'assignment-date'}))
    # Club students has no access to the page on center site
    student.groups.remove(AcademicRoles.VOLUNTEER)
    student.groups.add(AcademicRoles.STUDENT_CLUB)
    response = client.get(url_learning_assignments)
    assert response.status_code == 302


@pytest.mark.django_db
def test_first_comment_after_deadline(client):
    dt = datetime.datetime(2017, 1, 1, 23, 58, 0, 0, tzinfo=pytz.UTC)
    assignment = AssignmentFactory(deadline_at=dt,
                                   course__city_id='spb')
    sa = StudentAssignmentFactory(assignment=assignment, student__city_id='spb')
    student = sa.student
    EnrollmentFactory(student=student, course=assignment.course)
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
def test_studentassignment_submission_grade(client):
    """
    Make sure we can remove zeroed grade for student assignment and use
    1.23 and 1,23 formats
    """
    sa = StudentAssignmentFactory()
    teacher = TeacherCenterFactory.create()
    CourseTeacherFactory(course=sa.assignment.course,
                         teacher=teacher)
    sa.assignment.passing_score = 1
    sa.assignment.maximum_score = 10
    sa.assignment.save()
    assert sa.score is None
    student = sa.student
    form = {"score": 0, "grading_form": True}
    client.login(teacher)
    response = client.post(sa.get_teacher_url(), form, follow=True)
    assert response.status_code == 200
    sa.refresh_from_db()
    assert sa.score == 0
    form = {"score": "", "grading_form": True}
    response = client.post(sa.get_teacher_url(), form, follow=True)
    assert response.status_code == 200
    sa.refresh_from_db()
    assert sa.score is None
    form = {"score": "1.22", "grading_form": True}
    response = client.post(sa.get_teacher_url(), form, follow=True)
    sa.refresh_from_db()
    assert sa.score == Decimal("1.22")
    form = {"score": "2,34", "grading_form": True}
    response = client.post(sa.get_teacher_url(), form, follow=True)
    sa.refresh_from_db()
    assert sa.score == Decimal("2.34")


@pytest.mark.django_db
def test_assignment_attachment_permissions(curator, client, tmpdir):
    teacher = TeacherCenterFactory()
    term = SemesterFactory.create_current()
    co = CourseFactory.create(semester=term, teachers=[teacher])
    form = factory.build(dict, FACTORY_CLASS=AssignmentFactory)
    deadline_date = form['deadline_at'].strftime(DATE_FORMAT_RU)
    deadline_time = form['deadline_at'].strftime(TIME_FORMAT_RU)
    tmp_file = tmpdir.mkdir("attachment").join("attachment.txt")
    tmp_file.write("content")
    form.update({'course': co.pk,
                 'attachments': tmp_file.open(),
                 'deadline_at_0': deadline_date,
                 'deadline_at_1': deadline_time})
    url = co.get_create_assignment_url()
    client.login(teacher)
    client.post(url, form)
    assert Assignment.objects.count() == 1
    assert AssignmentAttachment.objects.count() == 1
    a_attachment = AssignmentAttachment.objects.first()
    assert a_attachment.attachment.read() == b"content"
    client.logout()
    task_attachment_url = a_attachment.file_url()
    response = client.get(task_attachment_url)
    assert response.status_code == 302  # LoginRequiredMixin
    student_spb = StudentCenterFactory(city_id='spb')
    client.login(student_spb)
    response = client.get(task_attachment_url)
    assert response.status_code == 403  # not enrolled in
    EnrollmentFactory(student=student_spb, course=co)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    student_spb.status = StudentStatuses.EXPELLED
    student_spb.save()
    response = client.get(task_attachment_url)
    assert response.status_code == 403  # expelled
    # Should be the same for volunteer
    volunteer_spb = VolunteerFactory(city_id='spb')
    response = client.get(task_attachment_url)
    assert response.status_code == 403
    client.login(volunteer_spb)
    EnrollmentFactory(student=volunteer_spb, course=co)
    response = client.get(task_attachment_url)
    assert response.status_code == 200
    # Check not actual teacher access
    other_teacher = TeacherCenterFactory()
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