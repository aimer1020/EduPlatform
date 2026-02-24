from rest_framework import permissions
from courses.models.interactionCourse_models import Enrollment


class IsTeacherOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only teachers to create/edit courses.
    Read-only access for everyone else.
    """

    message = "Only teachers can create or modify courses."

    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to teachers
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.user_type == "teacher"
        )


class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only students to enroll in courses.
    Read-only access for everyone else.
    """

    message = "Only students can enroll in courses."

    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to students
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.user_type == "student"
        )


class IsTeacherOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only teachers to modify their own courses.
    Read-only access for everyone else.
    """

    message = "Only the teacher who owns this course can modify it."

    def has_object_permission(self, request, view, obj):
        # Allow read-only access for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the teacher who owns the course
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or (
                request.user.user_type == "teacher"
                and obj.teacher.user_id == request.user.id
            )
        )


class IsStudentEnrolledOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only students enrolled in a course to access it.
    Read-only access for everyone else.
    """

    message = "You can only access your own enrollments."

    def has_object_permission(self, request, view, obj):
        # Allow staff or superuser to access all enrollments
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Students can only access their own enrollments
        return Enrollment.objects.filter(
            student__user_id=request.user.id, course_id=obj.id
        ).exists()


class IsStudentOrTeacher(permissions.BasePermission):
    """
    Permission that allows access only to authenticated students and teachers.
    """

    message = "You must be logged in as a student or teacher to access this resource."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.user_type in ["student", "teacher"]
        )


class IsTeacher(permissions.BasePermission):
    """
    Permission that allows access only to authenticated teachers.
    """

    message = "You must be logged in as a teacher to access this resource."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.user_type == "teacher"
        )


class IsStudent(permissions.BasePermission):
    """
    Permission that allows access only to authenticated students.
    """

    message = "You must be logged in as a student to access this resource."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.user_type == "student"
        )


class IsEnrollmentOwner(permissions.BasePermission):
    """
    Permission to allow only enrollment owners or staff to view/modify enrollments.
    """

    message = "You can only access your own enrollments."

    def has_object_permission(self, request, view, obj):
        # Allow staff or superuser to access all enrollments
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Students can only access their own enrollments
        if request.user.is_authenticated and request.user.user_type == "student":
            return obj.student.user_id == request.user.id

        # Teachers can access enrollments for their courses
        if request.user.is_authenticated and request.user.user_type == "teacher":
            return obj.course.teacher.user_id == request.user.id

        return False


class IsLessonCourseTeacherOrReadOnly(permissions.BasePermission):
    """
    Permission to allow only the course teacher to create/edit lessons.
    """

    message = "Only the course teacher can modify lessons."

    def has_object_permission(self, request, view, obj):
        # Allow read-only access for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for course teacher
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or obj.course.teacher.user_id == request.user.id
        )


class IsStudentAndOwnerProfile(permissions.BasePermission):
    """
    Permission to allow only students to access their own profiles.
    """

    message = "You can only access your own profile."

    def has_permission(self, request, view):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True

        if view.action == "create":
            if request.user and request.user.is_authenticated:
                return False
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user == request.user


class IsTeacherAndOwnerProfile(permissions.BasePermission):
    """
    Permission to allow only teachers to access their own profiles.
    """

    message = "You can only access your own profile."

    def has_permission(self, request, view):
        if request.user.is_staff or request.user.is_superuser:
            return True
        if view.action == "create":
            return False
        return request.user.is_authenticated and request.user.user_type == "teacher"

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user == request.user


class IsAuthenticated(permissions.BasePermission):
    """
    Permission to allow only authenticated users to access their own resources.
    """

    message = "You can only access your own resources."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsStudentOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "list":
            return request.user.is_authenticated and (
                request.user.is_staff or request.user.is_superuser
            )

        if view.action == "create":
            return request.user.is_authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return obj.student.user == request.user
