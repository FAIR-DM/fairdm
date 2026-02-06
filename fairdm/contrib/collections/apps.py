from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from fairdm.menus import AppMenu


class CollectionsConfig(AppConfig):
    """Configuration for the Collections app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.collections"
    label = "collections"
    verbose_name = _("Collections")

    def ready(self) -> None:
        """Initialize the collections app."""
        self.populate_data_collection_menu()
        return super().ready()

    def populate_data_collection_menu(self):
        """
        Populates the data collection menu with sample and measurement collection links.
        This function is called during the `CollectionsConfig.ready` method.
        """
        from flex_menu import MenuItem

        from fairdm.registry import registry

        # Get the "Data" menu item using the proper API
        sample_menu = AppMenu.get("Samples")

        for model_class in registry.samples:
            config = registry.get_for_model(model_class)
            sample_menu.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-collection",
                )
            )

        measurement_menu = AppMenu.get("Measurements")

        for model_class in registry.measurements:
            config = registry.get_for_model(model_class)
            measurement_menu.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-collection",
                )
            )
