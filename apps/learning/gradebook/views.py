import csv
import itertools
from typing import Optional

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Prefetch
from django.http import HttpResponseRedirect, Http404, HttpResponse, \
    HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from vanilla import FormView

from courses.models import Course, Semester, Assignment
from courses.settings import SemesterTypes
from courses.utils import get_current_term_pair, get_term_index
from learning.gradebook import GradeBookFormFactory, gradebook_data
from learning.gradebook.imports import AssignmentGradesImport
from users.mixins import TeacherOnlyMixin

__all__ = [
    "GradeBookTeacherView",
    "GradeBookTeacherCSVView", "AssignmentScoresImportByStepikIDView",
    "AssignmentScoresImportByYandexLoginView"
]


class GradeBookListBaseView(generic.ListView):
    model = Semester

    def get_course_queryset(self):
        return (Course.objects
                .select_related("meta_course")
                .order_by("meta_course__name"))

    def get_queryset(self):
        # FIXME: Is it ok to use 'spb' here?
        current_year, term_type = get_current_term_pair('spb')
        term_index = get_term_index(current_year, term_type)
        # Skip to the spring semester
        # FIXME: why?!
        if term_type == SemesterTypes.AUTUMN:
            spring_order = SemesterTypes.get_choice(SemesterTypes.SPRING).order
            autumn_order = SemesterTypes.get_choice(SemesterTypes.AUTUMN).order
            # How many terms between spring and autumn
            spring_autumn_gap = autumn_order - spring_order - 1
            term_index += spring_autumn_gap
        return (Semester.objects
                .filter(index__lte=term_index)
                .exclude(type=SemesterTypes.SUMMER)
                .prefetch_related(
                    Prefetch(
                        "course_set",
                        queryset=self.get_course_queryset(),
                        to_attr="courseofferings"
                    )))


def _get_course(get_params, user) -> Optional[Course]:
    try:
        filter_kwargs = dict(
            city=get_params['city'].lower(),
            meta_course__slug=get_params['course_slug'],
            semester__type=get_params['semester_type'],
            semester__year=int(get_params['semester_year'])
        )
        if not user.is_curator:
            filter_kwargs["teachers"] = user
        return (Course.objects
                .select_related('semester', 'meta_course')
                .get(**filter_kwargs))
    except (ValueError, KeyError, AttributeError, ObjectDoesNotExist):
        return None


class GradeBookTeacherView(TeacherOnlyMixin, FormView):
    is_for_staff = False
    user_type = 'teacher'
    template_name = "learning/gradebook/form.html"
    context_object_name = 'assignment_list'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.course = None
        self.is_for_staff = kwargs.get('is_for_staff', False)

    def get_form(self, data=None, files=None, **kwargs):
        cls = self.get_form_class()
        # Set initial data for all GET-requests
        if not data and "initial" not in kwargs:
            initial = GradeBookFormFactory.transform_to_initial(self.data)
            kwargs["initial"] = initial
        return cls(data=data, files=files, **kwargs)

    def get_form_class(self):
        if self.course is None:
            self.course = _get_course(self.kwargs, self.request.user)
        if self.course is None:
            raise Http404('Course offering not found')
        self.data = gradebook_data(self.course)
        return GradeBookFormFactory.build_form_class(self.data)

    def form_valid(self, form):
        conflicts_on_save = form.save()
        if conflicts_on_save:
            msg = _("<b>Внимание, часть данных не была сохранена!</b><br>"
                    "В процессе редактирования данные были "
                    "изменены другими участниками. Необходимо вручную "
                    "разрешить конфликты и повторить отправку формы.")
            messages.warning(self.request, msg)
            # Replace form data with actual db values and user input
            # for conflict fields
            self.data = gradebook_data(self.course)
            current_data = GradeBookFormFactory.transform_to_initial(self.data)
            data = form.data.copy()
            for k, v in current_data.items():
                if k not in data:
                    data[k] = v
            form.data = data
            return super().form_invalid(form)
        return redirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request,
                         _('Gradebook successfully saved.'),
                         extra_tags='timeout')
        return self.data.course.get_gradebook_url(for_curator=self.is_for_staff)

    def form_invalid(self, form):
        """
        Append initial to form.data since we didn't sent full image of
        form data in POST-request, but only changed data
        """
        msg = _("Gradebook hasn't been saved.")
        messages.error(self.request, msg)
        initial = GradeBookFormFactory.transform_to_initial(self.data)
        data = form.data.copy()
        for k, v in initial.items():
            if k not in data:
                data[k] = v
        form.data = data
        return super().form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gradebook"] = self.data
        # List of user gradebooks
        # TODO: Move to the model
        filter_kwargs = {}
        if not self.request.user.is_curator:
            filter_kwargs["teachers"] = self.request.user
        courses = (Course.objects
                   .filter(**filter_kwargs)
                   .order_by('-semester__index',
                             '-pk')
                   .select_related('semester', 'meta_course'))
        context['course_offering_list'] = courses
        context['user_type'] = self.user_type

        return context


class GradeBookTeacherCSVView(TeacherOnlyMixin, generic.base.View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        course = _get_course(self.kwargs, request.user)
        if course is None:
            raise Http404('Course not found')

        data = gradebook_data(course)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = "{}-{}-{}.csv".format(kwargs['course_slug'],
                                         kwargs['semester_year'],
                                         kwargs['semester_type'])
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            filename)

        writer = csv.writer(response)
        writer.writerow(data.get_headers())
        for student in data.students.values():
            writer.writerow(
                itertools.chain(
                    [student.last_name,
                     student.first_name,
                     student.final_grade_display,
                     student.total_score],
                    [(a.score if a and a.score is not None else '')
                     for a in data.submissions[student.index]]))
        return response


class AssignmentGradesImportBaseView(TeacherOnlyMixin, generic.View):
    def post(self, request, course_id, *args, **kwargs):
        try:
            assignment_id = int(request.POST['assignment'])
            csv_file = request.FILES['csv_file']
        except (MultiValueDictKeyError, ValueError, TypeError):
            return HttpResponseBadRequest()
        filters = {
            "pk": assignment_id,
            "course_id": course_id,
            "is_online": False
        }
        if not request.user.is_curator:
            filters['course__teachers__id'] = request.user.pk
        try:
            assignment = (Assignment.objects
                          .select_related("course")
                          .get(**filters))
        except Assignment.DoesNotExist:
            return HttpResponseForbidden()
        try:
            total, success = self.import_grades_for_assignment(assignment)
            messages.info(self.request,
                          _("Successfully imported {} results").format(success))
        except ValidationError as e:
            messages.error(self.request, e.message)
        url = assignment.course.get_gradebook_url()
        return HttpResponseRedirect(url)

    def import_grades_for_assignment(self, assignment):
        raise NotImplementedError()


class AssignmentScoresImportByStepikIDView(AssignmentGradesImportBaseView):
    def import_grades_for_assignment(self, assignment):
        csv_file = self.request.FILES['csv_file']
        return AssignmentGradesImport(assignment, csv_file, "stepic_id").process()


class AssignmentScoresImportByYandexLoginView(AssignmentGradesImportBaseView):
    def import_grades_for_assignment(self, assignment):
        csv_file = self.request.FILES['csv_file']
        return AssignmentGradesImport(assignment, csv_file, "yandex_id").process()