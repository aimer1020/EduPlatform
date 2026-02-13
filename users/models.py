import os
import re
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator
)
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from decimal import Decimal


# =====================
# CUSTOM VALIDATORS
# =====================

def validate_file_size(value):
    """
    Validate uploaded file size.
    Maximum allowed: 5MB for CV files.
    """
    max_size_mb = 5
    filesize = value.size
    
    if filesize > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"File size cannot exceed {max_size_mb}MB. "
            f"Current size: {filesize / (1024 * 1024):.2f}MB"
        )


def validate_pdf(file):
    """
    Validate PDF by checking file header magic bytes.
    PDF files always start with %PDF- signature.
    """
    try:
        file.seek(0)
        header = file.read(5)
        file.seek(0)  # Reset file pointer
        
        if not header.startswith(b'%PDF-'):
            raise ValidationError(
                "Invalid PDF file. The file may be corrupted or in the wrong format."
            )
    except AttributeError:
        # Handle case where file object doesn't support seek
        raise ValidationError("Unable to validate file format.")
    except Exception as e:
        raise ValidationError(f"Error validating PDF: {str(e)}")


def validate_phone(value):
    """
    Validate Egyptian phone number format.
    Expected: 11 digits starting with 010, 011, 012, or 015
    Example: 01012345678
    """
    if not value:
        return
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)]', '', str(value))
    
    # Egyptian mobile pattern: 010/011/012/015 + 8 digits
    pattern = r'^(010|011|012|013|014|015)(\d{8}|\d{7})$'
    
    if not re.match(pattern, cleaned):
        raise ValidationError(
            "Invalid Egyptian phone number. Must be 11 digits starting with "
            "010, 011, 012, or 015. Example: 01012345678"
        )


def validate_phone_optional(value):
    """
    Optional phone validator that allows empty values.
    """
    if not value or str(value).strip() == '':
        return
    validate_phone(value)


def validate_academic_year(value):
    """
    Validate academic year is within reasonable range.
    K-12 education: grades 1-12
    """
    if not (1 <= value <= 12):
        raise ValidationError(
            f"Academic year must be between 1 and 12. Got: {value}"
        )


# =====================
# UPLOAD PATH FUNCTIONS
# =====================

def cv_upload_path(instance, filename):
    """
    Generate secure upload path for teacher CV files.
    
    Path structure: users/cv/{user_id}/{username}-cv.pdf
    Example: users/cv/123/john-doe-cv.pdf
    
    Args:
        instance: Teacher model instance
        filename: Original uploaded filename
        
    Returns:
        str: Secure file path
    """
    ext = filename.split('.')[-1].lower()
    
    # Create safe filename using username (limit to 50 chars)
    safe_name = slugify(instance.user.username)[:50]
    new_filename = f"{safe_name}-cv.{ext}"
    
    return os.path.join(
        'users',
        'cv',
        str(instance.user.id),
        new_filename
    )


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
        max_length=1000,
        help_text="Biography or introduction (max 1000 characters)"
    )
    
    USER_TYPE_CHOICES = (
        ('Teacher', 'Teacher'),
        ('Student', 'Student'),
    )
    
    userType = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='Student',
        db_index=True,
        help_text="User role in the platform"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['userType', '-date_joined']),
        ]
    
    def __str__(self):
        """Return formatted full name or username as fallback"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username
    
    def get_full_name(self):
        """
        Return the user's full name.
        
        Returns:
            str: Full name or username
        """
        return str(self)
    
    @property
    def has_profile(self):
        """Check if user has an associated profile"""
        if self.userType == 'Teacher':
            return hasattr(self, 'teacher_profile')
        elif self.userType == 'Student':
            return hasattr(self, 'student_profile')
        return False


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
        related_name='teacher_profile',
        limit_choices_to={'userType': 'Teacher'},
        help_text="User account with Teacher type"
    )
    
    subject = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        db_index=True,
        help_text="Subject specialization (e.g., Mathematics, Physics, Chemistry)"
    )
    
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(50)
        ],
        help_text="Years of teaching experience (0-50)"
    )
    
    cv = models.FileField(
        upload_to=cv_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size,
            validate_pdf,
        ],
        help_text="Upload CV in PDF format (max 5MB)"
    )
    
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Admin verification status for teacher authenticity"
    )
    
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Hourly teaching rate in local currency (optional)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_verified', '-created_at']),
            models.Index(fields=['subject']),
            models.Index(fields=['user', 'is_verified']),
        ]
    
    def __str__(self):
        """Return teacher's full name"""
        return str(self.user)
    
    def clean(self):
        """
        Custom validation to ensure business logic constraints.
        """
        super().clean()
        
        # Skip validation if user not yet assigned (during creation)
        if not self.user_id:
            return
        
        # Ensure linked user has Teacher userType
        if self.user.userType != 'Teacher':
            raise ValidationError({
                'user': 'Only users with userType="Teacher" can have a teacher profile.'
            })
        
        # Validate experience years is reasonable
        if self.experience_years > 50:
            raise ValidationError({
                'experience_years': 'Experience years exceeds maximum allowed (50 years).'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run full_clean validation"""
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
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
    
    def verify_teacher(self):
        """Mark teacher as verified (admin action)"""
        self.is_verified = True
        self.save(update_fields=['is_verified', 'updated_at'])
    
    def unverify_teacher(self):
        """Remove verification status"""
        self.is_verified = False
        self.save(update_fields=['is_verified', 'updated_at'])


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
        related_name='student_profile',
        limit_choices_to={'userType': 'Student'},
        help_text="User account with Student type"
    )
    
    academic_year = models.PositiveSmallIntegerField(
        default=1,
        validators=[validate_academic_year],
        db_index=True,
        help_text="Current academic year/grade (1-12)"
    )
    
    phone = models.CharField(
        max_length=15,
        validators=[validate_phone],
        help_text="Student's phone number (Egyptian format: 01XXXXXXXXX)"
    )
    
    parent_phone = models.CharField(
        max_length=15,
        validators=[validate_phone],
        help_text="Parent/guardian phone number (Egyptian format: 01XXXXXXXXX)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering = ['academic_year', '-created_at']
        indexes = [
            models.Index(fields=['academic_year']),
            models.Index(fields=['user', 'academic_year']),
        ]
    
    def __str__(self):
        """Return student's full name and grade"""
        return f"{self.user} - {self.grade_level}"
    
    def clean(self):
        """
        Custom validation to ensure business logic constraints.
        """
        super().clean()
        
        # Skip validation if user not yet assigned (during creation)
        if not self.user_id:
            return
        
        # Ensure linked user has Student userType
        if self.user.userType != 'Student':
            raise ValidationError({
                'user': 'Only users with userType="Student" can have a student profile.'
            })
        
        # Ensure parent phone is different from student phone
        if self.phone and self.parent_phone and self.phone == self.parent_phone:
            raise ValidationError({
                'parent_phone': 'Parent phone number must be different from student phone number.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run full_clean validation"""
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def grade_level(self):
        """Return human-readable grade level"""
        grade_mapping = {
            1: "1st Grade",
            2: "2nd Grade",
            3: "3rd Grade",
        }
        
        # Use mapping for first 3 grades, otherwise use "Nth Grade"
        if self.academic_year in grade_mapping:
            return grade_mapping[self.academic_year]
        else:
            return f"{self.academic_year}th Grade"
    
    def promote_to_next_year(self):
        """
        Promote student to next academic year.
        
        Returns:
            bool: True if promoted, False if already in final year
        """
        if self.academic_year < 12:
            self.academic_year += 1
            self.save(update_fields=['academic_year', 'updated_at'])
            return True
        return False  # Already in final year (Grade 12)
    
    @property
    def is_senior(self):
        """Check if student is in senior years (grades 10-12)"""
        return self.academic_year >= 10