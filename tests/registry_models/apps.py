from django.apps import AppConfig


class RegistryModelsConfig(AppConfig):
    """Test-only app hosting concrete Sample and Measurement subclasses.

    The registry refuses the polymorphic base classes, so tests need concrete
    subclasses to register. Those models need a real installed app, or admin and
    URL resolution fails with "No installed app with label ...".
    """

    name = "tests.registry_models"
    label = "registry_models"
