"""
Tests for Measurement registry configuration (BaseMeasurementConfiguration).

Tests verify that the registry auto-generates forms, filters, tables, and
admin configurations for custom measurement types via
BaseMeasurementConfiguration, and that polymorphic measurement queries
return correctly typed instances.
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
        assert config.get_form_class() is not None
        assert hasattr(config.get_form_class(), "Meta")
        assert config.get_form_class().Meta.model == XRFMeasurement

    def test_auto_generated_form_includes_configured_fields(self, clean_registry):
        """Test that auto-generated form includes fields from configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Form should include configured base fields
        form_class = config.get_form_class()
        form = form_class()

        # Check that fields every measurement has are present (from BaseMeasurementConfiguration)
        assert "name" in form.fields
        assert "sample" in form.fields
        assert "dataset" in form.fields

    def test_auto_generated_form_includes_the_type_s_own_fields(self, clean_registry):
        """T030: the form also carries fields declared only on XRFMeasurementConfig itself."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        form = config.get_form_class()()

        assert "element" in form.fields
        assert "concentration_ppm" in form.fields


@pytest.mark.django_db
class TestRegistryAutoGenerateFilters:
    """Test registry auto-generates filters for custom measurement types."""

    def test_registry_generates_filter_for_measurement(self, clean_registry):
        """Test that registry auto-generates FilterSet for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated filter
        assert config.get_filterset_class() is not None
        assert hasattr(config.get_filterset_class(), "Meta")
        assert config.get_filterset_class().Meta.model == XRFMeasurement

    def test_auto_generated_filter_includes_configured_fields(self, clean_registry):
        """Test that auto-generated filter includes fields from configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # FilterSet should include configured filter fields
        filterset_class = config.get_filterset_class()

        # Check that filterset has expected attributes
        assert hasattr(filterset_class, "Meta")
        assert filterset_class.Meta.model == XRFMeasurement

    def test_auto_generated_filter_includes_the_type_s_own_fields(self, clean_registry):
        """T030: the filterset also carries fields declared only on XRFMeasurementConfig."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        filterset = config.get_filterset_class()()

        assert "element" in filterset.filters
        assert "concentration_ppm" in filterset.filters


@pytest.mark.django_db
class TestRegistryAutoGenerateTables:
    """Test registry auto-generates tables for custom measurement types."""

    def test_registry_generates_table_for_measurement(self, clean_registry):
        """Test that registry auto-generates Table for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated table
        assert config.get_table_class() is not None
        assert hasattr(config.get_table_class(), "Meta")
        assert config.get_table_class().Meta.model == XRFMeasurement

    def test_auto_generated_table_includes_configured_columns(self, clean_registry):
        """Test that auto-generated table includes columns from configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Table should have columns
        table_class = config.get_table_class()
        # Pass a queryset instead of empty list (table expects queryset for prefetch_related)
        table = table_class(XRFMeasurement.objects.none())

        # Check that table has some columns
        assert len(table.columns) > 0

    def test_auto_generated_table_includes_the_type_s_own_fields(self, clean_registry):
        """T030: the table also carries columns for fields declared only on XRFMeasurementConfig."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        table = config.get_table_class()(XRFMeasurement.objects.none())

        column_names = list(table.columns.columns.keys())
        assert "element" in column_names
        assert "concentration_ppm" in column_names


@pytest.mark.django_db
class TestRegistryAutoGenerateAdmin:
    """Test registry auto-generates admin for custom measurement types."""

    def test_registry_generates_admin_for_measurement(self, clean_registry):
        """Test that registry auto-generates ModelAdmin for registered measurement type."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        # Should have auto-generated admin
        assert config.get_admin_class() is not None

        # Admin should be registered with admin site
        # (Note: This might require additional setup depending on registry implementation)

    def test_auto_generated_admin_has_basic_configuration(self, clean_registry):
        """Test that auto-generated admin has basic configuration."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        admin_class = config.get_admin_class()

        # Admin should have some basic attributes
        # (Actual attributes depend on registry implementation)
        assert admin_class is not None

    def test_auto_generated_admin_includes_the_type_s_own_fields(self, clean_registry):
        """T030: the admin's list_display carries fields declared only on XRFMeasurementConfig."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        admin_class = config.get_admin_class()

        assert "element" in admin_class.list_display


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

    def test_mixed_polymorphic_queries(
        self, xrf_measurement, icp_ms_measurement, example_measurement
    ):
        """Test querying multiple measurement types returns correct subclass instances."""
        from fairdm.core.measurement.models import Measurement

        # Query all measurements
        measurements = list(Measurement.objects.all())

        # Should have 3 measurements
        assert len(measurements) == 3

        # Each should be correctly typed (don't assume order)
        types = {type(m).__name__ for m in measurements}
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
        """T034: a type inheriting BaseMeasurementConfiguration receives the fields every
        measurement has, asserted by name rather than by ``hasattr`` - ``hasattr`` is true
        of an empty list too, and establishes nothing about what it contains."""
        from fairdm_demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        assert "name" in config.table_fields
        assert "sample" in config.table_fields
        assert "dataset" in config.table_fields

        assert "name" in config.form_fields
        assert "sample" in config.form_fields
        assert "dataset" in config.form_fields

        assert "sample" in config.filterset_fields
        assert "dataset" in config.filterset_fields
