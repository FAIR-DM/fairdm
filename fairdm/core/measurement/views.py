"""Views for the Measurement app."""

from fairdm.plugins import PluginMixin

from .models import Measurement


class MeasurementDetailView(PluginMixin):
    """Measurement detail view with plugin support.

    Provides a detail page for Measurement instances that can be extended
    with registered plugins. The plugin system allows modular additions
    to the detail page without modifying the core view.

    Attributes:
        model: The Measurement model class
        template_name: Path to the detail template
    """

    model = Measurement
    template_name = "measurement/detail.html"
