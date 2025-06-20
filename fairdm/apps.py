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

        self.update_drf_field_mapping()
        self.populate_data_collection_menu()
        return super().ready()

    def update_drf_field_mapping(self):
        """
        Updates the default field mapping of Django Rest Framework's ModelSerializer to include proper serializers for
        some of the custom model fields included in FairDM. Doing this means that we don't have to specify the
        serializer for these fields every time we create a new serializer.

        Note: At the moment, `QuantityField` serializer is used for all `QuantityField` types. However, this will need to be updated if non-readonly models are to be supported.

        This function is called during the `FairDMConfig.ready` method.
        """

        from rest_framework.serializers import ModelSerializer

        from fairdm.contrib.api import fields
        from fairdm.db import models

        # if settings.GIS_ENABLED:
        #     from django.contrib.gis.db import models as gis_models
        #     from rest_framework_gis.fields import GeometryField

        #     ModelSerializer.serializer_field_mapping.update(
        #         {
        #             gis_models.PointField: GeometryField,
        #         }
        #     )

        # at the moment we are using the QuantifyField serializer for all QuantityField types
        # however, we will need to update this if we want to support non-readonly models
        ModelSerializer.serializer_field_mapping.update(
            {
                models.QuantityField: fields.QuantityField,
                models.DecimalQuantityField: fields.QuantityDecimalField,
                models.IntegerQuantityField: fields.QuantityField,
                models.BigIntegerQuantityField: fields.QuantityField,
                models.PositiveIntegerQuantityField: fields.QuantityField,
            }
        )

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
