from __future__ import annotations

from django.db.models.base import Model as Model

from .views import PluggableView


class PluginRegistry:
    """
    Central registry for managing plugins and their associated models.

    Usage:
        from fairdm import plugins

        @plugins.register(Project)
        class MyPlugin(plugins.Explore):
            menu_item = plugins.MenuItem(name="My Plugin", icon="view")
    """

    def __init__(self):
        # Maps models to their PluggableView classes
        self._model_view_registry: dict[type[Model], type[PluggableView]] = {}

    def register(self, *models: type[Model]):
        """
        Register a plugin with one or more models.

        Usage:
            # Single model
            @plugins.register(Project)
            class MyPlugin(FairDMPlugin):
                category = "explore"
                menu_item = PluginMenuItem(name="My Plugin", icon="view")

            # Multiple models
            @plugins.register(Project, Dataset, Sample, Measurement)
            class ContributorsPlugin(FairDMPlugin):
                category = "explore"
                menu_item = PluginMenuItem(name="Contributors", icon="people")

        Args:
            *models: One or more Django Model classes to register the plugin with

        Returns:
            A decorator function that registers the plugin class
        """

        def decorator(plugin_class):
            if not models:
                raise ValueError("plugins.register requires at least one model")

            # Validate all models first
            for model in models:
                if not (isinstance(model, type) and issubclass(model, Model)):
                    raise TypeError(f"plugins.register expects Django Model subclasses, got {type(model)}")

            # Register the plugin with each model
            registered_class = None
            for model in models:
                view_class = self.get_or_create_view_for_model(model)
                registered_class = view_class.register_plugin(plugin_class)

            # Return the last registered class (they should all be equivalent)
            return registered_class

        return decorator

    def get_or_create_view_for_model(self, model: type[Model]) -> type[PluggableView]:
        """
        Get or create a PluggableView subclass for the given model.

        This function maintains a registry of dynamically created view classes,
        one per model. If a view doesn't exist for the model yet, it creates one.

        Args:
            model: The Django model class to create/retrieve a view for

        Returns:
            A PluggableView subclass configured for the given model
        """
        if model not in self._model_view_registry:
            # Create a new PluggableView subclass for this model
            view_class = type(
                f"{model.__name__}DetailView",
                (PluggableView,),
                {
                    "base_model": model,
                    "model": model,
                },
            )
            self._model_view_registry[model] = view_class

        return self._model_view_registry[model]

    def get_view_for_model(self, model: type[Model]) -> type[PluggableView] | None:
        """
        Get the PluggableView for a model if it exists.

        Args:
            model: The Django model class

        Returns:
            The PluggableView subclass for the model, or None if not found
        """
        return self._model_view_registry.get(model)


# Global plugin registry instance
registry = PluginRegistry()

# Convenience alias for cleaner syntax: plugins.register(Model) instead of plugins.registry.register(Model)
register = registry.register
