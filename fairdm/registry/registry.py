"""
FairDM Registry - Model registration and discovery system.

This module provides the FairDMRegistry class and registration decorators for
managing Sample and Measurement models in the FairDM framework.
"""

import inspect
from typing import TYPE_CHECKING

from django.apps import apps
from django.contrib import admin
from django.db.models import Model

if TYPE_CHECKING:
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

# Import configuration classes from fairdm.registry.config
from fairdm.registry.config import ModelConfiguration


def _caller_location() -> str:
    """The module and qualified name that called into the registry.

    Import order decides which registration of a model arrives first, and that
    order is not visible from either file, so a duplicate-registration error has to
    say where the first one was.
    """
    frame = inspect.currentframe()
    try:
        # Walk out of this helper and out of the registry module itself.
        while frame is not None:
            module = frame.f_globals.get("__name__", "")
            if not module.startswith("fairdm.registry"):
                name = frame.f_code.co_qualname
                return f"{module}.{name}" if name != "<module>" else module
            frame = frame.f_back
        return "an unknown module"
    finally:
        del frame


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
        self._registry: dict[type[Model], ModelConfiguration] = {}
        # Where each model was registered from, so a duplicate can name the first.
        self._locations: dict[type[Model], str] = {}

    def _validate_model_is_registrable(self, model_class: type[Model]) -> None:
        """Only a concrete subclass of one of the two hierarchies may register.

        Registering a polymorphic base would generate six components for a class no
        portal stores rows in, and register a second admin against it.
        """
        from fairdm.registry.exceptions import ConfigurationError

        if model_class._meta.abstract:
            raise ConfigurationError(
                f"{model_class.__name__} is abstract. Only a concrete model can be "
                f"registered."
            )

        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        if model_class in (Sample, Measurement):
            raise ConfigurationError(
                f"{model_class.__name__} is a polymorphic base class. Register a "
                f"concrete subclass of it instead."
            )

        if not issubclass(model_class, (Sample, Measurement)):
            raise ConfigurationError(
                f"{model_class.__name__} must be a concrete subclass of "
                f"fairdm.core.sample.models.Sample or "
                f"fairdm.core.measurement.models.Measurement",
                model=model_class,
            )

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
                raise LookupError(
                    f"Model '{model_reference}' not found in Django apps"
                ) from err
        else:
            # Assume it's a model class
            model_cls = model_reference

        # Check if model is registered
        if model_cls not in self._registry:
            from fairdm.registry.exceptions import NotRegisteredError

            raise NotRegisteredError(model_cls)

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

    def register(
        self, model_class: type[Model], config: ModelConfiguration | None = None
    ) -> None:
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
        from fairdm.registry.exceptions import DuplicateRegistrationError

        self._validate_model_is_registrable(model_class)

        if model_class in self._registry:
            raise DuplicateRegistrationError(
                model=model_class,
                original_location=self._locations.get(model_class, "an unknown module"),
                new_location=_caller_location(),
            )

        # Get or create configuration instance
        config_instance = self.get_config(model_class, config)

        # Register admin using the config
        self.register_admin(model_class, config_instance)

        self._registry[model_class] = config_instance
        self._locations[model_class] = _caller_location()

    def register_admin(
        self, model_class: type[Model], config_instance: ModelConfiguration
    ) -> None:
        """Register the model's admin class with the Django admin site.

        A model already present in the admin site is left alone. A portal that wrote
        `@admin.register(RockSample)` has said which admin class it wants, and the
        registry does not overrule that. Autodiscovery runs before registration, so
        this is the normal path for any portal with a hand-written admin.

        Every other failure propagates. The previous implementation wrapped the whole
        method in `except Exception: pass`, which did express the rule above, but
        expressed it as a swallowed exception -- so a genuinely broken admin class
        registered as nothing, and looked identical to a model nobody registered.
        """
        if model_class in admin.site._registry:
            return

        admin.site.register(model_class, config_instance.get_admin_class())

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
