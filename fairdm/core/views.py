from django.urls import path
from django.views.generic import RedirectView
from django_tables2.views import SingleTableMixin

from fairdm.contrib.import_export.utils import export_choices
from fairdm.menus import SiteNavigation
from fairdm.registry import registry
from fairdm.views import FairDMListView


class DataTableView(SingleTableMixin, FairDMListView):
    export_formats = ["csv", "xls", "xlsx", "json", "latex", "ods", "tsv", "yaml"]
    template_name_suffix = "_table"
    template_name = "fairdm/data_table.html"
    sections = {
        "header": "datatable.header",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registry"] = registry
        context["collection_menu"] = SiteNavigation.get("Data Collections")
        context["export_choices"] = export_choices
        return context

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

    @classmethod
    def get_urls(cls, **kwargs):
        """
        Return the URLs for the table view.
        """
        urls = []
        for item in [*registry.samples, *registry.measurements]:
            urls.append(
                path(
                    f"{item['type']}s/{item['slug']}/",
                    cls.as_view(model=item["class"], **kwargs),
                    name=f"{item['slug']}-collection",
                )
            )
        return urls


class CollectionRedirectView(RedirectView):
    """
    Redirects to the first registered collection.
    This is useful for the default view when no specific collection is requested.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Redirect to the first registered collection.
        """
        if not registry.samples or not registry.measurements:
            return "/"
        first_collection = registry.samples[0]
        return f"/{first_collection['type']}s/{first_collection['slug']}/"
