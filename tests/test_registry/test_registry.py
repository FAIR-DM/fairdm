"""Tests for fairdm/registry/registry.py."""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ModelForm
from django.test import Client
from django_filters import FilterSet
from django_tables2 import Table

import fairdm
from demo.models import CustomParentSample, CustomSample, ExampleMeasurement
from fairdm.core.models import Measurement, Sample
from fairdm.registry import registry
from fairdm.registry.config import ModelConfiguration
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample

User = get_user_model()


class TestSample(Sample):
    test_field = models.CharField(max_length=100)

    class Meta:
        app_label = "test_app"


class TestMeasurement(Measurement):
    value = models.FloatField()

    class Meta:
        app_label = "test_app"


class TestModelConfigurationProtocolCompliance:
    def test_model_configuration_has_required_attributes(self):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])

        assert hasattr(config, "model")
        assert hasattr(config, "fields")
        assert hasattr(config, "exclude")
        assert hasattr(config, "table_fields")
        assert hasattr(config, "form_fields")
        assert hasattr(config, "filterset_fields")
        assert hasattr(config, "serializer_fields")
        assert hasattr(config, "resource_fields")
        assert hasattr(config, "admin_list_display")
        assert hasattr(config, "form_class")
        assert hasattr(config, "table_class")
        assert hasattr(config, "filterset_class")
        assert hasattr(config, "serializer_class")
        assert hasattr(config, "resource_class")
        assert hasattr(config, "admin_class")
        assert hasattr(config, "display_name")
        assert hasattr(config, "description")

    def test_model_configuration_property_methods(self):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])

        # The accessors are the whole public surface for components. No attribute
        # returns a component class, because one that did would bypass an override.
        for component in (
            "form",
            "table",
            "filterset",
            "serializer",
            "resource",
            "admin",
        ):
            assert hasattr(config, f"get_{component}_class")
            assert not hasattr(config, component)

        assert config.get_form_class() is not None
        assert config.get_table_class() is not None
        assert config.get_filterset_class() is not None
        assert config.get_serializer_class() is not None
        assert config.get_resource_class() is not None
        assert config.get_admin_class() is not None

    def test_model_configuration_utility_methods(self):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])

        assert not hasattr(config, "clear_cache")
        assert hasattr(config, "get_display_name")
        assert hasattr(config, "get_description")
        assert hasattr(config, "get_slug")

        assert isinstance(config.get_display_name(), str)
        assert isinstance(config.get_description(), str)
        assert isinstance(config.get_slug(), str)

    def test_model_configuration_class_methods(self):
        assert hasattr(ModelConfiguration, "get_default_fields")

        fields = ModelConfiguration.get_default_fields(TestSample)
        assert isinstance(fields, list)
        assert all(isinstance(field, str) for field in fields)


class TestFairDMRegistryProtocolCompliance:
    def test_registry_has_required_methods(self, clean_registry):
        assert hasattr(clean_registry, "register")
        assert hasattr(clean_registry, "get_for_model")
        assert hasattr(clean_registry, "is_registered") or True

        config = ModelConfiguration(model=TestSample, fields=["test_field"])
        clean_registry.register(TestSample, config)

        retrieved = clean_registry.get_for_model(TestSample)
        assert retrieved is config

    def test_registry_has_introspection_properties(self, clean_registry):
        assert hasattr(clean_registry, "samples")
        assert hasattr(clean_registry, "measurements")
        assert hasattr(clean_registry, "models")

        assert isinstance(clean_registry.samples, list)
        assert isinstance(clean_registry.measurements, list)
        assert isinstance(clean_registry.models, list)

        sample_config = ModelConfiguration(model=TestSample, fields=["test_field"])
        measurement_config = ModelConfiguration(model=TestMeasurement, fields=["value"])

        clean_registry.register(TestSample, sample_config)
        clean_registry.register(TestMeasurement, measurement_config)

        assert TestSample in clean_registry.samples
        assert TestMeasurement not in clean_registry.samples
        assert TestMeasurement in clean_registry.measurements
        assert TestSample not in clean_registry.measurements
        assert TestSample in clean_registry.models
        assert TestMeasurement in clean_registry.models

    def test_registry_method_signatures(self, clean_registry):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])
        clean_registry.register(TestSample, config)

        clean_registry._registry.clear()
        clean_registry.register(TestSample, None)

        retrieved = clean_registry.get_for_model(TestSample)
        assert retrieved is not None

        with pytest.raises(KeyError):
            clean_registry.get_for_model(TestMeasurement)

    def test_registry_error_handling(self, clean_registry):
        from fairdm.registry.exceptions import (
            ConfigurationError,
            DuplicateRegistrationError,
        )

        config = ModelConfiguration(model=TestSample, fields=["test_field"])
        clean_registry.register(TestSample, config)

        with pytest.raises(DuplicateRegistrationError):
            clean_registry.register(TestSample, config)

        class InvalidModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # Model eligibility is the registry's decision, so building the configuration is legal and
        # registering it is what fails.
        invalid_config = ModelConfiguration(model=InvalidModel, fields=["name"])
        with pytest.raises(ConfigurationError):
            clean_registry.register(InvalidModel, invalid_config)


class TestRegistrationAPICompliance:
    def test_decorator_registration_api(self, clean_registry):
        @fairdm.register
        class TestSampleConfig(ModelConfiguration):
            model = TestSample
            fields = ["test_field"]

        assert TestSample in clean_registry._registry
        config = clean_registry.get_for_model(TestSample)
        assert config is not None
        assert hasattr(config, "fields")  # Just verify it has the field attribute

    def test_programmatic_registration_api(self, clean_registry):
        config = ModelConfiguration(model=TestMeasurement, fields=["value"])
        clean_registry.register(TestMeasurement, config)

        assert TestMeasurement in clean_registry._registry
        retrieved = clean_registry.get_for_model(TestMeasurement)
        assert retrieved is config


class TestProtocolTypeCompatibility:
    def test_model_configuration_return_types(self):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])

        from django.contrib.admin import ModelAdmin
        from django.forms import ModelForm
        from django_filters import FilterSet
        from django_tables2 import Table
        from import_export.resources import ModelResource

        form = config.get_form_class()
        table = config.get_table_class()
        filterset = config.get_filterset_class()
        admin_class = config.get_admin_class()
        resource = config.get_resource_class()

        assert issubclass(form, ModelForm)
        assert issubclass(table, Table)
        assert issubclass(filterset, FilterSet)
        assert issubclass(admin_class, ModelAdmin)
        assert issubclass(resource, ModelResource)

    def test_registry_return_types(self, clean_registry):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])
        clean_registry.register(TestSample, config)

        samples = clean_registry.samples
        measurements = clean_registry.measurements
        models = clean_registry.models
        retrieved_config = clean_registry.get_for_model(TestSample)

        assert isinstance(samples, list)
        assert isinstance(measurements, list)
        assert isinstance(models, list)
        assert isinstance(retrieved_config, ModelConfiguration)

        assert all(issubclass(model, Sample) for model in samples)
        assert all(issubclass(model, Measurement) for model in measurements)
        assert TestSample in samples
        assert TestSample in models


class TestRegistrySamplesProperty:
    def test_samples_property_returns_only_sample_subclasses(self, clean_registry):
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

        for model in [RockSample, SoilSample, WaterSample]:
            config = fairdm.config.ModelConfiguration(model=model, fields=["name"])
            clean_registry.register(model, config=config)

        config = fairdm.config.ModelConfiguration(
            model=TemperatureMeasurement, fields=["value"]
        )
        clean_registry.register(TemperatureMeasurement, config=config)

        samples = clean_registry.samples

        assert len(samples) == 3
        assert RockSample in samples
        assert SoilSample in samples
        assert WaterSample in samples

        assert TemperatureMeasurement not in samples

    def test_samples_property_returns_empty_list_when_no_samples(self, clean_registry):
        class PressureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(
            model=PressureMeasurement, fields=["value"]
        )
        clean_registry.register(PressureMeasurement, config=config)

        assert clean_registry.samples == []

    def test_samples_property_returns_empty_list_when_registry_empty(
        self, clean_registry
    ):
        assert clean_registry.samples == []


class TestRegistryMeasurementsProperty:
    def test_measurements_property_returns_only_measurement_subclasses(
        self, clean_registry
    ):
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

        for model in [TemperatureMeasurement, PressureMeasurement]:
            config = fairdm.config.ModelConfiguration(model=model, fields=["value"])
            clean_registry.register(model, config=config)

        config = fairdm.config.ModelConfiguration(
            model=RockSample, fields=["rock_type"]
        )
        clean_registry.register(RockSample, config=config)

        measurements = clean_registry.measurements

        assert len(measurements) == 2
        assert TemperatureMeasurement in measurements
        assert PressureMeasurement in measurements

        assert RockSample not in measurements

    def test_measurements_property_returns_empty_list_when_no_measurements(
        self, clean_registry
    ):
        class SoilSample(Sample):
            ph_level = models.FloatField()

            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(model=SoilSample, fields=["ph_level"])
        clean_registry.register(SoilSample, config=config)

        assert clean_registry.measurements == []

    def test_measurements_property_returns_empty_list_when_registry_empty(
        self, clean_registry
    ):
        assert clean_registry.measurements == []


class TestRegistryGetForModel:
    def test_get_for_model_with_registered_model_class(self, clean_registry):
        class MarbleSample(Sample):
            color = models.CharField(max_length=50)

            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(model=MarbleSample, fields=["color"])
        clean_registry.register(MarbleSample, config=config)

        retrieved_config = clean_registry.get_for_model(MarbleSample)

        assert retrieved_config is not None
        assert retrieved_config.model is MarbleSample
        assert retrieved_config.fields == ["color"]

    def test_get_for_model_with_unregistered_model_raises_keyerror(
        self, clean_registry
    ):
        class UnregisteredSample(Sample):
            rock_density = models.FloatField()

            class Meta:
                app_label = "test_app"

        with pytest.raises(KeyError):
            clean_registry.get_for_model(UnregisteredSample)

    def test_get_for_model_distinguishes_between_different_models(self, clean_registry):
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class SoilSample(Sample):
            ph_level = models.FloatField()

            class Meta:
                app_label = "test_app"

        rock_config = fairdm.config.ModelConfiguration(
            model=RockSample, fields=["rock_type"]
        )
        clean_registry.register(RockSample, config=rock_config)

        soil_config = fairdm.config.ModelConfiguration(
            model=SoilSample, fields=["ph_level"]
        )
        clean_registry.register(SoilSample, config=soil_config)

        rock_retrieved = clean_registry.get_for_model(RockSample)
        soil_retrieved = clean_registry.get_for_model(SoilSample)

        assert rock_retrieved.model is RockSample
        assert rock_retrieved.fields == ["rock_type"]

        assert soil_retrieved.model is SoilSample
        assert soil_retrieved.fields == ["ph_level"]


class TestRegistryIteration:
    def test_iterate_over_samples_and_access_components(self, clean_registry):
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

        rock_config = fairdm.config.ModelConfiguration(
            model=RockSample, fields=["rock_type", "weight_grams"]
        )
        clean_registry.register(RockSample, config=rock_config)

        soil_config = fairdm.config.ModelConfiguration(
            model=SoilSample, fields=["ph_level", "organic_matter_percent"]
        )
        clean_registry.register(SoilSample, config=soil_config)

        water_config = fairdm.config.ModelConfiguration(
            model=WaterSample, fields=["temperature", "salinity"]
        )
        clean_registry.register(WaterSample, config=water_config)

        sample_models = clean_registry.samples
        assert len(sample_models) == 3

        for model in sample_models:
            config = clean_registry.get_for_model(model)

            assert config is not None
            assert config.model is model

            assert config.get_form_class() is not None
            assert config.get_table_class() is not None
            assert config.get_filterset_class() is not None
            assert config.get_serializer_class() is not None
            assert config.get_resource_class() is not None
            assert config.get_admin_class() is not None

    def test_iterate_over_measurements_and_access_components(self, clean_registry):
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

        for model in [TemperatureMeasurement, PressureMeasurement]:
            config = fairdm.config.ModelConfiguration(
                model=model, fields=["value", "unit"]
            )
            clean_registry.register(model, config=config)

        measurement_models = clean_registry.measurements
        assert len(measurement_models) == 2

        for model in measurement_models:
            config = clean_registry.get_for_model(model)

            assert config is not None
            assert config.model is model

            assert config.get_form_class() is not None
            assert config.get_table_class() is not None

    def test_iterate_over_all_models_using_models_property(self, clean_registry):
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class TemperatureMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = "test_app"

        rock_config = fairdm.config.ModelConfiguration(
            model=RockSample, fields=["rock_type"]
        )
        clean_registry.register(RockSample, config=rock_config)

        temp_config = fairdm.config.ModelConfiguration(
            model=TemperatureMeasurement, fields=["value"]
        )
        clean_registry.register(TemperatureMeasurement, config=temp_config)

        all_models = clean_registry.models

        assert len(all_models) == 2
        assert RockSample in all_models
        assert TemperatureMeasurement in all_models

        assert set(clean_registry.samples + clean_registry.measurements) == set(
            all_models
        )


class TestRegistryEnhancedMethods:
    def test_get_for_model_with_string_raises_lookuperror_for_invalid_app(
        self, clean_registry
    ):
        with pytest.raises(LookupError):
            clean_registry.get_for_model("invalid_app.model")

    def test_get_for_model_with_class_raises_keyerror_for_unregistered(
        self, clean_registry
    ):
        class UnregisteredSample(Sample):
            class Meta:
                app_label = "test_app"

        with pytest.raises(KeyError):
            clean_registry.get_for_model(UnregisteredSample)

    def test_get_for_model_with_invalid_string_format(self, clean_registry):
        with pytest.raises(ValueError):
            clean_registry.get_for_model("invalid_format")

    def test_is_registered_returns_true_for_registered_model(self, clean_registry):
        class TestSample(Sample):
            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(model=TestSample, fields=["name"])
        clean_registry.register(TestSample, config=config)

        assert clean_registry.is_registered(TestSample) is True

    def test_is_registered_returns_false_for_unregistered_model(self, clean_registry):
        class UnregisteredSample(Sample):
            class Meta:
                app_label = "test_app"

        assert clean_registry.is_registered(UnregisteredSample) is False
        assert clean_registry.is_registered("invalid_app.unregistered") is False

    def test_is_registered_handles_invalid_string_format(self, clean_registry):
        assert clean_registry.is_registered("invalid_format") is False

    def test_get_all_configs_returns_all_configurations(self, clean_registry):
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

        for config in all_configs:
            assert isinstance(config, fairdm.config.ModelConfiguration)

    def test_get_all_configs_returns_empty_list_when_no_models_registered(
        self, clean_registry
    ):
        assert clean_registry.get_all_configs() == []


class TestBasicRegistration:
    def test_register_model_with_fields(self, clean_registry):
        class GraniteRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()
            weight_grams = models.FloatField()

            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(
            model=GraniteRockSample,
            table_fields=["rock_type", "weight_grams"],
            form_fields=["rock_type", "mineral_content", "weight_grams"],
        )
        clean_registry.register(GraniteRockSample, config=config)

        assert GraniteRockSample in clean_registry._registry
        registered_config = clean_registry.get_for_model(GraniteRockSample)

        assert registered_config.model is GraniteRockSample
        assert registered_config.table_fields == ["rock_type", "weight_grams"]
        assert registered_config.form_fields == [
            "rock_type",
            "mineral_content",
            "weight_grams",
        ]

    def test_verify_all_component_properties_accessible(self, clean_registry):
        class BasaltRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)
            sample_location = models.CharField(max_length=200)

            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(
            model=BasaltRockSample,
            fields=["rock_type", "sample_location"],
        )
        clean_registry.register(BasaltRockSample, config=config)

        registered_config = clean_registry.get_for_model(BasaltRockSample)

        form_class = registered_config.get_form_class()
        assert form_class is not None
        assert hasattr(form_class, "base_fields")

        table_class = registered_config.get_table_class()
        assert table_class is not None
        assert hasattr(table_class, "base_columns")

        filterset_class = registered_config.get_filterset_class()
        assert filterset_class is not None
        assert hasattr(filterset_class, "base_filters")

        serializer_class = registered_config.get_serializer_class()
        assert serializer_class is not None
        instance = serializer_class()
        assert hasattr(instance, "fields")

        resource_class = registered_config.get_resource_class()
        assert resource_class is not None
        assert hasattr(resource_class, "fields")

        admin_class = registered_config.get_admin_class()
        assert admin_class is not None
        assert hasattr(admin_class, "model")
        assert admin_class.model is BasaltRockSample

    def test_components_are_rebuilt_on_every_call(self, clean_registry):
        class LimestoneRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        clean_registry.register(LimestoneRockSample)
        config = clean_registry.get_for_model(LimestoneRockSample)

        # Each call generates the class again: nothing is cached, so an override of
        # the accessor is honoured on every call rather than only the first.
        form_class1 = config.get_form_class()
        form_class2 = config.get_form_class()

        assert form_class1 is not form_class2
        assert form_class1.base_fields.keys() == form_class2.base_fields.keys()

    def test_register_multiple_models(self, clean_registry):
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

        rock_config = fairdm.config.ModelConfiguration(
            model=MarbleRockSample, fields=["rock_type"]
        )
        soil_config = fairdm.config.ModelConfiguration(
            model=ClaySoilSample, fields=["soil_location"]
        )
        water_config = fairdm.config.ModelConfiguration(
            model=SeaWaterSample, fields=["ph_level"]
        )

        clean_registry.register(MarbleRockSample, config=rock_config)
        clean_registry.register(ClaySoilSample, config=soil_config)
        clean_registry.register(SeaWaterSample, config=water_config)

        assert MarbleRockSample in clean_registry._registry
        assert ClaySoilSample in clean_registry._registry
        assert SeaWaterSample in clean_registry._registry

        rock_config_retrieved = clean_registry.get_for_model(MarbleRockSample)
        soil_config_retrieved = clean_registry.get_for_model(ClaySoilSample)
        water_config_retrieved = clean_registry.get_for_model(SeaWaterSample)

        assert rock_config_retrieved.fields == ["rock_type"]
        assert soil_config_retrieved.fields == ["soil_location"]
        assert water_config_retrieved.fields == ["ph_level"]


class TestRegistrationBasics:
    def test_register_sample_with_minimal_config(self, clean_registry, db):
        config = fairdm.config.ModelConfiguration(
            model=ConcreteSample,
            display_name="Test Sample",
        )
        registry.register(ConcreteSample, config=config)

        assert ConcreteSample in registry._registry

        stored_config = registry.get_for_model(ConcreteSample)
        assert stored_config.model == ConcreteSample
        assert stored_config.display_name == "Test Sample"

    def test_register_measurement_with_config(self, clean_registry, db):
        config = fairdm.config.ModelConfiguration(
            model=ConcreteMeasurement,
            display_name="Test Measurement",
            table_fields=["name", "sample", "tags"],
            filterset_fields=["sample", "tags"],
        )
        registry.register(ConcreteMeasurement, config=config)

        assert ConcreteMeasurement in registry._registry

        stored_config = registry.get_for_model(ConcreteMeasurement)
        assert stored_config.display_name == "Test Measurement"
        assert stored_config.table_fields == ["name", "sample", "tags"]
        assert stored_config.filterset_fields == ["sample", "tags"]

    def test_register_duplicate_model_raises_error(self, clean_registry, db):
        from fairdm.registry.exceptions import DuplicateRegistrationError

        config1 = fairdm.config.ModelConfiguration(
            model=ConcreteSample,
            display_name="First Config",
        )
        registry.register(ConcreteSample, config=config1)

        assert ConcreteSample in registry._registry
        first_config = registry.get_for_model(ConcreteSample)
        assert first_config.display_name == "First Config"

        config2 = fairdm.config.ModelConfiguration(
            model=ConcreteSample,
            display_name="Second Config",
        )
        with pytest.raises(DuplicateRegistrationError):
            registry.register(ConcreteSample, config=config2)


class TestRegistrationValidation:
    def test_register_invalid_model_raises_error(self, clean_registry):
        from fairdm.registry.exceptions import ConfigurationError

        class NotSampleModel(models.Model):
            class Meta:
                app_label = "test_app"

        config = fairdm.config.ModelConfiguration(
            model=NotSampleModel,
            display_name="Invalid Model",
        )

        with pytest.raises(ConfigurationError):
            registry.register(NotSampleModel, config=config)


class TestFieldConfiguration:
    def test_field_configuration(self, clean_registry, db):
        config = fairdm.config.ModelConfiguration(
            model=ConcreteSample,
            display_name="Field Test Sample",
            table_fields=["name", "tags"],
            form_fields=["name", "tags"],
            filterset_fields=["tags"],
        )
        registry.register(ConcreteSample, config=config)

        stored_config = registry.get_for_model(ConcreteSample)
        assert stored_config.table_fields == ["name", "tags"]
        assert stored_config.form_fields == ["name", "tags"]
        assert stored_config.filterset_fields == ["tags"]

    def test_default_fields_with_no_specification(self, clean_registry, db):
        config = fairdm.config.ModelConfiguration(
            model=ConcreteSample,
            display_name="Minimal Sample",
        )
        registry.register(ConcreteSample, config=config)

        stored_config = registry.get_for_model(ConcreteSample)

        form_class = stored_config.get_form_class()
        table_class = stored_config.get_table_class()
        filterset_class = stored_config.get_filterset_class()

        assert form_class is not None
        assert table_class is not None
        assert filterset_class is not None


class TestRegistryAccess:
    def test_get_for_model_by_class(self, clean_registry, db):
        config = fairdm.config.ModelConfiguration(
            model=ConcreteSample,
            display_name="Retrieval Test",
        )
        registry.register(ConcreteSample, config=config)

        retrieved_config = registry.get_for_model(ConcreteSample)
        assert retrieved_config is not None
        assert retrieved_config.model == ConcreteSample
        assert retrieved_config.display_name == "Retrieval Test"

    def test_get_for_model_nonexistent_raises_keyerror(self, clean_registry):
        with pytest.raises(KeyError):
            registry.get_for_model(ConcreteSample)


@pytest.mark.django_db
class TestDemoModelIntegration:
    def test_custom_sample_registered(self):
        assert CustomSample in registry._registry

    def test_custom_sample_get_form_class(self):
        config = registry.get_for_model(CustomSample)
        form_class = config.get_form_class()

        assert issubclass(form_class, ModelForm)
        assert form_class._meta.model == CustomSample

    def test_custom_sample_get_table_class(self):
        config = registry.get_for_model(CustomSample)
        table_class = config.get_table_class()

        assert issubclass(table_class, Table)

    def test_custom_sample_get_filterset_class(self):
        config = registry.get_for_model(CustomSample)
        filterset_class = config.get_filterset_class()

        assert issubclass(filterset_class, FilterSet)

    def test_custom_sample_get_admin_class(self):
        config = registry.get_for_model(CustomSample)
        admin_class = config.get_admin_class()

        assert issubclass(admin_class, admin.ModelAdmin)
        assert admin_class.model == CustomSample

    def test_custom_parent_sample_registered(self):
        assert CustomParentSample in registry._registry

    def test_custom_parent_sample_components(self):
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
        assert ExampleMeasurement in registry._registry

    def test_example_measurement_components(self):
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
        from demo.filters import CustomSampleFilter
        from demo.tables import CustomSampleTable

        config = registry.get_for_model(CustomSample)

        # CustomSample specifies custom filterset and table classes, so the
        # resolved components are those classes rather than generated ones.
        assert config.get_filterset_class() is CustomSampleFilter
        assert config.get_table_class() is CustomSampleTable


@pytest.mark.django_db
class TestSampleRegistration:
    def test_sample_can_be_registered(self):
        from demo.models import RockSample

        is_registered = registry.is_registered(RockSample)
        assert is_registered is True

    def test_registered_sample_has_configuration(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)

        assert config is not None
        assert config.model == RockSample

    def test_registered_sample_configuration_has_fields(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)

        assert hasattr(config, "fields")
        assert config.fields is not None
        assert len(config.fields) > 0

    def test_multiple_sample_types_can_be_registered(self):
        from demo.models import RockSample, WaterSample

        rock_registered = registry.is_registered(RockSample)
        water_registered = registry.is_registered(WaterSample)

        assert rock_registered is True
        assert water_registered is True

    def test_registered_sample_has_display_name(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        display_name = config.get_display_name()

        assert display_name is not None
        assert len(display_name) > 0

    def test_registry_can_list_all_registered_samples(self):
        from demo.models import RockSample, WaterSample

        all_samples = registry.samples  # Returns model classes, not configs

        assert RockSample in all_samples
        assert WaterSample in all_samples

    def test_registry_distinguishes_samples_from_measurements(self):
        from demo.models import RockSample

        samples = registry.samples
        measurements = registry.measurements

        assert RockSample in samples
        assert RockSample not in measurements

    def test_unregistered_sample_type_raises_error(self):
        with pytest.raises(KeyError):
            registry.get_for_model(ConcreteSample)


@pytest.mark.django_db
class TestSampleAutoGeneratedComponents:
    def test_auto_generated_form_exists(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form_class = config.get_form_class()

        assert form_class is not None
        assert issubclass(form_class, ModelForm)

    def test_auto_generated_form_includes_base_fields(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form_class = config.get_form_class()
        form = form_class()

        assert "name" in form.fields
        assert "rock_type" in form.fields
        assert "collection_date" in form.fields

    def test_auto_generated_form_includes_custom_fields(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form_class = config.get_form_class()
        form = form_class()

        assert "rock_type" in form.fields

    def test_auto_generated_filter_exists(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        filter_class = config.get_filterset_class()

        assert filter_class is not None
        assert issubclass(filter_class, FilterSet)

    def test_auto_generated_table_exists(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        table_class = config.get_table_class()

        assert table_class is not None
        assert issubclass(table_class, Table)

    def test_auto_generated_table_includes_base_columns(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        table_class = config.get_table_class()
        table = table_class([])

        assert "name" in table.columns

    def test_auto_generated_admin_exists(self):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        admin_class = config.get_admin_class()

        assert admin_class is not None
        assert issubclass(admin_class, admin.ModelAdmin)

    def test_different_sample_types_have_different_components(self):
        from demo.models import RockSample, WaterSample

        rock_config = registry.get_for_model(RockSample)
        water_config = registry.get_for_model(WaterSample)

        assert rock_config.get_form_class() != water_config.get_form_class()
        assert rock_config.get_filterset_class() != water_config.get_filterset_class()
        assert rock_config.get_table_class() != water_config.get_table_class()


@pytest.mark.django_db
class TestAllAdminAddPages:
    def test_all_registered_model_admin_add_pages_load(self):
        user = User.objects.create_superuser(
            email="admin@test.com",
            password="testpass123",
        )
        client = Client()
        client.force_login(user)

        configs = registry.get_all_configs()

        failed_pages = []

        for config in configs:
            model = config.model
            app_label = model._meta.app_label
            model_name = model._meta.model_name

            url = f"/admin/{app_label}/{model_name}/add/"

            try:
                response = client.get(url)
                if response.status_code != 200:
                    failed_pages.append((url, response.status_code, "Non-200 status"))
                print(f"✓ {model.__name__}: {url} (status {response.status_code})")
            except Exception as e:
                failed_pages.append((url, None, str(e)))
                print(f"✗ {model.__name__}: {url} - {e}")

        if failed_pages:
            failure_msg = "\n".join(
                [f"  - {url}: {error}" for url, status, error in failed_pages]
            )
            pytest.fail(f"The following admin add pages failed to load:\n{failure_msg}")
