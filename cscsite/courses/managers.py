from typing import List

from django.apps import apps
from django.conf import settings

from django.db import models
from django.db.models import query, Subquery, Q, Prefetch, Count, Case, When, \
    Value, IntegerField

from core.utils import is_club_site
from learning.calendar import get_bounds_for_calendar_month
from learning.settings import CENTER_FOUNDATION_YEAR
from courses.settings import SemesterTypes
from learning.utils import get_term_index


class CourseTeacherQuerySet(query.QuerySet):
    def for_course(self, course_slug):
        course_pks = (self.model.course.field.related_model.objects
                         .filter(meta_course__slug=course_slug)
                         # Note: can't reset default ordering in a Subquery
                         .order_by("pk")
                         .values("pk"))
        return self.filter(course__in=Subquery(course_pks))


CourseTeacherManager = models.Manager.from_queryset(CourseTeacherQuerySet)


class AssignmentQuerySet(query.QuerySet):
    def list(self):
        return (self
                .only("title", "course_id", "is_online", "deadline_at")
                .prefetch_related("assignmentattachment_set")
                .order_by('deadline_at', 'title'))

    def with_progress(self, student):
        """Prefetch progress on assignments for student"""
        from learning.models import StudentAssignment
        qs = (StudentAssignment.objects
              .only("pk", "assignment_id", "score")
              .filter(student=student)
              .annotate(student_comments_cnt=Count(
                Case(When(assignmentcomment__author_id=student.pk,
                          then=Value(1)),
                     output_field=IntegerField())))
              .order_by("pk"))  # optimize by overriding default order
        return self.prefetch_related(
            Prefetch("studentassignment_set", queryset=qs))


AssignmentManager = models.Manager.from_queryset(AssignmentQuerySet)


class CourseClassQuerySet(query.QuerySet):
    # FIXME: Tests for club part!!!
    def for_calendar(self, user):
        q = (self
             .select_related('venue',
                             'course',
                             'course__meta_course',
                             'course__semester')
             .order_by('date', 'starts_at'))
        # Hide summer classes on compsciclub.ru if user not enrolled in
        # FIXME: Performance issue.
        if is_club_site():
            # XXX: On join enrollment table we get a lot of duplicates.
            # Clean them with right `.order` and `.distinct()`!
            summer_classes_enrolled_in = Q(
                course__is_open=True,
                course__semester__type=SemesterTypes.SUMMER,
                course__enrollment__student_id=user.pk,
                course__enrollment__is_deleted=False)
            others = (Q(course__is_open=True) &
                      ~Q(course__semester__type=SemesterTypes.SUMMER))
            q = q.filter(others)
        return q

    def in_city(self, city_code):
        return self.filter(Q(course__city_id=city_code,
                             course__is_correspondence=False) |
                           Q(course__is_correspondence=True))

    def in_cities(self, city_codes: List[str]):
        return self.filter(course__city_id__in=city_codes)

    def in_month(self, year, month):
        date_start, date_end = get_bounds_for_calendar_month(year, month)
        return self.filter(date__gte=date_start, date__lte=date_end)

    def open_only(self):
        return self.filter(course__is_open=True)

    def for_student(self, user):
        """More strict than in `.for_calendar`. Let DB optimize it later."""
        return self.filter(course__enrollment__student_id=user.pk,
                           course__enrollment__is_deleted=False)

    def for_teacher(self, user):
        return self.filter(course__teachers=user)


class _CourseDefaultManager(models.Manager):
    """On compsciclub.ru always restrict selection by open reading"""
    def get_queryset(self):
        # TODO: add test
        if is_club_site():
            return super().get_queryset().filter(is_open=True)
        else:
            return super().get_queryset()


class CourseQuerySet(models.QuerySet):
    def in_city(self, city_code):
        _q = {"is_correspondence": False}
        if isinstance(city_code, (list, tuple)):
            _q["city_id__in"] = city_code
        else:
            _q["city_id__exact"] = city_code
        return self.filter(Q(**_q) | Q(is_correspondence=True))

    def in_center_branches(self):
        return self.filter(city_id__in=settings.CENTER_BRANCHES_CITY_CODES)

    def for_teacher(self, user):
        return self.filter(teachers=user)

    def from_center_foundation(self):
        Semester = apps.get_model('courses', 'Semester')
        center_foundation_term_index = get_term_index(CENTER_FOUNDATION_YEAR,
                                                      SemesterTypes.AUTUMN)
        return self.filter(semester__index__gte=center_foundation_term_index)

    def get_offerings_base_queryset(self):
        """Returns list of available courses for CS Center"""
        User = apps.get_model('users', 'User')
        prefetch_teachers = Prefetch(
            'teachers',
            queryset=User.objects.only("id", "first_name", "last_name",
                                       "patronymic"))
        return (self
                .select_related('meta_course', 'semester')
                .only("pk", "city_id", "is_open",
                      "materials_video", "materials_slides", "materials_files",
                      "meta_course__name", "meta_course__slug",
                      "semester__year", "semester__index", "semester__type")
                .from_center_foundation()
                .prefetch_related(prefetch_teachers)
                .order_by('-semester__year', '-semester__index',
                          'meta_course__name'))

    def reviews_for_course(self, co):
        return (self
                .defer("description")
                .select_related("semester")
                .filter(meta_course_id=co.meta_course_id,
                        semester__index__lte=co.semester.index)
                .in_city(co.get_city())
                .exclude(reviews__isnull=True)
                .exclude(reviews__exact='')
                .order_by("-semester__index"))


CourseDefaultManager = _CourseDefaultManager.from_queryset(CourseQuerySet)