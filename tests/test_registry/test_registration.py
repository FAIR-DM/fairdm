"""Test the FairDM registration API functionality.

This module tests the @fairdm.register decorator system using
the actual Sample and Measurement classes from the core framework.
"""

import pytest

import fairdm
from fairdm.config import MeasurementConfig, SampleConfig
from fairdm.config_components import FiltersConfig, FormConfig, TableConfig
from fairdm.core.models import Measurement, Sample
from fairdm.factories import MeasurementFactory, SampleFactory
from fairdm.registry import registry


class TestRegistrationBasics:
    """Test basic registration functionality."""

    def test_register_sample_with_minimal_config(self, clean_registry, db):
        """Test registering a Sample with minimal configuration."""

        @fairdm.register
        class TestSampleConfig(SampleConfig):
            model = Sample
            display_name = "Test Sample"

        # Check that model was registered
        assert Sample in registry._registry

        # Check configuration (registry now stores config directly)
        config = registry._registry[Sample]
        assert config.model == Sample
        assert config.display_name == "Test Sample"
        assert isinstance(config, SampleConfig)

    def test_register_measurement_with_config(self, clean_registry, db):
        """Test registering a Measurement with configuration."""

        @fairdm.register
        class TestMeasurementConfig(MeasurementConfig):
            model = Measurement
            display_name = "Test Measurement"
            # In new API, list_fields → table.fields, filter_fields → filters.fields

            table = TableConfig(fields=["name", "sample", "created"])
            filters = FiltersConfig(fields=["sample", "created"])

        # Check registration
        assert Measurement in registry._registry

        # Check config fields (registry now stores config directly)
        config = registry._registry[Measurement]
        assert config.display_name == "Test Measurement"
        assert config.table.fields == ["name", "sample", "created"]
        assert config.filters.fields == ["sample", "created"]

    def test_register_duplicate_model_skipped(self, clean_registry, db):
        """Test that registering the same model twice skips the second registration."""

        @fairdm.register
        class FirstConfig(SampleConfig):
            model = Sample
            display_name = "First Config"

        # Should be registered
        assert Sample in registry._registry
        first_config = registry._registry[Sample]
        assert first_config.display_name == "First Config"

        @fairdm.register
        class SecondConfig(SampleConfig):
            model = Sample
            display_name = "Second Config"

        # Should still have the first config (duplicate skipped)
        config = registry._registry[Sample]
        assert config.display_name == "First Config"


class TestRegistrationValidation:
    """Test validation and error handling in registration."""

    def test_register_invalid_model_raises_error(self, clean_registry):
        """Test that registering a non-Sample/Measurement model raises TypeError."""

        class NotSampleModel:
            pass

        with pytest.raises(TypeError) as exc_info:

            @fairdm.register
            class InvalidConfig(SampleConfig):
                model = NotSampleModel
                display_name = "Invalid Model"

        assert "must be a subclass of" in str(exc_info.value)

    def test_register_missing_model_raises_error(self, clean_registry):
        """Test that missing model attribute raises ValueError."""

        with pytest.raises(ValueError) as exc_info:

            @fairdm.register
            class MissingModelConfig(SampleConfig):
                display_name = "Missing Model"
                # Missing: model = SomeModel

        assert "must specify a 'model' attribute" in str(exc_info.value)

    def test_register_none_model_raises_error(self, clean_registry):
        """Test that model = None raises ValueError."""

        with pytest.raises(ValueError) as exc_info:

            @fairdm.register
            class NoneModelConfig(SampleConfig):
                model = None
                display_name = "None Model"

        assert "must specify a 'model' attribute" in str(exc_info.value)


class TestFieldConfiguration:
    """Test field configuration options."""

    def test_field_configuration(self, clean_registry, db):
        """Test field configuration options."""

        @fairdm.register
        class FieldConfig(SampleConfig):
            model = Sample
            display_name = "Field Test Sample"
            # In new API, use nested configs for component-specific fields
            table = TableConfig(fields=["name", "created", "modified"])
            form = FormConfig(fields=["name", "description", "created", "modified"])
            filters = FiltersConfig(fields=["created", "modified"])
            private_fields = ["internal_field"]

        config = registry._registry[Sample]

        assert config.table.fields == ["name", "created", "modified"]
        assert config.form.fields == ["name", "description", "created", "modified"]
        assert config.filters.fields == ["created", "modified"]
        assert config.private_fields == ["internal_field"]

    def test_default_fields_with_no_specification(self, clean_registry, db):
        """Test that sensible defaults are generated when no fields specified."""

        @fairdm.register
        class MinimalConfig(SampleConfig):
            model = Sample
            display_name = "Minimal Sample"

        config = registry._registry[Sample]

        # Should have default nested configs created
        assert config.table is not None
        assert config.form is not None
        assert config.filters is not None

        # Factory will generate defaults when get_*_class() is called
        # These methods use factories with inspector-based defaults
        table_class = config.get_table_class()
        form_class = config.get_form_class()
        filterset_class = config.get_filterset_class()

        assert table_class is not None
        assert form_class is not None
        assert filterset_class is not None


class TestRegistryAccess:
    """Test registry access and retrieval methods."""

    def test_get_for_model_by_class(self, clean_registry, db):
        """Test retrieving registered models by class."""

        @fairdm.register
        class RetrievalConfig(SampleConfig):
            model = Sample
            display_name = "Retrieval Test"

        # Test get_for_model method with model class
        config = registry.get_for_model(Sample)
        assert config is not None
        assert config.model == Sample
        assert config.display_name == "Retrieval Test"

    def test_get_for_model_by_string(self, clean_registry, db):
        """Test retrieving registered models by string reference."""

        @fairdm.register
        class RetrievalConfig(SampleConfig):
            model = Sample
            display_name = "String Retrieval Test"

        # Test get_for_model method with string reference
        config = registry.get_for_model("sample.sample")
        assert config is not None
        assert config.model == Sample
        assert config.display_name == "String Retrieval Test"

    def test_get_for_model_nonexistent_returns_none(self, clean_registry):
        """Test that getting a non-registered model returns None."""

        # Test with model class
        config = registry.get_for_model(Sample)
        assert config is None

        # Test with string reference
        config = registry.get_for_model("sample.sample")
        assert config is None

    def test_get_for_model_invalid_string_returns_none(self, clean_registry):
        """Test that invalid string references return None."""

        # Test with invalid format
        config = registry.get_for_model("invalid_format")
        assert config is None

        # Test with non-existent model
        config = registry.get_for_model("nonexistent.Model")
        assert config is None

    def test_registry_properties(self, clean_registry, db):
        """Test registry properties for samples and measurements."""

        @fairdm.register
        class SampleConfig1(SampleConfig):
            model = Sample
            display_name = "Test Sample"

        @fairdm.register
        class MeasurementConfig1(MeasurementConfig):
            model = Measurement
            display_name = "Test Measurement"

        # Check samples property (returns list of model classes)
        samples = registry.samples
        assert len(samples) == 1
        assert Sample in samples

        # Check measurements property (returns list of model classes)
        measurements = registry.measurements
        assert len(measurements) == 1
        assert Measurement in measurements

        # Check registry has both models
        assert len(registry._registry) == 2
        assert Sample in registry._registry
        assert Measurement in registry._registry


class TestIntegrationWithFactories:
    """Test integration with existing factory patterns."""

    def test_register_with_factory_created_models(self, clean_registry, db):
        """Test registering models created by factories."""

        # Create test models using factories
        sample = SampleFactory()
        measurement = MeasurementFactory()

        # Get the actual model classes
        SampleModel = sample.__class__
        MeasurementModel = measurement.__class__

        @fairdm.register
        class FactorySampleConfig(SampleConfig):
            model = SampleModel
            display_name = "Factory Sample"
            list_fields = ["name", "local_id", "status"]

        @fairdm.register
        class FactoryMeasurementConfig(MeasurementConfig):
            model = MeasurementModel
            display_name = "Factory Measurement"
            list_fields = ["name", "sample"]

        # Should register successfully
        assert SampleModel in registry._registry
        assert MeasurementModel in registry._registry

        # Check configurations work
        sample_config = registry._registry[SampleModel]
        measurement_config = registry._registry[MeasurementModel]

        assert sample_config.display_name == "Factory Sample"
        assert measurement_config.display_name == "Factory Measurement"


class TestConfigInheritance:
    """Test configuration class inheritance."""

    def test_sample_config_inheritance(self, clean_registry, db):
        """Test that SampleConfig properly inherits from BaseModelConfig."""

        @fairdm.register
        class InheritedSampleConfig(SampleConfig):
            model = Sample
            display_name = "Inherited Sample"
            # In new API, fields is the primary field config
            fields = ["name", "created"]

        config = registry._registry[Sample]

        # Should work the same as BaseModelConfig
        assert config.display_name == "Inherited Sample"
        assert config.fields == ["name", "created"]
        assert isinstance(config, SampleConfig)

    def test_measurement_config_inheritance(self, clean_registry, db):
        """Test that MeasurementConfig properly inherits from BaseModelConfig."""

        @fairdm.register
        class InheritedMeasurementConfig(MeasurementConfig):
            model = Measurement
            display_name = "Inherited Measurement"
            # In new API, fields is the primary field config
            fields = ["name", "sample", "created"]

        config = registry._registry[Measurement]

        assert config.display_name == "Inherited Measurement"
        assert config.fields == ["name", "sample", "created"]
        assert isinstance(config, MeasurementConfig)


class TestAutoGeneration:
    """Test auto-generation functionality."""

    def test_auto_generation_factories_loading(self, clean_registry, db):
        """Test that auto-generation factories are properly loaded."""

        @fairdm.register
        class AutoGenConfig(SampleConfig):
            model = Sample
            display_name = "Auto Generation Sample"
            list_fields = ["name", "created"]

        # Should be able to get auto-generation factories
        factories = registry._get_auto_factories()
        assert factories is not None

        # Factories should have the expected methods
        assert hasattr(factories, "generate_form")
        assert hasattr(factories, "generate_filterset")
        assert hasattr(factories, "generate_table")
        assert hasattr(factories, "generate_resource")
        assert hasattr(factories, "generate_serializer")


class TestRegistrationDecorator:
    """Test the @fairdm.register decorator specifically."""

    def test_decorator_returns_config_class(self, clean_registry, db):
        """Test that the decorator returns the configuration class for chaining."""

        @fairdm.register
        class DecoratorConfig(SampleConfig):
            model = Sample
            display_name = "Decorator Test"

        # The decorator should return the config class
        assert DecoratorConfig.model == Sample
        assert DecoratorConfig.display_name == "Decorator Test"

    def test_decorator_can_be_chained(self, clean_registry, db):
        """Test that the decorator can be used in chained operations."""

        # This should work without errors
        config_class = fairdm.register(
            type("ChainedConfig", (SampleConfig,), {"model": Sample, "display_name": "Chained Config"})
        )

        assert config_class.model == Sample
        assert Sample in registry._registry


class TestRegistrySummary:
    """Test the registry summary functionality."""

    def test_summarise_method_with_print_output(self, clean_registry, db):
        """Test the summarise method with print output enabled."""

        @fairdm.register
        class TestSampleConfig(SampleConfig):
            model = Sample
            display_name = "Test Sample"

        @fairdm.register
        class TestMeasurementConfig(MeasurementConfig):
            model = Measurement
            display_name = "Test Measurement"

        # Test with print output (should not raise errors)
        summary = registry.summarise(print_output=True)

        # Verify summary structure
        assert isinstance(summary, dict)
        assert "total_registered" in summary
        assert "samples" in summary
        assert "measurements" in summary
        assert summary["total_registered"] == 2
        assert summary["samples"]["count"] == 1
        assert summary["measurements"]["count"] == 1

    def test_summarise_method_without_print_output(self, clean_registry, db):
        """Test the summarise method without print output."""

        @fairdm.register
        class TestSampleConfig(SampleConfig):
            model = Sample
            display_name = "Water Sample"

        @fairdm.register
        class TestMeasurementConfig(MeasurementConfig):
            model = Measurement
            display_name = "Chemical Analysis"

        # Test without print output
        summary = registry.summarise(print_output=False)

        # Verify summary data structure
        assert summary["total_registered"] == 2
        assert summary["samples"]["count"] == 1
        assert summary["measurements"]["count"] == 1

        # Check sample data
        sample_data = summary["samples"]["models"][0]
        assert sample_data["name"] == "Sample"
        assert sample_data["display_name"] == "Water Sample"
        assert sample_data["app"] == "sample"

        # Check measurement data
        measurement_data = summary["measurements"]["models"][0]
        assert measurement_data["name"] == "Measurement"
        assert measurement_data["display_name"] == "Chemical Analysis"
        assert measurement_data["app"] == "measurement"

    def test_summarise_with_empty_registry(self, clean_registry):
        """Test summarise method with no registered models."""

        summary = registry.summarise(print_output=False)

        assert summary["total_registered"] == 0
        assert summary["samples"]["count"] == 0
        assert summary["measurements"]["count"] == 0
        assert len(summary["samples"]["models"]) == 0
        assert len(summary["measurements"]["models"]) == 0

    def test_summarise_with_only_samples(self, clean_registry, db):
        """Test summarise method with only sample models registered."""

        @fairdm.register
        class OnlySampleConfig(SampleConfig):
            model = Sample
            display_name = "Only Sample"

        summary = registry.summarise(print_output=False)

        assert summary["total_registered"] == 1
        assert summary["samples"]["count"] == 1
        assert summary["measurements"]["count"] == 0
        assert len(summary["samples"]["models"]) == 1
        assert len(summary["measurements"]["models"]) == 0

    def test_summarise_with_only_measurements(self, clean_registry, db):
        """Test summarise method with only measurement models registered."""

        @fairdm.register
        class OnlyMeasurementConfig(MeasurementConfig):
            model = Measurement
            display_name = "Only Measurement"

        summary = registry.summarise(print_output=False)

        assert summary["total_registered"] == 1
        assert summary["samples"]["count"] == 0
        assert summary["measurements"]["count"] == 1
        assert len(summary["samples"]["models"]) == 0
        assert len(summary["measurements"]["models"]) == 1
