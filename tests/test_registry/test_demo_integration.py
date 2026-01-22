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
        config = registry.get_for_model(CustomSample)
        form_class = config.get_form_class()

        assert issubclass(form_class, ModelForm)
        assert form_class._meta.model == CustomSample

    def test_custom_sample_get_table_class(self):
        """Test table class generation for CustomSample."""
        config = registry.get_for_model(CustomSample)
        table_class = config.get_table_class()

        # CustomSample uses a custom table class
        assert issubclass(table_class, Table)

    def test_custom_sample_get_filterset_class(self):
        """Test filterset class generation for CustomSample."""
        config = registry.get_for_model(CustomSample)
        filterset_class = config.get_filterset_class()

        # CustomSample uses a custom filterset class
        assert issubclass(filterset_class, FilterSet)

    def test_custom_sample_get_admin_class(self):
        """Test admin class generation for CustomSample."""
        config = registry.get_for_model(CustomSample)
        admin_class = config.get_admin_class()

        assert issubclass(admin_class, admin.ModelAdmin)
        assert admin_class.model == CustomSample

    def test_custom_parent_sample_registered(self):
        """Test CustomParentSample is registered."""
        assert CustomParentSample in registry._registry

    def test_custom_parent_sample_components(self):
        """Test all components can be generated for CustomParentSample."""
        config = registry.get_for_model(CustomParentSample)

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
        config = registry.get_for_model(ExampleMeasurement)

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
        config = registry.get_for_model(CustomSample)

        # CustomSample specifies custom filterset and table classes
        assert config.has_custom_filterset()
        assert config.has_custom_table()


# ============================================================================
# Feature 007: Sample Type Registration Tests
# ============================================================================


@pytest.mark.django_db
class TestSampleRegistration:
    """Test custom sample type registration with Feature 004 registry."""

    def test_sample_can_be_registered(self):
        """Test that a custom sample type can be registered with the registry."""
        from fairdm_demo.models import RockSample

        is_registered = registry.is_registered(RockSample)
        assert is_registered is True

    def test_registered_sample_has_configuration(self):
        """Test that registered sample types have accessible configuration objects."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        assert config is not None
        assert config.model == RockSample

    def test_registered_sample_configuration_has_fields(self):
        """Test that registered sample configuration includes field definitions."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)

        assert hasattr(config, "fields")
        assert config.fields is not None
        assert len(config.fields) > 0

    def test_multiple_sample_types_can_be_registered(self):
        """Test that multiple sample types can be registered independently."""
        from fairdm_demo.models import RockSample, WaterSample

        rock_registered = registry.is_registered(RockSample)
        water_registered = registry.is_registered(WaterSample)

        assert rock_registered is True
        assert water_registered is True

    def test_registered_sample_has_display_name(self):
        """Test that registered samples have human-readable display names."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        display_name = config.get_display_name()

        assert display_name is not None
        assert len(display_name) > 0

    def test_registry_can_list_all_registered_samples(self):
        """Test that registry can provide list of all registered sample types."""
        from fairdm_demo.models import RockSample, WaterSample

        all_samples = registry.samples  # Returns model classes, not configs

        assert RockSample in all_samples
        assert WaterSample in all_samples

    def test_registry_distinguishes_samples_from_measurements(self):
        """Test that registry correctly categorizes samples vs measurements."""
        from fairdm_demo.models import RockSample

        samples = registry.samples  # Returns model classes
        measurements = registry.measurements  # Returns model classes

        assert RockSample in samples
        assert RockSample not in measurements

    def test_unregistered_sample_type_raises_error(self):
        """Test that accessing unregistered model raises appropriate error."""
        from fairdm.core.sample.models import Sample

        # We can't create a test model on the fly because Django requires app_label
        # So we'll just test that a model that's not registered raises KeyError
        # We'll use the base Sample class which is not registered
        with pytest.raises(KeyError, match="not registered with the FairDM registry"):
            registry.get_for_model(Sample)


@pytest.mark.django_db
class TestSampleAutoGeneratedComponents:
    """Test that registry auto-generates components for registered sample types."""

    def test_auto_generated_form_exists(self):
        """Test that registry auto-generates a ModelForm for registered sample."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form_class = config.get_form_class()

        assert form_class is not None
        assert issubclass(form_class, ModelForm)

    def test_auto_generated_form_includes_base_fields(self):
        """Test that auto-generated form includes configured fields."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form_class = config.get_form_class()
        form = form_class()

        # Check for configured fields from RockSampleConfig
        assert "name" in form.fields
        assert "rock_type" in form.fields
        assert "collection_date" in form.fields

    def test_auto_generated_form_includes_custom_fields(self):
        """Test that auto-generated form includes subclass-specific fields."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form_class = config.get_form_class()
        form = form_class()

        # RockSample has rock_type field
        assert "rock_type" in form.fields

    def test_auto_generated_filter_exists(self):
        """Test that registry auto-generates a FilterSet for registered sample."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        filter_class = config.get_filterset_class()

        assert filter_class is not None
        assert issubclass(filter_class, FilterSet)

    def test_auto_generated_table_exists(self):
        """Test that registry auto-generates a Table for registered sample."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        table_class = config.get_table_class()

        assert table_class is not None
        assert issubclass(table_class, Table)

    def test_auto_generated_table_includes_base_columns(self):
        """Test that auto-generated table includes base Sample columns."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        table_class = config.get_table_class()
        table = table_class([])

        assert "name" in table.columns

    def test_auto_generated_admin_exists(self):
        """Test that registry auto-generates a ModelAdmin for registered sample."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        admin_class = config.get_admin_class()

        assert admin_class is not None
        assert issubclass(admin_class, admin.ModelAdmin)

    def test_different_sample_types_have_different_components(self):
        """Test that different sample types get different auto-generated components."""
        from fairdm_demo.models import RockSample, WaterSample

        rock_config = registry.get_for_model(RockSample)
        water_config = registry.get_for_model(WaterSample)

        assert rock_config.get_form_class() != water_config.get_form_class()
        assert rock_config.get_filterset_class() != water_config.get_filterset_class()
        assert rock_config.get_table_class() != water_config.get_table_class()
