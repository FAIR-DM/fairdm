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


class ComponentGenerationError(RegistryError):
    """Error during component class generation.

    Raised when factory fails to generate a component class.
    Wraps the original exception with additional context.

    Attributes:
        component_type: Type of component ('form', 'table', 'filterset', etc.)
        model: The Django model class
        original_exception: The underlying exception that caused failure
    """

    def __init__(
        self,
        component_type: str,
        model: type["models.Model"],
        original_exception: Exception,
    ):
        """Initialize ComponentGenerationError.

        Args:
            component_type: Component type being generated
            model: Django model class
            original_exception: Underlying exception

        Example:
            try:
                # Factory generation code
                pass
            except Exception as e:
                raise ComponentGenerationError(
                    'table',
                    RockSample,
                    e
                ) from e
            # Error message: "Failed to generate table for RockSample:
            #                 AttributeError: 'NoneType' object has no attribute 'related_model'"
        """
        self.component_type = component_type
        self.model = model
        self.original_exception = original_exception

        message = (
            f"Failed to generate {component_type} for {model.__name__}: "
            f"{original_exception.__class__.__name__}: {original_exception}"
        )

        super().__init__(message)


class FieldResolutionError(RegistryError):
    """Error resolving field path with double-underscore notation.

    Raised when a related field path (e.g., 'project__title') cannot be resolved
    because the intermediate relationship doesn't exist.

    Attributes:
        field_path: The full field path that failed
        model: The starting model
        failed_at: The part of the path where resolution failed
    """

    def __init__(
        self,
        field_path: str,
        model: type["models.Model"],
        failed_at: str,
    ):
        """Initialize FieldResolutionError.

        Args:
            field_path: Full field path (e.g., 'project__dataset__title')
            model: Starting model
            failed_at: Part where resolution failed

        Example:
            raise FieldResolutionError(
                'project__dataset__title',
                RockSample,
                failed_at='dataset'
            )
            # Error message: "Cannot resolve field path 'project__dataset__title'
            #                 on RockSample. Failed at 'dataset'."
        """
        self.field_path = field_path
        self.model = model
        self.failed_at = failed_at

        message = f"Cannot resolve field path '{field_path}' on {model.__name__}. Failed at '{failed_at}'."

        super().__init__(message)


class ComponentWarning(UserWarning):
    """Warning during component generation (non-fatal).

    Used for:
    - Fields excluded due to type incompatibility
    - Deprecated patterns
    - Performance concerns

    Example:
        import warnings

        warnings.warn(
            f"JSONField '{field_name}' excluded from table (not displayable)",
            ComponentWarning
        )
    """
