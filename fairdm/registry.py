from django.apps import apps
from django.contrib import admin
from django.utils.text import slugify


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
            # Model already registered or admin not available
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
            from fairdm.metadata import ModelConfig

            return ModelConfig(model_class)

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
