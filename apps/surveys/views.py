from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import FormView

from core.exceptions import Redirect
from core.urls import reverse
from courses.models import Course
from surveys.forms import FormBuilder
from surveys.models import CourseSurvey


class CourseSurveyDetailView(FormView):
    template_name = "surveys/survey_detail.html"

    def get_success_url(self):
        return reverse("surveys:form_success", kwargs=self.kwargs)

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        survey = get_object_or_404(
            (CourseSurvey.objects
             .select_related("form", "course",
                             "course__meta_course",
                             "course__semester")),
            course__meta_course__slug=self.kwargs['course_slug'],
            course__city_id=self.request.city_code,
            course__semester__year=self.kwargs['semester_year'],
            course__semester__type=self.kwargs['semester_type'],
            form__slug=self.kwargs["slug"])
        if not survey.is_published and not self.request.user.is_curator:
            raise Http404
        if not survey.is_active:
            msg = "Опрос окончен. Перенаправляем на страницу курса."
            messages.info(self.request, msg,
                          extra_tags='timeout')
            raise Redirect(to=survey.course.get_absolute_url())
        return FormBuilder(survey, **self.get_form_kwargs())

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        form.save()
        return super().form_valid(form)


form_detail = CourseSurveyDetailView.as_view()


def form_success(request, slug, **kwargs):
    co = get_object_or_404(
        Course.objects.filter(
            meta_course__slug=kwargs['course_slug'],
            city_id=request.city_code,
            semester__year=kwargs['semester_year'],
            semester__type=kwargs['semester_type']))
    return render(request, 'surveys/survey_success.html', context={
        "course": co
    })
