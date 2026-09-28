"""FairDM Demo Registry API Tests."""

from demo.config import DEMO_REGISTERED_MODELS
from demo.models import (
    CustomParentSample,
    CustomSample,
    ExampleMeasurement,
    RockSample,
    SoilSample,
    WaterSample,
)
from fairdm.registry import registry


class TestDemoRegistryIntrospection:
    def test_access_all_registered_samples(self):
        samples = registry.samples

        expected_samples = [
            CustomParentSample,
            CustomSample,
            RockSample,
            SoilSample,
            WaterSample,
        ]

        for sample_model in expected_samples:
            assert sample_model in samples, (
                f"{sample_model.__name__} should be registered"
            )

        for sample_model in samples:
            config = registry.get_for_model(sample_model)
            assert config is not None
            print(f"Sample: {sample_model.__name__} - Fields: {config.fields}")

    def test_access_all_registered_measurements(self):
        measurements = registry.measurements

        expected_measurements = [ExampleMeasurement]

        for measurement_model in expected_measurements:
            assert measurement_model in measurements, (
                f"{measurement_model.__name__} should be registered"
            )

        for measurement_model in measurements:
            config = registry.get_for_model(measurement_model)
            assert config is not None
            print(
                f"Measurement: {measurement_model.__name__} - Fields: {config.fields}"
            )

    def test_iterate_over_all_registered_models(self):
        all_models = registry.models

        assert len(all_models) == len(DEMO_REGISTERED_MODELS)

        for model_class in all_models:
            config = registry.get_for_model(model_class)

            form_class = config.get_form_class()
            table_class = config.get_table_class()
            filterset_class = config.get_filterset_class()

            assert form_class is not None
            assert table_class is not None
            assert filterset_class is not None

            print(f"Model: {model_class.__name__}")
            print(f"  Form: {form_class.__name__}")
            print(f"  Table: {table_class.__name__}")
            print(f"  Filterset: {filterset_class.__name__}")

    def test_check_model_registration_status(self, unique_app_label):
        assert registry.is_registered(RockSample) is True
        assert registry.is_registered(WaterSample) is True
        assert registry.is_registered(ExampleMeasurement) is True

        assert registry.is_registered("demo.rocksample") is True
        assert registry.is_registered("demo.watersample") is True
        assert registry.is_registered("demo.examplemeasurement") is True

        from fairdm.core.sample.models import Sample

        class UnregisteredSample(Sample):
            class Meta:
                app_label = unique_app_label

        assert registry.is_registered(UnregisteredSample) is False

    def test_access_all_configurations(self):
        all_configs = registry.get_all_configs()

        assert len(all_configs) == len(DEMO_REGISTERED_MODELS)

        for config in all_configs:
            assert config.model is not None
            assert config.fields is not None

            print(f"Configuration for {config.model.__name__}:")
            print(f"  Display name: {config.display_name}")
            print(f"  Fields: {config.fields}")
            print(f"  Description: {config.description}")

    def test_dynamic_model_discovery(self):
        model_choices = []

        for sample_model in registry.samples:
            config = registry.get_for_model(sample_model)
            model_choices.append(
                (sample_model.__name__, config.display_name or sample_model.__name__)
            )

        for measurement_model in registry.measurements:
            config = registry.get_for_model(measurement_model)
            model_choices.append(
                (
                    measurement_model.__name__,
                    config.display_name or measurement_model.__name__,
                )
            )

        assert len(model_choices) == len(DEMO_REGISTERED_MODELS)

        choice_names = [choice[0] for choice in model_choices]
        assert "RockSample" in choice_names
        assert "WaterSample" in choice_names
        assert "ExampleMeasurement" in choice_names

        print("Dynamic model choices for UI:")
        for name, display_name in model_choices:
            print(f"  {name}: {display_name}")

    def test_component_access_patterns(self):
        rock_config = registry.get_for_model(RockSample)
        rock_form = rock_config.get_form_class()
        rock_table = rock_config.get_table_class()

        components_by_model = {}
        for model_class in registry.models:
            config = registry.get_for_model(model_class)
            components_by_model[model_class] = {
                "form": config.get_form_class(),
                "table": config.get_table_class(),
                "filterset": config.get_filterset_class(),
                "serializer": config.get_serializer_class(),
            }

        assert len(components_by_model) == len(DEMO_REGISTERED_MODELS)
        assert RockSample in components_by_model
        assert components_by_model[RockSample]["form"] is not None

        for model_class in registry.samples:
            config = registry.get_for_model(model_class)

            # The accessor already resolves a supplied class, so a caller never needs to check for one.
            form = config.get_form_class()

            assert form is not None
            print(f"{model_class.__name__} uses form: {form.__name__}")


class TestDemoRegistryAPIPatterns:
    def test_filtering_models_by_criteria(self):
        samples_with_location = []
        for sample_model in registry.samples:
            config = registry.get_for_model(sample_model)
            if "location" in config.fields:
                samples_with_location.append(sample_model)

        print(
            f"Samples with location field: {[s.__name__ for s in samples_with_location]}"
        )

        samples_with_custom_forms = []
        for sample_model in registry.samples:
            config = registry.get_for_model(sample_model)
            if hasattr(config, "form_class") and config.form_class:
                samples_with_custom_forms.append(sample_model)

        print(
            f"Samples with custom forms: {[s.__name__ for s in samples_with_custom_forms]}"
        )

    def test_registry_integration_with_django_admin(self):
        for model_class in registry.models:
            config = registry.get_for_model(model_class)

            admin_class = config.get_admin_class()

            assert admin_class is not None
            assert hasattr(admin_class, "list_display")

            print(f"Admin for {model_class.__name__}: {admin_class.__name__}")

    def test_api_endpoint_generation_pattern(self):
        api_metadata = {}

        for model_class in registry.models:
            config = registry.get_for_model(model_class)

            serializer = config.get_serializer_class()

            api_metadata[model_class.__name__.lower()] = {
                "model": model_class.__name__,
                "display_name": config.display_name,
                "serializer": serializer.__name__,
                "fields": config.fields,
                "endpoint": f"/api/{model_class.__name__.lower()}/",
            }

        assert "rocksample" in api_metadata
        assert "watersample" in api_metadata
        assert "examplemeasurement" in api_metadata

        print("Generated API metadata:")
        for endpoint, metadata in api_metadata.items():
            print(f"  {endpoint}: {metadata}")
