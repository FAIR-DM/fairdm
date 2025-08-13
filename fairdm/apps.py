from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import gettext_lazy as _


class FairDMConfig(AppConfig):
    name = "fairdm"

    def ready(self) -> None:
        # adds a default renderer to all forms to keep a consistent look across the site. This way we don't have to specify it every time
        # patch django-filters to not use crispy forms. should be safe to remove on the
        # next release of fairdm

        autodiscover_modules("config")
        autodiscover_modules("plugins")

        from django_filters import compat

        compat.is_crispy = lambda: False

        self.populate_data_collection_menu()
        return super().ready()

    def populate_data_collection_menu(self):
        """
        Populates the data collection menu with sample types and their respective views.
        This function is called during the `FairDMConfig.ready` method.
        """
        from fairdm.menus import DropdownHeader, SiteNavigation, get_measurement_menu_items, get_sample_menu_items

        SiteNavigation.get("Data").get("Data Collections").children = [
            DropdownHeader(_("Sample Collections")),
            *get_sample_menu_items(),
            DropdownHeader(_("Measurement Collections")),
            *get_measurement_menu_items(),
        ]

        # print(SiteNavigation.get("DataCollectionsMenu").children)
