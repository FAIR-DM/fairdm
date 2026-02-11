"""
FairDM Registry - Model registration and discovery system.

This module provides the FairDMRegistry class and registration decorators for
managing Sample and Measurement models in the FairDM framework.
"""

from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.contrib import admin
from django.db.models import Model

if TYPE_CHECKING:
    pass

    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

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

    def __init__(self) -> None:
        self._registry: dict[type[Model], ModelConfiguration] = {}  # Stores model -> config_instance mapping
        self._auto_factories = None  # Lazy loaded factories

    def _validate_model_class(self, model_class: type[Model]) -> None:
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

    def get_for_model(self, model_reference: type[Model] | str) -> ModelConfiguration:
        """
        Retrieve the registered configuration for a model.

        This method can accept either a model class directly or a string reference
        in the format "app_label.model_name" (compatible with apps.get_model).

        Args:
            model_reference: Either a Django model class or a string in format "app_label.model_name"
                            Note: Use the actual Django app name and lowercase model name,
                            e.g., "sample.sample" for the Sample model in the sample app

        Returns:
            ModelConfiguration: The configuration instance for the model.

        Raises:
            KeyError: If the model is not registered with the registry
            ValueError: If the string format is invalid (must be "app_label.model_name")
            LookupError: If the model cannot be found in Django apps

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
            except ValueError as err:
                raise ValueError(
                    f"Invalid model reference format '{model_reference}'. Expected 'app_label.model_name'"
                ) from err

            try:
                model_cls = apps.get_model(app_label, model_name)
            except LookupError as err:
                raise LookupError(f"Model '{model_reference}' not found in Django apps") from err
        else:
            # Assume it's a model class
            model_cls = model_reference

        # Check if model is registered
        if model_cls not in self._registry:
            model_name = getattr(model_cls._meta, "label", str(model_cls))
            raise KeyError(f"Model '{model_name}' is not registered with the FairDM registry")

        return self._registry[model_cls]

    def is_registered(self, model_reference: type[Model] | str) -> bool:
        """
        Check if a model is registered with the registry.

        Args:
            model_reference: Either a Django model class or a string in format "app_label.model_name"

        Returns:
            bool: True if the model is registered, False otherwise

        Examples:
            # Using model class
            if registry.is_registered(MySample):
                print("MySample is registered")

            # Using string reference
            if registry.is_registered("myapp.mysample"):
                print("MySample is registered")
        """
        try:
            self.get_for_model(model_reference)
            return True  # noqa: TRY300
        except (KeyError, ValueError, LookupError):
            return False

    @property
    def samples(self) -> list[type["Sample"]]:
        """
        Retrieves all registered Sample models.

        Returns:
            list[type]: A list of registered Sample model classes.
        """
        from fairdm.core.sample.models import Sample

        return [model for model in self._registry if issubclass(model, Sample)]

    @property
    def measurements(self) -> list[type["Measurement"]]:
        """
        Retrieves all registered Measurement models.

        Returns:
            list[type]: A list of registered Measurement model classes.
        """
        from fairdm.core.measurement.models import Measurement

        return [model for model in self._registry if issubclass(model, Measurement)]

    @property
    def models(self) -> list[type[Model]]:
        """
        Retrieves all registered models (Samples + Measurements).

        Returns:
            list[type]: A combined list of all registered Sample and Measurement model classes.
        """
        return list(self._registry.keys())

    def get_all_configs(self) -> list[ModelConfiguration]:
        """
        Retrieve all registered ModelConfiguration instances.

        Returns:
            list[ModelConfiguration]: A list of all ModelConfiguration instances
                                     in registration order.

        Examples:
            # Iterate over all registered configurations
            for config in registry.get_all_configs():
                print(f"Model: {config.model.__name__}")
                print(f"Fields: {config.fields}")
        """
        return list(self._registry.values())

    def register(self, model_class: type[Model], config: ModelConfiguration | None = None) -> None:
        """
        Registers a Sample or Measurement subclass with associated configuration.

        Args:
            model_class (django.db.models.Model): The Django model class to register.
                Must be a subclass of Sample or Measurement.
            config (type, optional): Configuration class for the model.

        Raises:
            ConfigurationError: If model_class is not a Sample or Measurement subclass.
            DuplicateRegistrationError: If model_class is already registered.
        """
        from fairdm.registry.exceptions import (
            ConfigurationError,
            DuplicateRegistrationError,
        )

        # Validate that this is a Sample or Measurement subclass
        try:
            from fairdm.core.measurement.models import Measurement
            from fairdm.core.sample.models import Sample

            if not (issubclass(model_class, Sample) or issubclass(model_class, Measurement)):
                raise ConfigurationError(
                    f"{model_class.__name__} must inherit from Sample or Measurement",
                    model=model_class,
                )
        except ImportError as e:
            raise ImportError(
                f"Could not import Sample or Measurement models to validate {model_class.__name__}: {e}"
            ) from e

        # Check if already registered (T030)
        if model_class in self._registry:
            raise DuplicateRegistrationError(
                model=model_class,
                original_location="Unknown",  # TODO: Track registration location
                new_location="Unknown",
            )

        # Get or create configuration instance
        config_instance = self.get_config(model_class, config)

        # Register admin using the config
        self.register_admin(model_class, config_instance)

        # Store just the config instance
        self._registry[model_class] = config_instance

    def register_admin(self, model_class: type[Model], config_instance: ModelConfiguration) -> None:
        """Register model with Django admin using auto-generated admin class from config."""
        try:
            # Get admin class from config
            admin_class = config_instance.get_admin_class()
            admin.site.register(model_class, admin_class)
        except Exception:  # noqa: S110
            # Model already registered or admin not available - this is expected
            # Silently ignore admin registration failures as they are non-critical
            pass

    def summarise(self, print_output: bool = True) -> dict[str, Any]:
        """
        Generate a summary of all registered models in the registry.

        Args:
            print_output (bool): Whether to print the summary to stdout. Default True.

        Returns:
            dict: A dictionary containing summary information about registered models.
        """
        samples = self.samples
        measurements = self.measurements

        summary: dict[str, Any] = {
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
            samples_info = summary["samples"]
            if isinstance(samples_info, dict) and samples_info.get("models"):
                for model_info in samples_info["models"]:
                    if isinstance(model_info, dict):
                        print(f"  • {model_info['name']} ({model_info['app']})")
                        print(f"    Display: {model_info['display_name']}")
                        print(f"    Verbose: {model_info['verbose_name']}")
                        print()
            else:
                print("  No samples registered")

            print(f"📊 MEASUREMENTS ({summary['measurements']['count']})")
            print("-" * 40)
            measurements_info = summary["measurements"]
            if isinstance(measurements_info, dict) and measurements_info.get("models"):
                for model_info in measurements_info["models"]:
                    if isinstance(model_info, dict):
                        print(f"  • {model_info['name']} ({model_info['app']})")
                        print(f"    Display: {model_info['display_name']}")
                        print(f"    Verbose: {model_info['verbose_name']}")
                        print()
            else:
                print("  No measurements registered")

            print("=" * 60)

        return summary

    def get_config(
        self,
        model_class: type[Model],
        config: ModelConfiguration | type[ModelConfiguration] | None = None,
    ) -> ModelConfiguration:
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

    def register_model(self, model_class: type[Model], **kwargs):
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


def register(config_cls: type) -> type:
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

    # Register the model with the configuration instance (not class)
    config_instance = config_cls() if isinstance(config_cls, type) else config_cls
    registry.register(model_class, config_instance)

    return config_cls


# Export the main classes and objects that should be publicly available
__all__ = [
    "FairDMRegistry",
    "register",
    "registry",
]
