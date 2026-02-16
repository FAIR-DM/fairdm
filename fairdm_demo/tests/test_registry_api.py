"""
FairDM Demo Registry API Tests

This module demonstrates the FairDM registry introspection API patterns
with practical examples that developers can adapt for their own portals.

These tests serve as both validation and documentation for the registry API,
showing how to:
- Access registered models programmatically
- Iterate over registered samples and measurements
- Get configuration details for models
- Check if models are registered
- Access auto-generated components

See: quickstart.md for complete registry usage patterns
See: data-model.md for API specifications
See: contracts/ for type definitions
"""

from fairdm.registry import registry
from fairdm_demo.config import DEMO_REGISTERED_MODELS
from fairdm_demo.models import (
    CustomParentSample,
    CustomSample,
    ExampleMeasurement,
    RockSample,
    SoilSample,
    WaterSample,
)


class TestDemoRegistryIntrospection:
    """Demonstrate registry introspection patterns using demo models."""

    def test_access_all_registered_samples(self):
        """Demonstrate accessing all registered Sample models."""
        # Get all registered Sample models
        samples = registry.samples

        # Verify we have the expected demo samples
        expected_samples = [
            CustomParentSample,
            CustomSample,
            RockSample,
            SoilSample,
            WaterSample,
        ]

        for sample_model in expected_samples:
            assert sample_model in samples, f"{sample_model.__name__} should be registered"

        # Demonstrate accessing configuration for each sample
        for sample_model in samples:
            config = registry.get_for_model(sample_model)
            assert config is not None
            print(f"Sample: {sample_model.__name__} - Fields: {config.fields}")

    def test_access_all_registered_measurements(self):
        """Demonstrate accessing all registered Measurement models."""
        # Get all registered Measurement models
        measurements = registry.measurements

        # Verify we have the expected demo measurement
        expected_measurements = [ExampleMeasurement]

        for measurement_model in expected_measurements:
            assert measurement_model in measurements, f"{measurement_model.__name__} should be registered"

        # Demonstrate accessing configuration for each measurement
        for measurement_model in measurements:
            config = registry.get_for_model(measurement_model)
            assert config is not None
            print(f"Measurement: {measurement_model.__name__} - Fields: {config.fields}")

    def test_iterate_over_all_registered_models(self):
        """Demonstrate iterating over all registered models (samples + measurements)."""
        # Get all registered models
        all_models = registry.models

        # Verify total count matches demo expectations
        assert len(all_models) == len(DEMO_REGISTERED_MODELS)

        # Demonstrate iteration with component access
        for model_class in all_models:
            config = registry.get_for_model(model_class)

            # Access auto-generated components
            form_class = config.form
            table_class = config.table
            filterset_class = config.filterset

            # Verify components were generated
            assert form_class is not None
            assert table_class is not None
            assert filterset_class is not None

            print(f"Model: {model_class.__name__}")
            print(f"  Form: {form_class.__name__}")
            print(f"  Table: {table_class.__name__}")
            print(f"  Filterset: {filterset_class.__name__}")

    def test_check_model_registration_status(self):
        """Demonstrate checking if models are registered."""
        # Test with registered models
        assert registry.is_registered(RockSample) is True
        assert registry.is_registered(WaterSample) is True
        assert registry.is_registered(ExampleMeasurement) is True

        # Test with string references (using real apps)
        assert registry.is_registered("fairdm_demo.rocksample") is True
        assert registry.is_registered("fairdm_demo.watersample") is True
        assert registry.is_registered("fairdm_demo.examplemeasurement") is True

        # Test with unregistered model
        from fairdm.core.sample.models import Sample

        class UnregisteredSample(Sample):
            class Meta:
                app_label = "fairdm_demo"

        assert registry.is_registered(UnregisteredSample) is False

    def test_access_all_configurations(self):
        """Demonstrate accessing all ModelConfiguration instances."""
        # Get all configurations
        all_configs = registry.get_all_configs()

        # Verify we have configurations for all registered models
        assert len(all_configs) == len(DEMO_REGISTERED_MODELS)

        # Demonstrate accessing configuration details
        for config in all_configs:
            assert config.model is not None
            assert config.fields is not None

            print(f"Configuration for {config.model.__name__}:")
            print(f"  Display name: {config.display_name}")
            print(f"  Fields: {config.fields}")
            print(f"  Description: {config.description}")

    def test_dynamic_model_discovery(self):
        """Demonstrate dynamic model discovery for building UIs."""
        # Example: Build a dynamic model selection form
        model_choices = []

        # Add sample choices
        for sample_model in registry.samples:
            config = registry.get_for_model(sample_model)
            model_choices.append((sample_model.__name__, config.display_name or sample_model.__name__))

        # Add measurement choices
        for measurement_model in registry.measurements:
            config = registry.get_for_model(measurement_model)
            model_choices.append(
                (
                    measurement_model.__name__,
                    config.display_name or measurement_model.__name__,
                )
            )

        # Verify choices were created
        assert len(model_choices) == len(DEMO_REGISTERED_MODELS)

        # Example choices should include our demo models
        choice_names = [choice[0] for choice in model_choices]
        assert "RockSample" in choice_names
        assert "WaterSample" in choice_names
        assert "ExampleMeasurement" in choice_names

        print("Dynamic model choices for UI:")
        for name, display_name in model_choices:
            print(f"  {name}: {display_name}")

    def test_component_access_patterns(self):
        """Demonstrate different patterns for accessing auto-generated components."""
        # Pattern 1: Direct model access
        rock_config = registry.get_for_model(RockSample)
        rock_form = rock_config.form
        rock_table = rock_config.table

        # Pattern 2: Iteration with component caching
        component_cache = {}
        for model_class in registry.models:
            config = registry.get_for_model(model_class)
            component_cache[model_class] = {
                "form": config.form,
                "table": config.table,
                "filterset": config.filterset,
                "serializer": config.serializer,
            }

        # Verify cache was built
        assert len(component_cache) == len(DEMO_REGISTERED_MODELS)
        assert RockSample in component_cache
        assert component_cache[RockSample]["form"] is not None

        # Pattern 3: Conditional component access
        for model_class in registry.samples:
            config = registry.get_for_model(model_class)

            # Only access components we need
            form = config.form_class if hasattr(config, "form_class") and config.form_class else config.form

            assert form is not None
            print(f"{model_class.__name__} uses form: {form.__name__}")


class TestDemoRegistryAPIPatterns:
    """Demonstrate advanced registry API usage patterns."""

    def test_filtering_models_by_criteria(self):
        """Demonstrate filtering registered models by various criteria."""
        # Filter samples by field availability
        samples_with_location = []
        for sample_model in registry.samples:
            config = registry.get_for_model(sample_model)
            if "location" in config.fields:
                samples_with_location.append(sample_model)

        print(f"Samples with location field: {[s.__name__ for s in samples_with_location]}")

        # Filter by custom configuration
        samples_with_custom_forms = []
        for sample_model in registry.samples:
            config = registry.get_for_model(sample_model)
            if hasattr(config, "form_class") and config.form_class:
                samples_with_custom_forms.append(sample_model)

        print(f"Samples with custom forms: {[s.__name__ for s in samples_with_custom_forms]}")

    def test_registry_integration_with_django_admin(self):
        """Demonstrate how to integrate registry with Django admin dynamically."""

        # Example: Register all models with admin using registry configurations
        for model_class in registry.models:
            config = registry.get_for_model(model_class)

            # Access the auto-generated admin class
            admin_class = config.admin

            # Verify admin class was generated
            assert admin_class is not None
            assert hasattr(admin_class, "list_display")

            print(f"Admin for {model_class.__name__}: {admin_class.__name__}")

    def test_api_endpoint_generation_pattern(self):
        """Demonstrate how to use registry for API endpoint generation."""
        # Example: Generate API metadata for all registered models
        api_metadata = {}

        for model_class in registry.models:
            config = registry.get_for_model(model_class)

            # Access serializer for API
            serializer = config.serializer

            # Build API metadata
            api_metadata[model_class.__name__.lower()] = {
                "model": model_class.__name__,
                "display_name": config.display_name,
                "serializer": serializer.__name__,
                "fields": config.fields,
                "endpoint": f"/api/{model_class.__name__.lower()}/",
            }

        # Verify metadata was generated
        assert "rocksample" in api_metadata
        assert "watersample" in api_metadata
        assert "examplemeasurement" in api_metadata

        print("Generated API metadata:")
        for endpoint, metadata in api_metadata.items():
            print(f"  {endpoint}: {metadata}")
