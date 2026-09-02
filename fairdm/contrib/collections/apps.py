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
        from mvp.menus import MenuCollapse

        from fairdm.registry import registry

        # Get-or-create, mirroring fairdm/contrib/plugins/registration.py:148-157 - a
        # renamed or absent node must not raise here (research.md R8).
        sample_menu = AppMenu.get("Samples")
        if sample_menu is None:
            sample_menu = MenuCollapse(name=_("Samples"))
            AppMenu.append(sample_menu)
        # `_check`, not `check`: `check` is a bound method on MenuItem, and the
        # per-request copy flex_menu builds reads `_check`, not `check` - assigning to
        # `check` would shadow the method rather than feed the copy. A childless
        # container is not auto-hidden by flex_menu (it only suppresses a parent that
        # HAD children which all resolved invisible), so this is the only thing
        # standing between an empty registry and a visible, empty heading (FR-040).
        sample_menu._check = lambda request, **kwargs: bool(registry.samples)

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
            AppMenu.append(measurement_menu)
        measurement_menu._check = lambda request, **kwargs: bool(registry.measurements)

        for model_class in registry.measurements:
            config = registry.get_for_model(model_class)
            measurement_menu.append(
                MenuItem(
                    name=config.get_verbose_name_plural(),
                    view_name=f"{config.get_slug()}-list",
                )
            )
