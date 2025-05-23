from django.views.generic import UpdateView

from fairdm.plugins import GenericPlugin, register

from .models import Point


# LOCATION PLUGINS
@register(["location"])
class PointOverview(GenericPlugin, UpdateView):
    model = Point
    template_name = "fairdm/plugins/overview.html"
    icon = "location"
    # base_template = "location/location_detail.html"
    # template_name = "fairdm/plugins/map.html"
