"""Exception Classes - FairDM Registry System Error Types.

This module defines the complete exception hierarchy for the registry system
with helpful error messages, suggestions, and context preservation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db import models


class RegistryError(Exception):
    """Base exception for all registry errors.

    All registry-specific exceptions inherit from this class,
    allowing catching of all registry errors with a single except block.

    Example:
        try:
            @register
            class BadConfig(ModelConfiguration):
                model = BadModel  # Missing Sample/Measurement inheritance
        except RegistryError as e:
            logger.error(f"Registration failed: {e}")
    """


class ConfigurationError(RegistryError):
    """Invalid ModelConfiguration setup.

    Raised when:
    - Model doesn't inherit from Sample or Measurement
    - Required model attribute is missing
    - Custom class doesn't inherit from expected base
    - Invalid configuration combination

    Attributes:
        model: The Django model class (if known)
        config_class: The ModelConfiguration class (if known)
    """

    def __init__(
        self,
        message: str,
        model: type["models.Model"] | None = None,
        config_class: type | None = None,
    ):
        """Initialize ConfigurationError.

        Args:
            message: Error description
            model: Django model class (optional)
            config_class: ModelConfiguration class (optional)

        Example:
            raise ConfigurationError(
                "model attribute is required",
                config_class=RockSampleConfig
            )
        """
        self.model = model
        self.config_class = config_class

        # Add model name to message if available
        if model:
            message = f"{model.__name__}: {message}"
        elif config_class:
            message = f"{config_class.__name__}: {message}"

        super().__init__(message)


class FieldValidationError(RegistryError):
    """A field name in a configuration does not resolve on the model.

    The message names the four things a portal developer needs in order to fix it:
    the model, the attribute that declared the name, the name itself, and either a
    close match or the reason the path stopped resolving.

    Attributes:
        field_name: the name or path that failed
        model: the Django model it was declared against
        attribute: the configuration attribute that declared it
        suggestion: a comma-separated list of close matches, if any
        reason: why the path stopped resolving, where that is not a missing name
    """

    def __init__(
        self,
        field_name: str,
        model: type["models.Model"],
        attribute: str | None = None,
        suggestion: str | None = None,
        reason: str | None = None,
    ):
        """Build the error.

        Example:
            raise FieldValidationError(
                "loction", RockSample, attribute="fields", suggestion="location"
            )
            # "Invalid field 'loction' in RockSample.fields: no such field on
            #  RockSample. Did you mean: location?"
        """
        self.field_name = field_name
        self.model = model
        self.attribute = attribute
        self.suggestion = suggestion
        self.reason = reason

        where = f"{model.__name__}.{attribute}" if attribute else model.__name__
        why = reason or f"no such field on {model.__name__}"
        message = f"Invalid field {field_name!r} in {where}: {why}"

        if suggestion:
            message += f". Did you mean: {suggestion}?"

        super().__init__(message)


class NotRegisteredError(RegistryError, KeyError):
    """The configuration of a model that was never registered was requested.

    Subclasses ``KeyError`` so that callers written against the registry's earlier
    behaviour keep working, while the message names the model rather than repeating
    its label as a bare key.
    """

    def __init__(self, model: "type[models.Model] | str"):
        self.model = model
        name = model if isinstance(model, str) else model._meta.label
        super().__init__(
            f"{name} is not registered with the FairDM registry. Register it with "
            f"@fairdm.register, or use registry.is_registered() to ask without "
            f"raising."
        )

    def __str__(self) -> str:
        # KeyError repr()s its argument, which would quote the whole sentence.
        return str(self.args[0])


class DuplicateRegistrationError(RegistryError):
    """Model registered multiple times.

    Raised when attempting to register a model that's already registered.
    Each model can only be registered once.

    Attributes:
        model: The Django model class
        original_location: Module path where model was first registered
        new_location: Module path of duplicate registration attempt
    """

    def __init__(
        self,
        model: type["models.Model"],
        original_location: str,
        new_location: str | None = None,
    ):
        """Initialize DuplicateRegistrationError.

        Args:
            model: Django model class
            original_location: Module path of first registration
            new_location: Module path of duplicate attempt (optional)

        Example:
            raise DuplicateRegistrationError(
                RockSample,
                original_location='myapp.registry',
                new_location='myapp.another_registry'
            )
            # Error message: "RockSample already registered at myapp.registry.
            #                 Attempted duplicate registration from myapp.another_registry."
        """
        self.model = model
        self.original_location = original_location
        self.new_location = new_location

        message = f"{model.__name__} already registered at {original_location}. Each model can only be registered once."

        if new_location:
            message += f" Attempted duplicate registration from {new_location}."

        super().__init__(message)
