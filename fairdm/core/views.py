from functools import cached_property

from django_tables2.views import SingleTableMixin

from fairdm.contrib.import_export.utils import export_choices
from fairdm.registry import registry
from fairdm.views import FairDMListView


class DataTableView(SingleTableMixin, FairDMListView):
    export_formats = ["csv", "xls", "xlsx", "json", "latex", "ods", "tsv", "yaml"]
    template_name_suffix = "_table"
    template_name = "fairdm/data_table.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registry"] = registry
        context["export_choices"] = export_choices
        return context

    def get_card(self):
        return False

    @cached_property
    def model(self):
        self.dtype = self.request.GET.get("type")

        if not self.dtype:
            # Default to the first registered model if no type is provided
            if not registry.all:
                raise ValueError("No models are registered in the FairDMRegistry.")
            self.meta = registry.samples[0]
            self.dtype = f"{self.meta['app_label']}.{self.meta['model']}"  # Ensures dtype is still assigned
        else:
            # Retrieve the model metadata from the registry
            result = registry.get(*self.dtype.split("."))
            if not result:
                raise ValueError(f"This data type is not supported: {self.dtype}")
            self.meta = result[0]

        return self.meta["class"]

    def get_table_class(self):
        """
        Return the class to use for the table.
        """
        return self.model.config.get_table_class()

    def get_table_kwargs(self):
        """
        Return the keyword arguments for instantiating the table.

        Allows passing customized arguments to the table constructor, for example,
        to remove the buttons column, you could define this method in your View::

            def get_table_kwargs(self):
                return {"exclude": ("buttons",)}
        """
        return {
            "exclude": [
                "polymorphic_ctype",
                "measurement_ptr",
                "sample_ptr",
                "options",
                "image",
                "created",
                "modified",
            ],
        }

    def get_file(self):
        """Return :class:`django.core.files.base.ContentFile` object."""
        resource_class = self.model._fairdm.config.get_resource_class()
        dataset = resource_class().export(queryset=self.get_queryset())
        self.export_type = self.request.GET.get("_export")
        return dataset.export(self.export_type)

    def get_basename(self):
        return f"{self.model._meta.verbose_name_plural}.csv"

    def get_content_type(self, file):
        """Define the MIME type for the ZIP file."""
        return "text/csv"
