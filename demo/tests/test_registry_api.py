"""FairDM Demo Registry API Tests."""

from demo.models import ExampleMeasurement, RockSample, WaterSample
from fairdm.registry import registry


class TestDemoRegistry:
    def test_every_registered_demo_model_builds_its_components(self):
        failures = []
        for model_class in registry.models:
            config = registry.get_for_model(model_class)
            for name, build in (
                ("form", config.get_form_class),
                ("table", config.get_table_class),
                ("filterset", config.get_filterset_class),
                ("serializer", config.get_serializer_class),
                ("admin", config.get_admin_class),
            ):
                try:
                    if build() is None:
                        failures.append(f"{model_class.__name__}: no {name} class")
                except Exception as error:
                    failures.append(f"{model_class.__name__}: {name}: {error!r}")

        assert not failures, "\n".join(failures)

    def test_the_demo_samples_and_measurements_are_registered(self):
        assert {RockSample, WaterSample} <= set(registry.samples)
        assert ExampleMeasurement in registry.measurements
