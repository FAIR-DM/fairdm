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
    """Invalid field name or field configuration.

    Raised when:
    - Field name doesn't exist on model
    - Field path (with __) cannot be resolved
    - Field type incompatible with component

    Attributes:
        field_name: The invalid field name
        model: The Django model class
        suggestion: Suggested correct field name (fuzzy match)
        valid_fields: List of all valid field names
    """

    def __init__(
        self,
        field_name: str,
        model: type["models.Model"],
        suggestion: str | None = None,
        valid_fields: list[str] | None = None,
    ):
        """Initialize FieldValidationError.

        Args:
            field_name: Invalid field name
            model: Django model class
            suggestion: Suggested correction (optional)
            valid_fields: All valid field names (optional)

        Example:
            raise FieldValidationError(
                'loction',  # Typo
                RockSample,
                suggestion='location'
            )
            # Error message: "Field 'loction' does not exist on RockSample.
            #                 Did you mean 'location'?"
        """
        self.field_name = field_name
        self.model = model
        self.suggestion = suggestion
        self.valid_fields = valid_fields

        message = f"Field '{field_name}' does not exist on {model.__name__}"

        if suggestion:
            message += f". Did you mean '{suggestion}'?"
        elif valid_fields:
            # Show first 5 valid fields
            field_list = ", ".join(valid_fields[:5])
            if len(valid_fields) > 5:
                field_list += f" (and {len(valid_fields) - 5} more)"
            message += f". Available fields: {field_list}"

        super().__init__(message)


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
