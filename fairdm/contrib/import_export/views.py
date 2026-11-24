"""Views for importing and exporting dataset records, publishing, and package downloads."""

from io import StringIO

from django.http import Http404, JsonResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView, View
from django.views.generic.detail import SingleObjectMixin
from django_downloadview import VirtualDownloadView

from fairdm.contrib.import_export.utils import build_metadata
from fairdm.core.models import Dataset
from fairdm.forms import Form
from fairdm.utils.utils import user_guide

from .definitions import get_definition
from .utils import DataPackage


class DatasetPublishConfirm(FormView):
    """Ask the user to confirm publishing a dataset."""

    name = "get-published"
    title = _("Get Published")
    heading_config = {
        "title": _("Publish your dataset"),
        "description": _(
            "Get your dataset formally published. A data repository gives it a DOI (Digital Object Identifier), which you record on the dataset's identifiers page so that the dataset is discoverable and citable in the academic community."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/get-published"),
                "icon": "documentation",
            }
        ],
    }
    sections = {
        "components.form.default",
    }
    form_class = Form
    form_config = {
        "submit_button": {
            "text": _("Confirm submission"),
            "icon": "fa-solid fa-file-export",
        },
    }

    @staticmethod
    def check(request, instance, **kwargs):
        """Allow users holding the dataset's publish permission."""
        user = request.user
        if not user.is_authenticated:
            return False
        return user.has_perm(f"{instance._meta.app_label}.can_publish", instance)

    def get_context_data(self, **kwargs):
        """Add an empty confirmation form."""
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class()
        return context


class DatasetPackageDownloadView(SingleObjectMixin, VirtualDownloadView):
    """Download a dataset and its metadata as a ZIP package."""

    model = Dataset

    def get_file(self):
        """Build the ZIP package for the dataset."""
        return DataPackage(self.get_object(), self.request).build_package()

    def get_basename(self):
        """Name the file after the dataset."""
        return f"{self.get_object()}.zip"

    def get_content_type(self, file):
        """Return the ZIP MIME type."""
        return "application/zip"


class MetadataDownloadView(VirtualDownloadView):
    """Download a dataset's DataCite metadata as XML."""

    template_name = "publishing/datacite44.xml"

    def get_file(self):
        """Render the dataset's metadata XML."""
        return StringIO(build_metadata(self.get_object(), self.request))

    def get_basename(self):
        """Name the file after the dataset."""
        return f"{self.get_object()}.xml"


class TableSchemaView(View):
    """Download the Frictionless Table Schema of a type's file, open to everyone."""

    def get(self, request, name):
        """Answer with the type's Table Schema as a JSON file.

        Args:
            request: The request.
            name: The import definition's name, which is the type's model name.

        Returns:
            The JSON document as a download.

        Raises:
            Http404: No import definition has the name.
        """
        definition = get_definition(name)
        if definition is None:
            raise Http404(name)
        response = JsonResponse(
            definition.table_schema().as_frictionless(),
            json_dumps_params={"indent": 2},
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{name}-table-schema.json"'
        )
        return response
