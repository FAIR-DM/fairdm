"""Registry Protocol - FairDM Registry System API Contract.

This module defines the Protocol (interface) for FairDMRegistry,
specifying exact method signatures and expected behavior.
"""

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from django.db import models

    from fairdm.core.models import Measurement, Sample

    from .config import ModelConfigurationProtocol

ModelT = TypeVar("ModelT", bound="models.Model")


class FairDMRegistryProtocol(Protocol):
    """Protocol defining the FairDMRegistry public API.

    The registry is a singleton that manages ModelConfiguration instances
    for all registered Sample and Measurement models. It provides:

    1. Registration API (@register decorator)
    2. Introspection API (get_for_model, samples, measurements properties)
    3. Validation (duplicate detection, inheritance checking)

    Example:
        Basic registration::

            from fairdm.registry import registry


            @registry.register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ["name", "location"]

        Introspection::

            # Get config for a specific model
            config = registry.get_for_model(RockSample)
            form_class = config.get_form_class()

            # List all registered samples
            for model in registry.samples:
                print(f"Sample: {model.__name__}")
    """

    def register(self, config_class: type["ModelConfigurationProtocol"]) -> type["ModelConfigurationProtocol"]:
        """Register a ModelConfiguration class via decorator.

        This method is designed to be used as a decorator on ModelConfiguration
        subclasses. It validates the configuration and stores it in the registry.

        Validation includes:
        - Model must inherit from Sample or Measurement
        - Model must not already be registered
        - All field names must exist on model
        - Custom classes must inherit from expected base classes

        Args:
            config_class: ModelConfiguration subclass to register

        Returns:
            The same config_class (for decorator chaining)

        Raises:
            ConfigurationError: If model doesn't inherit from Sample/Measurement
            DuplicateRegistrationError: If model already registered
            FieldValidationError: If field names are invalid

        Example:
            @registry.register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ['name', 'location', 'date_collected']
        """
        ...

    def get_for_model(self, model: type[ModelT]) -> "ModelConfigurationProtocol":
        """Get ModelConfiguration for a registered model.

        This is the primary introspection API. Use it to access the
        configuration for any registered model and retrieve generated components.

        Args:
            model: Django model class (must be registered)

        Returns:
            ModelConfiguration instance for the model

        Raises:
            KeyError: If model is not registered

        Example:
            # Get configuration
            config = registry.get_for_model(RockSample)

            # Access components
            form_class = config.get_form_class()
            table_class = config.get_table_class()

            # Check metadata
            print(config.display_name)  # "Rock Sample"
        """
        ...

    def is_registered(self, model: type[ModelT]) -> bool:
        """Check if a model is registered.

        Args:
            model: Django model class

        Returns:
            True if model is registered, False otherwise

        Example:
            if registry.is_registered(RockSample):
                config = registry.get_for_model(RockSample)
        """
        ...

    @property
    def samples(self) -> list[type["Sample"]]:
        """Get all registered Sample models.

        Returns:
            List of Sample subclasses that have been registered

        Example:
            for sample_model in registry.samples:
                config = registry.get_for_model(sample_model)
                print(f"{config.display_name}: {len(config.fields)} fields")
        """
        ...

    @property
    def measurements(self) -> list[type["Measurement"]]:
        """Get all registered Measurement models.

        Returns:
            List of Measurement subclasses that have been registered

        Example:
            for measurement_model in registry.measurements:
                config = registry.get_for_model(measurement_model)
                print(f"{config.display_name}: {len(config.fields)} fields")
        """
        ...

    @property
    def models(self) -> list[type["Sample | Measurement"]]:
        """Get all registered models (Samples + Measurements).

        Returns:
            Combined list of all registered Sample and Measurement models

        Example:
            print(f"Total registered models: {len(registry.models)}")
            for model in registry.models:
                print(f"- {model.__name__}")
        """
        ...

    def get_all_configs(self) -> list["ModelConfigurationProtocol"]:
        """Get all registered ModelConfiguration instances.

        Returns:
            List of all ModelConfiguration instances in registration order

        Example:
            for config in registry.get_all_configs():
                print(f"{config.model.__name__}: {config.display_name}")
        """
        ...

    def clear(self):
        """Clear all registrations (testing only).

        WARNING: This is intended for testing and should never be called
        in production code. Clearing the registry after Django startup
        will break component access.

        Example (pytest):
            def test_registration():
                registry.clear()  # Start with empty registry

                @registry.register
                class TestConfig(ModelConfiguration):
                    model = TestModel
                    fields = ['name']

                assert registry.is_registered(TestModel)
        """
        ...


class RegistryDecoratorProtocol(Protocol):
    """Protocol for the @register decorator function.

    This protocol defines the expected behavior of the decorator
    that can be used in two ways:

    1. Direct decorator: @register
    2. Called decorator: @register(some_arg=value)

    Currently only the direct decorator pattern is used.
    """

    def __call__(self, config_class: type["ModelConfigurationProtocol"]) -> type["ModelConfigurationProtocol"]:
        """Decorator function for registering configuration classes.

        Args:
            config_class: ModelConfiguration subclass

        Returns:
            The same config_class unchanged

        Raises:
            ConfigurationError: If configuration is invalid
            DuplicateRegistrationError: If model already registered
            FieldValidationError: If field names are invalid
        """
        ...
