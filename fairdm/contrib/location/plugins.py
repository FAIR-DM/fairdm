from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin

from .models import Point


# LOCATION PLUGINS
@plugins.register(Point, label=_("Overview"), icon="location", order=0)
class PointOverview(Plugin, UpdateView):
    model = Point
    sections = {
        "sidebar_primary": False,
        "sidebar_secondary": False,
        "header": False,
    }
