"""Tests for AdminFactory component generation."""

import pytest
from django.contrib import admin
from django.db import models

from fairdm.config_components import AdminConfig
from fairdm.utils.component_factories import AdminFactory


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
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        assert factory.model == sample_model
        assert factory.config == config

    def test_generate_creates_admin_class(self, sample_model):
        """Test generate() creates a ModelAdmin subclass."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert issubclass(admin_class, admin.ModelAdmin)
        assert admin_class.model == sample_model

    def test_custom_admin_class_preserved(self, sample_model):
        """Test that custom admin_class is preserved when provided."""

        class CustomAdmin(admin.ModelAdmin):
            list_display = ["custom_field"]

        config = AdminConfig(admin_class=CustomAdmin)
        factory = AdminFactory(sample_model, config)
        result = factory.generate()

        assert result == CustomAdmin


class TestListDisplay:
    """Test list_display generation."""

    def test_explicit_list_display(self, sample_model):
        """Test explicit list_display is used when provided."""
        config = AdminConfig(list_display=["name", "status"])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.list_display == ["name", "status"]

    def test_auto_list_display_from_parent_fields(self, sample_model):
        """Test list_display uses parent_fields as fallback."""
        config = AdminConfig()
        parent_fields = ["name", "description", "collected_at", "status", "is_public", "contributor"]
        factory = AdminFactory(sample_model, config, parent_fields=parent_fields)
        admin_class = factory.generate()

        # Should use first 5 from parent fields
        assert admin_class.list_display == ["name", "description", "collected_at", "status", "is_public"]

    def test_auto_list_display_from_inspector(self, sample_model):
        """Test list_display auto-generated from inspector when no config."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        # Should have reasonable defaults from inspector
        assert isinstance(admin_class.list_display, list)
        assert len(admin_class.list_display) > 0
        assert "name" in admin_class.list_display  # Common field


class TestListFilter:
    """Test list_filter generation."""

    def test_explicit_list_filter(self, sample_model):
        """Test explicit list_filter is used when provided."""
        config = AdminConfig(list_filter=["status", "is_public"])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.list_filter == ["status", "is_public"]

    def test_auto_list_filter(self, sample_model):
        """Test auto-generated list_filter includes dates, choices, booleans."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        # Should include date, choice, and boolean fields
        assert isinstance(admin_class.list_filter, list)
        # Should include these filterable types
        filters_set = set(admin_class.list_filter)
        assert "collected_at" in filters_set or "status" in filters_set or "is_public" in filters_set

    def test_list_filter_limited_to_five(self, sample_model):
        """Test list_filter is limited to 5 items max."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert len(admin_class.list_filter) <= 5


class TestSearchFields:
    """Test search_fields generation."""

    def test_explicit_search_fields(self, sample_model):
        """Test explicit search_fields is used when provided."""
        config = AdminConfig(search_fields=["name", "description"])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.search_fields == ["name", "description"]

    def test_auto_search_fields(self, sample_model):
        """Test auto-generated search_fields prioritizes common fields."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        # Should include text fields, prioritizing "name"
        assert isinstance(admin_class.search_fields, list)
        assert "name" in admin_class.search_fields  # Priority field

    def test_search_fields_limited_to_three(self, sample_model):
        """Test search_fields is limited to 3 items max."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert len(admin_class.search_fields) <= 3


class TestFieldsets:
    """Test fieldsets generation."""

    def test_explicit_fieldsets_dict_format(self, sample_model):
        """Test dict-format fieldsets are converted to Django format."""
        config = AdminConfig(
            fieldsets={
                "Basic Info": ["name", "description"],
                "Metadata": ["collected_at", "status"],
            }
        )
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        # Should convert to Django tuple format
        assert isinstance(admin_class.fieldsets, list)
        assert len(admin_class.fieldsets) == 2
        assert admin_class.fieldsets[0][0] == "Basic Info"
        assert admin_class.fieldsets[0][1]["fields"] == ["name", "description"]

    def test_explicit_fieldsets_django_format(self, sample_model):
        """Test Django-format fieldsets are preserved."""
        fieldsets = [
            ("Basic", {"fields": ["name", "description"]}),
            ("Meta", {"fields": ["collected_at"]}),
        ]
        config = AdminConfig(fieldsets=fieldsets)
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.fieldsets == fieldsets

    def test_auto_fieldsets_from_inspector(self, sample_model):
        """Test auto-generated fieldsets group fields logically."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        # Should have fieldsets from inspector grouping
        assert hasattr(admin_class, "fieldsets")
        if admin_class.fieldsets:  # May be None if no logical grouping
            assert isinstance(admin_class.fieldsets, list)
            # Each fieldset should be a tuple with section name and dict
            for fieldset in admin_class.fieldsets:
                assert isinstance(fieldset, tuple)
                assert len(fieldset) == 2
                assert isinstance(fieldset[1], dict)
                assert "fields" in fieldset[1]


class TestOptionalAttributes:
    """Test optional admin attributes."""

    def test_list_per_page(self, sample_model):
        """Test list_per_page attribute is set."""
        config = AdminConfig(list_per_page=50)
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.list_per_page == 50

    def test_list_editable(self, sample_model):
        """Test list_editable attribute is set."""
        config = AdminConfig(list_editable=["status"])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.list_editable == ["status"]

    def test_ordering(self, sample_model):
        """Test ordering attribute is set."""
        config = AdminConfig(ordering=["-collected_at"])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.ordering == ["-collected_at"]

    def test_date_hierarchy(self, sample_model):
        """Test date_hierarchy attribute is set."""
        config = AdminConfig(date_hierarchy="collected_at")
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.date_hierarchy == "collected_at"

    def test_readonly_fields(self, sample_model):
        """Test readonly_fields attribute is set."""
        config = AdminConfig(readonly_fields=["id", "created_at"])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.readonly_fields == ["id", "created_at"]

    def test_prepopulated_fields(self, sample_model):
        """Test prepopulated_fields attribute is set."""
        config = AdminConfig(prepopulated_fields={"slug": ("name",)})
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.prepopulated_fields == {"slug": ("name",)}

    def test_inlines(self, sample_model):
        """Test inlines attribute is set."""

        class SampleInline(admin.TabularInline):
            model = sample_model

        config = AdminConfig(inlines=[SampleInline])
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.inlines == [SampleInline]


class TestAdminClassNaming:
    """Test admin class naming conventions."""

    def test_generated_class_name(self, sample_model):
        """Test generated admin class has correct name."""
        config = AdminConfig()
        factory = AdminFactory(sample_model, config)
        admin_class = factory.generate()

        assert admin_class.__name__ == "SampleModelAdmin"
