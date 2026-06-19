"""Shared image upload utilities for core FairDM models.

Provides the common help text, file-size validator, and upload constants
used by Project, Dataset, Sample, and Measurement image fields.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Maximum allowed upload size for representative images (5 MB)
MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# Standard help text displayed on all four core model image fields.
# Communicates the expected aspect ratio, accepted formats, size cap, and
# the centre-crop behaviour applied when the source does not match 3:2.
IMAGE_HELP_TEXT = _(
    "Upload a representative image (recommended 3:2 ratio, e.g. 1200×800 px). "
    "Accepted formats: JPEG, PNG, WebP. Maximum file size: 5 MB. "
    "Images that do not match the 3:2 ratio will be centre-cropped on display."
)


def validate_image_file_size(file):
    """Raise ValidationError if *file* exceeds MAX_IMAGE_UPLOAD_BYTES.

    Args:
        file: An uploaded file object with a ``size`` attribute (bytes).

    Raises:
        ValidationError: When the uploaded file is larger than 5 MB, with a
            human-readable message that includes the actual size in MB.
    """
    if file.size > MAX_IMAGE_UPLOAD_BYTES:
        actual_mb = file.size / (1024 * 1024)
        raise ValidationError(
            _("The uploaded file is %(actual).1f MB. Please upload an image smaller than 5 MB."),
            params={"actual": actual_mb},
        )
