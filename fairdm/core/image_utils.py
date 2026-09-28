"""Shared image upload help text, size limit and validator for the core models."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024

IMAGE_HELP_TEXT = _(
    "Upload a representative image (recommended 3:2 ratio, e.g. 1200x800 px). "
    "Accepted formats: JPEG, PNG, WebP. Maximum file size: 5 MB. "
    "Images that do not match the 3:2 ratio will be centre-cropped on display."
)


def validate_image_file_size(file):
    """Reject an uploaded file larger than ``MAX_IMAGE_UPLOAD_BYTES``.

    Args:
        file: An uploaded file object with a ``size`` attribute (bytes).

    Raises:
        ValidationError: The uploaded file is larger than 5 MB. The message
            includes the actual size in MB.
    """
    if file.size > MAX_IMAGE_UPLOAD_BYTES:
        actual_mb = file.size / (1024 * 1024)
        raise ValidationError(
            _(
                "The uploaded file is %(actual).1f MB. Please upload an image smaller than 5 MB."
            ),
            params={"actual": actual_mb},
        )
