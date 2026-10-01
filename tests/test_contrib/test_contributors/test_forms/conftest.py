"""Fixtures for the contributor forms: an uploaded image and a complete profile submission."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


@pytest.fixture
def image_upload():
    """Build a small valid image upload."""

    def build(name="photo.png"):
        buffer = BytesIO()
        Image.new("RGB", (20, 20), "blue").save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    return build


@pytest.fixture
def profile_data():
    """Every field of a person's profile form, filled in with valid values."""
    return {
        "name": "Dr. Ada Lovelace",
        "alternative_names": "A. Lovelace\nAugusta Ada King",
        "profile": "Mathematician and writer.",
        "links": "https://example.org/ada\nhttp://example.org/notes",
        "lang": ["en", "fr"],
    }
