"""Views for the Sample app."""

from fairdm.plugins import PluginMixin

from .models import Sample


class SampleDetailView(PluginMixin):
    """Sample detail view with plugin support."""

    model = Sample
    template_name = "sample/detail.html"
