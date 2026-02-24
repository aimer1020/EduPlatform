from pydantic_core import ValidationError
from rest_framework import serializers
from ..models.course_models import Course, Education, Subject
from django.utils.translation import gettext_lazy as _
from ..validators import (
    MAX_COURSE_PRICE,
    MIN_COURSE_PRICE,
    validate_image_size,
    validate_image_dimensions,
)


class EducationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = "__all__"


class EducationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "title",
            "description",
            "price",
            "education_img",
            "is_published",
        ]


class SubjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class SubjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "description"]


class CourseDetailSerializer(serializers.ModelSerializer):
    teacher_info = serializers.SerializerMethodField()
    education_name = serializers.ReadOnlyField(source="education.country")
    subject_name = serializers.ReadOnlyField(source="subject.name")

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "teacher_info",
            "subject_name",
            "education_name",
            "description",
            "price",
            "course_img",
            "subject",
            "enrollment_count",
            "review_count",
            "average_rating",
            "created_at",
        ]

    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                "name": str(obj.teacher),
                "experience_years": obj.teacher.experience_years,
            }
        return None


class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.StringRelatedField(read_only=True, source="teacher")

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "price",
            "subject",
            "teacher_name",
        ]


class CourseCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = [
            "id",
            "education",
            "subject",
            "title",
            "description",
            "price",
            "course_img",
            "is_published",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        if user.is_staff or user.is_superuser:
            return attrs

        if self.instance and (
            (not (user.is_staff or user.is_superuser))
            or getattr(user, "user_type", None) == "student"
        ):
            raise serializers.ValidationError(
                _("Students are not allowed to update courses.")
            )

        is_active = attrs.get(
            "is_active", self.instance.is_active if self.instance else True
        )
        is_published = attrs.get(
            "is_published", self.instance.is_published if self.instance else False
        )

        if not is_active and is_published:
            raise serializers.ValidationError(
                {"is_published": _("Cannot publish a course that is not active.")}
            )
        return attrs

    def validate_price(self, value):
        if value < MIN_COURSE_PRICE or value > MAX_COURSE_PRICE:
            raise serializers.ValidationError(
                _("Price must be between {min_price} and {max_price} EGP.").format(
                    min_price=MIN_COURSE_PRICE, max_price=MAX_COURSE_PRICE
                )
            )
        return value

    def validate_title(self, value):
        if value.isdigit():
            raise serializers.ValidationError(_("Title cannot be purely numeric."))
        return value

    def validate_course_img(self, value):
        if value:
            validate_image_size(value)
            validate_image_dimensions(value)

            if not value.name.lower().endswith((".jpg", ".jpeg", ".png")):
                raise serializers.ValidationError(
                    _("Unsupported file extension. Allowed: .jpg, .jpeg, .png")
                )
        return value

    def validate_teacher(self, value):
        # Ensure teacher is verified
        if not value.is_verified:
            raise ValidationError(
                {"teacher": _("Only verified teachers can create courses.")}
            )
        return value

    def validate_education(self, value):
        # Ensure education system is active
        if not value.is_active:
            raise ValidationError(
                {"education": _("Cannot create course in inactive education system.")}
            )
        return value

    def create(self, validated_data):
        validated_data["teacher"] = self.context["request"].user.teacher_profile
        return super().create(validated_data)
