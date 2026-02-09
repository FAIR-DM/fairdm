"""Test the FairDM registry introspection API functionality.

This module tests the registry's introspection capabilities:
- registry.samples property (T035)
- registry.measurements property (T036)
- registry.get_for_model() method (T037)
- Registry iteration and config access (T038)
"""

import pytest
from django.db import models

import fairdm
from fairdm.core.models import Measurement, Sample
from fairdm.registry import registry


@pytest.fixture
def clean_registry():
    """Clean the registry before and after each test."""
    registry._registry.clear()
    yield registry
    registry._registry.clear()


class TestRegistrySamplesProperty:
    """T035: Unit test for registry.samples property."""

    def test_samples_property_returns_only_sample_subclasses(self, clean_registry):
        """Verify registry.samples returns only Sample subclasses."""

        # Define test models
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class SoilSample(Sample):
            ph_level = models.FloatField()

            class Meta:
                app_label = "test_app"

        class WaterSample(Sample):
            temperature = models.FloatField()

            class Meta:
                app_label = "test_app"

        class TemperatureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register 3 Samples and 1 Measurement
        for model in [RockSample, SoilSample, WaterSample]:
            config = fairdm.config.ModelConfiguration(model=model, fields=["name"])
            clean_registry.register(model, config=config)

        config = fairdm.config.ModelConfiguration(model=TemperatureMeasurement, fields=["value"])
        clean_registry.register(TemperatureMeasurement, config=config)

        # Test registry.samples property
        samples = clean_registry.samples

        # Should return exactly 3 Sample models
        assert len(samples) == 3
        assert RockSample in samples
        assert SoilSample in samples
        assert WaterSample in samples

        # Should exclude Measurement models
        assert TemperatureMeasurement not in samples

    def test_samples_property_returns_empty_list_when_no_samples(self, clean_registry):
        """Verify registry.samples returns empty list when no Samples registered."""

        class PressureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register only a Measurement
        config = fairdm.config.ModelConfiguration(model=PressureMeasurement, fields=["value"])
        clean_registry.register(PressureMeasurement, config=config)

        # samples should be empty
        assert clean_registry.samples == []

    def test_samples_property_returns_empty_list_when_registry_empty(self, clean_registry):
        """Verify registry.samples returns empty list when registry is empty."""
        assert clean_registry.samples == []


class TestRegistryMeasurementsProperty:
    """T036: Unit test for registry.measurements property."""

    def test_measurements_property_returns_only_measurement_subclasses(self, clean_registry):
        """Verify registry.measurements returns only Measurement subclasses."""

        # Define test models
        class TemperatureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        class PressureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # Register 2 Measurements and 1 Sample
        for model in [TemperatureMeasurement, PressureMeasurement]:
            config = fairdm.config.ModelConfiguration(model=model, fields=["value"])
            clean_registry.register(model, config=config)

        config = fairdm.config.ModelConfiguration(model=RockSample, fields=["rock_type"])
        clean_registry.register(RockSample, config=config)

        # Test registry.measurements property
        measurements = clean_registry.measurements

        # Should return exactly 2 Measurement models
        assert len(measurements) == 2
        assert TemperatureMeasurement in measurements
        assert PressureMeasurement in measurements

        # Should exclude Sample models
        assert RockSample not in measurements

    def test_measurements_property_returns_empty_list_when_no_measurements(self, clean_registry):
        """Verify registry.measurements returns empty list when no Measurements registered."""

        class SoilSample(Sample):
            ph_level = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register only a Sample
        config = fairdm.config.ModelConfiguration(model=SoilSample, fields=["ph_level"])
        clean_registry.register(SoilSample, config=config)

        # measurements should be empty
        assert clean_registry.measurements == []

    def test_measurements_property_returns_empty_list_when_registry_empty(self, clean_registry):
        """Verify registry.measurements returns empty list when registry is empty."""
        assert clean_registry.measurements == []


class TestRegistryGetForModel:
    """T037: Unit test for registry.get_for_model() method."""

    def test_get_for_model_with_registered_model_class(self, clean_registry):
        """Verify get_for_model() returns config for registered model."""

        class MarbleSample(Sample):
            color = models.CharField(max_length=50)

            class Meta:
                app_label = "test_app"

        # Register model
        config = fairdm.config.ModelConfiguration(model=MarbleSample, fields=["color"])
        clean_registry.register(MarbleSample, config=config)

        # Get config back
        retrieved_config = clean_registry.get_for_model(MarbleSample)

        assert retrieved_config is not None
        assert retrieved_config.model is MarbleSample
        assert retrieved_config.fields == ["color"]

    def test_get_for_model_with_unregistered_model_raises_keyerror(self, clean_registry):
        """Verify get_for_model() raises KeyError for unregistered model."""

        class UnregisteredSample(Sample):
            rock_density = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Should raise KeyError for unregistered model
        with pytest.raises(KeyError, match="not registered with the FairDM registry"):
            clean_registry.get_for_model(UnregisteredSample)

    def test_get_for_model_distinguishes_between_different_models(self, clean_registry):
        """Verify get_for_model() returns correct config for each model."""

        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class SoilSample(Sample):
            ph_level = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register both with different fields
        rock_config = fairdm.config.ModelConfiguration(model=RockSample, fields=["rock_type"])
        clean_registry.register(RockSample, config=rock_config)

        soil_config = fairdm.config.ModelConfiguration(model=SoilSample, fields=["ph_level"])
        clean_registry.register(SoilSample, config=soil_config)

        # Verify each returns correct config
        rock_retrieved = clean_registry.get_for_model(RockSample)
        soil_retrieved = clean_registry.get_for_model(SoilSample)

        assert rock_retrieved.model is RockSample
        assert rock_retrieved.fields == ["rock_type"]

        assert soil_retrieved.model is SoilSample
        assert soil_retrieved.fields == ["ph_level"]


class TestRegistryIteration:
    """T038: Integration test for registry iteration and config access."""

    def test_iterate_over_samples_and_access_components(self, clean_registry):
        """Verify iteration over registry.samples and component access works."""

        # Define multiple sample models
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)
            weight_grams = models.FloatField()

            class Meta:
                app_label = "test_app"

        class SoilSample(Sample):
            ph_level = models.FloatField()
            organic_matter_percent = models.FloatField()

            class Meta:
                app_label = "test_app"

        class WaterSample(Sample):
            temperature = models.FloatField()
            salinity = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register all three with simple field lists
        rock_config = fairdm.config.ModelConfiguration(model=RockSample, fields=["rock_type", "weight_grams"])
        clean_registry.register(RockSample, config=rock_config)

        soil_config = fairdm.config.ModelConfiguration(model=SoilSample, fields=["ph_level", "organic_matter_percent"])
        clean_registry.register(SoilSample, config=soil_config)

        water_config = fairdm.config.ModelConfiguration(model=WaterSample, fields=["temperature", "salinity"])
        clean_registry.register(WaterSample, config=water_config)

        # Iterate over registered samples
        sample_models = clean_registry.samples
        assert len(sample_models) == 3

        for model in sample_models:
            # Get config for each
            config = clean_registry.get_for_model(model)

            # Verify config is accessible
            assert config is not None
            assert config.model is model

            # Verify component properties are accessible
            assert config.form is not None
            assert config.table is not None
            assert config.filterset is not None
            assert config.serializer is not None
            assert config.resource is not None
            assert config.admin is not None

    def test_iterate_over_measurements_and_access_components(self, clean_registry):
        """Verify iteration over registry.measurements and component access works."""

        # Define multiple measurement models
        class TemperatureMeasurement(Measurement):
            value = models.FloatField()
            unit = models.CharField(max_length=10)

            class Meta:
                app_label = "test_app"

        class PressureMeasurement(Measurement):
            value = models.FloatField()
            unit = models.CharField(max_length=10)

            class Meta:
                app_label = "test_app"

        # Register both
        for model in [TemperatureMeasurement, PressureMeasurement]:
            config = fairdm.config.ModelConfiguration(model=model, fields=["value", "unit"])
            clean_registry.register(model, config=config)

        # Iterate over registered measurements
        measurement_models = clean_registry.measurements
        assert len(measurement_models) == 2

        for model in measurement_models:
            # Get config for each
            config = clean_registry.get_for_model(model)

            # Verify config is accessible
            assert config is not None
            assert config.model is model

            # Verify component properties are accessible
            assert config.form is not None
            assert config.table is not None

    def test_iterate_over_all_models_using_models_property(self, clean_registry):
        """Verify iteration over registry.models returns all registered models."""

        # Define test models
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class TemperatureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        # Register both
        rock_config = fairdm.config.ModelConfiguration(model=RockSample, fields=["rock_type"])
        clean_registry.register(RockSample, config=rock_config)

        temp_config = fairdm.config.ModelConfiguration(model=TemperatureMeasurement, fields=["value"])
        clean_registry.register(TemperatureMeasurement, config=temp_config)

        # Test registry.models property (combined list)
        all_models = clean_registry.models

        assert len(all_models) == 2
        assert RockSample in all_models
        assert TemperatureMeasurement in all_models

        # Verify samples + measurements = models
        assert set(clean_registry.samples + clean_registry.measurements) == set(all_models)


class TestRegistryEnhancedMethods:
    """Tests for enhanced registry methods: get_for_model, is_registered, get_all_configs."""

    def test_get_for_model_with_string_raises_lookuperror_for_invalid_app(self, clean_registry):
        """Verify get_for_model raises LookupError for invalid app reference."""
        with pytest.raises(LookupError, match="not found in Django apps"):
            clean_registry.get_for_model("invalid_app.model")

    def test_get_for_model_with_class_raises_keyerror_for_unregistered(self, clean_registry):
        """Verify get_for_model raises KeyError for unregistered model class."""

        class UnregisteredSample(Sample):
            class Meta:
                app_label = "test_app"

        with pytest.raises(KeyError, match="not registered with the FairDM registry"):
            clean_registry.get_for_model(UnregisteredSample)

    def test_get_for_model_with_invalid_string_format(self, clean_registry):
        """Verify get_for_model raises ValueError for invalid string format."""
        with pytest.raises(ValueError, match="Invalid model reference format.*Expected 'app_label.model_name'"):
            clean_registry.get_for_model("invalid_format")

    def test_is_registered_returns_true_for_registered_model(self, clean_registry):
        """Verify is_registered returns True for registered model."""

        class TestSample(Sample):
            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(model=TestSample, fields=["name"])
        clean_registry.register(TestSample, config=config)

        assert clean_registry.is_registered(TestSample) is True

    def test_is_registered_returns_false_for_unregistered_model(self, clean_registry):
        """Verify is_registered returns False for unregistered model."""

        class UnregisteredSample(Sample):
            class Meta:
                app_label = "test_app"

        assert clean_registry.is_registered(UnregisteredSample) is False
        assert clean_registry.is_registered("invalid_app.unregistered") is False

    def test_is_registered_handles_invalid_string_format(self, clean_registry):
        """Verify is_registered returns False for invalid string format."""
        assert clean_registry.is_registered("invalid_format") is False

    def test_get_all_configs_returns_all_configurations(self, clean_registry):
        """Verify get_all_configs returns all ModelConfiguration instances."""

        class Sample1(Sample):
            class Meta:
                app_label = "test_app"

        class Sample2(Sample):
            class Meta:
                app_label = "test_app"

        config1 = fairdm.config.ModelConfiguration(model=Sample1, fields=["name"])
        config2 = fairdm.config.ModelConfiguration(model=Sample2, fields=["name"])

        clean_registry.register(Sample1, config=config1)
        clean_registry.register(Sample2, config=config2)

        all_configs = clean_registry.get_all_configs()

        assert len(all_configs) == 2
        assert config1 in all_configs
        assert config2 in all_configs

        # Verify they are ModelConfiguration instances
        for config in all_configs:
            assert isinstance(config, fairdm.config.ModelConfiguration)

    def test_get_all_configs_returns_empty_list_when_no_models_registered(self, clean_registry):
        """Verify get_all_configs returns empty list when no models are registered."""
        assert clean_registry.get_all_configs() == []
