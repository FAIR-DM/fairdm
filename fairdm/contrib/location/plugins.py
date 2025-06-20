from django.views.generic import UpdateView

from fairdm import plugins

from .models import Point


# LOCATION PLUGINS
@plugins.location.register()
class PointOverview(plugins.Explore, UpdateView):
    model = Point
    sections = {
        "sidebar_primary": False,
        "sidebar_secondary": False,
        "header": False,
    }
    menu_item = {
        "name": "Overview",
        "icon": "location",
    }
