"""Views for the Measurement app."""

from fairdm.plugins import PluggableView

from .models import Measurement


class MeasurementDetailView(PluggableView):
    """Measurement detail view with plugin support.

    Provides a detail page for Measurement instances that can be extended
    with registered plugins. The plugin system allows modular additions
    to the detail page without modifying the core view.

    Attributes:
        model: The Measurement model class
        template_name: Path to the detail template
    """

    base_model = Measurement
