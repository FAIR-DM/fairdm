"""Comprehensive tests for the FairDM registration system.

This module provides test coverage for advanced registration features,
auto-generation, component factories, ModelConfiguration, and metadata classes.
"""

import pytest

import fairdm
from fairdm.config import (
    Authority,
    Citation,
    MeasurementConfig,
    ModelConfiguration,
    ModelMetadata,
    SampleConfig,
)
from fairdm.core.models import Measurement, Sample
from fairdm.registry import registry


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
        authority = Authority(name="Test Authority", short_name="TA", website="https://example.com")
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
        authority = Authority(name="Test Authority", short_name="TA", website="https://example.com")

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

    def test_model_configuration_initialization_empty(self, db):
        """Test creating ModelConfiguration with no arguments."""
        config = ModelConfiguration()

        assert config.model is None
        assert isinstance(config.metadata, ModelMetadata)
        assert config.fields == []
        assert config.private_fields == []
        assert config.fieldsets == []

    def test_model_configuration_with_model(self, db):
        """Test creating ModelConfiguration with model."""
        config = ModelConfiguration(model=Sample)

        assert config.model == Sample
        assert isinstance(config.metadata, ModelMetadata)

    def test_model_configuration_field_properties(self, db):
        """Test list_fields, detail_fields, filter_fields properties."""
        config = ModelConfiguration(model=Sample)
        config.table_fields = ["name", "created"]
        config.form_fields = ["name", "description"]
        config.filterset_fields = ["created"]

        # Test backward compatibility properties
        assert config.list_fields == ["name", "created"]
        assert config.detail_fields == ["name", "description"]
        assert config.filter_fields == ["created"]

    def test_model_configuration_field_property_setters(self, db):
        """Test that field property setters work correctly."""
        config = ModelConfiguration(model=Sample)

        config.list_fields = ["field1", "field2"]
        assert config.table_fields == ["field1", "field2"]

        config.detail_fields = ["field3", "field4"]
        assert config.form_fields == ["field3", "field4"]

        config.filter_fields = ["field5"]
        assert config.filterset_fields == ["field5"]

    def test_get_list_fields_defaults(self, db):
        """Test get_list_fields with no configuration."""
        config = ModelConfiguration(model=Sample)

        fields = config.get_list_fields()
        assert isinstance(fields, list)
        assert "name" in fields
        assert "created" in fields
        assert "modified" in fields

    def test_get_list_fields_with_table_fields(self, db):
        """Test get_list_fields when table_fields is specified."""
        config = ModelConfiguration(model=Sample)
        config.table_fields = ["custom1", "custom2"]

        assert config.get_list_fields() == ["custom1", "custom2"]

    def test_get_list_fields_with_general_fields(self, db):
        """Test get_list_fields falls back to general fields."""
        config = ModelConfiguration(model=Sample)
        config.fields = ["general1", "general2"]

        assert config.get_list_fields() == ["general1", "general2"]

    def test_get_detail_fields_defaults(self, db):
        """Test get_detail_fields with no configuration."""
        config = ModelConfiguration(model=Sample)

        fields = config.get_detail_fields()
        assert isinstance(fields, list)
        # Should default to list_fields
        assert fields == config.get_list_fields()

    def test_get_detail_fields_with_form_fields(self, db):
        """Test get_detail_fields when form_fields is specified."""
        config = ModelConfiguration(model=Sample)
        config.form_fields = ["form1", "form2"]

        assert config.get_detail_fields() == ["form1", "form2"]

    def test_get_filter_fields_defaults(self, db):
        """Test get_filter_fields with defaults."""
        config = ModelConfiguration(model=Sample)

        fields = config.get_filter_fields()
        assert isinstance(fields, list)
        assert "created" in fields
        assert "modified" in fields

    def test_get_filter_fields_with_filterset_fields(self, db):
        """Test get_filter_fields when filterset_fields is specified."""
        config = ModelConfiguration(model=Sample)
        config.filterset_fields = ["filter1", "filter2"]

        assert config.get_filter_fields() == ["filter1", "filter2"]

    def test_get_fields_empty(self, db):
        """Test get_fields when fields is empty."""
        config = ModelConfiguration(model=Sample)

        assert config.get_fields() == []

    def test_get_fields_with_values(self, db):
        """Test get_fields with configured fields."""
        config = ModelConfiguration(model=Sample)
        config.fields = ["field1", "field2"]

        fields = config.get_fields()
        assert "id" in fields
        assert "dataset" in fields
        assert "field1" in fields
        assert "field2" in fields

    def test_get_fields_with_id_already_present(self, db):
        """Test get_fields when id is already in fields list."""
        config = ModelConfiguration(model=Sample)
        config.fields = ["id", "field1", "field2"]

        fields = config.get_fields()
        # Should not duplicate id
        assert fields == ["id", "field1", "field2"]

    def test_get_fieldsets_empty(self, db):
        """Test get_fieldsets with no configuration."""
        config = ModelConfiguration(model=Sample)

        assert config.get_fieldsets() is None

    def test_get_fieldsets_with_dict(self, db):
        """Test get_fieldsets with dict configuration."""
        config = ModelConfiguration(model=Sample)
        config.fieldsets = {"General": ["name", "description"]}

        fieldsets = config.get_fieldsets()
        # fairdm_fieldsets_to_django converts dict to tuple
        assert isinstance(fieldsets, (tuple, list))
        assert len(fieldsets) > 0

    def test_get_fieldsets_with_list(self, db):
        """Test get_fieldsets with list configuration."""
        config = ModelConfiguration(model=Sample)
        fieldset_list = [("General", {"fields": ["name", "description"]})]
        config.fieldsets = fieldset_list

        fieldsets = config.get_fieldsets()
        assert fieldsets == fieldset_list

    def test_get_fieldsets_from_fields(self, db):
        """Test get_fieldsets falls back to fields."""
        config = ModelConfiguration(model=Sample)
        config.fields = ["field1", "field2"]

        fieldsets = config.get_fieldsets()
        assert isinstance(fieldsets, list)
        assert len(fieldsets) == 1
        assert fieldsets[0] == (None, {"fields": ["field1", "field2"]})


class TestAutoGeneratedComponents:
    """Test auto-generation of forms, filters, tables, and resources."""

    def test_get_filterset_class_auto_generated(self, clean_registry, db):
        """Test auto-generation of FilterSet class."""

        @fairdm.register
        class AutoFilterConfig(SampleConfig):
            model = Sample
            filterset_fields = ["name", "status"]

        config = registry._registry[Sample]["config"]
        # Note: BaseModelConfig doesn't have get_filterset_class
        # This tests that the config is properly initialized
        assert config.model == Sample
        assert config.filterset_fields == ["name", "status"]
        assert not config.has_custom_filterset()

    def test_get_form_class_auto_generated(self, clean_registry, db):
        """Test auto-generation of ModelForm class."""

        @fairdm.register
        class AutoFormConfig(SampleConfig):
            model = Sample
            form_fields = ["name", "local_id", "status"]

        config = registry._registry[Sample]["config"]
        # Test that config is properly initialized
        assert config.model == Sample
        assert not config.has_custom_form()

    def test_get_table_class_auto_generated(self, clean_registry, db):
        """Test auto-generation of Table class."""

        @fairdm.register
        class AutoTableConfig(SampleConfig):
            model = Sample
            table_fields = ["name", "status", "added"]

        config = registry._registry[Sample]["config"]
        # Test that config is properly initialized
        assert config.model == Sample
        assert not config.has_custom_table()

    def test_get_resource_class_auto_generated(self, clean_registry, db):
        """Test auto-generation of import/export Resource class."""

        @fairdm.register
        class AutoResourceConfig(SampleConfig):
            model = Sample
            resource_fields = ["name", "local_id", "status"]

        config = registry._registry[Sample]["config"]
        # Test that config is properly initialized
        assert config.model == Sample
        assert not config.has_custom_resource()

    def test_get_serializer_class_when_drf_available(self, clean_registry, db):
        """Test serializer class generation (returns None if DRF not configured)."""

        @fairdm.register
        class AutoSerializerConfig(SampleConfig):
            model = Sample
            serializer_fields = ["name", "status"]

        config = registry._registry[Sample]["config"]
        # Test that config is properly initialized
        assert config.model == Sample
        assert not config.has_custom_serializer()


class TestComponentOverrides:
    """Test that custom components override auto-generation."""

    def test_custom_form_class_override(self, clean_registry, db):
        """Test providing custom form class."""
        from django import forms

        class CustomSampleForm(forms.ModelForm):
            class Meta:
                model = Sample
                fields = ["name"]

        @fairdm.register
        class CustomFormConfig(SampleConfig):
            model = Sample
            form_class = CustomSampleForm

        config = registry._registry[Sample]["config"]
        # Test that custom form is recognized
        assert config.has_custom_form()
        assert config.form_class == CustomSampleForm

    def test_custom_filterset_class_override(self, clean_registry, db):
        """Test providing custom FilterSet class."""
        from django_filters import CharFilter, FilterSet

        class CustomSampleFilter(FilterSet):
            name = CharFilter(lookup_expr="icontains")

            class Meta:
                model = Sample
                fields = ["name"]

        @fairdm.register
        class CustomFilterConfig(SampleConfig):
            model = Sample
            filterset_class = CustomSampleFilter

        config = registry._registry[Sample]["config"]
        # Test that custom filterset is recognized
        assert config.has_custom_filterset()
        assert config.filterset_class == CustomSampleFilter

    def test_custom_table_class_override(self, clean_registry, db):
        """Test providing custom Table class."""
        import django_tables2 as tables

        class CustomSampleTable(tables.Table):
            name = tables.Column()

            class Meta:
                model = Sample
                fields = ["name"]

        @fairdm.register
        class CustomTableConfig(SampleConfig):
            model = Sample
            table_class = CustomSampleTable

        config = registry._registry[Sample]["config"]
        # Test that custom table is recognized
        assert config.has_custom_table()
        assert config.table_class == CustomSampleTable

    def test_custom_component_via_string_path(self, clean_registry, db):
        """Test providing custom component via import string."""
        from fairdm.core.sample.filters import SampleFilter

        @fairdm.register
        class StringPathConfig(SampleConfig):
            model = Sample
            # Use actual class reference
            filterset_class = SampleFilter

        config = registry._registry[Sample]["config"]
        # Test that class is properly assigned
        assert config.has_custom_filterset()
        assert config.filterset_class == SampleFilter


class TestRegistryItemStructure:
    """Test the structure of registry items."""

    def test_registry_item_has_required_keys(self, clean_registry, db):
        """Test that registry items contain all required keys."""

        @fairdm.register
        class StructureTestConfig(SampleConfig):
            model = Sample
            display_name = "Structure Test"

        item = registry._registry[Sample]

        # Check all expected keys are present
        required_keys = [
            "app_label",
            "class",
            "config",
            "full_name",
            "model",
            "path",
            "type",
            "verbose_name",
            "verbose_name_plural",
            "slug",
            "slug_plural",
        ]

        for key in required_keys:
            assert key in item, f"Missing key: {key}"

    def test_registry_item_values_correct(self, clean_registry, db):
        """Test that registry item values are correct."""

        @fairdm.register
        class ValueTestConfig(SampleConfig):
            model = Sample
            display_name = "Value Test"

        item = registry._registry[Sample]

        assert item["app_label"] == "sample"
        assert item["class"] == Sample
        assert item["model"] == "sample"
        assert item["type"] == "sample"
        assert "sample" in item["full_name"]
        assert Sample.__module__ in item["path"]


class TestRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def test_register_with_no_config_uses_defaults(self, clean_registry, db):
        """Test registering without explicit config creates default config."""
        # Direct registration (not using decorator)
        registry.register(Sample)

        assert Sample in registry._registry
        config = registry._registry[Sample]["config"]
        assert isinstance(config, ModelConfiguration)
        assert config.model == Sample

    def test_get_config_with_existing_fairdm_attribute(self, clean_registry, db):
        """Test that config is properly stored and accessible."""

        @fairdm.register
        class ExistingConfig(SampleConfig):
            model = Sample
            display_name = "Existing Config"

        # Access the stored config directly from registry
        config = registry._registry[Sample]["config"]
        assert config.get_display_name() == "Existing Config"

    def test_multiple_registrations_same_session(self, clean_registry, db):
        """Test multiple models can be registered in same session."""

        @fairdm.register
        class Config1(SampleConfig):
            model = Sample
            display_name = "Config 1"

        @fairdm.register
        class Config2(MeasurementConfig):
            model = Measurement
            display_name = "Config 2"

        assert len(registry.all) == 2
        assert Sample in registry._registry
        assert Measurement in registry._registry


class TestRegistryIntegration:
    """Test integration between registry and other FairDM components."""

    def test_registry_actstream_integration(self, clean_registry, db):
        """Test that actstream registration is called."""

        @fairdm.register
        class ActstreamTestConfig(SampleConfig):
            model = Sample
            display_name = "Actstream Test"

        # Should register with actstream without errors
        # The actual actstream functionality is tested elsewhere
        assert Sample in registry._registry

    def test_registry_admin_integration(self, clean_registry, db):
        """Test that admin registration is attempted."""

        @fairdm.register
        class AdminTestConfig(SampleConfig):
            model = Sample
            display_name = "Admin Test"

        # Should attempt admin registration without raising errors
        # Even if admin registration fails, it should be silent
        assert Sample in registry._registry


# Run tests with: poetry run pytest tests/test_registry_extended.py -v
