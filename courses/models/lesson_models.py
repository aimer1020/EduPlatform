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
def validate_video_duration(value):
    """Validate video duration (1 second to 4 hours)"""
    if not (1 <= value <= 14400):  # 4 hours = 14400 seconds
        raise ValidationError(
            f"Video duration must be between 1 second and 4 hours. Got: {value} seconds"
        )

# =====================
# LESSON MODEL
# =====================

class Lesson(models.Model):
    """Individual lessons within chapters"""
    
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.CASCADE,
        related_name='lessons_of_chapter',
        help_text="Parent chapter"
    )
    
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Lesson title"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Lesson description (optional)"
    )
    
    video_url = models.URLField(
        max_length=500,
        help_text="Video URL (YouTube, Vimeo, Google Drive, etc.)"
    )
    
    duration_seconds = models.PositiveIntegerField(
        validators=[validate_video_duration],
        help_text="Video duration in seconds (1s to 4 hours)"
    )
    
    order = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        db_index=True,
        help_text="Display order within chapter"
    )
    
    is_preview = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Free preview lesson (accessible without enrollment)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['chapter', 'order']
        indexes = [
            models.Index(fields=['chapter', 'order']),
            models.Index(fields=['is_preview']),
        ]
        unique_together = [
            ['chapter', 'title'],
            ['chapter', 'order'],  # Unique order per chapter
        ]
    
    def __str__(self):
        return f"{self.chapter.title} - {self.title}"
    
    def clean(self):
        """Validate lesson data"""
        super().clean()
        
        # Auto-assign next order if not provided
        if not self.order and self.chapter_id:
            max_order = Lesson.objects.filter(
                chapter=self.chapter
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
    
    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    # Helper properties
    @property
    def course(self):
        """Access parent course via chapter"""
        return self.chapter.course
    
    @property
    def duration_minutes(self):
        """Duration in minutes (rounded)"""
        return round(self.duration_seconds / 60, 1)
    
    @property
    def formatted_duration(self):
        """Human-readable duration (e.g., '1h 30m' or '45m')"""
        total_seconds = self.duration_seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s" if seconds > 0 else f"{minutes}m"
        else:
            return f"{seconds}s"
    
    @property
    def resources_count(self):
        """Total resources (if model exists)"""
        return self.resources_of_lesson.count() if hasattr(self, 'resources_of_lesson') else 0
    
    @property
    def quizzes_count(self):
        """Total quizzes (if model exists)"""
        return self.quizzes_of_lesson.count() if hasattr(self, 'quizzes_of_lesson') else 0
    
    def set_preview(self, is_preview=True):
        """Toggle preview status"""
        self.is_preview = is_preview
        self.save(update_fields=['is_preview', 'updated_at'])
    
    def enable_preview(self):
        """Make lesson available as preview"""
        self.set_preview(True)
    
    def disable_preview(self):
        """Remove preview access"""
        self.set_preview(False)