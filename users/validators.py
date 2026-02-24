import os
import re
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# =====================
# CONFIGURATION CONSTANTS
# =====================

MIN_EXPERIENCE_YEARS = 1
MAX_EXPERIENCE_YEARS = 50
MAX_CV_FILE_SIZE_MB = getattr(settings, "MAX_CV_FILE_SIZE_MB", 5)
ALLOWED_CV_EXTENSIONS = getattr(settings, "ALLOWED_CV_EXTENSIONS", ["pdf"])
MIN_ACADEMIC_YEAR = 1
MAX_ACADEMIC_YEAR = 12

# =====================
# CUSTOM VALIDATORS
# =====================


def validate_file_size(value):
    """
    Validate uploaded file size.

    Args:
        value: Django UploadedFile object

    Raises:
        ValidationError: If file exceeds maximum size
    """
    if not value:
        return

    max_size_bytes = MAX_CV_FILE_SIZE_MB * 1024 * 1024
    filesize = value.size

    if filesize > max_size_bytes:
        raise ValidationError(
            _(
                "File size cannot exceed %(max_size)sMB. "
                "Current size: %(current_size).2fMB"
            ),
            params={
                "max_size": MAX_CV_FILE_SIZE_MB,
                "current_size": filesize / (1024 * 1024),
            },
            code="file_too_large",
        )


def validate_pdf(file):
    """
    Validate PDF by checking file header magic bytes.

    PDF files must start with %PDF- signature.
    This prevents users from uploading malicious files with .pdf extension.

    Args:
        file: Django UploadedFile object

    Raises:
        ValidationError: If file is not a valid PDF

    Note:
        For production, integrate with virus scanning (ClamAV) and
        consider using PyPDF2 for deeper validation.
    """
    if not file:
        return

    try:
        # Ensure file pointer is at start
        file.seek(0)

        # Read first 5 bytes for PDF signature
        header = file.read(5)

        # Reset file pointer for subsequent operations
        file.seek(0)

        # Validate PDF signature
        if not header or not header.startswith(b"%PDF-"):
            raise ValidationError(
                _(
                    "Invalid PDF file. The file may be corrupted or in the wrong format."
                ),
                code="invalid_pdf_format",
            )

    except AttributeError:
        # File object doesn't support seek (shouldn't happen with UploadedFile)
        raise ValidationError(
            _("Unable to validate file format. Invalid file object."),
            code="invalid_file_object",
        )
    except Exception as e:
        # Log this in production
        raise ValidationError(
            _("Error validating PDF: %(error)s"),
            params={"error": str(e)},
            code="pdf_validation_error",
        )


def validate_phone(value):
    """
    Validate Egyptian phone number format.
    Expected: 11 digits starting with 010, 011, 012, or 015
    Example: 01012345678
    """
    if not value:
        return

    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\(\)]", "", str(value))

    # Egyptian mobile pattern: 010/011/012/015 + 8 digits
    pattern = r"^(010|011|012|013|014|015)(\d{8}|\d{7})$"

    if not re.match(pattern, cleaned):
        raise ValidationError(
            "Invalid Egyptian phone number. Must be 11 digits starting with "
            "010, 011, 012, or 015. Example: 01012345678"
        )


def validate_phone_optional(value):
    """
    Optional phone validator that allows empty/null values.

    Args:
        value: Phone number string or None
    """
    if not value or str(value).strip() == "":
        return
    validate_phone(value)


def validate_academic_year(value):
    """
    Validate academic year is within K-12 education range.

    Args:
        value: Academic year (grade level)

    Raises:
        ValidationError: If year is outside valid range
    """
    if not (MIN_ACADEMIC_YEAR <= value <= MAX_ACADEMIC_YEAR):
        raise ValidationError(
            _("Academic year must be between %(min)s and %(max)s. Got: %(value)s"),
            params={"min": MIN_ACADEMIC_YEAR, "max": MAX_ACADEMIC_YEAR, "value": value},
            code="invalid_academic_year",
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
    ext = filename.split(".")[-1].lower()

    # Create safe filename using username (limit to 50 chars)
    safe_name = slugify(instance.user.username)[:50]
    new_filename = f"{safe_name}-cv.{ext}"

    return os.path.join("users", "cv", str(instance.user.id), new_filename)
