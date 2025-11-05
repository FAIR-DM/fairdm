from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from fairdm.plugins import EXPLORE, register_plugin

from .models import Point


# LOCATION PLUGINS
@register_plugin
class PointOverview(UpdateView):
    category = EXPLORE
    model = Point
    menu_item = {"name": _("Overview"), "icon": "location"}
    sections = {
        "sidebar_primary": False,
        "sidebar_secondary": False,
        "header": False,
    }
