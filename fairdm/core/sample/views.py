"""Views for the Sample app."""

from fairdm.plugins import PluginMixin

from .models import Sample


class SampleDetailView(PluginMixin):
    """Sample detail view with plugin support.

    Provides a detail page for Sample instances that can be extended
    with registered plugins. The plugin system allows modular additions
    to the detail page without modifying the core view.

    Attributes:
        model: The Sample model class
        template_name: Path to the detail template
    """

    model = Sample
    template_name = "sample/detail.html"
