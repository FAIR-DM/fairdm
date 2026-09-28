"""App configuration for collections."""

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
        """Add the sample and measurement listings to the data menu."""
        self.populate_data_collection_menu()
        return super().ready()

    def populate_data_collection_menu(self):
        """Add a menu entry for every registered sample and measurement type."""
        from flex_menu import MenuItem
        from mvp.menus import MenuCollapse

        from fairdm.registry import registry

        # A node declared in `fairdm/menus/menus.py` carries its own emptiness check. One created
        # here is a node the portal renamed or removed, so it needs the check supplied.
        # `_check`, not `check`: flex_menu's per-request copy reads `_check`.
        sample_menu = AppMenu.get("Samples")
        if sample_menu is None:
            sample_menu = MenuCollapse(name=_("Samples"))
            sample_menu._check = lambda request, **kwargs: bool(registry.samples)
            AppMenu.append(sample_menu)

        for model_class in registry.samples:
            config = registry.get_for_model(model_class)
            sample_menu.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-list",
                )
            )

        measurement_menu = AppMenu.get("Measurements")
        if measurement_menu is None:
            measurement_menu = MenuCollapse(name=_("Measurements"))
            measurement_menu._check = lambda request, **kwargs: bool(
                registry.measurements
            )
            AppMenu.append(measurement_menu)

        for model_class in registry.measurements:
            config = registry.get_for_model(model_class)
            measurement_menu.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-list",
                )
            )
