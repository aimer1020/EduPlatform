from typing import Optional
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator,
)
from .validators import (
    ALLOWED_CV_EXTENSIONS as ALLOWED_CV_EXTENSIONS,
    MAX_ACADEMIC_YEAR as MAX_ACADEMIC_YEAR,
    MAX_CV_FILE_SIZE_MB as MAX_CV_FILE_SIZE_MB,
    MAX_EXPERIENCE_YEARS as MAX_EXPERIENCE_YEARS,
    MIN_ACADEMIC_YEAR as MIN_ACADEMIC_YEAR,
    MIN_EXPERIENCE_YEARS as MIN_EXPERIENCE_YEARS,
    ValidationError as ValidationError,
    cv_upload_path as cv_upload_path,
    re as re,
    settings as settings,
    validate_academic_year as validate_academic_year,
    validate_file_size as validate_file_size,
    validate_pdf as validate_pdf,
    validate_phone as validate_phone,
    validate_phone_optional as validate_phone_optional,
    )

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# =====================
# USER MODEL
# =====================


class User(AbstractUser):
    """
    Extended User model with user type classification.

    Inherits from AbstractUser and adds:
    - User type (Teacher/Student)
    - Biography field
    - Timestamps for tracking
    """

    bio = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text=_("Biography or introduction (max 500 characters)"),
    )

    USER_TYPE_TEACHER = "teacher"
    USER_TYPE_STUDENT = "student"
    USER_TYPE_CHOICES = (
        (USER_TYPE_TEACHER, _("Teacher")),
        (USER_TYPE_STUDENT, _("Student")),
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_STUDENT,
        db_index=True,
        help_text=_("User role in the platform"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text=_("Timestamp when user was soft-deleted")
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["user_type", "-date_joined"]),
            models.Index(fields=["is_active", "user_type"]),
        ]

    def __str__(self):
        """Return formatted full name or username as fallback"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username

    def get_full_name(self):
        """
        Return the user's full name.

        Returns:
            str: Full name or empty string
        """
        return f"{self.first_name} {self.last_name}".strip()

    def soft_delete(self):
        """
        Soft delete user (set is_active=False, preserve data).

        Benefits:
        - Maintain referential integrity
        - Enable data recovery
        - Support audit requirements
        - Allow re-activation
        """

        self.active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["active", "deleted_at", "updated_at"])

    def restore(self):
        """Restore soft-deleted user"""
        self.active = True
        self.deleted_at = None
        self.save(update_fields=["active", "deleted_at", "updated_at"])


# =====================
# TEACHER MODEL
# =====================


class Teacher(models.Model):
    """
    Teacher profile model containing additional information for teachers.

    Linked to User model with OneToOne relationship.
    Contains teacher-specific fields like subject specialization,
    experience, CV, and verification status.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"user_type": User.USER_TYPE_TEACHER},
        help_text=_("User account with Teacher type"),
    )

    subject = models.ForeignKey(
        "courses.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_subject",
        help_text=_("Primary subject specialization"),
    )

    additional_subjects = models.ManyToManyField(
        "courses.Subject",
        blank=True,
        related_name="additional_teacher_subject",
        help_text=_("Additional subjects this teacher can teach"),
    )

    experience_years = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(MIN_EXPERIENCE_YEARS),
            MaxValueValidator(MAX_EXPERIENCE_YEARS),
        ],
        help_text=_(
            f"Years of teaching experience ({MIN_EXPERIENCE_YEARS}-{MAX_EXPERIENCE_YEARS})"
        ),
    )

    cv = models.FileField(
        upload_to=cv_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_CV_EXTENSIONS),
            validate_file_size,
            validate_pdf,
        ],
        blank=True,  # Made optional for initial profile creation
        null=True,
        help_text=_(f"Upload CV in PDF format (max {MAX_CV_FILE_SIZE_MB}MB)"),
    )

    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Admin verification status for teacher authenticity"),
    )

    # Audit trail for verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_teachers",
        help_text=_("Admin who verified this teacher"),
    )

    verified_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When teacher was verified")
    )

    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Hourly teaching rate in local currency (optional)"),
    )

    is_active = models.BooleanField(
        default=True, db_index=True, help_text=_("Active profile status")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Teacher Profile")
        verbose_name_plural = _("Teacher Profiles")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_verified", "-created_at"]),
            models.Index(fields=["subject"]),
            models.Index(fields=["user", "is_verified"]),
            models.Index(fields=["is_active", "is_verified"]),
        ]

    def __str__(self):
        """Return teacher's full name"""
        return str(self.user)

    def clean(self):
        """
        Custom validation to ensure business logic constraints.

        Raises:
            ValidationError: If validation fails
        """
        super().clean()

        # Skip validation if user not yet assigned (during creation)
        if not self.user_id:
            return

        # Ensure linked user has Teacher user_type
        if self.user.user_type != User.USER_TYPE_TEACHER:
            raise ValidationError(
                {
                    "user": _(
                        'Only users with user_type="teacher" can have a teacher profile.'
                    )
                }
            )

        # Ensure user is active
        if not self.user.is_active:
            raise ValidationError(
                {"user": _("Cannot create profile for inactive user.")}
            )

    def save(self, *args, **kwargs):
        """
        Override save to run validation and update user's updated_at.

        Note: Use skip_validation=True to bypass validation when needed
        (e.g., during data migrations)
        """
        if not kwargs.pop("skip_validation", False):
            self.full_clean()

        super().save(*args, **kwargs)

        # Update parent user's timestamp for cache invalidation
        self.user.save(update_fields=["updated_at"])

    @property
    def is_experienced(self):
        """Check if teacher has significant experience (5+ years)"""
        return self.experience_years >= 5

    @property
    def experience_level(self):
        """Return human-readable experience level"""
        if self.experience_years == 0:
            return "Entry Level"
        elif self.experience_years < 3:
            return "Junior"
        elif self.experience_years < 7:
            return "Mid-Level"
        elif self.experience_years < 15:
            return "Senior"
        else:
            return "Expert"

    @property
    def active_courses(self):
        return self.teacher_courses.filter(is_active=True)

    @property
    def courses_count(self):
        return self.active_courses.count()

    def verify_teacher(self, verified_by_user):
        """
        Mark teacher as verified (admin action).

        Args:
            verified_by_user: User object of admin performing verification
            notes: Optional verification notes

        Returns:
            bool: True if verification successful
        """
        if self.is_verified:
            return False  # Already verified

        self.is_verified = True
        self.verified_by = verified_by_user
        self.verified_at = timezone.now()

        self.save(
            update_fields=["is_verified", "verified_by", "verified_at", "updated_at"]
        )

        return True

    def unverify_teacher(self):
        """
        Remove verification status.

        Args:
            reason: Reason for unverification (logged for audit)

        Returns:
            bool: True if unverification successful
        """
        if not self.is_verified:
            return False  # Not verified

        self.is_verified = False
        self.save(update_fields=["is_verified", "updated_at"])

        return True


# =====================
# STUDENT MODEL
# =====================


class Student(models.Model):
    """
    Student profile model containing additional information for students.

    Linked to User model with OneToOne relationship.
    Contains student-specific fields like academic year,
    contact information, and parent/guardian details.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"user_type": User.USER_TYPE_STUDENT},
        help_text=_("User account with Student type"),
    )

    academic_year = models.PositiveSmallIntegerField(
        default=1,
        validators=[validate_academic_year],
        db_index=True,
        help_text=_(
            f"Current academic year/grade ({MIN_ACADEMIC_YEAR}-{MAX_ACADEMIC_YEAR})"
        ),
    )

    phone = models.CharField(
        max_length=15,
        validators=[validate_phone, validate_phone_optional],
        help_text=_("Student's phone number (Egyptian/KSA format: 01XXXXXXXXX)"),
    )

    parent_phone = models.CharField(
        max_length=15,
        validators=[validate_phone, validate_phone_optional],
        help_text=_("Student's parent/guardian phone number (Egyptian/KSA format: 01XXXXXXXXX)"),
    )

    parent_name = models.CharField(
        max_length=200, blank=True, help_text=_("Parent/guardian full name")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Student Profile")
        verbose_name_plural = _("Student Profiles")
        ordering = ["academic_year", "-created_at"]
        indexes = [
            models.Index(fields=["academic_year"]),
            models.Index(fields=["user", "academic_year"]),
        ]

    def __str__(self):
        """Return student's full name and grade"""
        return f"{self.user} - {self.grade_level}"

    def clean(self):
        """
        Custom validation to ensure business logic constraints.

        Raises:
            ValidationError: If validation fails
        """
        super().clean()

        # Skip validation if user not yet assigned (during creation)
        if not self.user_id:
            return

        # Ensure linked user has Student user_type
        if self.user.user_type != User.USER_TYPE_STUDENT:
            raise ValidationError(
                {
                    "user": _(
                        'Only users with user_type="student" can have a student profile.'
                    )
                }
            )

        # Ensure user is active
        if not self.user.is_active:
            raise ValidationError(
                {"user": _("Cannot create profile for inactive user.")}
            )

        # Ensure parent phone is different from student phone
        if self.phone and self.parent_phone:
            # Clean both for comparison
            cleaned_student = re.sub(r"[\s\-\(\)\.]", "", str(self.phone))
            cleaned_parent = re.sub(r"[\s\-\(\)\.]", "", str(self.parent_phone))

            if cleaned_student == cleaned_parent:
                raise ValidationError(
                    {
                        "parent_phone": _(
                            "Parent phone number must be different from student phone number."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """
        Override save to run validation and update user's updated_at.

        Note: Use skip_validation=True to bypass validation when needed
        """
        if not kwargs.pop("skip_validation", False):
            self.full_clean()

        super().save(*args, **kwargs)

        # Update parent user's timestamp
        self.user.save(update_fields=["updated_at"])

    @property
    def grade_level(self):
        """
        Return human-readable grade level.

        Returns:
            str: Formatted grade level
        """
        # Special handling for 1st, 2nd, 3rd
        if self.academic_year == 1:
            return _("1st Grade")
        elif self.academic_year == 2:
            return _("2nd Grade")
        elif self.academic_year == 3:
            return _("3rd Grade")
        else:
            return _(f"{self.academic_year}th Grade")

    def promote_to_next_year(self, promoted_by: Optional["User"] = None):
        """
        Promote student to next academic year.

        Args:
            promoted_by: User who performed the promotion (for audit)

        Returns:
            bool: True if promoted, False if already in final year

        Note:
            In production, this should trigger:
            - Grade change notification to student/parent
            - Enrollment updates for next year
            - Academic record updates
        """
        if self.academic_year >= MAX_ACADEMIC_YEAR:
            return False

        self.academic_year += 1
        self.save(update_fields=["academic_year", "updated_at"])
        return True

    @property
    def is_senior(self):
        """Check if student is in senior years (grades 10-12)"""
        return self.academic_year >= 10

    @property
    def enrolled_courses_count(self):
        return self.enrollments.filter(course__is_active=True).count()


# =====================
# MANAGER CLASSES (Optional Enhancement)
# =====================


class ActiveUserManager(models.Manager):
    """Manager that returns only active (non-deleted) users"""

    def get_queryset(self):
        return super().get_queryset().filter(user__is_active=True)


class VerifiedTeacherManager(models.Manager):
    """Manager that returns only verified teachers"""

    def get_queryset(self):
        return super().get_queryset().filter(is_verified=True, user__is_active=True)
