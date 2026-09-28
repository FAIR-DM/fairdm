"""Admin mixin for models with a point geometry."""

from django.contrib.gis import admin

from .functions import Lat, Lon


class SiteAdminMixin(admin.GISModelAdmin):
    """GIS admin that shows the location on a map."""

    geom_field = "point"

    def get_queryset(self, request):
        """Annotate ``lat`` and ``lon`` from the geometry field."""
        qs = super().get_queryset(request)
        if "__" in self.geom_field:
            qs = qs.select_related(self.geom_field.split("__")[0])
        return qs.annotate(lat=Lat(self.geom_field), lon=Lon(self.geom_field))
