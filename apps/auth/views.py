from braces.views import LoginRequiredMixin
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.views import generic
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from core.urls import reverse
from auth.forms import UserPasswordResetForm, LoginForm
from users.constants import Roles
from users.models import User
from auth.tasks import EMAIL_RESTORE_PASSWORD_TEMPLATE, subject_template_name


class LoginView(generic.FormView):
    redirect_field_name = auth.REDIRECT_FIELD_NAME
    form_class = LoginForm
    template_name = "login.html"

    @method_decorator(never_cache)
    @method_decorator(sensitive_post_parameters('password'))
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        auth.login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_next"] = (self.redirect_field_name in self.request.POST
                               or self.redirect_field_name in self.request.GET)
        return context

    def get_success_url(self):
        redirect_to = self.request.GET.get(self.redirect_field_name)

        if not redirect_to:
            user_roles = self.request.user.roles
            if user_roles == {Roles.STUDENT}:
                redirect_to = reverse("study:assignment_list")
            elif user_roles == {Roles.TEACHER}:
                redirect_to = reverse("teaching:assignment_list")

        if not is_safe_url(redirect_to,
                           allowed_hosts={self.request.get_host()}):
            redirect_to = settings.LOGOUT_REDIRECT_URL

        return redirect_to

    def get(self, request, *args, **kwargs):
        self.request.session.set_test_cookie()
        return super(LoginView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            if self.request.session.test_cookie_worked():
                self.request.session.delete_test_cookie()
            return self.form_valid(form)
        else:
            self.request.session.set_test_cookie()
            return self.form_invalid(form)


class LogoutView(LoginRequiredMixin, generic.RedirectView):
    redirect_field_name = auth.REDIRECT_FIELD_NAME

    def get(self, request, *args, **kwargs):
        # FIXME: enable after bugfix in django-loginas
        # restore_original_login(request)
        auth.logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        redirect_to = settings.LOGOUT_REDIRECT_URL

        if self.redirect_field_name in self.request.GET:
            maybe_redirect_to = self.request.GET[self.redirect_field_name]
            if is_safe_url(maybe_redirect_to,
                           allowed_hosts={self.request.get_host()}):
                redirect_to = maybe_redirect_to

        return redirect_to


pass_reset_view = views.PasswordResetView.as_view(
    form_class=UserPasswordResetForm,
    email_template_name=EMAIL_RESTORE_PASSWORD_TEMPLATE,
    html_email_template_name=None,
    subject_template_name=subject_template_name)