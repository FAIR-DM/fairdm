"""Tests for fairdm/registry/config.py.

Covers ModelConfiguration and its metadata dataclasses (Authority, Citation,
ModelMetadata): default-field computation, the three-tier field resolution
algorithm implemented by the component cached_properties, admin-class
inheritance validation for polymorphic models, and field-name validation at
construction time.
"""

import pytest
from django.contrib import admin
from django.db import models

from fairdm.core.models import Measurement, Sample
from fairdm.core.sample.admin import SampleChildAdmin
from fairdm.registry import registry
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample
from fairdm.registry.config import (
    Authority,
    Citation,
    ModelConfiguration,
    ModelMetadata,
)
from fairdm.registry.exceptions import (
    ConfigurationError,
    DuplicateRegistrationError,
    FieldValidationError,
)
from fairdm_demo.models import RockSample


class TestGetDefaultFields:
    """T012: Unit tests for ModelConfiguration.get_default_fields()."""

    def test_get_default_fields_basic(self):
        """Test get_default_fields() returns standard model fields."""

        class TestModel(Sample):
            """Test Sample with basic fields."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()
            sample_count = models.IntegerField()

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        # Should include standard fields
        assert "rock_type" in defaults
        assert "mineral_content" in defaults
        assert "sample_count" in defaults

        # Should exclude id
        assert "id" not in defaults

    def test_get_default_fields_excludes_polymorphic(self):
        """Test get_default_fields() excludes polymorphic_ctype field."""

        class TestModel(Sample):
            """Test Sample (inherits from polymorphic base)."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        # Should exclude polymorphic_ctype
        assert "polymorphic_ctype" not in defaults

        # Should include regular fields
        assert "rock_type" in defaults

    def test_get_default_fields_excludes_ptr_fields(self):
        """Test get_default_fields() excludes _ptr fields from inheritance."""

        class ParentSample(Sample):
            """Parent Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class ChildSample(ParentSample):
            """Child Sample inheriting from ParentSample."""

            mineral_content = models.TextField()

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(ChildSample)

        # Should exclude parentsample_ptr field
        assert "parentsample_ptr" not in defaults

        # Should include inherited and own fields
        assert "rock_type" in defaults
        assert "mineral_content" in defaults

    def test_get_default_fields_excludes_auto_now(self):
        """Test get_default_fields() excludes auto_now and auto_now_add fields."""

        class TestModel(Sample):
            """Test Sample with auto timestamp fields."""

            rock_type = models.CharField(max_length=100)
            sample_created_at = models.DateTimeField(auto_now_add=True)
            sample_updated_at = models.DateTimeField(auto_now=True)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        # Should exclude auto timestamp fields
        assert "sample_created_at" not in defaults
        assert "sample_updated_at" not in defaults

        # Should include regular fields
        assert "rock_type" in defaults

    def test_get_default_fields_excludes_non_editable(self):
        """Test get_default_fields() excludes editable=False fields."""

        class TestModel(Sample):
            """Test Sample with non-editable field."""

            rock_type = models.CharField(max_length=100)
            readonly_field = models.CharField(max_length=100, editable=False)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        # Should exclude readonly field
        assert "readonly_field" not in defaults

        # Should include editable fields
        assert "rock_type" in defaults

    def test_get_default_fields_comprehensive_exclusions(self):
        """Test get_default_fields() with all exclusion types together."""

        class ParentModel(Sample):
            """Parent Sample model."""

            parent_rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class TestModel(ParentModel):
            """Test Sample with various field types."""

            rock_name = models.CharField(max_length=100)
            mineral_description = models.TextField()
            sample_count = models.IntegerField()
            readonly_code = models.CharField(max_length=100, editable=False)
            sample_created_at = models.DateTimeField(auto_now_add=True)
            sample_updated_at = models.DateTimeField(auto_now=True)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        # Should include only editable, standard fields
        assert "rock_name" in defaults
        assert "mineral_description" in defaults
        assert "sample_count" in defaults
        assert "parent_rock_type" in defaults

        # Should exclude all special fields
        assert "id" not in defaults
        assert "polymorphic_ctype" not in defaults
        assert "parentmodel_ptr" not in defaults
        assert "readonly_code" not in defaults
        assert "sample_created_at" not in defaults
        assert "sample_updated_at" not in defaults


class TestModelMetadata:
    """Test ModelMetadata dataclass functionality."""

    def test_model_metadata_creation_empty(self):
        """Test creating empty metadata."""
        metadata = ModelMetadata()

        assert metadata.description == ""
        assert metadata.authority is None
        assert metadata.keywords == []
        assert metadata.repository_url == ""
        assert metadata.citation is None
        assert metadata.maintainer == ""
        assert metadata.maintainer_email == ""

    def test_model_metadata_with_all_fields(self):
        """Test creating metadata with all fields populated."""
        authority = Authority(
            name="Test Authority", short_name="TA", website="https://example.com"
        )
        citation = Citation(text="Test Citation", doi="10.1234/test")

        metadata = ModelMetadata(
            description="A comprehensive test metadata",
            authority=authority,
            keywords=["test", "metadata", "comprehensive"],
            repository_url="https://github.com/test/repo",
            citation=citation,
            maintainer="Test Maintainer",
            maintainer_email="maintainer@example.com",
        )

        assert metadata.description == "A comprehensive test metadata"
        assert metadata.authority.name == "Test Authority"
        assert metadata.keywords == ["test", "metadata", "comprehensive"]
        assert metadata.repository_url == "https://github.com/test/repo"
        assert metadata.citation.doi == "10.1234/test"
        assert metadata.maintainer == "Test Maintainer"
        assert metadata.maintainer_email == "maintainer@example.com"


class TestAuthority:
    """Test Authority dataclass functionality."""

    def test_authority_minimal(self):
        """Test creating authority with only required fields."""
        authority = Authority(name="Test Authority")

        assert authority.name == "Test Authority"
        assert authority.short_name == ""
        assert authority.website == ""

    def test_authority_complete(self):
        """Test creating authority with all fields."""
        authority = Authority(
            name="Test Authority", short_name="TA", website="https://example.com"
        )

        assert authority.name == "Test Authority"
        assert authority.short_name == "TA"
        assert authority.website == "https://example.com"

    def test_authority_frozen(self):
        """Test that Authority is immutable (frozen dataclass)."""
        authority = Authority(name="Test")

        with pytest.raises(AttributeError):
            authority.name = "Changed"


class TestCitation:
    """Test Citation dataclass functionality."""

    def test_citation_empty(self):
        """Test creating empty citation."""
        citation = Citation()

        assert citation.text == ""
        assert citation.doi == ""

    def test_citation_with_text_only(self):
        """Test creating citation with text only."""
        citation = Citation(text="Test Citation Text")

        assert citation.text == "Test Citation Text"
        assert citation.doi == ""

    def test_citation_with_doi_only(self):
        """Test creating citation with DOI only."""
        citation = Citation(doi="10.1234/test.doi")

        assert citation.text == ""
        assert citation.doi == "10.1234/test.doi"

    def test_citation_complete(self):
        """Test creating complete citation."""
        citation = Citation(text="Complete Citation", doi="10.1234/complete")

        assert citation.text == "Complete Citation"
        assert citation.doi == "10.1234/complete"

    def test_citation_frozen(self):
        """Test that Citation is immutable (frozen dataclass)."""
        citation = Citation(text="Test")

        with pytest.raises(AttributeError):
            citation.text = "Changed"


class TestModelConfiguration:
    """Test ModelConfiguration class functionality."""

    def test_model_configuration_with_model(self, db):
        """Test creating ModelConfiguration with model."""
        config = ModelConfiguration(model=ConcreteSample)

        assert config.model == ConcreteSample
        assert isinstance(config.metadata, ModelMetadata)

    def test_model_configuration_field_attributes(self, db):
        """Test component-specific field attributes."""
        config = ModelConfiguration(
            model=ConcreteSample,
            table_fields=["name", "status"],
            form_fields=["name", "status"],
            filterset_fields=["status"],
        )

        # Test field attributes directly
        assert config.table_fields == ["name", "status"]
        assert config.form_fields == ["name", "status"]
        assert config.filterset_fields == ["status"]


class TestAutoGeneratedComponents:
    """Test auto-generation of forms, filters, tables, and resources using property-based API."""

    def test_filterset_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of FilterSet class via property."""
        from django_filters import FilterSet

        config = ModelConfiguration(
            model=ConcreteSample,
            filterset_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        # Access via property to trigger auto-generation
        filterset_class = config.get_filterset_class()
        assert issubclass(filterset_class, FilterSet)

    def test_form_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of ModelForm class via property."""
        from django.forms import ModelForm

        config = ModelConfiguration(
            model=ConcreteSample,
            form_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        # Access via property to trigger auto-generation
        form_class = config.get_form_class()
        assert issubclass(form_class, ModelForm)

    def test_table_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of Table class via property."""
        from django_tables2 import Table

        config = ModelConfiguration(
            model=ConcreteSample,
            table_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        # Access via property to trigger auto-generation
        table_class = config.get_table_class()
        assert issubclass(table_class, Table)

    def test_resource_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of import/export Resource class via property."""
        from import_export.resources import ModelResource

        config = ModelConfiguration(
            model=ConcreteSample,
            resource_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        # Access via property to trigger auto-generation
        resource_class = config.get_resource_class()
        assert issubclass(resource_class, ModelResource)

    def test_admin_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of ModelAdmin class via property."""
        from django.contrib.admin import ModelAdmin

        config = ModelConfiguration(
            model=ConcreteSample,
            admin_list_display=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        # Access via property to trigger auto-generation
        admin_class = config.get_admin_class()
        assert issubclass(admin_class, ModelAdmin)


class TestComponentOverrides:
    """Test that custom components override auto-generation."""

    def test_custom_form_class_override(self, clean_registry, db):
        """Test providing custom form class."""
        from django import forms

        class CustomSampleForm(forms.ModelForm):
            class Meta:
                model = ConcreteSample
                fields = ["name"]

        config = ModelConfiguration(
            model=ConcreteSample,
            form_class=CustomSampleForm,
        )
        registry.register(ConcreteSample, config=config)

        # Test that custom form is recognized
        assert config.form_class == CustomSampleForm
        assert config.get_form_class() == CustomSampleForm

    def test_custom_filterset_class_override(self, clean_registry, db):
        """Test providing custom FilterSet class."""
        from django_filters import CharFilter, FilterSet

        class CustomSampleFilter(FilterSet):
            name = CharFilter(lookup_expr="icontains")

            class Meta:
                model = ConcreteSample
                fields = ["name"]

        config = ModelConfiguration(
            model=ConcreteSample,
            filterset_class=CustomSampleFilter,
        )
        registry.register(ConcreteSample, config=config)

        # Test that custom filterset is recognized
        assert config.filterset_class == CustomSampleFilter
        assert config.get_filterset_class() == CustomSampleFilter

    def test_custom_table_class_override(self, clean_registry, db):
        """Test providing custom Table class."""
        import django_tables2 as tables

        class CustomSampleTable(tables.Table):
            name = tables.Column()

            class Meta:
                model = ConcreteSample
                fields = ["name"]

        config = ModelConfiguration(
            model=ConcreteSample,
            table_class=CustomSampleTable,
        )
        registry.register(ConcreteSample, config=config)

        # Test that custom table is recognized
        assert config.table_class == CustomSampleTable
        assert config.get_table_class() == CustomSampleTable


class TestRegistryItemStructure:
    """Test the structure of registry items."""

    def test_registry_item_has_config(self, clean_registry, db):
        """Test that registry items contain config."""
        config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Structure Test",
        )
        registry.register(ConcreteSample, config=config)

        # Test that Sample is in registry and has config
        assert ConcreteSample in registry._registry
        stored_config = registry.get_for_model(ConcreteSample)
        assert isinstance(stored_config, ModelConfiguration)
        assert stored_config.display_name == "Structure Test"


class TestRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def test_register_with_config(self, clean_registry, db):
        """Test registering with explicit config."""
        config = ModelConfiguration(model=ConcreteSample)
        registry.register(ConcreteSample, config=config)

        assert ConcreteSample in registry._registry
        stored_config = registry.get_for_model(ConcreteSample)
        assert isinstance(stored_config, ModelConfiguration)
        assert stored_config.model == ConcreteSample

    def test_get_for_model_returns_config(self, clean_registry, db):
        """Test that get_for_model returns the stored config."""
        config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Test Config",
        )
        registry.register(ConcreteSample, config=config)

        # Access the stored config via get_for_model
        retrieved_config = registry.get_for_model(ConcreteSample)
        assert retrieved_config.get_display_name() == "Test Config"

    def test_multiple_registrations_same_session(self, clean_registry, db):
        """Test multiple models can be registered in same session."""
        sample_config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Sample Config",
        )
        measurement_config = ModelConfiguration(
            model=ConcreteMeasurement,
            display_name="Measurement Config",
        )

        registry.register(ConcreteSample, config=sample_config)
        registry.register(ConcreteMeasurement, config=measurement_config)

        assert ConcreteSample in registry._registry
        assert ConcreteMeasurement in registry._registry


class TestRegistryIntegration:
    """Test integration between registry and other FairDM components."""

    def test_registry_stores_config(self, clean_registry, db):
        """Test that registry properly stores and retrieves config."""
        config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Integration Test",
        )
        registry.register(ConcreteSample, config=config)

        # Verify registration succeeded
        assert ConcreteSample in registry._registry
        stored_config = registry.get_for_model(ConcreteSample)
        assert stored_config.get_display_name() == "Integration Test"


class TestAdminInheritanceValidation:
    """Test that registry validates admin class inheritance for polymorphic models."""

    def test_sample_with_wrong_admin_class_raises_error(self):
        """Sample subclass with admin not inheriting from SampleChildAdmin should raise error."""

        class WrongAdmin(admin.ModelAdmin):
            """Wrong admin class - doesn't inherit from SampleChildAdmin."""

            pass

        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                admin_class=WrongAdmin,
                fields=["name", "rock_type"],
            )

        assert "must inherit from SampleChildAdmin" in str(exc_info.value)
        assert "RockSample" in str(exc_info.value)
        assert "WrongAdmin" in str(exc_info.value)

    def test_sample_with_correct_admin_class_passes(self):
        """Sample subclass with admin inheriting from SampleChildAdmin should pass."""

        class CorrectAdmin(SampleChildAdmin):
            """Correct admin class - inherits from SampleChildAdmin."""

            base_model = RockSample
            show_in_index = True

        config = ModelConfiguration(
            model=RockSample,
            admin_class=CorrectAdmin,
            fields=["name", "rock_type"],
        )

        assert config.get_admin_class() == CorrectAdmin

    def test_sample_without_admin_class_passes(self):
        """Sample subclass without admin_class should pass (auto-generates)."""
        config = ModelConfiguration(
            model=RockSample,
            fields=["name", "rock_type"],
        )

        # Should auto-generate an admin class
        assert config.get_admin_class() is not None
        assert issubclass(config.get_admin_class(), admin.ModelAdmin)

    def test_autogenerated_sample_admin_inherits_from_child_admin(self):
        """Auto-generated Sample admin should inherit from SampleChildAdmin."""
        config = ModelConfiguration(
            model=RockSample,
            fields=["name", "rock_type"],
        )

        # Auto-generated admin should use SampleChildAdmin as base
        admin_class = config.get_admin_class()
        assert issubclass(admin_class, SampleChildAdmin), (
            f"Auto-generated admin for {RockSample.__name__} should inherit from SampleChildAdmin, "
            f"but got bases: {admin_class.__bases__}"
        )

        # Should have required polymorphic attributes
        assert hasattr(admin_class, "base_model")
        assert admin_class.base_model == RockSample
        assert hasattr(admin_class, "show_in_index")
        assert admin_class.show_in_index is True

    def test_measurement_with_wrong_admin_class_raises_error(self):
        """Measurement subclass with wrong admin should raise error."""
        from django.db import models

        from fairdm.core.models import Measurement

        # Create a simple Measurement subclass for testing
        class TestMeasurement(Measurement):
            """Test measurement model."""

            value = models.FloatField()

            class Meta:
                app_label = "fairdm_demo"

        class WrongMeasurementAdmin(admin.ModelAdmin):
            """Wrong admin class - doesn't inherit from MeasurementAdmin."""

            pass

        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfiguration(
                model=TestMeasurement,
                admin_class=WrongMeasurementAdmin,
                fields=["value"],
            )

        assert "must inherit from MeasurementAdmin" in str(exc_info.value)
        assert "TestMeasurement" in str(exc_info.value)

    def test_measurement_with_correct_admin_class_passes(self):
        """Measurement subclass with correct admin should pass."""
        from django.db import models

        from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin
        from fairdm.core.models import Measurement

        # Create a simple Measurement subclass for testing
        class TestMeasurement2(Measurement):
            """Test measurement model."""

            value = models.FloatField()

            class Meta:
                app_label = "fairdm_demo"

        class CorrectMeasurementAdmin(MeasurementChildAdmin):
            """Correct admin class - inherits from MeasurementAdmin."""

            base_model = TestMeasurement2
            show_in_index = True

        config = ModelConfiguration(
            model=TestMeasurement2,
            admin_class=CorrectMeasurementAdmin,
            fields=["value"],
        )

        assert config.get_admin_class() == CorrectMeasurementAdmin

    def test_autogenerated_measurement_admin_inherits_from_child_admin(self):
        """Auto-generated Measurement admin should inherit from MeasurementAdmin."""
        from django.db import models

        from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin
        from fairdm.core.models import Measurement

        # Create a simple Measurement subclass for testing
        class TestMeasurement3(Measurement):
            """Test measurement model."""

            value = models.FloatField()

            class Meta:
                app_label = "fairdm_demo"

        config = ModelConfiguration(
            model=TestMeasurement3,
            fields=["value"],
        )

        # Auto-generated admin should use MeasurementAdmin as base
        admin_class = config.get_admin_class()
        assert issubclass(admin_class, MeasurementChildAdmin), (
            f"Auto-generated admin for {TestMeasurement3.__name__} should inherit from MeasurementAdmin, "
            f"but got bases: {admin_class.__bases__}"
        )

        # Should have required polymorphic attributes
        assert hasattr(admin_class, "base_model")
        assert admin_class.base_model == TestMeasurement3
        assert hasattr(admin_class, "show_in_index")
        assert admin_class.show_in_index is True

    def test_admin_class_as_string_reference(self):
        """Admin class can be provided as string reference."""
        from fairdm_demo.models import WaterSample

        config = ModelConfiguration(
            model=WaterSample,
            admin_class="fairdm_demo.admin.WaterSampleAdmin",
            fields=["name", "ph_level"],
        )

        # Should resolve string reference and validate
        from fairdm_demo.admin import WaterSampleAdmin

        assert config.get_admin_class() == WaterSampleAdmin


class TestFieldResolutionAlgorithm:
    """Test 3-tier field resolution for each component type."""

    @pytest.fixture
    def test_model(self):
        """Fixture providing a test Sample model."""

        class SandstoneRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()
            sample_location = models.CharField(max_length=200)
            collection_date = models.DateField()
            weight_grams = models.FloatField()

            class Meta:
                app_label = "test_app"

        return SandstoneRockSample

    def test_tier1_component_specific_fields_table(self, test_model):
        """Test that component-specific table_fields takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],  # Parent fields
            table_fields=["rock_type", "weight_grams"],  # Component-specific
        )

        # get_table_class() should use table_fields
        table_class = config.get_table_class()

        # Verify columns match component-specific fields
        assert "rock_type" in table_class.base_columns
        assert "weight_grams" in table_class.base_columns

        # Parent fields should NOT appear
        assert "sample_location" not in table_class.base_columns

    def test_tier2_parent_fields_fallback_table(self, test_model):
        """Test that parent list_fields is used when table_fields not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],  # Parent fields
            table_fields=None,  # No component-specific fields
        )

        # get_table_class() should fall back to fields
        table_class = config.get_table_class()

        # Verify columns match parent fields
        assert "rock_type" in table_class.base_columns
        assert "sample_location" in table_class.base_columns
        assert "collection_date" in table_class.base_columns

    def test_tier3_smart_defaults_table(self, test_model):
        """Test that smart defaults are used when no fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            table_fields=None,  # No component-specific fields
        )

        # get_table_class() should use get_default_fields()
        table_class = config.get_table_class()

        # Verify model fields appear (text fields may be excluded from table defaults)
        assert "rock_type" in table_class.base_columns
        # Note: mineral_content is a TextField and may be excluded from table defaults
        # (text fields typically don't belong in table columns)
        assert "sample_location" in table_class.base_columns
        assert "collection_date" in table_class.base_columns
        assert "weight_grams" in table_class.base_columns

        # Note: BaseTable defines 'id' column but marks it visible=False
        # The 'id' field is in base_columns but hidden from display
        # This is correct behavior - id is needed for linkify but hidden
        assert "polymorphic_ctype" not in table_class.base_columns

    def test_tier1_component_specific_fields_form(self, test_model):
        """Test that component-specific form_fields takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "mineral_content", "sample_location"],  # Parent fields
            form_fields=["rock_type", "weight_grams"],  # Component-specific
        )

        # get_form_class() should use form_fields
        form_class = config.get_form_class()

        # Verify form fields match component-specific fields
        assert "rock_type" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

        # Parent fields should NOT appear
        assert "mineral_content" not in form_class.base_fields
        assert "sample_location" not in form_class.base_fields

    def test_tier2_parent_fields_fallback_form(self, test_model):
        """Test that parent detail_fields is used when form_fields not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "mineral_content", "weight_grams"],  # Parent fields
            form_fields=None,  # No component-specific fields
        )

        # get_form_class() should fall back to fields
        form_class = config.get_form_class()

        # Verify form fields match parent fields
        assert "rock_type" in form_class.base_fields
        assert "mineral_content" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

    def test_tier3_smart_defaults_form(self, test_model):
        """Test that smart defaults are used when no form fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            form_fields=None,  # No component-specific fields
        )

        # get_form_class() should use get_default_fields()
        form_class = config.get_form_class()

        # Verify all editable fields appear
        assert "rock_type" in form_class.base_fields
        assert "mineral_content" in form_class.base_fields
        assert "sample_location" in form_class.base_fields
        assert "collection_date" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

        # Verify exclusions
        assert "id" not in form_class.base_fields
        assert "polymorphic_ctype" not in form_class.base_fields

    def test_tier1_component_specific_fields_filterset(self, test_model):
        """Test that component-specific filterset_fields takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],  # Parent fields
            filterset_fields=["rock_type", "collection_date"],  # Component-specific
        )

        # get_filterset_class() should use filterset_fields
        filterset_class = config.get_filterset_class()

        # Verify filters match component-specific fields
        assert "rock_type" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters

        # Parent fields should NOT appear
        assert "location" not in filterset_class.base_filters

    def test_tier2_parent_fields_fallback_filterset(self, test_model):
        """Test that parent filter_fields is used when filterset_fields not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],  # Parent fields
            filterset_fields=None,  # No component-specific fields
        )

        # get_filterset_class() should fall back to fields
        filterset_class = config.get_filterset_class()

        # Verify filters match parent fields
        assert "rock_type" in filterset_class.base_filters
        assert "sample_location" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters

    def test_tier3_smart_defaults_filterset(self, test_model):
        """Test that smart defaults are used when no filter fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            filterset_fields=None,  # No component-specific fields
        )

        # get_filterset_class() should use get_default_fields()
        filterset_class = config.get_filterset_class()

        # Verify all model fields appear (except exclusions)
        assert "rock_type" in filterset_class.base_filters
        assert "mineral_content" in filterset_class.base_filters
        assert "sample_location" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters
        assert "weight_grams" in filterset_class.base_filters

        # Verify exclusions
        assert "id" not in filterset_class.base_filters
        assert "polymorphic_ctype" not in filterset_class.base_filters

    def test_tier1_component_specific_fields_admin(self, test_model):
        """Test that component-specific admin_list_display takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],  # Parent fields
            admin_list_display=["rock_type", "weight_grams"],  # Component-specific
        )

        # get_admin_class() should use admin_list_display
        admin_class = config.get_admin_class()

        # Verify list_display matches component-specific fields
        assert admin_class.list_display == ["rock_type", "weight_grams"]

    def test_tier2_parent_fields_fallback_admin(self, test_model):
        """Test that parent list_fields is used when admin_list_display not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],  # Parent fields
            admin_list_display=None,  # No component-specific fields
        )

        # get_admin_class() should fall back to fields (first 5)
        admin_class = config.get_admin_class()

        # Verify list_display matches parent fields (limited to 5)
        assert "rock_type" in admin_class.list_display
        assert "sample_location" in admin_class.list_display
        assert "collection_date" in admin_class.list_display

    def test_tier3_smart_defaults_admin(self, test_model):
        """Test that smart defaults are used when no admin fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            admin_list_display=None,  # No component-specific fields
        )

        # get_admin_class() should use get_default_fields() (first 5)
        admin_class = config.get_admin_class()

        # Verify list_display has content (may vary based on defaults)
        # Note: get_default_fields() returns ALL fields (including inherited Sample fields)
        # so list_display may contain Sample base class fields or SandstoneRockSample fields
        assert len(admin_class.list_display) > 0
        assert len(admin_class.list_display) <= 5  # AdminFactory limits to first 5

        # At least verify it's a valid field list (not empty, not just __str__)
        if (
            len(admin_class.list_display) == 1
            and admin_class.list_display[0] == "__str__"
        ):
            # This only happens if get_default_fields() returned empty list
            pytest.fail(
                "Admin list_display should have actual fields, not just __str__"
            )


class TestCustomClassOverride:
    """Test that custom classes bypass field resolution entirely (highest priority)."""

    @pytest.fixture
    def test_model(self):
        """Fixture providing a test Sample model."""

        class QuartzRockSample(Sample):
            """Test rock sample model."""

            quartz_type = models.CharField(max_length=100)
            sample_description = models.TextField()

            class Meta:
                app_label = "test_app"

        return QuartzRockSample

    def test_custom_form_class_wins_over_the_shared_field_list(self, test_model):
        """A supplied class replaces its component; the shared list feeds the rest."""
        from django import forms

        class CustomForm(forms.ModelForm):
            """Custom form with specific field."""

            custom_field = forms.CharField()

            class Meta:
                model = test_model
                fields = ["quartz_type"]

        config = ModelConfiguration(
            model=test_model,
            form_class=CustomForm,
            # Legal: the shared list still feeds the five generated components, so
            # it is not dead. Only a component's own list next to its own class is.
            fields=["sample_description"],
        )

        form_class = config.get_form_class()

        assert form_class is CustomForm
        assert "custom_field" in form_class.base_fields
        assert "quartz_type" in form_class.base_fields
        assert "sample_description" not in form_class.base_fields
        # The shared list is still what every other component is built from.
        assert config.resolve_fields("table") == ["sample_description"]

    def test_custom_table_class_wins_over_the_shared_field_list(self, test_model):
        """The same rule for the table, which is supplied rather than generated."""
        import django_tables2 as tables

        class CustomTable(tables.Table):
            """Custom table with specific columns."""

            quartz_type = tables.Column()

            class Meta:
                model = test_model

        config = ModelConfiguration(
            model=test_model,
            table_class=CustomTable,
            fields=["sample_description"],
        )

        table_class = config.get_table_class()

        assert table_class is CustomTable
        assert "quartz_type" in table_class.base_columns

    def test_component_field_list_beside_its_own_class_is_refused(self, test_model):
        """FR-023, decision D3: the field list could never take effect.

        Django refuses the same pair on ModelFormMixin. Silently preferring the
        class leaves a portal holding a list that does nothing, with nothing in the
        logs to explain it.
        """
        from django import forms
        from django.core.exceptions import ImproperlyConfigured

        class CustomForm(forms.ModelForm):
            class Meta:
                model = test_model
                fields = ["quartz_type"]

        with pytest.raises(ImproperlyConfigured, match="form_fields and form_class"):
            ModelConfiguration(
                model=test_model,
                form_class=CustomForm,
                form_fields=["sample_description"],
            )

    def test_the_refusal_covers_every_component(self, test_model):
        """Every component is refused the same way, not just the form."""
        import django_tables2 as tables
        from django.core.exceptions import ImproperlyConfigured

        class CustomTable(tables.Table):
            class Meta:
                model = test_model

        with pytest.raises(ImproperlyConfigured, match="table_fields and table_class"):
            ModelConfiguration(
                model=test_model,
                table_class=CustomTable,
                table_fields=["sample_description"],
            )


class TestRegistrationValidation:
    """T014: Unit tests for registration-time validation."""

    def test_model_required(self):
        """Test that ModelConfiguration requires a model."""
        with pytest.raises(ConfigurationError, match="model is required"):
            ModelConfiguration(model=None)

    def test_model_must_inherit_from_sample_or_measurement(self, clean_registry):
        """Test that only Sample/Measurement subclasses can be registered."""

        class InvalidModel(models.Model):
            """Regular Django model (not Sample/Measurement)."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(ConfigurationError, match="must be a concrete subclass of"):
            clean_registry.register(InvalidModel)

    def test_duplicate_registration_rejected(self, clean_registry):
        """Test that registering the same model twice raises DuplicateRegistrationError."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # First registration should succeed
        clean_registry.register(RockSample)

        # Second registration should fail
        with pytest.raises(DuplicateRegistrationError, match="already registered"):
            clean_registry.register(RockSample)

    def test_invalid_field_name_in_list_fields(self):
        """Test that invalid field names in fields raise FieldValidationError."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(
            FieldValidationError, match="Invalid field 'nonexistent_field'"
        ):
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "nonexistent_field"],
            )

    def test_invalid_field_name_in_component_specific_fields(self):
        """Test that invalid field names in component-specific fields raise FieldValidationError."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError, match="Invalid field 'bad_field'"):
            ModelConfiguration(
                model=RockSample,
                table_fields=["rock_type", "bad_field"],
            )

    def test_invalid_related_field_path(self):
        """Test that related field paths are validated for base field only.

        Note: We only validate that the base field (e.g., 'source_ref') exists on the model.
        We do not validate the full path (e.g., 'source_ref__title') because:
        1. It would require recursive model introspection
        2. Django will raise clear errors at runtime if the path is invalid
        3. The path might be valid for some querysets but not others (e.g., prefetch_related)
        """

        class RelatedModel(models.Model):
            """Related model."""

            title = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class RockSample(Sample):
            """Test Sample with foreign key."""

            rock_type = models.CharField(max_length=100)
            source_ref = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)

            class Meta:
                app_label = "test_app"

        # Valid path with base field existing should work
        config = ModelConfiguration(
            model=RockSample,
            fields=["rock_type", "source_ref__title"],
        )
        assert "source_ref__title" in config.fields

        # Path with nonexistent base field should fail
        with pytest.raises(FieldValidationError, match="Invalid field"):
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "nonexistent__title"],
            )


class TestFieldValidationWithFuzzyMatching:
    """Test fuzzy field name matching for helpful error messages."""

    def test_fuzzy_match_suggests_close_field_names(self):
        """Test that FieldValidationError suggests similar field names."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()

            class Meta:
                app_label = "test_app"

        # Typo: "mineral_contnt" instead of "mineral_content"
        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "mineral_contnt"],
            )

        # Error message should suggest the correct field
        assert "mineral_contnt" in str(exc_info.value)
        assert "Did you mean" in str(exc_info.value)
        assert "mineral_content" in str(exc_info.value)

    def test_no_suggestions_when_no_close_matches(self):
        """Test that no suggestions are given when no close matches exist."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # Completely wrong field name
        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "xyz123"],
            )

        # Error message should not suggest anything
        assert "xyz123" in str(exc_info.value)
        assert "Did you mean" not in str(exc_info.value)
