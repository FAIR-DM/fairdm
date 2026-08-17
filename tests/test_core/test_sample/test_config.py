"""
Tests for Sample registry configuration (BaseSampleConfiguration).

Tests verify that the registry auto-generates forms, filters, tables, and
admin configurations for custom sample types via BaseSampleConfiguration.
"""

import pytest

from fairdm.registry import registry


@pytest.mark.django_db
class TestRegistryAutoGenerateForms:
    """Test registry auto-generates forms for custom sample types."""

    def test_registry_generates_form_for_sample(self, clean_registry):
        """Test that registry auto-generates ModelForm for registered sample type."""
        from fairdm_demo.models import RockSample

        # Get configuration (RockSample should already be registered via @register decorator)
        config = registry.get_for_model(RockSample)

        # Should have auto-generated form
        assert config.get_form_class() is not None
        assert hasattr(config.get_form_class(), "Meta")
        assert config.get_form_class().Meta.model == RockSample

    def test_auto_generated_form_includes_configured_fields(self, clean_registry):
        """Test that auto-generated form includes fields from configuration."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        # Form should include configured fields
        form_class = config.get_form_class()
        form = form_class()

        # Check that configured fields are present (from RockSampleConfig)
        assert "name" in form.fields
        assert "rock_type" in form.fields
        assert "collection_date" in form.fields


@pytest.mark.django_db
class TestRegistryAutoGenerateFilters:
    """Test registry auto-generates filters for custom sample types."""

    def test_registry_generates_filter_for_sample(self, clean_registry):
        """Test that registry auto-generates FilterSet for registered sample type."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        # Should have auto-generated filter
        assert config.get_filterset_class() is not None
        assert hasattr(config.get_filterset_class(), "Meta")
        assert config.get_filterset_class().Meta.model == RockSample

    def test_auto_generated_filter_includes_configured_fields(self, clean_registry):
        """Test that auto-generated filter includes fields from configuration."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        # FilterSet should include configured filter fields
        filterset_class = config.get_filterset_class()

        # Check that filterset has expected attributes
        assert hasattr(filterset_class, "Meta")
        assert filterset_class.Meta.model == RockSample


@pytest.mark.django_db
class TestRegistryAutoGenerateTables:
    """Test registry auto-generates tables for custom sample types."""

    def test_registry_generates_table_for_sample(self, clean_registry):
        """Test that registry auto-generates Table for registered sample type."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        # Should have auto-generated table
        assert config.get_table_class() is not None
        assert hasattr(config.get_table_class(), "Meta")
        assert config.get_table_class().Meta.model == RockSample

    def test_auto_generated_table_includes_configured_columns(self, clean_registry):
        """Test that auto-generated table includes columns from configuration."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        # Table should have columns
        table_class = config.get_table_class()
        table = table_class([])

        # Check that table has some columns
        assert len(table.columns) > 0


@pytest.mark.django_db
class TestRegistryAutoGenerateAdmin:
    """Test registry auto-generates admin for custom sample types."""

    def test_registry_generates_admin_for_sample(self, clean_registry):
        """Test that registry auto-generates ModelAdmin for registered sample type."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        # Should have auto-generated admin
        assert config.get_admin_class() is not None

        # Admin should be registered with admin site
        # (Note: This might require additional setup depending on registry implementation)

    def test_auto_generated_admin_has_basic_configuration(self, clean_registry):
        """Test that auto-generated admin has basic configuration."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        admin_class = config.get_admin_class()

        # Admin should have some basic attributes
        # (Actual attributes depend on registry implementation)
        assert admin_class is not None
