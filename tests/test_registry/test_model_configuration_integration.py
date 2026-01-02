"""Integration tests for new ModelConfiguration with factories."""

# Import the NEW config system
import sys
from pathlib import Path

import pytest
from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

# Add project root to path to import tmp_new_model_config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fairdm.config_components import AdminConfig, FiltersConfig, FormConfig, TableConfig
from tmp_new_model_config import Authority, ModelConfiguration, ModelMetadata


@pytest.fixture
def sample_model():
    """Create a test model similar to real FairDM samples."""

    class WaterSample(models.Model):
        name = models.CharField(max_length=100)
        description = models.TextField()
        collected_at = models.DateTimeField()
        location = models.CharField(max_length=200)
        temperature = models.FloatField(null=True, blank=True)
        ph_level = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
        status = models.CharField(
            max_length=20,
            choices=[("draft", "Draft"), ("published", "Published")],
            default="draft",
        )
        is_public = models.BooleanField(default=False)
        contributor = models.ForeignKey(
            "auth.User",
            on_delete=models.CASCADE,
            related_name="water_samples",
        )

        class Meta:
            app_label = "test_app"

    return WaterSample


class TestModelConfigurationBasics:
    """Test basic ModelConfiguration functionality."""

    def test_initialization_with_model(self, sample_model):
        """Test config can be initialized with model."""
        config = ModelConfiguration(model=sample_model)
        assert config.model == sample_model

    def test_initialization_creates_nested_configs(self, sample_model):
        """Test initialization creates default nested config objects."""
        config = ModelConfiguration(model=sample_model)
        assert isinstance(config.form, FormConfig)
        assert isinstance(config.table, TableConfig)
        assert isinstance(config.filters, FiltersConfig)
        assert isinstance(config.admin, AdminConfig)

    def test_metadata_initialization(self, sample_model):
        """Test metadata is properly initialized."""
        test_metadata = ModelMetadata(
            description="Water samples from various locations",
            authority=Authority(name="Research Institute", website="https://example.org"),
            keywords=["water", "quality", "environmental"],
        )

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            metadata = test_metadata

        config = WaterSampleConfig()
        assert config.metadata.description == "Water samples from various locations"
        assert config.metadata.authority.name == "Research Institute"
        assert "water" in config.metadata.keywords


class TestSimpleFieldsAPI:
    """Test simplest usage: just define fields."""

    def test_simple_fields_only(self, sample_model):
        """Test that defining just fields auto-generates everything."""

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            fields = ["name", "collected_at", "location"]

        config = WaterSampleConfig()

        # Should auto-generate all components
        form_class = config.get_form_class()
        table_class = config.get_table_class()
        filterset_class = config.get_filterset_class()
        admin_class = config.get_admin_class()

        assert issubclass(form_class, ModelForm)
        assert issubclass(table_class, Table)
        assert issubclass(filterset_class, FilterSet)
        assert issubclass(admin_class, admin.ModelAdmin)

    def test_fields_used_as_fallback(self, sample_model):
        """Test that parent fields are used when component fields not specified."""

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            fields = ["name", "location"]
            table = TableConfig(orderable=True)  # Configure table but no fields

        config = WaterSampleConfig()
        table_class = config.get_table_class()

        # Should use parent fields for table
        assert "name" in str(table_class.Meta.fields)


class TestNestedConfigAPI:
    """Test intermediate usage: nested config objects."""

    def test_form_config(self, sample_model):
        """Test FormConfig customization."""

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            fields = ["name", "collected_at", "location"]
            form = FormConfig(
                fields=["name", "description"],
                widgets={"description": "Textarea"},
            )

        config = WaterSampleConfig()
        form_class = config.get_form_class()

        # Should use form-specific fields, not parent fields
        assert "name" in form_class._meta.fields
        assert "description" in form_class._meta.fields
        assert "location" not in form_class._meta.fields

    def test_table_config(self, sample_model):
        """Test TableConfig customization."""

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            fields = ["name", "collected_at", "location"]
            table = TableConfig(
                fields=["name", "collected_at"],
                orderable=True,
            )

        config = WaterSampleConfig()
        table_class = config.get_table_class()

        # Should use table-specific fields
        assert hasattr(table_class, "_meta")

    def test_filters_config(self, sample_model):
        """Test FiltersConfig customization."""

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            fields = ["name", "collected_at", "status"]
            filters = FiltersConfig(
                fields=["collected_at", "status"],
                range_fields=["collected_at"],
            )

        config = WaterSampleConfig()
        filterset_class = config.get_filterset_class()

        # Should create filterset with specified fields
        assert hasattr(filterset_class, "base_filters")

    def test_admin_config(self, sample_model):
        """Test AdminConfig customization."""

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            fields = ["name", "collected_at", "status"]
            admin = AdminConfig(
                list_display=["name", "status"],
                search_fields=["name", "location"],
                list_filter=["status"],
            )

        config = WaterSampleConfig()
        admin_class = config.get_admin_class()

        assert admin_class.list_display == ["name", "status"]
        assert admin_class.search_fields == ["name", "location"]
        assert admin_class.list_filter == ["status"]


class TestCustomClassesAPI:
    """Test advanced usage: custom component classes."""

    def test_custom_form_class(self, sample_model):
        """Test providing custom form class."""

        class CustomForm(ModelForm):
            class Meta:
                model = sample_model
                fields = ["name"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            form = FormConfig(form_class=CustomForm)

        config = WaterSampleConfig()
        result = config.get_form_class()

        assert result == CustomForm

    def test_custom_table_class(self, sample_model):
        """Test providing custom table class."""

        class CustomTable(Table):
            class Meta:
                model = sample_model
                fields = ["name"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            table = TableConfig(table_class=CustomTable)

        config = WaterSampleConfig()
        result = config.get_table_class()

        assert result == CustomTable

    def test_custom_filterset_class(self, sample_model):
        """Test providing custom filterset class."""

        class CustomFilterSet(FilterSet):
            class Meta:
                model = sample_model
                fields = ["name"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            filters = FiltersConfig(filterset_class=CustomFilterSet)

        config = WaterSampleConfig()
        result = config.get_filterset_class()

        assert result == CustomFilterSet

    def test_custom_admin_class(self, sample_model):
        """Test providing custom admin class."""

        class CustomAdmin(admin.ModelAdmin):
            list_display = ["custom_field"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            admin = AdminConfig(admin_class=CustomAdmin)

        config = WaterSampleConfig()
        result = config.get_admin_class()

        assert result == CustomAdmin


class TestBackwardsCompatibility:
    """Test backwards compatibility with old API."""

    def test_legacy_form_class_attribute(self, sample_model):
        """Test old form_class attribute still works."""

        class CustomForm(ModelForm):
            class Meta:
                model = sample_model
                fields = ["name"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            form_class = CustomForm

        config = WaterSampleConfig()
        result = config.get_form_class()

        assert result == CustomForm

    def test_legacy_table_class_attribute(self, sample_model):
        """Test old table_class attribute still works."""

        class CustomTable(Table):
            class Meta:
                model = sample_model
                fields = ["name"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            table_class = CustomTable

        config = WaterSampleConfig()
        result = config.get_table_class()

        assert result == CustomTable

    def test_legacy_filterset_class_attribute(self, sample_model):
        """Test old filterset_class attribute still works."""

        class CustomFilterSet(FilterSet):
            class Meta:
                model = sample_model
                fields = ["name"]

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            filterset_class = CustomFilterSet

        config = WaterSampleConfig()
        result = config.get_filterset_class()

        assert result == CustomFilterSet


class TestConvenienceMethods:
    """Test convenience/helper methods."""

    def test_get_display_name(self, sample_model):
        """Test display name generation."""
        config = ModelConfiguration(model=sample_model)
        display_name = config.get_display_name()
        assert isinstance(display_name, str)
        assert len(display_name) > 0

    def test_get_description_from_metadata(self, sample_model):
        """Test description from metadata."""
        test_metadata = ModelMetadata(description="Test description")

        class WaterSampleConfig(ModelConfiguration):
            model = sample_model
            metadata = test_metadata

        config = WaterSampleConfig()
        assert config.get_description() == "Test description"

    def test_has_custom_form(self, sample_model):
        """Test has_custom_form detection."""

        class CustomForm(ModelForm):
            class Meta:
                model = sample_model
                fields = ["name"]

        class ConfigWithCustom(ModelConfiguration):
            model = sample_model
            form = FormConfig(form_class=CustomForm)

        class ConfigWithoutCustom(ModelConfiguration):
            model = sample_model
            fields = ["name"]

        assert ConfigWithCustom().has_custom_form() is True
        assert ConfigWithoutCustom().has_custom_form() is False

    def test_has_custom_admin(self, sample_model):
        """Test has_custom_admin detection."""

        class CustomAdmin(admin.ModelAdmin):
            pass

        class ConfigWithCustom(ModelConfiguration):
            model = sample_model
            admin = AdminConfig(admin_class=CustomAdmin)

        class ConfigWithoutCustom(ModelConfiguration):
            model = sample_model
            fields = ["name"]

        assert ConfigWithCustom().has_custom_admin() is True
        assert ConfigWithoutCustom().has_custom_admin() is False
