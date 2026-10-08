"""Shared image ratio, upload help text, size limit and validator for the core models."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024

# Width to height of a core record's image. It is the shape of the banner across the top of the
# overview page, so an upload is cut to it and what the uploader sees is what the page shows.
IMAGE_RATIO = (3, 1)

IMAGE_HELP_TEXT = _(
    "Upload a representative image. It is shown as a banner at a 3:1 ratio (e.g. 2400x800 px), "
    "and an image of any other shape is cropped to that around its centre when it is uploaded. "
    "Accepted formats: JPEG, PNG, WebP. Maximum file size: 5 MB."
)


def crop_to_ratio(image, ratio=None, **kwargs):
    """Cut an image to a width-to-height ratio around its centre.

    An easy-thumbnails processor. It runs before ``scale_and_crop``, whose own cropping only
    reaches the target ratio when the image is at least the target size.

    Args:
        image: The PIL image being processed.
        ratio: ``(width, height)`` to cut to. The image is returned untouched without one.
        **kwargs: The other thumbnail options, which this processor does not read.

    Returns:
        The image, cut on its longer side so its shape matches ``ratio``.
    """
    if not ratio:
        return image
    width, height = image.size
    ratio_width, ratio_height = ratio
    target_width = min(width, round(height * ratio_width / ratio_height))
    target_height = min(height, round(width * ratio_height / ratio_width))
    left = (width - target_width) // 2
    top = (height - target_height) // 2
    return image.crop((left, top, left + target_width, top + target_height))


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
