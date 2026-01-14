"""Comprehensive tests for the FairDM registration system.

This module provides test coverage for advanced registration features,
auto-generation, component factories, ModelConfiguration, and metadata classes.
"""

import pytest
from django.db import models

from fairdm.config import (
    Authority,
    Citation,
    ModelConfiguration,
    ModelMetadata,
)
from fairdm.core.models import Measurement, Sample
from fairdm.registry import registry


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

    def test_model_configuration_with_model(self, db):
        """Test creating ModelConfiguration with model."""
        config = ModelConfiguration(model=Sample)

        assert config.model == Sample
        assert isinstance(config.metadata, ModelMetadata)

    def test_model_configuration_field_attributes(self, db):
        """Test component-specific field attributes."""
        config = ModelConfiguration(
            model=Sample,
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
            model=Sample,
            filterset_fields=["name", "status"],
        )
        registry.register(Sample, config=config)

        # Access via property to trigger auto-generation
        filterset_class = config.filterset
        assert issubclass(filterset_class, FilterSet)
        assert not config.has_custom_filterset()

    def test_form_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of ModelForm class via property."""
        from django.forms import ModelForm

        config = ModelConfiguration(
            model=Sample,
            form_fields=["name", "status"],
        )
        registry.register(Sample, config=config)

        # Access via property to trigger auto-generation
        form_class = config.form
        assert issubclass(form_class, ModelForm)
        assert not config.has_custom_form()

    def test_table_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of Table class via property."""
        from django_tables2 import Table

        config = ModelConfiguration(
            model=Sample,
            table_fields=["name", "status"],
        )
        registry.register(Sample, config=config)

        # Access via property to trigger auto-generation
        table_class = config.table
        assert issubclass(table_class, Table)
        assert not config.has_custom_table()

    def test_resource_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of import/export Resource class via property."""
        from import_export.resources import ModelResource

        config = ModelConfiguration(
            model=Sample,
            resource_fields=["name", "status"],
        )
        registry.register(Sample, config=config)

        # Access via property to trigger auto-generation
        resource_class = config.resource
        assert issubclass(resource_class, ModelResource)
        assert not config.has_custom_resource()

    def test_admin_property_auto_generated(self, clean_registry, db):
        """Test auto-generation of ModelAdmin class via property."""
        from django.contrib.admin import ModelAdmin

        config = ModelConfiguration(
            model=Sample,
            admin_list_display=["name", "status"],
        )
        registry.register(Sample, config=config)

        # Access via property to trigger auto-generation
        admin_class = config.admin
        assert issubclass(admin_class, ModelAdmin)
        assert not config.has_custom_admin()


class TestComponentOverrides:
    """Test that custom components override auto-generation."""

    def test_custom_form_class_override(self, clean_registry, db):
        """Test providing custom form class."""
        from django import forms

        class CustomSampleForm(forms.ModelForm):
            class Meta:
                model = Sample
                fields = ["name"]

        config = ModelConfiguration(
            model=Sample,
            form_class=CustomSampleForm,
        )
        registry.register(Sample, config=config)

        # Test that custom form is recognized
        assert config.has_custom_form()
        assert config.form_class == CustomSampleForm
        assert config.form == CustomSampleForm

    def test_custom_filterset_class_override(self, clean_registry, db):
        """Test providing custom FilterSet class."""
        from django_filters import CharFilter, FilterSet

        class CustomSampleFilter(FilterSet):
            name = CharFilter(lookup_expr="icontains")

            class Meta:
                model = Sample
                fields = ["name"]

        config = ModelConfiguration(
            model=Sample,
            filterset_class=CustomSampleFilter,
        )
        registry.register(Sample, config=config)

        # Test that custom filterset is recognized
        assert config.has_custom_filterset()
        assert config.filterset_class == CustomSampleFilter
        assert config.filterset == CustomSampleFilter

    def test_custom_table_class_override(self, clean_registry, db):
        """Test providing custom Table class."""
        import django_tables2 as tables

        class CustomSampleTable(tables.Table):
            name = tables.Column()

            class Meta:
                model = Sample
                fields = ["name"]

        config = ModelConfiguration(
            model=Sample,
            table_class=CustomSampleTable,
        )
        registry.register(Sample, config=config)

        # Test that custom table is recognized
        assert config.has_custom_table()
        assert config.table_class == CustomSampleTable
        assert config.table == CustomSampleTable


class TestRegistryItemStructure:
    """Test the structure of registry items."""

    def test_registry_item_has_config(self, clean_registry, db):
        """Test that registry items contain config."""
        config = ModelConfiguration(
            model=Sample,
            display_name="Structure Test",
        )
        registry.register(Sample, config=config)

        # Test that Sample is in registry and has config
        assert Sample in registry._registry
        stored_config = registry.get_for_model(Sample)
        assert isinstance(stored_config, ModelConfiguration)
        assert stored_config.display_name == "Structure Test"


class TestRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def test_register_with_config(self, clean_registry, db):
        """Test registering with explicit config."""
        config = ModelConfiguration(model=Sample)
        registry.register(Sample, config=config)

        assert Sample in registry._registry
        stored_config = registry.get_for_model(Sample)
        assert isinstance(stored_config, ModelConfiguration)
        assert stored_config.model == Sample

    def test_get_for_model_returns_config(self, clean_registry, db):
        """Test that get_for_model returns the stored config."""
        config = ModelConfiguration(
            model=Sample,
            display_name="Test Config",
        )
        registry.register(Sample, config=config)

        # Access the stored config via get_for_model
        retrieved_config = registry.get_for_model(Sample)
        assert retrieved_config.get_display_name() == "Test Config"

    def test_multiple_registrations_same_session(self, clean_registry, db):
        """Test multiple models can be registered in same session."""
        sample_config = ModelConfiguration(
            model=Sample,
            display_name="Sample Config",
        )
        measurement_config = ModelConfiguration(
            model=Measurement,
            display_name="Measurement Config",
        )

        registry.register(Sample, config=sample_config)
        registry.register(Measurement, config=measurement_config)

        assert Sample in registry._registry
        assert Measurement in registry._registry


class TestRegistryIntegration:
    """Test integration between registry and other FairDM components."""

    def test_registry_stores_config(self, clean_registry, db):
        """Test that registry properly stores and retrieves config."""
        config = ModelConfiguration(
            model=Sample,
            display_name="Integration Test",
        )
        registry.register(Sample, config=config)

        # Verify registration succeeded
        assert Sample in registry._registry
        stored_config = registry.get_for_model(Sample)
        assert stored_config.get_display_name() == "Integration Test"


# Run tests with: poetry run pytest tests/test_registry_extended.py -v
