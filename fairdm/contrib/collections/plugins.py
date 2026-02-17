from django.utils.translation import gettext_lazy as _

from fairdm.contrib.plugins import Plugin

from .views import DataTableView


class DataTablePlugin(Plugin, DataTableView):
    """
    Plugin for displaying tabular data collections for Sample and Measurement sub-types.

    This plugin provides a comprehensive table view with filtering, sorting, pagination,
    and export capabilities for all registered Sample and Measurement models.
    """

    title = _("Data")
    menu = {"label": _("Data"), "icon": "table", "order": 50}

    def get_queryset(self, *args, **kwargs):
        # return self.object.samples.instance_of(self.model)
        if hasattr(self.model, "sample_ptr"):
            return self.model.objects.filter(dataset=self.object)
        elif hasattr(self.model, "measurement_ptr"):
            return self.model.objects.filter(sample__dataset=self.object)

        return super().get_queryset(*args, **kwargs)

        # return self.model.objects.filter(dataset=self.base_object)
