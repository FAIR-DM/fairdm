"""Test new ModelConfiguration with fairdm_demo models."""

import pytest
from django.contrib import admin
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from fairdm.registry import registry
from fairdm_demo.models import CustomParentSample, CustomSample, ExampleMeasurement


@pytest.mark.django_db
class TestDemoModelIntegration:
    """Test that demo models work with new ModelConfiguration."""

    def test_custom_sample_registered(self):
        """Test CustomSample is registered."""
        assert CustomSample in registry._registry

    def test_custom_sample_get_form_class(self):
        """Test form class generation for CustomSample."""
        config = registry.get_config(CustomSample)
        form_class = config.get_form_class()

        assert issubclass(form_class, ModelForm)
        assert form_class._meta.model == CustomSample

    def test_custom_sample_get_table_class(self):
        """Test table class generation for CustomSample."""
        config = registry.get_config(CustomSample)
        table_class = config.get_table_class()

        # CustomSample uses a custom table class
        assert issubclass(table_class, Table)

    def test_custom_sample_get_filterset_class(self):
        """Test filterset class generation for CustomSample."""
        config = registry.get_config(CustomSample)
        filterset_class = config.get_filterset_class()

        # CustomSample uses a custom filterset class
        assert issubclass(filterset_class, FilterSet)

    def test_custom_sample_get_admin_class(self):
        """Test admin class generation for CustomSample."""
        config = registry.get_config(CustomSample)
        admin_class = config.get_admin_class()

        assert issubclass(admin_class, admin.ModelAdmin)
        assert admin_class.model == CustomSample

    def test_custom_parent_sample_registered(self):
        """Test CustomParentSample is registered."""
        assert CustomParentSample in registry._registry

    def test_custom_parent_sample_components(self):
        """Test all components can be generated for CustomParentSample."""
        config = registry.get_config(CustomParentSample)

        form_class = config.get_form_class()
        table_class = config.get_table_class()
        filterset_class = config.get_filterset_class()
        admin_class = config.get_admin_class()

        assert issubclass(form_class, ModelForm)
        assert issubclass(table_class, Table)
        assert issubclass(filterset_class, FilterSet)
        assert issubclass(admin_class, admin.ModelAdmin)

    def test_example_measurement_registered(self):
        """Test ExampleMeasurement is registered."""
        assert ExampleMeasurement in registry._registry

    def test_example_measurement_components(self):
        """Test all components can be generated for ExampleMeasurement."""
        config = registry.get_config(ExampleMeasurement)

        form_class = config.get_form_class()
        table_class = config.get_table_class()
        filterset_class = config.get_filterset_class()
        admin_class = config.get_admin_class()

        assert issubclass(form_class, ModelForm)
        assert issubclass(table_class, Table)
        assert issubclass(filterset_class, FilterSet)
        assert issubclass(admin_class, admin.ModelAdmin)

    def test_custom_classes_preserved(self):
        """Test that custom classes (table, filterset) are preserved."""
        config = registry.get_config(CustomSample)

        # CustomSample specifies custom filterset and table classes
        assert config.has_custom_filterset()
        assert config.has_custom_table()

    def test_backwards_compatibility(self):
        """Test old-style configurations still work."""
        config = registry.get_config(CustomParentSample)

        # Old style uses resource_class attribute
        assert hasattr(config, "resource_class")
        assert config.resource_class is not None
