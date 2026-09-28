"""The registry of Sample and Measurement models, and the ``register`` decorator."""

import inspect
from typing import TYPE_CHECKING

from django.apps import apps
from django.contrib import admin
from django.db.models import Model

if TYPE_CHECKING:
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

from fairdm.registry.config import ModelConfiguration


def _caller_location() -> str:
    """Return the module and qualified name that called into the registry.

    Import order decides which registration of a model arrives first, and that
    order is not visible from either file, so a duplicate-registration error has to
    say where the first one was.

    Returns:
        The caller as ``module.qualname``, the bare module for module-level code,
        or ``"an unknown module"`` when no caller outside the registry is found.
    """
    frame = inspect.currentframe()
    try:
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
    """Registry of Sample and Measurement models and their configurations.

    A model is registered with a configuration class that auto-generates forms,
    serializers, filters and tables when they are not given explicitly.

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
        """Require a concrete subclass of Sample or Measurement.

        Registering a polymorphic base would generate six components for a class no
        portal stores rows in, and register a second admin against it.

        Args:
            model_class: The model to check.

        Raises:
            ConfigurationError: The model is abstract, is one of the two polymorphic
                bases, or is not a subclass of either.
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
        """Return the registered configuration for a model.

        Args:
            model_reference: A Django model class, or a string in the format
                ``"app_label.model_name"`` as accepted by ``apps.get_model``. Use
                the Django app label and the lowercase model name, for example
                ``"sample.sample"`` for the core Sample model.

        Returns:
            The configuration instance for the model.

        Raises:
            NotRegisteredError: The model is not registered. It is also a
                ``KeyError``.
            ValueError: The string is not in the format ``"app_label.model_name"``.
            LookupError: The model cannot be found in the Django apps.

        Example:
            config = registry.get_for_model(MySample)
            config = registry.get_for_model("myapp.mysample")
        """
        if isinstance(model_reference, str):
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
            model_cls = model_reference

        if model_cls not in self._registry:
            from fairdm.registry.exceptions import NotRegisteredError

            raise NotRegisteredError(model_cls)

        return self._registry[model_cls]

    def is_registered(self, model_reference: type[Model] | str) -> bool:
        """Report whether a model is registered.

        Args:
            model_reference: A Django model class, or a string in the format
                ``"app_label.model_name"``.

        Returns:
            ``True`` if the model is registered, ``False`` otherwise, including when
            the reference does not resolve to a model.

        Example:
            if registry.is_registered("myapp.mysample"):
                ...
        """
        try:
            self.get_for_model(model_reference)
            return True  # noqa: TRY300
        except (KeyError, ValueError, LookupError):
            return False

    @property
    def samples(self) -> list[type["Sample"]]:
        """Return the registered Sample model classes."""
        from fairdm.core.sample.models import Sample

        return [model for model in self._registry if issubclass(model, Sample)]

    @property
    def measurements(self) -> list[type["Measurement"]]:
        """Return the registered Measurement model classes."""
        from fairdm.core.measurement.models import Measurement

        return [model for model in self._registry if issubclass(model, Measurement)]

    @property
    def models(self) -> list[type[Model]]:
        """Return every registered model class, Samples and Measurements together."""
        return list(self._registry.keys())

    def get_all_configs(self) -> list[ModelConfiguration]:
        """Return every registered configuration.

        Returns:
            The ``ModelConfiguration`` instances in registration order.

        Example:
            for config in registry.get_all_configs():
                print(config.model.__name__, config.fields)
        """
        return list(self._registry.values())

    def register(
        self, model_class: type[Model], config: ModelConfiguration | None = None
    ) -> None:
        """Register a Sample or Measurement subclass with its configuration.

        A model that is not a concrete Sample or Measurement subclass raises
        ``ConfigurationError``.

        Args:
            model_class: The model class to register.
            config: The configuration instance for the model. A default one is
                built when omitted.

        Raises:
            DuplicateRegistrationError: The model is already registered.
        """
        from fairdm.registry.exceptions import DuplicateRegistrationError

        self._validate_model_is_registrable(model_class)

        if model_class in self._registry:
            raise DuplicateRegistrationError(
                model=model_class,
                original_location=self._locations.get(model_class, "an unknown module"),
                new_location=_caller_location(),
            )

        config_instance = self.get_config(model_class, config)

        self.register_admin(model_class, config_instance)

        self._registry[model_class] = config_instance
        self._locations[model_class] = _caller_location()

    def register_admin(
        self, model_class: type[Model], config_instance: ModelConfiguration
    ) -> None:
        """Register the model's admin class with the Django admin site.

        A model already present in the admin site is left alone. A portal that wrote
        ``@admin.register(RockSample)`` has said which admin class it wants, and the
        registry does not overrule that. Autodiscovery runs before registration, so
        this is the normal path for any portal with a hand-written admin.

        Every other failure propagates.

        Args:
            model_class: The model to register.
            config_instance: The configuration that supplies the admin class.
        """
        if model_class in admin.site._registry:
            return

        admin.site.register(model_class, config_instance.get_admin_class())

    def get_config(
        self,
        model_class: type[Model],
        config: ModelConfiguration | type[ModelConfiguration] | None = None,
    ) -> ModelConfiguration:
        """Build the configuration instance for a model.

        Args:
            model_class: The Django model class.
            config: A configuration class, an instance, or ``None`` for the
                registered configuration or a default one.

        Returns:
            The configuration instance.
        """
        if config is None:
            if model_class in self._registry:
                return self._registry[model_class]

            return ModelConfiguration(model_class)

        if isinstance(config, type):
            return config(model_class)

        return config


registry = FairDMRegistry()


def register(config_cls: type) -> type:
    """Register a Sample or Measurement model with its configuration.

    The configuration class must have a ``model`` attribute pointing to the Sample or
    Measurement subclass to register. A model that is not a concrete subclass of
    either raises ``ConfigurationError``.

    Usage:
        @fairdm.register
        class MySampleConfig(SampleConfig):
            model = MySample
            display_name = "My Sample Type"
            list_fields = ["name", "created"]

    Args:
        config_cls: The configuration class to register.

    Returns:
        The configuration class, unchanged.

    Raises:
        ValueError: The configuration class has no ``model`` attribute.
    """
    if not hasattr(config_cls, "model") or not config_cls.model:
        raise ValueError(
            f"Configuration class {config_cls.__name__} must specify a 'model' attribute "
            f"pointing to the Sample or Measurement subclass to register"
        )

    model_class = config_cls.model

    config_instance = config_cls() if isinstance(config_cls, type) else config_cls
    registry.register(model_class, config_instance)

    return config_cls


__all__ = [
    "FairDMRegistry",
    "register",
    "registry",
]
