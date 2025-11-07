from dataclasses import dataclass, field
from typing import Any

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.utils import flatten
from django.forms import ModelForm
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django_filters import FilterSet
from django_tables2 import Table, table_factory
from import_export.resources import ModelResource

from fairdm.utils import factories
from fairdm.utils.utils import fairdm_fieldsets_to_django


@dataclass(frozen=True, kw_only=True)
class Authority:
    name: str
    """The name of the authority that created this metadata. This is required."""

    short_name: str = ""
    """The short name of the authority that created this metadata."""

    website: str = ""
    """The website of the authority that created this metadata."""


@dataclass(frozen=True, kw_only=True)
class Citation:
    text: str = ""
    """The citation for the data model."""

    doi: str = ""
    """The DOI for the citation."""


@dataclass
class ModelMetadata:
    """Structured metadata describing a registered model."""

    description: str = ""
    authority: Authority | None = None
    keywords: list[str] = field(default_factory=list)
    repository_url: str = ""
    citation: Citation | None = None
    maintainer: str = ""
    maintainer_email: str = ""


class ModelConfiguration:
    """Configuration for a registered model.

    This class uses declarative configuration similar to Django admin.
    Users can subclass this and define class attributes to configure their models.
    When custom class attributes are None, the get_* methods will auto-generate
    components using sensible defaults.
    """

    # Required attributes
    model = None
    metadata = None

    # Configurable UI/serialization/exchange attributes
    fields = []
    private_fields = []
    fieldsets = []

    # Field configuration for specific components
    # These allow fine-grained control over which fields are used for each component
    form_fields = None  # Fields for ModelForm generation
    filterset_fields = None  # Fields for FilterSet generation
    table_fields = None  # Fields for Table generation
    resource_fields = None  # Fields for import/export Resource generation
    serializer_fields = None  # Fields for DRF Serializer generation (when available)

    # Component classes (when None, auto-generate using field configs above)
    form_class = None
    filterset_class = None
    table_class = None
    resource_class = None
    serializer_class = None

    def __init__(self, model=None):
        # Allow model to be passed in constructor for backwards compatibility
        if model is not None:
            self.model = model

        # Use provided metadata or create empty one
        if self.metadata is None:
            self.metadata = ModelMetadata()

    @property
    def list_fields(self):
        """Backward compatibility: map to table_fields or general fields."""
        return self.table_fields or self.fields

    @list_fields.setter
    def list_fields(self, value):
        """Backward compatibility: set table_fields when list_fields is set."""
        self.table_fields = value

    @property
    def detail_fields(self):
        """Backward compatibility: map to form_fields or general fields."""
        return self.form_fields or self.fields

    @detail_fields.setter
    def detail_fields(self, value):
        """Backward compatibility: set form_fields when detail_fields is set."""
        self.form_fields = value

    @property
    def filter_fields(self):
        """Backward compatibility: map to filterset_fields or general fields."""
        return self.filterset_fields or self.fields

    @filter_fields.setter
    def filter_fields(self, value):
        """Backward compatibility: set filterset_fields when filter_fields is set."""
        self.filterset_fields = value

    def _get_class(self, class_or_path: str | type[Any]) -> type[Any]:
        if isinstance(class_or_path, str):
            return import_string(class_or_path)
        return class_or_path

    def get_list_fields(self):
        """Get fields for list views (tables). Uses table_fields, then general fields, then defaults."""
        return self.table_fields or self.fields or ["name", "created", "modified"]

    def get_detail_fields(self):
        """Get fields for detail forms. Uses form_fields, then general fields, then list_fields."""
        return self.form_fields or self.fields or self.get_list_fields()

    def get_filter_fields(self):
        """Get fields for filtering. Uses filterset_fields, then general fields, then defaults."""
        return self.filterset_fields or self.fields or ["created", "modified"]

    def get_flat_fields(self):
        # Type ignored: flatten expects Django model fields but we provide field names as strings
        return flatten(self.get_fields())  # type: ignore[arg-type]

    def get_fields(self):
        if not self.fields:
            return []

        if "id" not in self.fields:
            return ["id", "dataset", *self.fields]
        return self.fields

    def get_fieldsets(self):
        if self.fieldsets and isinstance(self.fieldsets, dict):
            return fairdm_fieldsets_to_django(self.fieldsets)
        elif self.fieldsets and isinstance(self.fieldsets, list):
            return self.fieldsets
        elif self.fields:
            return [(None, {"fields": self.fields})]
        return None

    def get_filterset_class(self) -> type[FilterSet]:
        if self.filterset_class is not None:
            return self._get_class(self.filterset_class)
        # Use filterset_fields if specified, otherwise use general fields, or default to model fields
        fields = self.filterset_fields or self.fields or "__all__"
        return factories.filterset_factory(self.model, fields=fields)

    def get_form_class(self) -> type[ModelForm]:
        if self.form_class is not None:
            return self._get_class(self.form_class)
        # Use form_fields if specified, otherwise use general fields, or default to "__all__"
        fields = self.form_fields or self.fields or "__all__"
        return factories.modelform_factory(self.model, fields=fields)

    def get_table_class(self) -> type[Table]:
        if self.table_class is not None:
            return self._get_class(self.table_class)

        # Use table_fields if specified, otherwise use general fields
        if self.table_fields:
            return table_factory(self.model, fields=self.table_fields)
        elif self.fields:
            return table_factory(self.model, fields=self.fields)
        else:
            # Default behavior with exclusions
            kwargs = {
                "exclude": [
                    "polymorphic_ctype",
                    "sample_ptr",
                    "measurement_ptr",
                    "image",
                    "keywords",
                    "created",
                    "modified",
                    "options",
                    "tags",
                ],
            }
            return table_factory(self.model, exclude=kwargs["exclude"])

    def get_resource_class(self) -> type[ModelResource]:
        if self.resource_class is not None:
            return self._get_class(self.resource_class)

        # Use resource_fields if specified, otherwise use general fields
        if self.resource_fields:
            return factories.modelresource_factory(self.model, fields=self.resource_fields)
        elif self.fields:
            return factories.modelresource_factory(self.model, fields=self.fields)
        else:
            # Default behavior with exclusions
            kwargs = {
                "exclude": [
                    "polymorphic_ctype",
                    "sample_ptr",
                    "image",
                    "keywords",
                    "created",
                    "modified",
                    "options",
                    "tags",
                ],
            }
            return factories.modelresource_factory(self.model, exclude=kwargs["exclude"])

    def get_serializer_class(self) -> type[Any] | None:
        """Get the serializer class for the model, if DRF is available."""
        if self.serializer_class is not None:
            return self._get_class(self.serializer_class)

        # Check if DRF is available and if we have a factory for it
        try:
            import importlib.util

            if importlib.util.find_spec("rest_framework") is None:
                return None
            if not hasattr(factories, "modelserializer_factory"):
                return None
        except ImportError:
            return None

        # Use serializer_fields if specified, otherwise use general fields
        # fields = self.serializer_fields or self.fields or "__all__"
        # TODO: Implement modelserializer_factory when DRF support is added
        # return factories.modelserializer_factory(self.model, fields=fields)
        return None


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
        self._registry = {}
        self.all = []
        self._config_registry = {}
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
            dict or None: The registry entry dictionary for the model, or None if not found.
                         The dictionary contains keys: 'app_label', 'model', 'class',
                         'verbose_name', 'verbose_name_plural', 'type', 'config'

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
        Retrieves all registered models categorized as 'sample'.

        Returns:
            list[dict]: A list of models with type 'sample'.
        """
        return [item for item in self.all if item["type"] == "sample"]

    @property
    def measurements(self):
        """
        Retrieves all registered models categorized as 'measurement'.

        Returns:
            list[dict]: A list of models with type 'measurement'.
        """
        return [item for item in self.all if item["type"] == "measurement"]

    def register(self, model_class, config=None):
        """
        Registers a Sample or Measurement subclass with associated configuration.

        Args:
            model_class (django.db.models.Model): The Django model class to register.
                Must be a subclass of Sample or Measurement.
            config (type, optional): Configuration class for the model.

        The registered model metadata includes:
        - `app_label`: The app label of the model.
        - `model`: The model name.
        - `class`: The model class itself.
        - `verbose_name`: The human-readable name of the model.
        - `verbose_name_plural`: The plural version of the verbose name.
        - `type`: The classification type of the model (sample or measurement).
        - `config`: The configuration instance for auto-generation.

        Raises:
            TypeError: If model_class is not a Sample or Measurement subclass.
        """
        # Validate that this is a Sample or Measurement subclass
        self._validate_model_class(model_class)

        # Check if already registered
        if model_class in self._registry:
            return  # Skip if already registered

        self.register_actstream(model_class)
        self.register_admin(model_class)

        # Get or create configuration
        config_instance = self.get_config(model_class, config)

        mtype = getattr(model_class, "type_of", None)
        if mtype is not None:
            mtype = mtype.__name__.lower()

        opts = model_class._meta
        item = {
            "app_label": opts.app_label,
            "class": model_class,
            "config": config_instance,
            "full_name": f"{opts.app_label}.{opts.model_name}",
            "model": opts.model_name,
            "path": f"{model_class.__module__}.{model_class.__name__}",
            "type": mtype,
            "verbose_name": opts.verbose_name,
            "verbose_name_plural": opts.verbose_name_plural,
            "slug": slugify(opts.verbose_name),
            "slug_plural": slugify(opts.verbose_name_plural),
        }
        self._registry[model_class] = item
        self.all.append(item)

    def register_actstream(self, model_class):
        from actstream import registry as actstream_registry

        actstream_registry.register(model_class)

    def register_admin(self, model_class):
        try:
            from fairdm.contrib.admin.admin import SampleAdmin

            admin.site.register(model_class, SampleAdmin)
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
            "total_registered": len(self.all),
            "samples": {
                "count": len(samples),
                "models": [
                    {
                        "name": item["class"].__name__,
                        "app": item["app_label"],
                        "verbose_name": item["verbose_name"],
                        "display_name": getattr(item["config"], "display_name", "N/A"),
                    }
                    for item in samples
                ],
            },
            "measurements": {
                "count": len(measurements),
                "models": [
                    {
                        "name": item["class"].__name__,
                        "app": item["app_label"],
                        "verbose_name": item["verbose_name"],
                        "display_name": getattr(item["config"], "display_name", "N/A"),
                    }
                    for item in measurements
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
                for model in summary["samples"]["models"]:
                    print(f"  • {model['name']} ({model['app']})")
                    print(f"    Display: {model['display_name']}")
                    print(f"    Verbose: {model['verbose_name']}")
                    print()
            else:
                print("  No samples registered")

            print(f"📊 MEASUREMENTS ({summary['measurements']['count']})")
            print("-" * 40)
            if summary["measurements"]["models"]:
                for model in summary["measurements"]["models"]:
                    print(f"  • {model['name']} ({model['app']})")
                    print(f"    Display: {model['display_name']}")
                    print(f"    Verbose: {model['verbose_name']}")
                    print()
            else:
                print("  No measurements registered")

            print("=" * 60)

        return summary

    def get_config(self, model_class, config):
        """
        Builds a configuration instance from the registered config class.
        Handles auto-generation of forms, serializers, filters, and tables.
        """
        if config is None:
            # Try to get from _fairdm attribute first
            existing_config = getattr(model_class, "_fairdm", None)
            if existing_config is not None and hasattr(existing_config, "config"):
                return existing_config.config

            # Check if we have a stored config class
            if model_class in self._config_registry:
                config_cls = self._config_registry[model_class]
                return config_cls(model_class)

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
                list_fields = ["name", "location", "collected_at"]
                detail_fields = ["name", "description", "metadata"]
                filter_fields = ["collected_at", "contributor"]
        """

        def _register(config_cls):
            # Store config class for later instantiation
            self._config_registry[model_class] = config_cls
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
    "Authority",
    "Citation",
    "FairDMRegistry",
    "ModelConfiguration",
    "ModelMetadata",
    "register",
    "registry",
]
