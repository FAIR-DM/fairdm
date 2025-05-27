from django.views.generic import UpdateView

from fairdm import plugins

from .models import Point


# LOCATION PLUGINS
@plugins.location.register()
class PointOverview(plugins.Explore, UpdateView):
    model = Point
    template_name = "fairdm/plugins/overview.html"
    menu_item = {
        "name": "Overview",
        "icon": "location",
    }
    # base_template = "location/location_detail.html"
    # template_name = "fairdm/plugins/map.html"
