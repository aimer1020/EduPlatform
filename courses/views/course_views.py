from rest_framework import viewsets, status
from rest_framework.response import Response

from ..models.course_models import Course
from ..Serializers.course_serializers import (
    CourseCreateUpdateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
)
from users.permissions import (
    IsTeacherOrReadOnly,
    IsTeacherOwnerOrReadOnly,
)


class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTeacherOrReadOnly, IsTeacherOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        elif self.action == "retrieve":
            return CourseDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer  # Default serializer

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.select_related("education", "teacher", "subject")

        if self.action == "list":
            if user.is_authenticated and user.user_type == "teacher":
                return queryset.filter(teacher__user=user)
            return queryset.filter(is_published=True, is_active=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher_profile)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    # def enroll(self, request, pk=None):
    #     course = self.get_object()
    #     user = request.user

    #     # Check if the user is already enrolled
    #     if Enrollment.objects.filter(course=course, student=user).exists():
    #         return Response(
    # {'detail': 'You are already enrolled in this course.'},
    # status=status.HTTP_400_BAD_REQUEST)

    #     # Create the enrollment
    #     Enrollment.objects.create(course=course, student=user)
    #     return Response(
    # {'detail': 'Enrollment successful.'},
    # status=status.HTTP_201_CREATED)
    # @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    # def unenroll(self, request, pk=None):
    #     course = self.get_object()
    #     user = request.user

    #     # Check if the user is enrolled
    #     enrollment = Enrollment.objects.filter(
    # course=course, student=user).first()
    #     if not enrollment:
    #         return Response(
    # {'detail': 'You are not enrolled in this course.'},
    # status=status.HTTP_400_BAD_REQUEST)

    #     # Delete the enrollment
    #     enrollment.delete()
    #     return Response(
    # {'detail': 'Unenrollment successful.'},
    # status=status.HTTP_200_OK)
