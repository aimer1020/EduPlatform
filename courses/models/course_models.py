from decimal import Decimal
from django.db import models
from django.db.models import Avg, Count, Q, Sum
from django.conf import settings
from django.core.exceptions import ValidationError  
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify 
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator
)
from django.utils import timezone  

from ..validators import *
from users.models import Teacher, Student

User = settings.AUTH_USER_MODEL

# =====================
# Education MODEL
# =====================
    
class Education(models.Model):
    """
    Education system model representing different countries/regions.
    Each education system has its own currency and country-specific settings.
    Supports multiple countries for international expansion.
    """
    country = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Country name (e.g., Egypt, Saudi Arabia)")
    )
    
    country_code = models.CharField(
        max_length=3,
        unique=True,
        help_text=_("ISO 3166-1 alpha-3 country code (e.g., EGY, SAU)")
    )
    
    flag = models.ImageField(
        upload_to=education_flag_path,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
            validate_image_dimensions,
        ],
        help_text=_(f"Country flag image (max {MAX_IMAGE_SIZE_MB}MB)")
    )
    
    CURRENCY_CHOICES = (
        ('EGP', _('Egyptian Pound')),
        ('SAR', _('Saudi Riyal')),
        ('USD', _('US Dollar')),
        ('EUR', _('Euro')),
        ('GBP', _('British Pound')),
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EGP',
        db_index=True,
        help_text=_("Currency used in this education system")
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this education system is currently active")
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp when education system was soft-deleted")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Education System')
        verbose_name_plural = _('Education Systems')
        ordering = ['country']
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['is_active', 'country']),
            models.Index(fields=['country_code']),
        ]
    
    def __str__(self):
        return self.country
    
    def clean(self):
        """Validate country code format"""
        super().clean()
        
        if self.country_code:
            # Ensure uppercase
            self.country_code = self.country_code.upper()
            
            # Validate format
            if len(self.country_code) != 3 or not self.country_code.isalpha():
                raise ValidationError({
                    'country_code': _('Country code must be 3 letters (ISO 3166-1 alpha-3)')
                })
    
    @property
    def active_courses(self):
        """Get queryset of active courses"""
        return self.education_courses.filter(is_active=True)
    
    @property
    def total_courses_count(self):
        """Total active courses in this education system"""
        return self.active_courses.count()
    
    def soft_delete(self):
        """Soft delete education system"""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

# =====================
# SUBJECT MODEL
# =====================

class Subject(models.Model):
    """
    Standardized subject/course category model.
    
    Enables:
    - Consistent subject classification
    - Easy filtering and search
    - Multi-language support
    - Analytics and reporting
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Subject name (e.g., Mathematics, Physics)")
    )
    
    name_ar = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Subject name in Arabic")
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text=_("Unique subject code (e.g., MATH, PHYS, CHEM)")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Subject description and scope")
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this subject is currently offered")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subject')
        verbose_name_plural = _('Subjects')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate and normalize code"""
        super().clean()
        
        if self.code:
            # Ensure uppercase
            self.code = self.code.upper()

# =====================
# COURSE MODEL
# =====================

class Course(models.Model):
    """
    Main course model with complete business logic.
    
    Features:
    - Teacher ownership and verification
    - Education system integration
    - Pricing with historical tracking
    - Image management
    - Enrollment tracking
    - Review system
    - Analytics support
    """
    
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='teacher_courses',
        help_text=_("Teacher who manages this course")
    )
    
    education = models.ForeignKey(
        Education,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='education_courses',
        help_text=_("Education system this course belongs to")
    )
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_courses',
        help_text=_("Subject category")
    )
    
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text=_("Course title")
    )
    
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text=_("URL-friendly version of title (auto-generated)")
    )
    
    description = models.TextField(
        help_text=_("Course description, objectives, and requirements")
    )
    
    course_img = models.ImageField(
        upload_to=course_image_path,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
            validate_image_dimensions,
        ],
        help_text=_(
            f"Course thumbnail (max {MAX_IMAGE_SIZE_MB}MB, "
            f"min {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}px)"
        )
    )
    
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_COURSE_PRICE),
            MaxValueValidator(MAX_COURSE_PRICE)
        ],
        db_index=True,
        help_text=_(f"Course price (min {MIN_COURSE_PRICE})")
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether course is available for enrollment")
    )
    
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Whether course is visible to students")
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When course was first published")
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp when course was soft-deleted")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['education', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['subject', '-created_at']),
            models.Index(fields=['is_active', 'is_published', '-created_at']),
            models.Index(fields=['price']),
        ]
        unique_together = [['teacher', 'title']]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """
        Custom validation for business logic.
        
        Validates:
        - Teacher must be verified
        - Education system must be active
        - Price must be reasonable
        """
        super().clean()
        
        # Skip if objects not yet assigned
        if not self.teacher_id or not self.education_id:
            return
        
        # Ensure teacher is verified
        if not self.teacher.is_verified:
            raise ValidationError({
                'teacher': _('Only verified teachers can create courses.')
            })
        
        # Ensure education system is active
        if not self.education.is_active:
            raise ValidationError({
                'education': _('Cannot create course in inactive education system.')
            })
        
        # Validate price is set
        if self.price is None or self.price <= 0:
            raise ValidationError({
                'price': _(f'Course price must be at least {MIN_COURSE_PRICE}')
            })
    
    def save(self, *args, **kwargs):
        """
        Override save to handle slug generation and validation.
        """
        # Auto-generate slug from title
        if not self.slug:
            base_slug = slugify(self.title)[:200]
            slug = base_slug
            counter = 1
            
            # Ensure unique slug
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Run validation unless explicitly skipped
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        
        super().save(*args, **kwargs)
    
    # Properties with correct naming
    @property
    def enrollment_count(self):
        """Total enrollements"""
        return self.course_enrollments.filter(status='active').count() if hasattr(self, 'students_enrollments') else 0
    
    @property
    def enrolled_students(self):
        """Get queryset of enrolled students"""
        return Student.objects.filter(enrollments__course=self,enrollments__is_active=True).distinct()
    
    @property
    def total_revenue(self):
        """
        Total revenue from active enrollments.
        Note: Use annotations for better performance:
        Course.objects.annotate(total_revenue=Sum('enrollments__price_paid'))
        """
        result = self.course_enrollments.filter(
            status='active'
        ).aggregate(total=Sum('price_paid'))
        return result['total'] or Decimal('0.00')
    
    @property
    def review_count(self):
        """total_revenue"""
        return self.course_reviews.count() if hasattr(self, 'course_reviews') else 0
    
    @property
    def average_rating(self):
        """
        Average course rating.
        
        Returns:
            Decimal: Average rating or 0 if no reviews
        """
        result = self.course_reviews.aggregate(avg=Avg('rating'))
        return result['avg'] or Decimal('0.0')
    
    @property
    def lesson_count(self):
        """Total lessons (via chapters)"""
        from .lesson_models import Lesson
        return Lesson.objects.filter(chapter__course=self).count()
    
    @property
    def chapter_count(self):
        """Total chapters"""
        return self.chapters_of_course.count()
    
    def publish(self, commit=True):
        """
        Publish course (make visible to students).
        
        Args:
            commit: Whether to save to database
            
        Returns:
            bool: True if published, False if already published
        """
        if self.is_published or not self.is_active:
            return False
        
        self.is_published = True
        
        if not self.published_at:
            self.published_at = timezone.now()
        
        if commit:
            self.save(update_fields=['is_published', 'published_at', 'updated_at'])
        
        return True
    
    def unpublish(self, commit=True):
        """Unpublish course (hide from students)"""
        if not self.is_published:
            return False
        
        self.is_published = False
        
        if commit:
            self.save(update_fields=['is_published', 'updated_at'])
        
        return True
    
    def activate(self):
        """Activate course"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def deactivate(self):
        """Deactivate course"""
        self.unpublish(commit=True)  # Unpublish before deactivating
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
        
    def soft_delete(self):
        """Soft delete course"""
        self.is_active = False
        self.is_published = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'is_published', 'deleted_at', 'updated_at'])
        
    def can_enroll(self, student):
        """
        Check if student can enroll in this course.
        
        Args:
            student: Student instance
            
        Returns:
            tuple: (bool, str) - (can_enroll, reason_if_not)
        """
        # Course must be active and published
        if not self.is_active:
            return False, _("Course is not currently active")
        
        if not self.is_published:
            return False, _("Course is not published yet")
        
        # Check if already enrolled
        from .interactionCourse_models import Enrollment
        if Enrollment.objects.filter(
            student=student,
            course=self,
            status='active'  # ✅ FIXED: Use string directly
        ).exists():
            return False, _("You are already enrolled in this course")
        
        # All checks passed
        return True, ""
    
    def get_course_stats(self):
        """
        Get comprehensive course statistics.
        Returns:
            dict: Course statistics
        """
        return {
            'enrollments': self.enrollment_count,
            'revenue': self.total_revenue,
            'reviews': self.review_count,
            'average_rating': self.average_rating,
            'chapters': self.chapter_count,
            'lessons': self.lesson_count,
        }