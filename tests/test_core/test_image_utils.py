"""Tests for image field behaviour across all four core model forms."""

import io

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.loader import render_to_string
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.core.image_utils import validate_image_file_size


def _make_small_jpeg() -> bytes:
    """Return bytes for a minimal valid JPEG (≈ a few KB)."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 100, 50)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_uploaded_file(
    content: bytes, name: str, content_type: str, size: int | None = None
):
    """Wrap *content* in an InMemoryUploadedFile."""
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


class TestImageFieldWidgetAndValidation:
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
    def test_image_field_uses_clearable_widget(self, import_path):
        module_path, class_name = import_path.rsplit(".", 1)
        import importlib

        mod = importlib.import_module(module_path)
        form_cls = getattr(mod, class_name)
        form = form_cls()
        widget = form.fields["image"].widget
        assert isinstance(widget, ImageClearableFileInput), (
            f"{class_name}.image.widget is {type(widget).__name__}, expected ImageClearableFileInput"
        )

    def test_image_field_rejects_oversized_file(self):
        from fairdm.core.project.forms import ProjectForm

        jpeg_bytes = _make_small_jpeg()
        oversized = _make_uploaded_file(
            content=jpeg_bytes,
            name="big.jpg",
            content_type="image/jpeg",
            size=6 * 1024 * 1024,
        )
        form = ProjectForm(data={}, files={"image": oversized})
        assert "image" in form.errors, "Expected 'image' in form.errors for 6 MB file"

    def test_image_field_accepts_valid_file(self):
        from fairdm.core.project.forms import ProjectForm

        jpeg_bytes = _make_small_jpeg()
        valid_file = _make_uploaded_file(
            content=jpeg_bytes,
            name="valid.jpg",
            content_type="image/jpeg",
            size=1 * 1024 * 1024,
        )
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

    def test_image_field_rejects_non_image(self):
        from fairdm.core.project.forms import ProjectForm

        pdf_file = _make_uploaded_file(
            content=_make_pdf_bytes(),
            name="document.pdf",
            content_type="application/pdf",
            size=1 * 1024 * 1024,
        )
        form = ProjectForm(data={}, files={"image": pdf_file})
        assert "image" in form.errors, "Expected 'image' in form.errors for a PDF file"

    @pytest.mark.django_db
    def test_image_field_clear_shows_placeholder(self):
        from fairdm.factories import ProjectFactory

        # The factory leaves `image` unset by default (issue #323), so this test
        # asks for one explicitly since the assertions below need a real file.
        project = ProjectFactory(with_image=True)
        assert project.image, (
            "Precondition: project should have an image after factory creation"
        )

        project.image = None
        project.save(update_fields=["image"])
        project.refresh_from_db()
        assert not project.image, "After clearing, project.image should be falsy"

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
            "object_card template should render the local placeholder image when 'image' is falsy. Got:\n"
            + html[:500]
        )


class TestImageThumbnailAliases:
    @pytest.mark.django_db
    def test_core_small_alias_resolves(self):
        from fairdm.factories import ProjectFactory

        project = ProjectFactory(with_image=True)
        assert project.image, "Precondition: project must have an image"
        thumbnail = project.image["core_small"]
        url = thumbnail.url
        assert url, f"core_small thumbnail URL should be non-empty, got: {url!r}"

    @pytest.mark.django_db
    def test_core_large_alias_resolves(self):
        from fairdm.factories import ProjectFactory

        project = ProjectFactory(with_image=True)
        assert project.image, "Precondition: project must have an image"
        thumbnail = project.image["core_large"]
        url = thumbnail.url
        assert url, f"core_large thumbnail URL should be non-empty, got: {url!r}"


    @pytest.mark.django_db
    def test_core_banner_alias_is_three_to_one(self):
        import factory
        from fairdm.factories import ProjectFactory

        project = ProjectFactory(
            image=factory.django.ImageField(width=3000, height=2000)
        )

        thumbnail = project.image["core_banner"]

        assert (thumbnail.width, thumbnail.height) == (1800, 600)


class TestCropToRatio:
    @pytest.mark.parametrize(
        ("size", "expected"),
        [
            ((800, 600), (800, 267)),  # too tall: rows are cut
            ((4000, 500), (1500, 500)),  # too wide: columns are cut
            ((900, 300), (900, 300)),  # already 3:1: untouched
        ],
    )
    def test_the_image_is_cut_to_the_ratio(self, size, expected):
        from fairdm.core.image_utils import crop_to_ratio
        from PIL import Image

        cropped = crop_to_ratio(Image.new("RGB", size), ratio=(3, 1))

        assert cropped.size == expected

    def test_the_cut_keeps_the_centre(self):
        from fairdm.core.image_utils import crop_to_ratio
        from PIL import Image

        image = Image.new("RGB", (300, 300), color=(0, 0, 0))
        image.paste((255, 255, 255), (0, 100, 300, 200))  # a white band across the middle

        cropped = crop_to_ratio(image, ratio=(3, 1))

        assert cropped.getpixel((0, 0)) == (255, 255, 255)
        assert cropped.getpixel((299, 99)) == (255, 255, 255)

    def test_an_image_is_left_alone_when_no_ratio_is_asked_for(self):
        from fairdm.core.image_utils import crop_to_ratio
        from PIL import Image

        image = Image.new("RGB", (800, 600))

        assert crop_to_ratio(image).size == (800, 600)


@pytest.mark.django_db
class TestUploadedImageRatio:
    @pytest.mark.parametrize(
        "factory_name",
        ["ProjectFactory", "DatasetFactory"],
    )
    def test_an_uploaded_image_is_stored_at_three_to_one(self, factory_name):
        import factory
        import fairdm.factories as factories

        record = getattr(factories, factory_name)(
            image=factory.django.ImageField(width=800, height=600)
        )

        assert (record.image.width, record.image.height) == (800, 267)

    def test_a_large_upload_is_scaled_down_after_the_cut(self):
        import factory
        from fairdm.factories import ProjectFactory

        project = ProjectFactory(
            image=factory.django.ImageField(width=3000, height=2000)
        )

        assert (project.image.width, project.image.height) == (2400, 800)


class TestImageFieldUniformity:
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
    def test_all_core_forms_image_field_uniform(self, import_path):
        module_path, class_name = import_path.rsplit(".", 1)
        import importlib

        mod = importlib.import_module(module_path)
        form_cls = getattr(mod, class_name)
        form = form_cls()
        field = form.fields["image"]

        assert isinstance(field.widget, ImageClearableFileInput), (
            f"{class_name}: widget must be ImageClearableFileInput, got {type(field.widget).__name__}"
        )

        assert validate_image_file_size in field.validators, (
            f"{class_name}: validate_image_file_size must be in image field validators"
        )

        assert field.required is False, (
            f"{class_name}: image field must not be required, got required={field.required}"
        )
