from rest_framework import serializers
from ..models import Enrollment, Review
from django.utils.translation import gettext_lazy as _


class CourseEnrollmentDetailSerializer(serializers.ModelSerializer):
    course_info = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course_info",
            "status",
            "price_paid",
            "enrolled_at",
            "activated_at",
            "completion_percentage",
            "transaction_id",
        ]

    def get_course_info(self, obj):
        course = obj.course
        return {
            "name": course.title,
            "teacher_name": (
                course.teacher.user.get_full_name() if course.teacher else None
            ),
            "course_img": course.course_img.url if course.course_img else None,
            "subject": course.subject.name if course.subject else None,
        }


class CourseEnrollmentListSerializer(serializers.ModelSerializer):
    student_name = serializers.StringRelatedField(source="student.user", read_only=True)
    course_title = serializers.StringRelatedField(source="course", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student_name", "course_title", "status", "enrolled_at"]


class CourseEnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "payment_method",
            "coupon_code",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        course = attrs.get("course")
        user = self.context["request"].user

        if not hasattr(user, "student_profile"):
            raise serializers.ValidationError(_("User must be a student to enroll."))

        student = user.student_profile

        if not self.instance:
            existing = Enrollment.objects.filter(
                student=student, course=course
            ).exclude(
                status__in=[Enrollment.STATUS_CANCELLED, Enrollment.STATUS_REFUNDED]
            )

            if existing.exists():
                raise serializers.ValidationError(
                    _("You are already enrolled in this course.")
                )

        if not course.is_active or not course.is_published:
            raise serializers.ValidationError(
                _("This course is not available for enrollment.")
            )

        return attrs

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user.student_profile
        return super().create(validated_data)


class CourseReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.StringRelatedField(source="student.user", read_only=True)
    course_name = serializers.StringRelatedField(source="course", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "student_name",
            "course_name",
            "rating",
            "created_at",
        ]


class CourseReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "course",
            "rating",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        course = attrs.get("course")
        user = self.context["request"].user

        if user.is_staff or user.is_superuser:
            return attrs

        if not hasattr(user, "student_profile"):
            raise serializers.ValidationError(_("User must be a student to review."))

        student = user.student_profile

        has_enrollment = student.my_enrollments.filter(
            course=course,
            status__in=[Enrollment.STATUS_ACTIVE, Enrollment.STATUS_COMPLETED],
        ).exists()

        if not has_enrollment:
            raise serializers.ValidationError(
                _(
                    "You must have an active or completed enrollment to review this course."
                )
            )

        if Review.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError(
                _("You have already reviewed this course.")
            )

        return attrs

    def validate_course(self, value):
        if not (value.is_active or value.is_published):
            raise serializers.ValidationError(
                _("Cannot review an inactive or unpublished course.")
            )
        return value

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user.student_profile
        return super().create(validated_data)
