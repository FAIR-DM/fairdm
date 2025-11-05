"""Views for the Measurement app."""

from fairdm.plugins import PluginMixin

from .models import Measurement


class MeasurementDetailView(PluginMixin):
    """Measurement detail view with plugin support."""

    model = Measurement
    template_name = "measurement/detail.html"
