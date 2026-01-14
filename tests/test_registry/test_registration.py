"""Test the FairDM registration API functionality.

This module tests the @fairdm.register decorator system using
the actual Sample and Measurement classes from the core framework.
"""

import pytest
from django.db import models

import fairdm
from fairdm.core.models import Measurement, Sample
from fairdm.registry import registry


class TestBasicRegistration:
    """T015: Integration test for basic model registration."""

    @pytest.fixture
    def clean_registry(self):
        """Clean the registry before and after each test."""
        registry._registry.clear()
        yield registry
        registry._registry.clear()

    def test_register_model_with_fields(self, clean_registry):
        """Test basic registration with field configuration."""

        class GraniteRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()
            weight_grams = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register with fields using ModelConfiguration
        config = fairdm.config.ModelConfiguration(
            model=GraniteRockSample,
            table_fields=["rock_type", "weight_grams"],
            form_fields=["rock_type", "mineral_content", "weight_grams"],
        )
        clean_registry.register(GraniteRockSample, config=config)

        # Verify registration
        assert GraniteRockSample in clean_registry._registry
        registered_config = clean_registry.get_for_model(GraniteRockSample)

        assert registered_config.model is GraniteRockSample
        assert registered_config.table_fields == ["rock_type", "weight_grams"]
        assert registered_config.form_fields == ["rock_type", "mineral_content", "weight_grams"]

    def test_verify_all_component_properties_accessible(self, clean_registry):
        """Test that all 6 component properties work after registration."""

        class BasaltRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)
            sample_location = models.CharField(max_length=200)

            class Meta:
                app_label = "test_app"

        # Register model with ModelConfiguration
        config = fairdm.config.ModelConfiguration(
            model=BasaltRockSample,
            fields=["rock_type", "sample_location"],
        )
        clean_registry.register(BasaltRockSample, config=config)

        registered_config = clean_registry.get_for_model(BasaltRockSample)

        # Access form property (should not raise)
        form_class = registered_config.form
        assert form_class is not None
        assert hasattr(form_class, "base_fields")

        # Access table property (should not raise)
        table_class = registered_config.table
        assert table_class is not None
        assert hasattr(table_class, "base_columns")

        # Access filterset property (should not raise)
        filterset_class = registered_config.filterset
        assert filterset_class is not None
        assert hasattr(filterset_class, "base_filters")

        # Access serializer property (should not raise)
        serializer_class = registered_config.serializer
        assert serializer_class is not None
        # DRF serializers have fields attribute
        instance = serializer_class()
        assert hasattr(instance, "fields")

        # Access resource property (should not raise)
        resource_class = registered_config.resource
        assert resource_class is not None
        # import-export resources have fields attribute
        assert hasattr(resource_class, "fields")

        # Access admin property (should not raise)
        admin_class = registered_config.admin
        assert admin_class is not None
        assert hasattr(admin_class, "model")
        assert admin_class.model is BasaltRockSample

    def test_cached_property_behavior(self, clean_registry):
        """Test that component properties are cached after first access."""

        class LimestoneRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        clean_registry.register(LimestoneRockSample)
        config = clean_registry.get_for_model(LimestoneRockSample)

        # First access - generates the class
        form_class1 = config.form

        # Second access - should return same cached instance
        form_class2 = config.form

        assert form_class1 is form_class2

    def test_register_multiple_models(self, clean_registry):
        """Test registering multiple models simultaneously."""

        class MarbleRockSample(Sample):
            """Rock sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class ClaySoilSample(Sample):
            """Soil sample model."""

            soil_location = models.CharField(max_length=200)

            class Meta:
                app_label = "test_app"

        class SeaWaterSample(Sample):
            """Water sample model."""

            ph_level = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register all three with ModelConfiguration
        rock_config = fairdm.config.ModelConfiguration(model=MarbleRockSample, fields=["rock_type"])
        soil_config = fairdm.config.ModelConfiguration(model=ClaySoilSample, fields=["soil_location"])
        water_config = fairdm.config.ModelConfiguration(model=SeaWaterSample, fields=["ph_level"])

        clean_registry.register(MarbleRockSample, config=rock_config)
        clean_registry.register(ClaySoilSample, config=soil_config)
        clean_registry.register(SeaWaterSample, config=water_config)

        # Verify all registered
        assert MarbleRockSample in clean_registry._registry
        assert ClaySoilSample in clean_registry._registry
        assert SeaWaterSample in clean_registry._registry

        # Verify configs are independent
        rock_config_retrieved = clean_registry.get_for_model(MarbleRockSample)
        soil_config_retrieved = clean_registry.get_for_model(ClaySoilSample)
        water_config_retrieved = clean_registry.get_for_model(SeaWaterSample)

        assert rock_config_retrieved.fields == ["rock_type"]
        assert soil_config_retrieved.fields == ["soil_location"]
        assert water_config_retrieved.fields == ["ph_level"]


class TestRegistrationBasics:
    """Test basic registration functionality using new ModelConfiguration API."""

    def test_register_sample_with_minimal_config(self, clean_registry, db):
        """Test registering a Sample with minimal configuration."""
        config = fairdm.config.ModelConfiguration(
            model=Sample,
            display_name="Test Sample",
        )
        registry.register(Sample, config=config)

        # Check that model was registered
        assert Sample in registry._registry

        # Check configuration
        stored_config = registry.get_for_model(Sample)
        assert stored_config.model == Sample
        assert stored_config.display_name == "Test Sample"

    def test_register_measurement_with_config(self, clean_registry, db):
        """Test registering a Measurement with configuration."""
        config = fairdm.config.ModelConfiguration(
            model=Measurement,
            display_name="Test Measurement",
            table_fields=["name", "sample", "tags"],
            filterset_fields=["sample", "tags"],
        )
        registry.register(Measurement, config=config)

        # Check registration
        assert Measurement in registry._registry

        # Check config fields
        stored_config = registry.get_for_model(Measurement)
        assert stored_config.display_name == "Test Measurement"
        assert stored_config.table_fields == ["name", "sample", "tags"]
        assert stored_config.filterset_fields == ["sample", "tags"]

    def test_register_duplicate_model_raises_error(self, clean_registry, db):
        """Test that registering the same model twice raises DuplicateRegistrationError."""
        from fairdm.registry.exceptions import DuplicateRegistrationError

        config1 = fairdm.config.ModelConfiguration(
            model=Sample,
            display_name="First Config",
        )
        registry.register(Sample, config=config1)

        # Should be registered
        assert Sample in registry._registry
        first_config = registry.get_for_model(Sample)
        assert first_config.display_name == "First Config"

        # Attempt duplicate registration
        config2 = fairdm.config.ModelConfiguration(
            model=Sample,
            display_name="Second Config",
        )
        with pytest.raises(DuplicateRegistrationError):
            registry.register(Sample, config=config2)


class TestRegistrationValidation:
    """Test validation and error handling in registration."""

    def test_register_invalid_model_raises_error(self, clean_registry):
        """Test that registering a non-Sample/Measurement model raises ConfigurationError."""
        from fairdm.registry.exceptions import ConfigurationError

        class NotSampleModel(models.Model):
            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(
            model=NotSampleModel,
            display_name="Invalid Model",
        )

        with pytest.raises(ConfigurationError) as exc_info:
            registry.register(NotSampleModel, config=config)

        assert "must inherit from Sample or Measurement" in str(exc_info.value)


class TestFieldConfiguration:
    """Test field configuration options."""

    def test_field_configuration(self, clean_registry, db):
        """Test field configuration options with component-specific fields."""
        config = fairdm.config.ModelConfiguration(
            model=Sample,
            display_name="Field Test Sample",
            table_fields=["name", "tags"],
            form_fields=["name", "tags"],
            filterset_fields=["tags"],
        )
        registry.register(Sample, config=config)

        stored_config = registry.get_for_model(Sample)
        assert stored_config.table_fields == ["name", "tags"]
        assert stored_config.form_fields == ["name", "tags"]
        assert stored_config.filterset_fields == ["tags"]

    def test_default_fields_with_no_specification(self, clean_registry, db):
        """Test that sensible defaults are used when no fields specified."""
        config = fairdm.config.ModelConfiguration(
            model=Sample,
            display_name="Minimal Sample",
        )
        registry.register(Sample, config=config)

        stored_config = registry.get_for_model(Sample)

        # Component properties should use get_default_fields() when no fields specified
        # Access the properties to trigger auto-generation
        form_class = stored_config.form
        table_class = stored_config.table
        filterset_class = stored_config.filterset

        assert form_class is not None
        assert table_class is not None
        assert filterset_class is not None


class TestRegistryAccess:
    """Test registry access and retrieval methods."""

    def test_get_for_model_by_class(self, clean_registry, db):
        """Test retrieving registered models by class."""
        config = fairdm.config.ModelConfiguration(
            model=Sample,
            display_name="Retrieval Test",
        )
        registry.register(Sample, config=config)

        # Test get_for_model method with model class
        retrieved_config = registry.get_for_model(Sample)
        assert retrieved_config is not None
        assert retrieved_config.model == Sample
        assert retrieved_config.display_name == "Retrieval Test"

    def test_get_for_model_nonexistent_raises_keyerror(self, clean_registry):
        """Test that getting a non-registered model raises KeyError."""
        # Test with model class - raises KeyError when not registered
        with pytest.raises(KeyError):
            registry.get_for_model(Sample)


# TestIntegrationWithFactories, TestConfigInheritance, TestAutoGeneration,
# TestRegistrationDecorator, and TestRegistrySummary removed - they tested
# the old decorator-based API with SampleConfig/MeasurementConfig classes.
# The functionality they tested (registration, config storage, introspection)
# is covered by TestBasicRegistration and TestRegistryAccess above.


# Run tests with: poetry run pytest tests/test_registry/test_registration.py -v
