from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from core.widgets import AdminRelatedDropdownFilter
from surveys.models import Form, Field, FieldChoice, FormSubmission, FieldEntry, \
    CourseOfferingSurvey


class FormFieldAdmin(admin.StackedInline):
    model = Field
    exclude = ("description",)
    extra = 0


class FormAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "publish_at", "expire_at"]
    list_filter = ("status", "is_template")
    search_fields = ("title",)
    radio_fields = {"status": admin.HORIZONTAL}
    inlines = [FormFieldAdmin]
    prepopulated_fields = {
        "slug": ("title",)
    }


class CourseOfferingSurveyAdmin(admin.ModelAdmin):
    list_display = ["pk", "course_offering", "get_slug", "get_form_link"]
    list_filter = (
        'course_offering__city',
        ('course_offering__semester', AdminRelatedDropdownFilter),
    )
    raw_id_fields = ["course_offering"]
    exclude = ("form",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['form', 'type']
        return []

    def get_slug(self, obj):
        return obj.form.slug
    get_slug.short_description = _("Type")

    def get_form_link(self, obj):
        http_url = reverse("admin:surveys_form_change", args=[obj.form_id])
        return mark_safe(f"<a href='{http_url}'>{obj.form.title}</a>")
    get_form_link.short_description = _("Form")
    get_form_link.sa = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (qs.select_related("course_offering",
                                  "course_offering__course",
                                  "form"))


class FieldChoiceAdminInline(admin.TabularInline):
    model = FieldChoice
    extra = 0


class FieldAdmin(admin.ModelAdmin):
    list_display = ["label", "field_type", "form", "order"]
    list_filter = ("form__is_template",)
    search_fields = ("form__title", "label")
    raw_id_fields = ("form",)
    inlines = [FieldChoiceAdminInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (qs.select_related("form")
                .annotate(total_choices=Count("choices")))


class FieldChoiceAdmin(admin.ModelAdmin):
    list_display = ["label", "field"]
    raw_id_fields = ("field",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("field")


class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("form")


class FieldEntryAdmin(admin.ModelAdmin):
    list_display = ["field_id", "value"]


admin.site.register(Form, FormAdmin)
admin.site.register(CourseOfferingSurvey, CourseOfferingSurveyAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(FieldChoice, FieldChoiceAdmin)
admin.site.register(FormSubmission, FormSubmissionAdmin)
admin.site.register(FieldEntry, FieldEntryAdmin)
