import os
import uuid
from PIL import Image
from decimal import Decimal
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

# =====================
# CONFIGURATION CONSTANTS
# =====================

# Image upload settings
MAX_IMAGE_SIZE_MB = getattr(settings, "MAX_COURSE_IMAGE_SIZE_MB", 2)
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 200
MAX_IMAGE_WIDTH = 4000
MAX_IMAGE_HEIGHT = 4000
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
# Course pricing
MIN_COURSE_PRICE = Decimal("5.00")
MAX_COURSE_PRICE = Decimal("999999.99")
# Review ratings
MIN_RATING = Decimal("1.0")
MAX_RATING = Decimal("5.0")

# ==================
# CUSTOM VALIDATORS
# ==================


def validate_image_size(value):
    """
    Validate uploaded image size.

    Args:
        value: Django UploadedFile object

    Raises:
        ValidationError: If file exceeds maximum size
    """
    if not value:
        return

    max_size_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    filesize = value.size

    if filesize > max_size_bytes:
        raise ValidationError(
            _(
                "Image size cannot exceed %(max_size)sMB. "
                "Current size: %(current_size).2fMB"
            ),
            params={
                "max_size": MAX_IMAGE_SIZE_MB,
                "current_size": filesize / (1024 * 1024),
            },
            code="image_too_large",
        )


def validate_image_dimensions(value):
    """
    Validate image dimensions.

    Requirements:
    - Minimum: 200x200px (ensures quality)
    - Maximum: 4000x4000px (prevents abuse)

    Args:
        value: Django UploadedFile object

    Raises:
        ValidationError: If dimensions are outside acceptable range
    """
    if not value:
        return

    try:
        # Open image and get dimensions
        img = Image.open(value)
        width, height = img.size

        # Validate minimum dimensions
        if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
            raise ValidationError(
                _("""Image dimensions too small. Minimum
                    %(min_width)sx%(min_height)spx. """ "Got: %(width)sx%(height)spx"),
                params={
                    "min_width": MIN_IMAGE_WIDTH,
                    "min_height": MIN_IMAGE_HEIGHT,
                    "width": width,
                    "height": height,
                },
                code="image_too_small",
            )

        # Validate maximum dimensions
        if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
            raise ValidationError(
                _(
                    """Image dimensions too large.
                    Maximum %(max_width)sx%(max_height)spx. """
                    "Got: %(width)sx%(height)spx"
                ),
                params={
                    "max_width": MAX_IMAGE_WIDTH,
                    "max_height": MAX_IMAGE_HEIGHT,
                    "width": width,
                    "height": height,
                },
                code="image_too_large",
            )

        value.seek(0)

    except Exception as e:
        raise ValidationError(
            _("Invalid image file: %(error)s"),
            params={"error": str(e)},
            code="invalid_image",
        )


# =====================
# UPLOAD PATH FUNCTIONS
# =====================


def education_flag_path(instance, filename):
    """
    Generate secure upload path for education country flags.

    Path: education/flags/{country_slug}-{uuid}.{ext}
    Example: education/flags/egypt-a1b2c3d4.png

    Security improvements:
    - Added UUID to prevent collisions
    - Sanitized extension
    - Validated extension exists

    Args:
        instance: Education model instance
        filename: Original uploaded filename

    Returns:
        str: Secure file path
    """
    # Validate extension exists
    if "." not in filename:
        raise ValidationError(
            _("Filename must have an extension"), code="missing_extension"
        )

    ext = filename.split(".")[-1].lower()

    # Security: Sanitize extension
    ext = "".join(c for c in ext if c.isalnum())

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            _("Invalid file extension: %(ext)s. Allowed: %(allowed)s"),
            params={"ext": ext, "allowed": ", ".join(ALLOWED_IMAGE_EXTENSIONS)},
            code="invalid_extension",
        )

    # Create safe filename with UUID to prevent collisions
    safe_name = slugify(instance.country)[:50]
    unique_id = str(uuid.uuid4())[:8]
    new_filename = f"{safe_name}-{unique_id}.{ext}"

    return os.path.join("education", "flags", new_filename)


def course_image_path(instance, filename):
    """
    Generate secure upload path for course thumbnails.

    Path: courses/thumbnails/{year}/{month}/{course-slug}-{uuid}.{ext}
    Example: courses/thumbnails/2025/02/intro-python-a1b2c3d4.jpg

    Benefits:
    - Organized by date for easier management
    - UUID prevents filename collisions
    - Supports multiple image versions

    Args:
        instance: Course model instance
        filename: Original uploaded filename

    Returns:
        str: Secure file path
    """
    # Validate extension exists
    if "." not in filename:
        raise ValidationError(
            _("Filename must have an extension"), code="missing_extension"
        )

    ext = filename.split(".")[-1].lower()

    # Security: Sanitize extension
    ext = "".join(c for c in ext if c.isalnum())

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            _("Invalid file extension: %(ext)s. Allowed: %(allowed)s"),
            params={"ext": ext, "allowed": ", ".join(ALLOWED_IMAGE_EXTENSIONS)},
            code="invalid_extension",
        )

    # Create safe filename
    safe_title = slugify(instance.title)[:50]
    unique_id = str(uuid.uuid4())[:8]
    new_filename = f"{safe_title}-{unique_id}.{ext}"

    # Use current date for organization
    now = timezone.now()
    year = now.year
    month = str(now.month).zfill(2)  # Zero-padded month

    return os.path.join("courses", "thumbnails", str(year), month, new_filename)


def validate_video_duration(value):
    """Validate video duration (1 second to 4 hours)"""
    if not (1 <= value <= 14400):  # 4 hours = 14400 seconds
        raise ValidationError(
            _(f"Video duration must be between 1s - 4h. Got: {value} seconds")
        )
