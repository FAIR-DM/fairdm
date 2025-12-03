from django.utils.translation import gettext_lazy as _

from fairdm.plugins import EXPLORE, FairDMPlugin, PluginMenuItem

from .views import DataTableView


class DataTablePlugin(FairDMPlugin, DataTableView):
    """
    Plugin for displaying tabular data collections for Sample and Measurement sub-types.

    This plugin provides a comprehensive table view with filtering, sorting, pagination,
    and export capabilities for all registered Sample and Measurement models.
    """

    title = _("Data")
    menu_item = PluginMenuItem(name=_("Data"), category=EXPLORE, icon="table")

    def get_queryset(self, *args, **kwargs):
        # return self.base_object.samples.instance_of(self.model)
        if hasattr(self.model, "sample_ptr"):
            return self.model.objects.filter(dataset=self.base_object)
        elif hasattr(self.model, "measurement_ptr"):
            return self.model.objects.filter(sample__dataset=self.base_object)

        return super().get_queryset(*args, **kwargs)

        # return self.model.objects.filter(dataset=self.base_object)
