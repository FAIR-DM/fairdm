"""Tests for Measurement registry configuration (BaseMeasurementConfiguration)."""

import pytest

from demo.models import XRFMeasurement
from fairdm.registry import registry


@pytest.mark.django_db
class TestRegistryAutoGenerateForms:
    def test_auto_generated_form_includes_the_type_s_own_fields(self):
        config = registry.get_for_model(XRFMeasurement)
        form = config.get_form_class()()

        assert {"name", "sample", "dataset"} <= set(form.fields)
        assert "element" in form.fields
        assert "concentration_ppm" in form.fields


@pytest.mark.django_db
class TestRegistryAutoGenerateFilters:
    def test_auto_generated_filter_includes_the_type_s_own_fields(self):
        config = registry.get_for_model(XRFMeasurement)
        filterset = config.get_filterset_class()()

        assert "sample" in filterset.filters
        assert "element" in filterset.filters
        assert "concentration_ppm" in filterset.filters


@pytest.mark.django_db
class TestRegistryAutoGenerateTables:
    def test_auto_generated_table_includes_the_type_s_own_fields(self):
        config = registry.get_for_model(XRFMeasurement)
        table = config.get_table_class()(XRFMeasurement.objects.none())

        column_names = list(table.columns.columns.keys())
        assert "sample" in column_names
        assert "element" in column_names
        assert "concentration_ppm" in column_names


@pytest.mark.django_db
class TestRegistryAutoGenerateAdmin:
    def test_auto_generated_admin_includes_the_type_s_own_fields(self):
        config = registry.get_for_model(XRFMeasurement)
        admin_class = config.get_admin_class()

        assert "element" in admin_class.list_display
