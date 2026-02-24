from rest_framework import viewsets, status
from rest_framework.response import Response
from users.permissions import (
    IsStudent,
    IsEnrollmentOwner,
    IsAuthenticated,
    IsStudentOrAdmin,
)
from courses.models.interactionCourse_models import Enrollment, Review
from ..Serializers.interactionCourse_serializers import (
    CourseEnrollmentCreateSerializer,
    CourseEnrollmentDetailSerializer,
    CourseEnrollmentListSerializer,
    CourseReviewCreateSerializer,
    CourseReviewSerializer,
)


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [IsStudent()]
        return [IsEnrollmentOwner()]

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CourseEnrollmentCreateSerializer
        elif self.action == "retrieve":
            return CourseEnrollmentDetailSerializer
        elif self.action == "list":
            return CourseEnrollmentListSerializer
        else:
            return CourseEnrollmentListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Enrollment.objects.select_related(
            "course", "course__teacher", "student__user"
        ).filter(status__in=[Enrollment.STATUS_ACTIVE, Enrollment.STATUS_COMPLETED])
        if user.is_staff or user.is_superuser:
            return queryset
        elif user.user_type == "student":
            return queryset.filter(student__user=user)
        elif user.user_type == "teacher":
            return queryset.filter(course__teacher__user=user)

        return queryset.none()

    def destroy(self, request, *args, **kwargs):
        """
        Instead of deleting the enrollment, we will mark it as cancelled (soft delete).
        """
        instance = self.get_object()

        if instance.status in [Enrollment.STATUS_CANCELLED, Enrollment.STATUS_REFUNDED]:
            return Response(
                {"detail": "enrollment is already cancelled or refunded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.cancel(reason="User requested cancellation")

        return Response(
            {"detail": "enrollment has been successfully cancelled"},
            status=status.HTTP_204_NO_CONTENT,
        )


class CourseReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStudentOrAdmin]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CourseReviewCreateSerializer
        return CourseReviewSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Review.objects.select_related("student__user", "course")

        if user.is_staff or user.is_superuser:
            return queryset

        if hasattr(user, "user_type") and user.user_type == "student":
            return queryset.filter(student__user=user)
        elif hasattr(user, "user_type") and user.user_type == "teacher":
            return queryset.filter(course__teacher__user=user)

        return queryset.none()
