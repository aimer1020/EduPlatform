from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Teacher, Student
from .serializers import (
    TeacherlistSerializer,
    TeacherDetailSerializer,
    StudentlistSerializer,
    StudentDetailSerializer,
    StudentCreateUpdateSerializer,
    teacherCreateUpdateSerializer,
)
from .permissions import (
    IsStudentAndOwnerProfile,
    IsTeacherAndOwnerProfile,
)


class TeacherViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsTeacherAndOwnerProfile
    ]  # Set appropriate permissions for teachers

    def get_serializer_class(self):
        if self.action == "list":
            return TeacherlistSerializer
        elif self.action == "retrieve":
            return TeacherDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return teacherCreateUpdateSerializer
        else:
            return TeacherDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Teacher.objectsqueryset.none()
        queryset = Teacher.objects.select_related("user").all()
        if user.is_staff or user.is_superuser:
            return queryset
        elif user.user_type == "teacher":
            return queryset.filter(user=user)
        return queryset.none()


class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsStudentAndOwnerProfile
    ]  # Set appropriate permissions for students

    def get_serializer_class(self):
        if self.action == "list":
            return StudentlistSerializer
        elif self.action == "retrieve":
            return StudentDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return StudentCreateUpdateSerializer
        else:
            return StudentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Student.objects.none()
        queryset = Student.objects.select_related("user").all()
        if user.is_staff or user.is_superuser:
            return queryset
        elif user.user_type == "teacher":
            return queryset.filter(enrollments__course__teacher__user=user).distinct()
        elif user.user_type == "student":
            return queryset.filter(user=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        # Debugging: Log the incoming request data
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Incoming request data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Debugging: Log serializer errors if any
        if serializer.errors:
            logger.debug(f"Serializer errors: {serializer.errors}")

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
