from djchoices import C, DjangoChoices

from django.apps import apps
from django.utils.translation import gettext_lazy as _

from auth.permissions import Role
from auth.registry import role_registry
from courses.permissions import (
    CreateAssignment, CreateCourseClass, CreateOwnAssignment, CreateOwnCourseClass,
    DeleteAssignment, DeleteAssignmentAttachment, DeleteAssignmentAttachmentAsTeacher,
    DeleteCourseClass, DeleteOwnAssignment, DeleteOwnCourseClass, EditAssignment,
    EditCourse, EditCourseClass, EditMetaCourse, EditOwnAssignment, EditOwnCourse,
    EditOwnCourseClass, ViewAssignment, ViewCourse, ViewCourseAssignments,
    ViewCourseClassMaterials, ViewCourseContacts, ViewCourseContactsAsLearner,
    ViewCourseContactsAsTeacher, ViewCourseInternalDescription,
    ViewCourseInternalDescriptionAsLearner, ViewCourseInternalDescriptionAsTeacher,
    ViewOwnAssignment, ViewCourseAsInvited
)
from info_blocks.permissions import ViewInternships
from users.permissions import (
    CreateCertificateOfParticipation, ViewAccountConnectedServiceProvider,
    ViewCertificateOfParticipation
)

from .permissions import (
    AccessTeacherSection, CreateAssignmentComment, CreateAssignmentCommentAsLearner,
    CreateAssignmentCommentAsTeacher, CreateAssignmentSolution, CreateCourseNews,
    CreateOwnAssignmentSolution, CreateOwnCourseNews, CreateStudentGroup,
    CreateStudentGroupAsTeacher, DeleteCourseNews, DeleteOwnCourseNews,
    DeleteStudentGroup, DeleteStudentGroupAsTeacher, DownloadAssignmentSolutions,
    EditCourseNews, EditGradebook, EditOwnAssignmentExecutionTime, EditOwnCourseNews,
    EditOwnGradebook, EditOwnStudentAssignment, EditStudentAssignment, EnrollInCourse,
    EnrollInCourseByInvitation, LeaveCourse, UpdateStudentGroup,
    UpdateStudentGroupAsTeacher, ViewAssignmentAttachment,
    ViewAssignmentAttachmentAsLearner, ViewAssignmentAttachmentAsTeacher,
    ViewAssignmentCommentAttachment, ViewAssignmentCommentAttachmentAsLearner,
    ViewAssignmentCommentAttachmentAsTeacher, ViewCourseEnrollment,
    ViewCourseEnrollments, ViewCourseNews, ViewCourseReviews, ViewCourses,
    ViewEnrollment, ViewEnrollments, ViewFAQ, ViewGradebook, ViewLibrary,
    ViewOwnEnrollment, ViewOwnEnrollments, ViewOwnGradebook, ViewOwnStudentAssignment,
    ViewOwnStudentAssignments, ViewRelatedStudentAssignment, ViewSchedule,
    ViewStudentAssignment, ViewStudentAssignmentList, ViewStudentGroup,
    ViewStudentGroupAsTeacher, ViewStudyMenu, ViewTeachingMenu
)


# TODO: Add description to each role
class Roles(DjangoChoices):
    CURATOR = C(5, _('Curator'), priority=0, permissions=(
        AccessTeacherSection,
        ViewAccountConnectedServiceProvider,
        ViewCourse,
        ViewCourseInternalDescription,
        EditCourse,
        CreateCertificateOfParticipation,
        ViewCertificateOfParticipation,
        EditMetaCourse,
        CreateAssignment,
        EditAssignment,
        ViewAssignment,
        DeleteAssignment,
        ViewCourseContacts,
        ViewCourseAssignments,
        ViewStudentAssignment,
        ViewStudentAssignmentList,
        EditStudentAssignment,
        CreateCourseClass,
        EditCourseClass,
        DeleteCourseClass,
        ViewCourseNews,
        CreateCourseNews,
        EditCourseNews,
        DeleteCourseNews,
        ViewCourseReviews,
        ViewLibrary,
        ViewEnrollments,
        ViewEnrollment,
        CreateAssignmentCommentAsTeacher,
        ViewGradebook,
        EditGradebook,
        CreateAssignmentComment,
        CreateAssignmentSolution,
        DownloadAssignmentSolutions,
        ViewAssignmentAttachment,
        DeleteAssignmentAttachment,
        ViewAssignmentCommentAttachment,
        ViewStudentGroup,
        UpdateStudentGroup,
        DeleteStudentGroup,
        CreateStudentGroup,
    ))
    STUDENT = C(1, _('Student'), priority=50, permissions=(
        ViewCourse,
        ViewCourseInternalDescriptionAsLearner,
        ViewStudyMenu,
        ViewCourseContactsAsLearner,
        ViewCourseAssignments,
        ViewCourseNews,
        ViewCourseReviews,
        ViewOwnEnrollments,
        ViewOwnEnrollment,
        ViewOwnStudentAssignments,
        ViewOwnStudentAssignment,
        ViewAssignmentAttachmentAsLearner,
        CreateAssignmentCommentAsLearner,
        CreateOwnAssignmentSolution,
        ViewAssignmentCommentAttachmentAsLearner,
        EditOwnAssignmentExecutionTime,
        ViewCourses,
        ViewSchedule,
        ViewFAQ,
        ViewLibrary,
        ViewInternships,
        EnrollInCourse,
        EnrollInCourseByInvitation,
        LeaveCourse,
    ))
    VOLUNTEER = C(4, _('Co-worker'), priority=50,
                  permissions=STUDENT.permissions)
    PARTNER = C(13, _("Master's Degree Student"), priority=50,
                permissions=STUDENT.permissions)
    INVITED = C(11, _('Invited User'), permissions=(
        ViewCourseAsInvited,
        ViewCourseInternalDescriptionAsLearner,
        ViewStudyMenu,
        ViewCourseContactsAsLearner,
        ViewCourseAssignments,
        ViewCourseNews,
        ViewCourseReviews,
        ViewOwnEnrollments,
        ViewOwnEnrollment,
        ViewOwnStudentAssignments,
        ViewOwnStudentAssignment,
        ViewAssignmentAttachmentAsLearner,
        CreateAssignmentCommentAsLearner,
        CreateOwnAssignmentSolution,
        ViewAssignmentCommentAttachmentAsLearner,
        ViewCourses,
        ViewSchedule,
        ViewFAQ,
        ViewLibrary,
        ViewInternships,
        EnrollInCourseByInvitation,
        LeaveCourse,
    ))
    GRADUATE = C(3, _('Graduate'), permissions=(
        ViewCourse,
        ViewCourseContactsAsLearner,
        ViewCourseInternalDescriptionAsLearner,
        ViewOwnEnrollments,
        ViewOwnEnrollment,
        ViewOwnStudentAssignment,
        ViewAssignmentAttachmentAsLearner,
        ViewAssignmentCommentAttachmentAsLearner,
    ))
    TEACHER = C(2, _('Teacher'), priority=30, permissions=(
        ViewTeachingMenu,
        AccessTeacherSection,
        ViewCourse,
        ViewCourseInternalDescriptionAsTeacher,
        EditOwnCourse,
        ViewCourseContactsAsTeacher,
        ViewCourseNews,
        CreateOwnCourseNews,
        EditOwnCourseNews,
        DeleteOwnCourseNews,
        CreateOwnAssignment,
        EditOwnAssignment,
        ViewOwnAssignment,
        DeleteOwnAssignment,
        ViewCourseAssignments,
        ViewRelatedStudentAssignment,
        ViewStudentAssignmentList,
        EditOwnStudentAssignment,
        CreateOwnCourseClass,
        EditOwnCourseClass,
        DeleteOwnCourseClass,
        ViewCourseEnrollments,
        ViewCourseEnrollment,
        ViewAssignmentAttachmentAsTeacher,
        CreateAssignmentCommentAsTeacher,
        ViewAssignmentCommentAttachmentAsTeacher,
        DeleteAssignmentAttachmentAsTeacher,
        ViewOwnGradebook,
        EditOwnGradebook,
        ViewStudentGroupAsTeacher,
        UpdateStudentGroupAsTeacher,
        DeleteStudentGroupAsTeacher,
        CreateStudentGroupAsTeacher,
    ))


for code, name in Roles.choices:
    choice = Roles.get_choice(code)
    role = Role(id=code, code=code, description=name,
                priority=getattr(choice, 'priority', 100),
                permissions=choice.permissions)
    role_registry.register(role)

# Add relations
teacher_role = role_registry[Roles.TEACHER]
teacher_role.add_relation(ViewCourseContacts,
                          ViewCourseContactsAsTeacher)
teacher_role.add_relation(ViewCourseInternalDescription,
                          ViewCourseInternalDescriptionAsTeacher)
teacher_role.add_relation(EditCourse,
                          EditOwnCourse)
teacher_role.add_relation(ViewAssignmentAttachment,
                          ViewAssignmentAttachmentAsTeacher)
teacher_role.add_relation(DeleteAssignmentAttachment,
                          DeleteAssignmentAttachmentAsTeacher)
teacher_role.add_relation(CreateAssignmentComment,
                          CreateAssignmentCommentAsTeacher)
teacher_role.add_relation(ViewAssignmentCommentAttachment,
                          ViewAssignmentCommentAttachmentAsTeacher)
teacher_role.add_relation(ViewStudentAssignment, ViewRelatedStudentAssignment)
teacher_role.add_relation(EditStudentAssignment, EditOwnStudentAssignment)
teacher_role.add_relation(CreateCourseClass, CreateOwnCourseClass)
teacher_role.add_relation(EditCourseClass, EditOwnCourseClass)
teacher_role.add_relation(DeleteCourseClass, DeleteOwnCourseClass)
teacher_role.add_relation(CreateCourseNews, CreateOwnCourseNews)
teacher_role.add_relation(EditCourseNews, EditOwnCourseNews)
teacher_role.add_relation(DeleteCourseNews, DeleteOwnCourseNews)
teacher_role.add_relation(CreateAssignment, CreateOwnAssignment)
teacher_role.add_relation(EditAssignment, EditOwnAssignment)
teacher_role.add_relation(ViewAssignment, ViewOwnAssignment)
teacher_role.add_relation(DeleteAssignment, DeleteOwnAssignment)
teacher_role.add_relation(ViewEnrollments, ViewCourseEnrollments)
teacher_role.add_relation(ViewGradebook, ViewOwnGradebook)
teacher_role.add_relation(EditGradebook, EditOwnGradebook)
teacher_role.add_relation(ViewStudentGroup, ViewStudentGroupAsTeacher)
teacher_role.add_relation(CreateStudentGroup, CreateStudentGroupAsTeacher)
teacher_role.add_relation(DeleteStudentGroup, DeleteStudentGroupAsTeacher)
teacher_role.add_relation(UpdateStudentGroup, UpdateStudentGroupAsTeacher)
teacher_role.add_relation(ViewEnrollment, ViewCourseEnrollment)


for role in (Roles.STUDENT, Roles.VOLUNTEER, Roles.PARTNER, Roles.INVITED):
    student_role = role_registry[role]
    student_role.add_relation(ViewAssignmentAttachment,
                              ViewAssignmentAttachmentAsLearner)
    student_role.add_relation(ViewCourseContacts,
                              ViewCourseContactsAsLearner)
    student_role.add_relation(ViewCourseInternalDescription,
                              ViewCourseInternalDescriptionAsLearner)
    student_role.add_relation(CreateAssignmentComment,
                              CreateAssignmentCommentAsLearner)
    student_role.add_relation(CreateAssignmentSolution,
                              CreateOwnAssignmentSolution)
    student_role.add_relation(ViewAssignmentCommentAttachment,
                              ViewAssignmentCommentAttachmentAsLearner)
    student_role.add_relation(ViewEnrollment,
                              ViewOwnEnrollment)

invited_role = role_registry[Roles.INVITED]
invited_role.add_relation(ViewCourse,
                          ViewCourseAsInvited)

graduate_role = role_registry[Roles.GRADUATE]
graduate_role.add_relation(ViewAssignmentAttachment, ViewAssignmentAttachmentAsLearner)
graduate_role.add_relation(ViewAssignmentCommentAttachment, ViewAssignmentCommentAttachmentAsLearner)
graduate_role.add_relation(ViewCourseContacts, ViewCourseContactsAsLearner)
graduate_role.add_relation(ViewCourseInternalDescription, ViewCourseInternalDescriptionAsLearner)
graduate_role.add_relation(ViewEnrollment, ViewOwnEnrollment)

anonymous_role = role_registry.anonymous_role
anonymous_role.add_permission(ViewCourseClassMaterials)


# TODO: Write util method to view all role permissions, register global roles
#  like student, teacher, curator with `core` (or `lms`) app, then move
#  code below to the `projects` app
if apps.is_installed('projects'):
    from projects.permissions import (
        ViewReportAttachment, ViewReportAttachmentAsLearner,
        ViewReportCommentAttachment, ViewReportCommentAttachmentAsLearner
    )

    curator_role = role_registry[Roles.CURATOR]
    curator_role.add_permission(ViewReportAttachment)
    curator_role.add_permission(ViewReportCommentAttachment)

    for role in (Roles.STUDENT, Roles.VOLUNTEER, Roles.PARTNER):
        student_role = role_registry[role]
        # Permissions
        student_role.add_permission(ViewReportAttachmentAsLearner)
        student_role.add_permission(ViewReportCommentAttachmentAsLearner)
        # Relations
        student_role.add_relation(ViewReportAttachment,
                                  ViewReportAttachmentAsLearner)
        student_role.add_relation(ViewReportCommentAttachment,
                                  ViewReportCommentAttachmentAsLearner)
