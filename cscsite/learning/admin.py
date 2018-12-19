from __future__ import absolute_import, unicode_literals

from bitfield import BitField
from dal import autocomplete
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models as db_models
from django.utils.translation import ugettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from core.admin import CityAwareModelForm, CityAwareAdminSplitDateTimeWidget, \
    CityAwareSplitDateTimeField, RelatedSpecMixin
from core.compat import Django21BitFieldCheckboxSelectMultiple
from core.utils import admin_datetime, is_club_site
from core.widgets import AdminRichTextAreaWidget, AdminRelatedDropdownFilter
from learning.models import InternshipCategory
from learning.settings import AcademicRoles
from users.models import User
from .models import StudentAssignment, \
    AssignmentComment, Enrollment, NonCourseEvent, OnlineCourse, \
    InternationalSchool, Useful, Internship, AreaOfStudy, \
    StudyProgram, StudyProgramCourseGroup
from courses.models import MetaCourse, Course, Semester, CourseTeacher, \
    CourseNews, Venue, CourseClass, CourseClassAttachment, Assignment, \
    AssignmentAttachment


class AreaOfStudyAdmin(TranslationAdmin, admin.ModelAdmin):
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }


class StudyProgramCourseGroupInline(admin.TabularInline):
    model = StudyProgramCourseGroup
    extra = 0
    formfield_overrides = {
        db_models.ManyToManyField: {'widget': autocomplete.Select2Multiple()}
    }

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields['courses'].widget.can_add_related = False
        form.base_fields['courses'].widget.can_change_related = False
        return formset


class StudyProgramAdmin(admin.ModelAdmin):
    list_filter = ["city", "year"]
    list_display = ["area", "city", "year"]
    inlines = [StudyProgramCourseGroupInline]
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }


class MetaCourseAdmin(TranslationAdmin, admin.ModelAdmin):
    list_display = ['name_ru', 'name_en']
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }


class CourseTeacherInline(admin.TabularInline):
    model = CourseTeacher
    extra = 0
    min_num = 1
    formfield_overrides = {
            BitField: {'widget': Django21BitFieldCheckboxSelectMultiple},
    }

    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(groups__in=[
                AcademicRoles.TEACHER_CENTER,
                AcademicRoles.TEACHER_CLUB]).distinct()
        return super().formfield_for_foreignkey(db_field, *args, **kwargs)


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

    def clean_is_open(self):
        is_open = self.cleaned_data['is_open']
        if is_club_site() and not is_open:
            raise ValidationError(_("You can create only open courses "
                                    "from CS club site"))
        return is_open


class CourseAdmin(TranslationAdmin, admin.ModelAdmin):
    list_filter = ['city', 'semester']
    list_display = ['meta_course', 'semester', 'is_published_in_video',
                    'is_open']
    inlines = (CourseTeacherInline,)
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }
    form = CourseAdminForm


class CourseClassAttachmentAdmin(admin.ModelAdmin):
    list_filter = ['course_class']
    list_display = ['course_class', '__str__']


class CourseClassAttachmentInline(admin.TabularInline):
    model = CourseClassAttachment


class CourseClassAdmin(admin.ModelAdmin):
    save_as = True
    date_hierarchy = 'date'
    list_filter = ['type', 'venue']
    search_fields = ['course__meta_course__name']
    list_display = ['id', 'name', 'course', 'date', 'venue', 'type']
    inlines = [CourseClassAttachmentInline]
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'course':
            kwargs['queryset'] = (Course.objects
                                  .select_related("meta_course", "semester"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CourseNewsAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['title', 'course', 'created_local']
    raw_id_fields = ["course", "author"]
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }

    def created_local(self, obj):
        return admin_datetime(obj.created_local())
    created_local.admin_order_field = 'created'
    created_local.short_description = _("Created")


class VenueAdminForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = '__all__'
        widgets = {
            'description': AdminRichTextAreaWidget(),
            'flags': Django21BitFieldCheckboxSelectMultiple()
        }


class VenueAdmin(admin.ModelAdmin):
    form = VenueAdminForm
    list_display = ['name', 'city']
    list_select_related = ["city"]


class AssignmentAdminForm(CityAwareModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        # We can select teachers only from related course offering
        if ('course' in cleaned_data
                and 'notify_teachers' in cleaned_data
                and cleaned_data['notify_teachers']):
            co = cleaned_data['course']
            co_teachers = [t.pk for t in co.course_teachers.all()]
            if any(t.pk not in co_teachers for t in cleaned_data['notify_teachers']):
                self.add_error('notify_teachers', ValidationError(
                        _("Assignment|Please, double check teachers list. Some "
                          "of them not related to selected course offering")))


class AssignmentAttachmentAdmin(admin.ModelAdmin):
    raw_id_fields = ["assignment"]


class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentAdminForm
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
        db_models.DateTimeField: {
            'widget': CityAwareAdminSplitDateTimeWidget,
            'form_class': CityAwareSplitDateTimeField
        },
    }
    list_display = ['id', 'title', 'course', 'created_local',
                    'deadline_at_local']
    search_fields = ['course__meta_course__name']

    def get_readonly_fields(self, request, obj=None):
        return ['course'] if obj else []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'course':
            kwargs['queryset'] = (Course.objects
                                  .select_related("meta_course", "semester"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "notify_teachers":
            qs = (CourseTeacher.objects
                  .select_related("teacher", "course"))
            try:
                assignment_pk = request.resolver_match.args[0]
                a = (Assignment.objects
                     .prefetch_related("course__course_teachers")
                     .get(pk=assignment_pk))
                teachers = [t.pk for t in a.course.teachers.all()]
                qs = qs.filter(teacher__in=teachers,
                               course=a.course)
            except IndexError:
                pass
            kwargs["queryset"] = qs.order_by("course_id").distinct()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_related(self, request, form, formsets, change):
        if not change and not form.cleaned_data['notify_teachers']:
            co_teachers = form.cleaned_data['course'].course_teachers.all()
            form.cleaned_data['notify_teachers'] = [t.pk for t in co_teachers if t.notify_by_default]
        return super().save_related(request, form, formsets, change)

    def created_local(self, obj):
        return admin_datetime(obj.created_local())
    created_local.admin_order_field = 'created'
    created_local.short_description = _("Created")

    def deadline_at_local(self, obj):
        return admin_datetime(obj.deadline_at_local())
    deadline_at_local.admin_order_field = 'deadline_at'
    deadline_at_local.short_description = _("Assignment|deadline")


class AssignmentCommentAdmin(RelatedSpecMixin, admin.ModelAdmin):
    readonly_fields = ['student_assignment']
    list_display = ["get_assignment_name", "get_student", "author"]
    search_fields = ["student_assignment__assignment__title",
                     "student_assignment__assignment__id"]
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }
    related_spec = {
        'select': [
            ('student_assignment', [
                 ('assignment', [('course', ['semester', 'meta_course'])]),
                 'student'
             ]),
            'author'
        ]}

    def get_student(self, obj: AssignmentComment):
        return obj.student_assignment.student
    get_student.short_description = _("Assignment|assigned_to")

    def get_assignment_name(self, obj: AssignmentComment):
        return obj.student_assignment.assignment.title
    get_assignment_name.admin_order_field = 'student_assignment__assignment__title'
    get_assignment_name.short_description = _("Asssignment|name")


class EnrollmentAdmin(admin.ModelAdmin):
    form = CityAwareModelForm
    formfield_overrides = {
        db_models.DateTimeField: {
            'widget': CityAwareAdminSplitDateTimeWidget,
            'form_class': CityAwareSplitDateTimeField
        }
    }
    list_display = ['student', 'course', 'is_deleted', 'grade',
                    'grade_changed_local']
    ordering = ['-pk']
    list_filter = [
        'course__city_id',
        ('course__semester', AdminRelatedDropdownFilter)
    ]
    search_fields = ['course__meta_course__name']
    exclude = ['grade_changed']
    raw_id_fields = ["student", "course"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['student', 'course', 'grade_changed_local', 'modified']
        else:
            return ['grade_changed_local', 'modified']

    def grade_changed_local(self, obj):
        return admin_datetime(obj.grade_changed_local())
    grade_changed_local.admin_order_field = 'grade_changed'
    grade_changed_local.short_description = _("Enrollment|grade changed")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'student':
            kwargs['queryset'] = (get_user_model().objects
                                  .filter(groups__in=[
                                        AcademicRoles.STUDENT_CENTER,
                                        AcademicRoles.VOLUNTEER]))
        return (super(EnrollmentAdmin, self)
                .formfield_for_foreignkey(db_field, request, **kwargs))


class StudentAssignmentAdmin(RelatedSpecMixin, admin.ModelAdmin):
    list_display = ['student', 'assignment', 'score', 'score_changed', 'state']
    related_spec = {'select': [('assignment',
                                [('course', ['semester', 'meta_course'])]),
                               'student']}
    search_fields = ['student__last_name']
    raw_id_fields = ["assignment", "student"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['student', 'assignment', 'score_changed', 'state']
        else:
            return ['score_changed', 'state']


class NonCourseEventAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_filter = ['venue']
    list_display = ['name', 'date', 'venue']


class OnlineCourseAdmin(admin.ModelAdmin):
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }


class InternationalSchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'deadline', 'has_grants']
    formfield_overrides = {
        db_models.TextField: {'widget': AdminRichTextAreaWidget},
    }


class UsefulAdmin(admin.ModelAdmin):
    list_filter = ['site']
    list_display = ['question', 'sort']


class InternshipCategoryAdmin(admin.ModelAdmin):
    list_filter = ['site']
    list_display = ['name', 'sort']


class InternshipAdmin(admin.ModelAdmin):
    list_select_related = ['category']
    list_filter = ['category']
    list_editable = ['sort']
    list_display = ['category', 'question', 'sort']


admin.site.register(AreaOfStudy, AreaOfStudyAdmin)
admin.site.register(StudyProgram, StudyProgramAdmin)
admin.site.register(MetaCourse, MetaCourseAdmin)
admin.site.register(OnlineCourse, OnlineCourseAdmin)
admin.site.register(InternationalSchool, InternationalSchoolAdmin)
admin.site.register(Semester)
admin.site.register(Course, CourseAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(CourseClass, CourseClassAdmin)
admin.site.register(CourseClassAttachment, CourseClassAttachmentAdmin)
admin.site.register(CourseNews, CourseNewsAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(AssignmentAttachment, AssignmentAttachmentAdmin)
admin.site.register(StudentAssignment, StudentAssignmentAdmin)
admin.site.register(AssignmentComment, AssignmentCommentAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(NonCourseEvent, NonCourseEventAdmin)
admin.site.register(Useful, UsefulAdmin)
admin.site.register(InternshipCategory, InternshipCategoryAdmin)
admin.site.register(Internship, InternshipAdmin)
