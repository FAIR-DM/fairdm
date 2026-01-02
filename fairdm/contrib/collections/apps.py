from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


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

        from fairdm.menus import SiteNavigation
        from fairdm.registry import registry

        # Get the "Data" menu item using the proper API
        data_menu = SiteNavigation.get("Data")
        if not data_menu:
            return

        # Get the "Data Collections" header using the proper API
        collections_header = data_menu.get("Data Collections")
        if not collections_header:
            return

        sample_collection = MenuItem(
            name=_("Sample Collections"),
            extra_context={"icon": "sample"},
        )

        for model_class in registry.samples:
            config = registry.get_for_model(model_class)
            sample_collection.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-collection",
                )
            )

        measurement_collection = MenuItem(
            name=_("Measurement Collections"),
            extra_context={"icon": "measurement"},
        )

        for model_class in registry.measurements:
            config = registry.get_for_model(model_class)
            measurement_collection.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-collection",
                )
            )

        data_menu.append(sample_collection)
        data_menu.append(measurement_collection)
