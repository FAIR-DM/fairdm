"""Views for the Sample app."""

from fairdm.plugins import PluggableView

from .models import Sample


class SampleDetailView(PluggableView):
    """Sample detail view with plugin support.

    Provides a detail page for Sample instances that can be extended
    with registered plugins. The plugin system allows modular additions
    to the detail page without modifying the core view.

    Attributes:
        model: The Sample model class
        template_name: Path to the detail template
    """

    base_model = Sample

    def get_meta_title(self, context):
        return f"{self.base_model._meta.verbose_name} - {self.base_object!s}"
