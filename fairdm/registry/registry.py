"""
FairDM Registry - Model registration and discovery system.

This module provides the FairDMRegistry class and registration decorators for
managing Sample and Measurement models in the FairDM framework.
"""

from django.apps import apps
from django.contrib import admin

# Import configuration classes from fairdm.registry.config
from fairdm.registry.config import ModelConfiguration


class FairDMRegistry:
    """
    A registry to manage Sample and Measurement subclass registration with auto-generated configurations.

    This registry implements the FairDM registration API that allows Sample and Measurement
    subclasses to be registered with configuration classes that auto-generate forms,
    serializers, filters, and tables when not explicitly provided.

    Usage:
        @fairdm.register
        class MySampleConfig:
            model = MySample
            display_name = "Water Sample"
            list_fields = ["name", "location", "collected_at"]
            detail_fields = ["name", "description", "metadata"]
            filter_fields = ["collected_at", "contributor"]
    """

    def __init__(self):
        self._registry = {}  # Stores model -> config_instance mapping
        self._auto_factories = None  # Lazy loaded factories

    def _validate_model_class(self, model_class):
        """
        Validate that the model class is a subclass of Sample or Measurement.

        Args:
            model_class: The Django model class to validate

        Raises:
            ValueError: If model is not a Sample or Measurement subclass
        """
        try:
            from fairdm.core.measurement.models import Measurement
            from fairdm.core.sample.models import Sample

            if not (issubclass(model_class, Sample) or issubclass(model_class, Measurement)):
                raise TypeError(
                    f"Model {model_class.__name__} must be a subclass of "
                    f"fairdm.core.sample.models.Sample or fairdm.core.measurement.models.Measurement"
                )
        except ImportError as e:
            raise ImportError(
                f"Could not import Sample or Measurement models to validate {model_class.__name__}: {e}"
            ) from e

    def _get_auto_factories(self):
        """Lazy load auto-generation factories."""
        if self._auto_factories is None:
            from fairdm.utils.factories import AutoGenerationFactories

            self._auto_factories = AutoGenerationFactories()
        return self._auto_factories

    def get_for_model(self, model_reference):
        """
        Retrieve the registered configuration for a model.

        This method can accept either a model class directly or a string reference
        in the format "app_label.model_name" (compatible with apps.get_model).

        Args:
            model_reference: Either a Django model class or a string in format "app_label.model_name"
                            Note: Use the actual Django app name and lowercase model name,
                            e.g., "sample.sample" for the Sample model in the sample app

        Returns:
            ModelConfiguration or None: The configuration instance for the model, or None if not found.

        Examples:
            # Using model class
            config = registry.get_for_model(MySample)

            # Using string reference (note lowercase model name)
            config = registry.get_for_model("myapp.mysample")
            config = registry.get_for_model("sample.sample")  # for core Sample model
        """
        if isinstance(model_reference, str):
            # Handle string format: "app_label.ModelName"
            try:
                app_label, model_name = model_reference.split(".", 1)
                model_cls = apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                # Invalid format or model not found
                return None
        else:
            # Assume it's a model class
            model_cls = model_reference

        return self._registry.get(model_cls)

    @property
    def samples(self):
        """
        Retrieves all registered Sample models.

        Returns:
            list[type]: A list of registered Sample model classes.
        """
        from fairdm.core.sample.models import Sample

        return [model for model in self._registry.keys() if issubclass(model, Sample)]

    @property
    def measurements(self):
        """
        Retrieves all registered Measurement models.

        Returns:
            list[type]: A list of registered Measurement model classes.
        """
        from fairdm.core.measurement.models import Measurement

        return [model for model in self._registry.keys() if issubclass(model, Measurement)]

    def register(self, model_class, config=None):
        """
        Registers a Sample or Measurement subclass with associated configuration.

        Args:
            model_class (django.db.models.Model): The Django model class to register.
                Must be a subclass of Sample or Measurement.
            config (type, optional): Configuration class for the model.

        Raises:
            TypeError: If model_class is not a Sample or Measurement subclass.
        """
        # Validate that this is a Sample or Measurement subclass
        self._validate_model_class(model_class)

        # Check if already registered
        if model_class in self._registry:
            return  # Skip if already registered

        self.register_actstream(model_class)

        # Get or create configuration instance
        config_instance = self.get_config(model_class, config)

        # Register admin using the config
        self.register_admin(model_class, config_instance)

        # Store just the config instance
        self._registry[model_class] = config_instance

    def register_actstream(self, model_class):
        from actstream import registry as actstream_registry

        actstream_registry.register(model_class)

    def register_admin(self, model_class, config_instance):
        """Register model with Django admin using auto-generated admin class from config."""
        try:
            # Get admin class from config
            admin_class = config_instance.get_admin_class()
            admin.site.register(model_class, admin_class)
        except Exception:
            # Model already registered or admin not available - this is expected
            # Silently ignore admin registration failures as they are non-critical
            pass

    def summarise(self, print_output=True):
        """
        Generate a summary of all registered models in the registry.

        Args:
            print_output (bool): Whether to print the summary to stdout. Default True.

        Returns:
            dict: A dictionary containing summary information about registered models.
        """
        samples = self.samples
        measurements = self.measurements

        summary = {
            "total_registered": len(self._registry),
            "samples": {
                "count": len(samples),
                "models": [
                    {
                        "name": model.__name__,
                        "app": model._meta.app_label,
                        "verbose_name": model._meta.verbose_name,
                        "display_name": self._registry[model].get_display_name(),
                    }
                    for model in samples
                ],
            },
            "measurements": {
                "count": len(measurements),
                "models": [
                    {
                        "name": model.__name__,
                        "app": model._meta.app_label,
                        "verbose_name": model._meta.verbose_name,
                        "display_name": self._registry[model].get_display_name(),
                    }
                    for model in measurements
                ],
            },
        }

        if print_output:
            print("\n" + "=" * 60)
            print("FairDM Registry Summary")
            print("=" * 60)
            print(f"Total Registered Models: {summary['total_registered']}")

            print(f"\n📊 SAMPLES ({summary['samples']['count']})")
            print("-" * 40)
            if summary["samples"]["models"]:
                for model_info in summary["samples"]["models"]:
                    print(f"  • {model_info['name']} ({model_info['app']})")
                    print(f"    Display: {model_info['display_name']}")
                    print(f"    Verbose: {model_info['verbose_name']}")
                    print()
            else:
                print("  No samples registered")

            print(f"📊 MEASUREMENTS ({summary['measurements']['count']})")
            print("-" * 40)
            if summary["measurements"]["models"]:
                for model_info in summary["measurements"]["models"]:
                    print(f"  • {model_info['name']} ({model_info['app']})")
                    print(f"    Display: {model_info['display_name']}")
                    print(f"    Verbose: {model_info['verbose_name']}")
                    print()
            else:
                print("  No measurements registered")

            print("=" * 60)

        return summary

    def get_config(self, model_class, config=None):
        """
        Builds a configuration instance from the registered config class.
        Handles auto-generation of forms, serializers, filters, and tables.

        Args:
            model_class: The Django model class
            config: Either a config class or instance, or None for default

        Returns:
            ModelConfiguration: The configuration instance
        """
        if config is None:
            # Check if already registered
            if model_class in self._registry:
                return self._registry[model_class]

            # Create default config with auto-generation
            return ModelConfiguration(model_class)

        if isinstance(config, type):
            # Instantiate the config class
            return config(model_class)

        # Assume it's already an instance
        return config

    def register_model(self, model_class, **kwargs):
        """
        Decorator method to register a model with an auto-generated configuration.

        This is the preferred API from the instructions that supports:
        - Auto-generation of forms, serializers, filters, tables
        - Simple field-based configuration

        Usage:
            @registry.register_model(MySample)
            class MySampleConfig:
                display_name = "Water Sample"
                fields = ["name", "location", "collected_at"]
        """

        def _register(config_cls):
            self.register(model_class, config_cls, **kwargs)
            return config_cls

        return _register


# Global registry instance
registry = FairDMRegistry()


def register(config_cls):
    """
    Decorator to register a Sample or Measurement model with its configuration.

    This decorator provides a consistent API for registering models with the FairDM framework.
    The configuration class must specify a 'model' attribute pointing to the Sample or
    Measurement subclass to register.

    Usage:
        @fairdm.register
        class MySampleConfig(SampleConfig):
            model = MySample
            display_name = "My Sample Type"
            list_fields = ["name", "created"]

    Args:
        config_cls: Configuration class inheriting from BaseModelConfig

    Returns:
        The configuration class (for chaining)

    Raises:
        ValueError: If config_cls doesn't specify a model attribute
        TypeError: If the model is not a Sample or Measurement subclass
    """
    # Validate that the config class has a model attribute
    if not hasattr(config_cls, "model") or not config_cls.model:
        raise ValueError(
            f"Configuration class {config_cls.__name__} must specify a 'model' attribute "
            f"pointing to the Sample or Measurement subclass to register"
        )

    model_class = config_cls.model

    # Register the model with the configuration
    registry.register(model_class, config_cls)

    return config_cls


# Export the main classes and objects that should be publicly available
__all__ = [
    "FairDMRegistry",
    "register",
    "registry",
]
