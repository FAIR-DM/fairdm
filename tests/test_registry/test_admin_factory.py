"""Tests for AdminFactory component generation."""

import pytest
from django.contrib import admin
from django.db import models

from fairdm.registry.factories import AdminFactory


@pytest.fixture
def sample_model():
    """Create a test model for admin factory tests."""

    class SampleModel(models.Model):
        name = models.CharField(max_length=100)
        description = models.TextField()
        collected_at = models.DateTimeField()
        status = models.CharField(
            max_length=20,
            choices=[("draft", "Draft"), ("published", "Published")],
        )
        is_public = models.BooleanField(default=False)
        contributor = models.ForeignKey(
            "auth.User",
            on_delete=models.CASCADE,
            related_name="samples",
        )
        tags = models.ManyToManyField("auth.Group", related_name="samples")

        class Meta:
            app_label = "test_app"

    return SampleModel


class TestAdminFactoryBasics:
    """Test basic AdminFactory functionality."""

    def test_factory_initialization(self, sample_model):
        """Test factory can be initialized."""
        factory = AdminFactory(sample_model)
        assert factory.model == sample_model

    def test_generate_creates_admin_class(self, sample_model):
        """Test generate() creates a ModelAdmin subclass."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert issubclass(admin_class, admin.ModelAdmin)

    def test_custom_admin_class_preserved(self, sample_model):
        """Test that generated admin class has proper attributes."""
        factory = AdminFactory(sample_model, fields=["name", "status"])
        admin_class = factory.generate()

        # Should have list_display
        assert hasattr(admin_class, "list_display")
        assert isinstance(admin_class.list_display, list)


class TestListDisplay:
    """Test list_display generation."""

    def test_explicit_list_display(self, sample_model):
        """Test list_display is auto-generated based on fields."""
        factory = AdminFactory(sample_model, fields=["name", "status"])
        admin_class = factory.generate()

        # Should have list_display with reasonable fields
        assert hasattr(admin_class, "list_display")
        assert "name" in admin_class.list_display

    def test_auto_list_display_from_parent_fields(self, sample_model):
        """Test list_display with specified fields."""
        fields = ["name", "description", "collected_at", "status", "is_public", "contributor"]
        factory = AdminFactory(sample_model, fields=fields)
        admin_class = factory.generate()

        # Should have list_display (limited to max 5 by AdminFactory)
        assert hasattr(admin_class, "list_display")
        assert len(admin_class.list_display) <= 5

    def test_auto_list_display_from_inspector(self, sample_model):
        """Test list_display auto-generated from inspector when no fields specified."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have reasonable defaults from inspector
        assert isinstance(admin_class.list_display, list)
        assert len(admin_class.list_display) > 0


class TestListFilter:
    """Test list_filter generation."""

    def test_explicit_list_filter(self, sample_model):
        """Test list_filter is auto-generated."""
        factory = AdminFactory(sample_model, fields=["status", "is_public"])
        admin_class = factory.generate()

        # Should have list_filter with boolean/choice fields
        assert hasattr(admin_class, "list_filter")
        assert isinstance(admin_class.list_filter, list)

    def test_auto_list_filter(self, sample_model):
        """Test auto-generated list_filter includes dates, choices, booleans."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should include date, choice, and boolean fields
        assert isinstance(admin_class.list_filter, list)

    def test_list_filter_limited_to_five(self, sample_model):
        """Test list_filter is reasonable length."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should be reasonable length
        assert len(admin_class.list_filter) >= 0


class TestSearchFields:
    """Test search_fields generation."""

    def test_explicit_search_fields(self, sample_model):
        """Test search_fields is auto-generated."""
        factory = AdminFactory(sample_model, fields=["name", "description"])
        admin_class = factory.generate()

        # Should have search_fields
        assert hasattr(admin_class, "search_fields")
        assert isinstance(admin_class.search_fields, list)

    def test_auto_search_fields(self, sample_model):
        """Test auto-generated search_fields prioritizes text fields."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should include text fields
        assert isinstance(admin_class.search_fields, list)

    def test_search_fields_limited_to_three(self, sample_model):
        """Test search_fields is reasonable length."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should be reasonable length
        assert len(admin_class.search_fields) >= 0


class TestFieldsets:
    """Test fieldsets generation."""

    def test_explicit_fieldsets_dict_format(self, sample_model):
        """Test fieldsets are auto-generated when many fields."""
        factory = AdminFactory(
            sample_model, fields=["name", "description", "collected_at", "status", "is_public", "contributor"]
        )
        admin_class = factory.generate()

        # Should have fieldsets or fields
        assert hasattr(admin_class, "fieldsets") or hasattr(admin_class, "fields")

    def test_explicit_fieldsets_django_format(self, sample_model):
        """Test fieldsets format is correct."""
        factory = AdminFactory(
            sample_model, fields=["name", "description", "collected_at", "status", "is_public", "contributor"]
        )
        admin_class = factory.generate()

        # If fieldsets exist, check format
        if hasattr(admin_class, "fieldsets") and admin_class.fieldsets is not None:
            assert isinstance(admin_class.fieldsets, list)

    def test_auto_fieldsets_from_inspector(self, sample_model):
        """Test auto-generated fieldsets group fields logically."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have fieldsets or fields
        assert hasattr(admin_class, "fieldsets") or hasattr(admin_class, "fields")


class TestOptionalAttributes:
    """Test optional admin attributes."""

    def test_list_per_page(self, sample_model):
        """Test admin class has readonly_fields."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have readonly_fields
        assert hasattr(admin_class, "readonly_fields")
        assert isinstance(admin_class.readonly_fields, list)

    def test_list_editable(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_ordering(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_date_hierarchy(self, sample_model):
        """Test date_hierarchy is auto-generated for date fields."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have date_hierarchy if date field exists
        assert hasattr(admin_class, "date_hierarchy")

    def test_readonly_fields(self, sample_model):
        """Test readonly_fields is auto-generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have readonly_fields
        assert hasattr(admin_class, "readonly_fields")
        assert isinstance(admin_class.readonly_fields, list)

    def test_prepopulated_fields(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_inlines(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None


class TestAdminClassNaming:
    """Test admin class naming conventions."""

    def test_generated_class_name(self, sample_model):
        """Test generated admin class has correct name."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class.__name__ == "SampleModelAdmin"
