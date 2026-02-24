from datetime import timezone
from decimal import Decimal
from typing import Optional
from django.db import models
from users.models import Student
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from ..validators import MAX_COURSE_PRICE

# =====================
# Enrollment MODEL
# =====================


class Enrollment(models.Model):
    """
    Enrollment model with complete payment tracking and state management.

    Features:
    - Status state machine (pending → active → completed/cancelled)
    - Payment verification
    - Historical price tracking
    - Refund support
    - Access control
    - Analytics
    """

    # Enrollment status choices
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = (
        (STATUS_PENDING, _("Pending Payment")),
        (STATUS_ACTIVE, _("Active")),
        (STATUS_COMPLETED, _("Completed")),
        (STATUS_CANCELLED, _("Cancelled")),
        (STATUS_REFUNDED, _("Refunded")),
        (STATUS_EXPIRED, _("Expired")),
    )
    # Payment method choices
    PAYMENT_CREDIT_CARD = "credit_card"
    PAYMENT_DEBIT_CARD = "debit_card"
    PAYMENT_PAYPAL = "paypal"
    PAYMENT_BANK_TRANSFER = "bank_transfer"
    PAYMENT_CASH = "vodafone_cash"
    PAYMENT_WALLET = "orange_cash"
    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_CREDIT_CARD, _("Credit Card")),
        (PAYMENT_DEBIT_CARD, _("Debit Card")),
        (PAYMENT_PAYPAL, _("PayPal")),
        (PAYMENT_BANK_TRANSFER, _("Bank Transfer")),
        (PAYMENT_CASH, _("Vodafone Cash")),
        (PAYMENT_WALLET, _("Orange Cash")),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="my_enrollments",
        help_text=_("Student who enrolled"),
    )

    course = models.ForeignKey(
        "Course",
        on_delete=models.PROTECT,
        related_name="course_enrollments",
        help_text=_("Course enrolled in"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text=_("Current enrollment status"),
    )

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        db_index=True,
        help_text=_("Payment method used"),
    )

    transaction_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        default=None,
        unique=True,
        help_text=_("Payment gateway transaction ID"),
    )

    price_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(MAX_COURSE_PRICE),
        ],
        help_text=_("Actual amount paid by student"),
    )

    # Discount/coupon support
    original_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(MAX_COURSE_PRICE),
        ],
        help_text=_("Original course price at time of enrollment"),
    )

    discount_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Discount applied (if any)"),
    )

    coupon_code = models.CharField(
        max_length=50, blank=True, help_text=_("Coupon code used (if any)")
    )

    # Refund tracking
    refund_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Refund amount (if refunded)"),
    )

    refund_reason = models.TextField(blank=True, help_text=_("Reason for refund"))

    refunded_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When refund was processed")
    )

    last_accessed_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When student last accessed course content")
    )

    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text=_("Course completion percentage"),
    )

    completed_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When student completed the course")
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True, help_text=_("When enrollment was created")
    )

    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When payment was confirmed and enrollment activated"),
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Enrollment")
        verbose_name_plural = _("Enrollments")
        ordering = ["-enrolled_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["transaction_id"],
                condition=models.Q(transaction_id__isnull=False),
                name="unique_transaction_id",
            )
        ]

        indexes = [
            models.Index(fields=["student", "-enrolled_at"]),
            models.Index(fields=["course", "-enrolled_at"]),
            models.Index(fields=["status", "-enrolled_at"]),
            models.Index(fields=["student", "course"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["course", "status"]),
            models.Index(fields=["transaction_id"]),
        ]
        unique_together = [["student", "course"]]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.course.title}"

    def clean(self):
        """Custom validation for enrollment"""
        super().clean()

        # Skip if objects not yet assigned
        if not self.student_id or not self.course_id:
            return

    def save(self, *args, **kwargs):
        """
        Override save to set default prices and run validation.
        """
        # Auto-set original_price from course if not provided
        if self.original_price is None and self.course_id:
            self.original_price = self.course.price

        # Auto-calculate price_paid if not provided
        if self.price_paid is None:
            self.price_paid = self.original_price - self.discount_amount

        # Validate completion percentage
        if self.completion_percentage == Decimal("100.00") and not self.completed_at:
            # Auto-set completed timestamp
            self.completed_at = timezone.now()
            self.status = self.STATUS_COMPLETED

        if "update_fields" in kwargs and kwargs["update_fields"] is not None:
            updated = set(kwargs["update_fields"])
            updated.add("completed_at")
            updated.add("status")
            kwargs["update_fields"] = list(updated)

        # Run validation unless explicitly skipped
        if not kwargs.pop("skip_validation", False):
            self.full_clean()

        super().save(*args, **kwargs)

    def activate(self, transaction_id: Optional[str] = None):
        """
        Activate enrollment after payment confirmation.

        Args:
            transaction_id: Payment gateway transaction ID

        Returns:
            bool: True if activated, False if already active
        """
        if self.status == self.STATUS_ACTIVE:
            return False

        self.status = self.STATUS_ACTIVE
        self.activated_at = timezone.now()

        if transaction_id:
            self.transaction_id = transaction_id

        self.save(
            update_fields=["status", "activated_at", "transaction_id", "updated_at"]
        )

        # TODO: Send enrollment confirmation email
        # from .tasks import send_enrollment_confirmation

        return True

    def complete(self):
        """Mark enrollment as completed"""
        if self.status == self.STATUS_COMPLETED:
            return False

        self.status = self.STATUS_COMPLETED
        self.completion_percentage = Decimal("100.00")
        self.completed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "completion_percentage",
                "completed_at",
                "updated_at",
            ]
        )

        # TODO: Send completion certificate
        # from .tasks import send_completion_certificate

        return True

    def cancel(self, reason: str = ""):
        """
        Cancel enrollment.

        Args:
            reason: Reason for cancellation

        Returns:
            bool: True if cancelled, False if already cancelled
        """
        if self.status in [self.STATUS_CANCELLED, self.STATUS_REFUNDED]:
            return False

        self.status = self.STATUS_CANCELLED

        if reason:
            self.refund_reason = reason

        self.save(update_fields=["status", "refund_reason", "updated_at"])

        return True

    def refund(self, amount: Decimal, reason: str = ""):
        """
        Process refund for enrollment.

        Args:
            amount: Refund amount
            reason: Refund reason

        Returns:
            bool: True if refunded successfully
        """
        if self.status == self.STATUS_REFUNDED:
            return False

        # Validate refund amount
        if amount > self.price_paid:
            raise ValidationError(_("Refund amount cannot exceed price paid"))

        self.status = self.STATUS_REFUNDED
        self.refund_amount = amount
        self.refund_reason = reason
        self.refunded_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "refund_amount",
                "refund_reason",
                "refunded_at",
                "updated_at",
            ]
        )

        # TODO: Process payment gateway refund
        # from .tasks import process_payment_refund
        # process_payment_refund.delay(self.id, amount)

        return True

    def update_progress(self, percentage: Decimal):
        """
        Update course completion progress.

        Args:
            percentage: Completion percentage (0-100)
        """
        if not (Decimal("0.00") <= percentage <= Decimal("100.00")):
            raise ValueError("Percentage must be between 0 and 100")

        self.completion_percentage = percentage
        self.last_accessed_at = timezone.now()

        # Auto-complete if 100%
        if percentage == Decimal("100.00") and not self.completed_at:
            self.completed_at = timezone.now()
            self.status = self.STATUS_COMPLETED

        self.save(
            update_fields=[
                "completion_percentage",
                "last_accessed_at",
                "completed_at",
                "status",
                "updated_at",
            ]
        )

    @property
    def is_active(self):
        """Check if enrollment is currently active"""
        return self.status == self.STATUS_ACTIVE

    @property
    def days_since_enrollment(self):
        """Days since enrollment was created"""
        return (timezone.now() - self.enrolled_at).days

    @property
    def has_accessed_content(self):
        """Check if student has accessed course content"""
        return self.last_accessed_at is not None


# =====================
# Review MODEL
# =====================


class Review(models.Model):
    """Review model for courses with rating and feedback."""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="students_review",
        help_text=_("Student who Review"),
    )

    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        related_name="course_reviews",
        help_text=_("course will Review it"),
    )

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=5,
        db_index=True,
        validators=[
            MinValueValidator(Decimal("1.0")),
            MaxValueValidator(Decimal("5.0")),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "-created_at"]),
            models.Index(fields=["course", "-created_at"]),
            models.Index(fields=["student", "course"]),
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
            models.Index(fields=["course", "rating"]),
        ]
        unique_together = [["student", "course"]]

    def __str__(self):
        return f"{self.course.title} - Rating: {self.rating}"

    def clean(self):
        """Custom validation"""
        super().clean()

        # Skip if objects not yet assigned
        if not self.student_id or not self.course_id:
            return

        has_enrollment = Enrollment.objects.filter(
            student=self.student,
            course=self.course,
            status__in=[Enrollment.STATUS_ACTIVE, Enrollment.STATUS_COMPLETED],
        ).exists()

        if not has_enrollment:
            raise ValidationError(
                {"student": _("Student must be enrolled to review the course.")}
            )

    def save(self, *args, **kwargs):
        if not kwargs.pop("skip_validation", False):
            self.full_clean()
        super().save(*args, **kwargs)
