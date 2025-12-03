from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from fairdm import plugins

from .models import Point


# LOCATION PLUGINS
@plugins.register
class PointOverview(UpdateView):
    model = Point
    menu_item = plugins.PluginMenuItem(name=_("Overview"), category=plugins.EXPLORE, icon="location")
    sections = {
        "sidebar_primary": False,
        "sidebar_secondary": False,
        "header": False,
    }
