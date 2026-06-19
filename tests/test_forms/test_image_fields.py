"""Tests for image field behaviour across all four core model forms.

Covers:
- US1: Help text, widget, file-size validation (T009–T012, T034, T035)
- US2: Thumbnail alias resolution (T019, T020)
- US3: Cross-model consistency (T026)

Test-first (TDD): these tests are written before the implementation tasks
T013–T016, T022. They should be RED initially and GREEN after implementation.
"""

import io

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.loader import render_to_string
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.core.image_utils import validate_image_file_size

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_small_jpeg() -> bytes:
    """Return bytes for a minimal valid JPEG (≈ a few KB)."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 100, 50)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_uploaded_file(content: bytes, name: str, content_type: str, size: int | None = None):
    """Wrap *content* in an InMemoryUploadedFile.

    *size* overrides the reported file size so we can test the validator
    without needing a genuinely enormous file on disk.
    """
    file_obj = io.BytesIO(content)
    reported_size = size if size is not None else len(content)
    return InMemoryUploadedFile(
        file=file_obj,
        field_name="image",
        name=name,
        content_type=content_type,
        size=reported_size,
        charset=None,
    )


def _make_pdf_bytes() -> bytes:
    """Return bytes for a minimal fake PDF (not a valid image)."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


# ---------------------------------------------------------------------------
# T009 — Help text contains "3:2"
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "import_path",
    [
        "fairdm.core.project.forms.ProjectForm",
        "fairdm.core.dataset.forms.DatasetForm",
        "fairdm.core.sample.forms.SampleForm",
        "fairdm.core.measurement.forms.MeasurementForm",
    ],
)
def test_image_help_text_contains_ratio(import_path):
    """T009: Each core form's image field help text contains '3:2'."""
    module_path, class_name = import_path.rsplit(".", 1)
    import importlib

    mod = importlib.import_module(module_path)
    form_cls = getattr(mod, class_name)
    form = form_cls()
    help_text = str(form.fields["image"].help_text)
    assert "3:2" in help_text, f"{class_name}.image.help_text does not contain '3:2'. Got: {help_text!r}"


# ---------------------------------------------------------------------------
# T010 — Widget is ImageClearableFileInput
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "import_path",
    [
        "fairdm.core.project.forms.ProjectForm",
        "fairdm.core.dataset.forms.DatasetForm",
        "fairdm.core.sample.forms.SampleForm",
        "fairdm.core.measurement.forms.MeasurementForm",
    ],
)
def test_image_field_uses_clearable_widget(import_path):
    """T010: Each core form's image field uses ImageClearableFileInput."""
    module_path, class_name = import_path.rsplit(".", 1)
    import importlib

    mod = importlib.import_module(module_path)
    form_cls = getattr(mod, class_name)
    form = form_cls()
    widget = form.fields["image"].widget
    assert isinstance(widget, ImageClearableFileInput), (
        f"{class_name}.image.widget is {type(widget).__name__}, expected ImageClearableFileInput"
    )


# ---------------------------------------------------------------------------
# T011 — Oversized file is rejected
# ---------------------------------------------------------------------------


def test_image_field_rejects_oversized_file():
    """T011: ProjectForm rejects an image reported as > 5 MB."""
    from fairdm.core.project.forms import ProjectForm

    jpeg_bytes = _make_small_jpeg()
    oversized = _make_uploaded_file(
        content=jpeg_bytes,
        name="big.jpg",
        content_type="image/jpeg",
        size=6 * 1024 * 1024,  # 6 MB reported size
    )
    form = ProjectForm(data={}, files={"image": oversized})
    assert "image" in form.errors, "Expected 'image' in form.errors for 6 MB file"
    error_text = " ".join(str(e) for e in form.errors["image"])
    assert "5" in error_text or "MB" in error_text, f"Expected file-size error message, got: {error_text!r}"


# ---------------------------------------------------------------------------
# T012 — Valid file is accepted
# ---------------------------------------------------------------------------


def test_image_field_accepts_valid_file():
    """T012: ProjectForm accepts a valid JPEG reported as ≤ 5 MB."""
    from fairdm.core.project.forms import ProjectForm

    jpeg_bytes = _make_small_jpeg()
    valid_file = _make_uploaded_file(
        content=jpeg_bytes,
        name="valid.jpg",
        content_type="image/jpeg",
        size=1 * 1024 * 1024,  # 1 MB
    )
    # Provide the minimum required non-file fields
    from fairdm.core.choices import ProjectStatus
    from fairdm.utils.choices import Visibility

    form = ProjectForm(
        data={
            "name": "Test project",
            "status": str(ProjectStatus.CONCEPT),
            "visibility": str(Visibility.PRIVATE),
        },
        files={"image": valid_file},
    )
    assert form.is_valid(), f"Expected valid form, got errors: {form.errors}"


# ---------------------------------------------------------------------------
# T034 — Non-image file (PDF) is rejected
# ---------------------------------------------------------------------------


def test_image_field_rejects_non_image():
    """T034: ProjectForm rejects a file that is not a valid image (FR-004)."""
    from fairdm.core.project.forms import ProjectForm

    pdf_file = _make_uploaded_file(
        content=_make_pdf_bytes(),
        name="document.pdf",
        content_type="application/pdf",
        size=1 * 1024 * 1024,
    )
    form = ProjectForm(data={}, files={"image": pdf_file})
    assert "image" in form.errors, "Expected 'image' in form.errors for a PDF file"


# ---------------------------------------------------------------------------
# T035 — Clearing the image field leaves image falsy; template shows placeholder
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_image_field_clear_shows_placeholder():
    """T035: Clearing the image field leaves instance.image falsy (FR-008 / Edge Case 5).

    Also asserts that the object_card template renders the static placeholder
    asset in the <img src> attribute when image is absent.
    """
    from fairdm.factories import ProjectFactory

    # Create a project that initially has an image (factory generates one by default)
    project = ProjectFactory()
    assert project.image, "Precondition: project should have an image after factory creation"

    # Clear the image by saving the project without an image
    project.image = None
    project.save(update_fields=["image"])
    project.refresh_from_db()
    assert not project.image, "After clearing, project.image should be falsy"

    # Assert the object_card template renders the static placeholder path
    # (requires T022 to update the template; this assertion is RED until then)
    html = render_to_string(
        "cotton/components/object_card.html",
        {
            "image": None,
            "title": "Test Project",
            "object": project,
            "object_type": "project",
            "subtitle": "",
            "description": "",
            "tags": project.tags,
            "badge_text": "",
        },
    )
    assert "placeholder-3x2.png" in html, (
        "object_card template should render the local placeholder image when 'image' is falsy. Got:\n" + html[:500]
    )


# ---------------------------------------------------------------------------
# T019 — core_small alias resolves for a project with an image
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_core_small_alias_resolves():
    """T019: project.image['core_small'] returns a non-empty URL."""
    from fairdm.factories import ProjectFactory

    project = ProjectFactory()
    assert project.image, "Precondition: project must have an image"
    thumbnail = project.image["core_small"]
    url = thumbnail.url
    assert url, f"core_small thumbnail URL should be non-empty, got: {url!r}"


# ---------------------------------------------------------------------------
# T020 — core_large alias resolves for a project with an image
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_core_large_alias_resolves():
    """T020: project.image['core_large'] returns a non-empty URL."""
    from fairdm.factories import ProjectFactory

    project = ProjectFactory()
    assert project.image, "Precondition: project must have an image"
    thumbnail = project.image["core_large"]
    url = thumbnail.url
    assert url, f"core_large thumbnail URL should be non-empty, got: {url!r}"


# ---------------------------------------------------------------------------
# T026 — All four forms are uniform (parametrised consistency test)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "import_path",
    [
        "fairdm.core.project.forms.ProjectForm",
        "fairdm.core.dataset.forms.DatasetForm",
        "fairdm.core.sample.forms.SampleForm",
        "fairdm.core.measurement.forms.MeasurementForm",
    ],
)
def test_all_core_forms_image_field_uniform(import_path):
    """T026: All four core forms expose identical image field configuration."""
    module_path, class_name = import_path.rsplit(".", 1)
    import importlib

    mod = importlib.import_module(module_path)
    form_cls = getattr(mod, class_name)
    form = form_cls()
    field = form.fields["image"]

    # help_text contains "3:2"
    assert "3:2" in str(field.help_text), f"{class_name}: help_text must contain '3:2', got {field.help_text!r}"

    # widget is ImageClearableFileInput
    assert isinstance(field.widget, ImageClearableFileInput), (
        f"{class_name}: widget must be ImageClearableFileInput, got {type(field.widget).__name__}"
    )

    # validate_image_file_size is in validators
    assert validate_image_file_size in field.validators, (
        f"{class_name}: validate_image_file_size must be in image field validators"
    )

    # required is False
    assert field.required is False, f"{class_name}: image field must not be required, got required={field.required}"
