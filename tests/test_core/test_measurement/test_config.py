"""Tests for Measurement registry configuration (BaseMeasurementConfiguration)."""

import pytest

from fairdm.registry import registry


@pytest.mark.django_db
class TestRegistryAutoGenerateForms:
    def test_registry_generates_form_for_measurement(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        assert config.get_form_class() is not None
        assert hasattr(config.get_form_class(), "Meta")
        assert config.get_form_class().Meta.model == XRFMeasurement

    def test_auto_generated_form_includes_configured_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        form_class = config.get_form_class()
        form = form_class()

        assert "name" in form.fields
        assert "sample" in form.fields
        assert "dataset" in form.fields

    def test_auto_generated_form_includes_the_type_s_own_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        form = config.get_form_class()()

        assert "element" in form.fields
        assert "concentration_ppm" in form.fields


@pytest.mark.django_db
class TestRegistryAutoGenerateFilters:
    def test_registry_generates_filter_for_measurement(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        assert config.get_filterset_class() is not None
        assert hasattr(config.get_filterset_class(), "Meta")
        assert config.get_filterset_class().Meta.model == XRFMeasurement

    def test_auto_generated_filter_includes_configured_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        filterset_class = config.get_filterset_class()

        assert hasattr(filterset_class, "Meta")
        assert filterset_class.Meta.model == XRFMeasurement

    def test_auto_generated_filter_includes_the_type_s_own_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        filterset = config.get_filterset_class()()

        assert "element" in filterset.filters
        assert "concentration_ppm" in filterset.filters


@pytest.mark.django_db
class TestRegistryAutoGenerateTables:
    def test_registry_generates_table_for_measurement(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        assert config.get_table_class() is not None
        assert hasattr(config.get_table_class(), "Meta")
        assert config.get_table_class().Meta.model == XRFMeasurement

    def test_auto_generated_table_includes_configured_columns(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        table_class = config.get_table_class()
        table = table_class(XRFMeasurement.objects.none())

        assert len(table.columns) > 0

    def test_auto_generated_table_includes_the_type_s_own_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        table = config.get_table_class()(XRFMeasurement.objects.none())

        column_names = list(table.columns.columns.keys())
        assert "element" in column_names
        assert "concentration_ppm" in column_names


@pytest.mark.django_db
class TestRegistryAutoGenerateAdmin:
    def test_registry_generates_admin_for_measurement(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        assert config.get_admin_class() is not None

    def test_auto_generated_admin_has_basic_configuration(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        admin_class = config.get_admin_class()

        assert admin_class is not None

    def test_auto_generated_admin_includes_the_type_s_own_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)
        admin_class = config.get_admin_class()

        assert "element" in admin_class.list_display


@pytest.mark.django_db
class TestPolymorphicMeasurementQueries:
    def test_polymorphic_query_returns_subclass_instance(self, xrf_measurement):
        from demo.models import XRFMeasurement
        from fairdm.core.measurement.models import Measurement

        measurement = Measurement.objects.get(pk=xrf_measurement.pk)

        assert isinstance(measurement, XRFMeasurement)
        assert measurement.element == xrf_measurement.element
        assert measurement.concentration_ppm == xrf_measurement.concentration_ppm

    def test_mixed_polymorphic_queries(
        self, xrf_measurement, icp_ms_measurement, example_measurement
    ):
        from fairdm.core.measurement.models import Measurement

        measurements = list(Measurement.objects.all())

        assert len(measurements) == 3

        types = {type(m).__name__ for m in measurements}
        assert "ExampleMeasurement" in types
        assert "XRFMeasurement" in types
        assert "ICP_MS_Measurement" in types


@pytest.mark.django_db
class TestBaseMeasurementConfigurationIntegration:
    def test_measurement_config_inherits_from_base(self, clean_registry):
        from demo.models import XRFMeasurement
        from fairdm.core.measurement.config import BaseMeasurementConfiguration

        config = registry.get_for_model(XRFMeasurement)

        assert isinstance(config, BaseMeasurementConfiguration)

    def test_base_config_provides_standard_fields(self, clean_registry):
        from demo.models import XRFMeasurement

        config = registry.get_for_model(XRFMeasurement)

        assert "name" in config.table_fields
        assert "sample" in config.table_fields
        assert "dataset" in config.table_fields

        assert "name" in config.form_fields
        assert "sample" in config.form_fields
        assert "dataset" in config.form_fields

        assert "sample" in config.filterset_fields
        assert "dataset" in config.filterset_fields
