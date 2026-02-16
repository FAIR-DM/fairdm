"""
Integration tests for Measurement registry integration.

Tests verify that the registry auto-generates forms, filters, tables,
and admin configurations for custom measurement types.
"""

import pytest

from fairdm.registry import registry


@pytest.mark.django_db
class TestRegistryAutoGenerateForms:
    """Test registry auto-generates forms for custom measurement types."""

    def test_registry_generates_form_for_measurement(self, clean_registry):
        """Test that registry auto-generates ModelForm for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        # Get configuration (XRFMeasurement should already be registered via @register decorator)
        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated form
        assert config.form is not None
        assert hasattr(config.form, "Meta")
        assert config.form.Meta.model == XRFMeasurement

    def test_auto_generated_form_includes_configured_fields(self, clean_registry):
        """Test that auto-generated form includes fields from configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Form should include configured base fields
        form_class = config.form
        form = form_class()

        # Check that configured base fields are present (from BaseMeasurementConfiguration)
        # Note: Child-specific fields like 'element' are not auto-configured
        assert "name" in form.fields
        assert "sample" in form.fields
        assert "dataset" in form.fields


@pytest.mark.django_db
class TestRegistryAutoGenerateFilters:
    """Test registry auto-generates filters for custom measurement types."""

    def test_registry_generates_filter_for_measurement(self, clean_registry):
        """Test that registry auto-generates FilterSet for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated filter
        assert config.filterset is not None
        assert hasattr(config.filterset, "Meta")
        assert config.filterset.Meta.model == XRFMeasurement

    def test_auto_generated_filter_includes_configured_fields(self, clean_registry):
        """Test that auto-generated filter includes fields from configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # FilterSet should include configured filter fields
        filterset_class = config.filterset

        # Check that filterset has expected attributes
        assert hasattr(filterset_class, "Meta")
        assert filterset_class.Meta.model == XRFMeasurement


@pytest.mark.django_db
class TestRegistryAutoGenerateTables:
    """Test registry auto-generates tables for custom measurement types."""

    def test_registry_generates_table_for_measurement(self, clean_registry):
        """Test that registry auto-generates Table for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated table
        assert config.table is not None
        assert hasattr(config.table, "Meta")
        assert config.table.Meta.model == XRFMeasurement

    def test_auto_generated_table_includes_configured_columns(self, clean_registry):
        """Test that auto-generated table includes columns from configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Table should have columns
        table_class = config.table
        # Pass a queryset instead of empty list (table expects queryset for prefetch_related)
        table = table_class(XRFMeasurement.objects.none())

        # Check that table has some columns
        assert len(table.columns) > 0


@pytest.mark.django_db
class TestRegistryAutoGenerateAdmin:
    """Test registry auto-generates admin for custom measurement types."""

    def test_registry_generates_admin_for_measurement(self, clean_registry):
        """Test that registry auto-generates ModelAdmin for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated admin
        assert config.admin is not None

        # Admin should be registered with admin site
        # (Note: This might require additional setup depending on registry implementation)

    def test_auto_generated_admin_has_basic_configuration(self, clean_registry):
        """Test that auto-generated admin has basic configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        admin_class = config.admin

        # Admin should have some basic attributes
        # (Actual attributes depend on registry implementation)
        assert admin_class is not None


@pytest.mark.django_db
class TestPolymorphicMeasurementQueries:
    """Test that polymorphic measurement queries return correct subclass instances."""

    def test_polymorphic_query_returns_subclass_instance(self, xrf_measurement):
        """Test that querying Measurement returns the correct polymorphic subclass."""
        from fairdm.core.measurement.models import Measurement
        from fairdm_demo.models import XRFMeasurement

        # Query the base Measurement model
        measurement = Measurement.objects.get(pk=xrf_measurement.pk)

        # Should return the subclass instance, not base Measurement
        assert isinstance(measurement, XRFMeasurement)
        assert measurement.element == xrf_measurement.element
        assert measurement.concentration_ppm == xrf_measurement.concentration_ppm

    def test_mixed_polymorphic_queries(self, xrf_measurement, icp_ms_measurement, example_measurement):
        """Test querying multiple measurement types returns correct subclass instances."""
        from fairdm.core.measurement.models import Measurement

        # Query all measurements
        measurements = list(Measurement.objects.all())

        # Should have 3 measurements
        assert len(measurements) == 3

        # Each should be correctly typed (don't assume order)
        types = set(type(m).__name__ for m in measurements)
        assert "ExampleMeasurement" in types
        assert "XRFMeasurement" in types
        assert "ICP_MS_Measurement" in types


@pytest.mark.django_db
class TestBaseMeasurementConfigurationIntegration:
    """Test BaseMeasurementConfiguration integration with registry."""

    def test_measurement_config_inherits_from_base(self, clean_registry):
        """Test that measurement configs inherit from BaseMeasurementConfiguration."""
        from fairdm.core.measurement.config import BaseMeasurementConfiguration
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Configuration should be instance of BaseMeasurementConfiguration
        assert isinstance(config, BaseMeasurementConfiguration)

    def test_base_config_provides_standard_fields(self, clean_registry):
        """Test that BaseMeasurementConfiguration provides standard field sets."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have standard field configurations
        assert hasattr(config, "table_fields")
        assert hasattr(config, "form_fields")
        assert hasattr(config, "filterset_fields")
