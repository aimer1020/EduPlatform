from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator
)
from PIL import Image
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import ValidationError
from users.models import (
    Teacher, Student
)
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from decimal import Decimal
import os

User = get_user_model()

# =====================
# CUSTOM VALIDATORS
# =====================
def validate_image_size(value):
    """
    Validate uploaded image size.
    Maximum allowed: 2MB for images.
    """
    max_size_mb = 2
    filesize = value.size
    
    if filesize > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"Image size cannot exceed {max_size_mb}MB. "
            f"Current size: {filesize / (1024 * 1024):.2f}MB"
        )


def validate_image_dimensions(value):
    """
    Validate image dimensions.
    Minimum: 200x200, Maximum: 4000x4000
    """
    try:
        img = Image.open(value)
        width, height = img.size
        
        if width < 200 or height < 200:
            raise ValidationError(
                f"Image dimensions too small. Minimum 200x200px. Got: {width}x{height}px"
            )
        
        if width > 4000 or height > 4000:
            raise ValidationError(
                f"Image dimensions too large. Maximum 4000x4000px. Got: {width}x{height}px"
            )
    except Exception as e:
        raise ValidationError(f"Invalid image file: {str(e)}")
    
# =====================
# UPLOAD PATH FUNCTIONS
# =====================
def education_flag_path(instance, filename):
    """
    Generate secure upload path for education country flags.
    
    Path: education/flags/{country_slug}.{ext}
    Example: education/flags/egypt.png
    """
    ext = filename.split('.')[-1].lower()
    safe_name = slugify(instance.country)[:50]
    new_filename = f"{safe_name}.{ext}"
    
    return os.path.join('education', 'flags', new_filename)

def course_image_path(instance, filename):
    """
    Generate secure upload path for course thumbnails.
    
    Path: courses/thumbnails/{year}/{month}/{course-title}.{ext}
    Example: courses/thumbnails/2025/02/introduction-to-python.jpg
    """
    ext = filename.split('.')[-1].lower()
    safe_title = slugify(instance.title)[:50]
    new_filename = f"{safe_title}-{instance.pk or 'new'}.{ext}"
    
    # Use created_at if available, otherwise use 'temp'
    year = instance.created_at.year if instance.created_at else 'temp'
    month = instance.created_at.month if instance.created_at else 'temp'
    
    return os.path.join(
        'courses',
        'thumbnails',
        str(year),
        str(month),
        new_filename
    )
    
# =====================
# Education MODEL
# =====================
    
class Education(models.Model):
    """
    Education system model representing different countries/regions.
    Each education system has its own currency and country-specific settings.
    """
    country = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Country name (e.g., Egypt, Saudi Arabia)")
    )
    
    flag = models.ImageField(
        upload_to=education_flag_path,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
        help_text=_("Country flag image (max 2MB, formats: jpg, png, webp)")
    )
    
    CURRENCY_CHOICES = (
        ('EGP', 'Egyptian Pound'),
        ('SAR', 'Saudi Riyal'),
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
        
    class Meta:
        verbose_name = _('Education')
        verbose_name_plural = _('Educations')
        ordering = ['country']
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['is_active', 'country']),
        ]
    
    def __str__(self):
        return f"{self.country}"
    
    @property
    def total_courses(self):
        """Get queryset of active courses"""
        return self.education_courses.filter(is_active=True)


# =====================
# SUBJECT MODEL
# =====================

class Subject(models.Model):
    """
    Standardized subject/course model.
    
    Benefits:
    - Consistent subject names across platform
    - Enable filtering and reporting
    - Support for multiple languages
    - Hierarchical subject organization (future: categories)
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
        help_text=_("Unique subject code (e.g., MATH101)")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Subject description")
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
        ]
    
    def __str__(self):
        return self.name

# =====================
# COURSE MODEL
# =====================

class Course(models.Model):
    """Main course model"""
    
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='teacher_courses',
        help_text=_("Teacher who manages this course")
    )
    
    education = models.ForeignKey(
        Education,
        on_delete=models.CASCADE,
        related_name='education_courses',
        help_text=_("Education system")
    )
    
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text=_("Course title")
    )
    
    description = models.TextField(
        help_text=_("Course description, objectives, and requirements")
    )
    
    course_img = models.ImageField(
        upload_to=course_image_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
            validate_image_dimensions,
        ],
        help_text=_("Course thumbnail (max 2MB, min 200x200px)")
    )
    
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('5.00')),
            MaxValueValidator(Decimal('999999.99'))
        ],
        db_index=True,
        help_text=_("Course price (min 5.00)")
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether course is available for enrollment")
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
            models.Index(fields=['price']),
        ]
        unique_together = [['teacher', 'title']]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Skip if objects not yet assigned
        if not self.teacher_id or not self.education_id:
            return
        
        if not self.teacher.is_verified:
            raise ValidationError({
                'teacher': 'Only verified teachers can create courses.'
            })
        
        if not self.education.is_active:
            raise ValidationError({
                'education': 'Cannot create course in inactive education system.'
            })
    
    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    # Properties with correct naming
    @property
    def enrollment_count(self):
        """Total enrolled students"""
        return self.students_enrollments.count() if hasattr(self, 'students_enrollments') else 0
    
    @property
    def lesson_count(self):
        """Total lessons (via chapters)"""
        from .lesson_models import Lesson
        return Lesson.objects.filter(chapter__course=self).count()
    
    @property
    def chapter_count(self):
        """Total chapters"""
        return self.chapters_of_course.count()
    
    @property
    def total_chapters(self):
        """All chapters queryset"""
        return self.chapters_of_course.all()
    
    def activate(self):
        """Activate course"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def deactivate(self):
        """Deactivate course"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


# =====================
# CHAPTER MODEL
# =====================

class Chapter(models.Model):
    """Course chapters for organizing lessons"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='chapters_of_course',
        help_text="Parent course"
    )
    
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Chapter title"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Chapter description (optional)"
    )
    
    order = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        db_index=True,
        help_text="Display order within course"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Chapter'
        verbose_name_plural = 'Chapters'
        ordering = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
        unique_together = [
            ['course', 'title'],
            ['course', 'order'],  # Unique order per course
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def clean(self):
        """Validate chapter belongs to course"""
        super().clean()
        
        # Auto-assign next order if not provided
        if not self.order and self.course_id:
            max_order = Chapter.objects.filter(
                course=self.course
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
    
    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def lesson_count(self):
        """Total lessons in this chapter"""
        return self.lessons_of_chapter.count()
    
    @property
    def total_lessons(self):
        """All lessons queryset"""
        return self.lessons_of_chapter.all()