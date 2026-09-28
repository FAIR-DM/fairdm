"""Views for importing and exporting dataset records, publishing, and package downloads."""

from io import StringIO

from braces.views import MessageMixin
from django import forms
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django_downloadview import VirtualDownloadView

from fairdm.contrib.import_export.utils import build_metadata
from fairdm.core.models import Dataset
from fairdm.forms import Form
from fairdm.registry import registry
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMModelFormMixin

from .forms import ExportForm, ImportForm
from .utils import DataPackage, get_export_formats, get_import_formats


class BaseImportExportView(MessageMixin, FormView):
    """Base view for importing and exporting a dataset's records with django-import-export.

    Attributes:
        from_encoding: Encoding used to read uploaded text files.
        model: The model whose records are imported and exported.
        form_class: The form class, set by subclasses.
        success_url: Where to send the user after success, set by subclasses.
        import_kwargs: Default keyword arguments for the import.
    """

    from_encoding = "utf-8-sig"
    model = Dataset
    form_class = None
    success_url = None
    import_kwargs = {}

    def get_context_data(self, **kwargs):
        """Add the formats, the data type, the import result and which error details to show."""
        context = super().get_context_data()
        context["export_formats"] = self.export_formats
        context["import_formats"] = self.import_formats
        context["data_type"] = self.get_resource_model()._meta.verbose_name_plural
        context["result"] = kwargs.get("result")
        context["import_error_display"] = ["message"]
        if self.request.user.is_superuser:
            context["import_error_display"].extend(["row", "traceback"])
        return context

    @property
    def export_formats(self):
        """Map each export format's title to its format class."""
        return {fmat().get_title(): fmat for fmat in get_export_formats()}

    @property
    def import_formats(self):
        """Map each import format's title to its format class."""
        return get_import_formats()

    def dispatch(self, request, *args, **kwargs):
        """Resolve the model being imported or exported before handling the request."""
        self.resource_model = self.get_resource_model()
        return super().dispatch(request, *args, **kwargs)

    def get_resource(self):
        """Return the resource for the resolved model, bound to the current dataset.

        Returns:
            An instance of the model's registered resource class.
        """
        from fairdm.registry import registry

        config = registry.get_for_model(self.resource_model)
        return config.get_resource_class()(dataset=self.get_object())

    def get_resource_model(self):
        """Resolve the model class named by the ``type`` query parameter.

        Without a ``type`` the first registered sample model is used.

        Returns:
            The model class for the requested type.

        Raises:
            ValueError: No models are registered, or ``type`` matches none.
        """
        self.dtype = self.request.GET.get("type")

        if not self.dtype:
            if not registry.all:
                raise ValueError("No models are registered in the FairDMRegistry.")
            self.meta = registry.samples[0]
            self.dtype = f"{self.meta['app_label']}.{self.meta['model']}"
        else:
            result = registry.get_for_model(self.dtype)
            if not result:
                raise ValueError(f"This data type is not supported: {self.dtype}")
            self.meta = result

        return self.meta["class"]

    def get_resource_qs(self):
        """Return the current dataset's records of the resolved model.

        Returns:
            A queryset filtered to the current dataset.
        """
        return self.resource_model.objects.filter(dataset=self.get_object())

    def get_dataset_format(self, file):
        """Choose the import format from the uploaded file's extension.

        Args:
            file: The uploaded file.

        Returns:
            An instance of the matching import format.

        Raises:
            ValueError: The extension matches no import format.
        """
        extension = file.name.split(".")[-1].lower()
        fmt = self.import_formats.get(extension)
        if fmt is None:
            raise ValueError(f"Unsupported file format: {extension}")
        return fmt(encoding=self.from_encoding)

    def result_has_errors(self, result, form):
        """Re-render the form with the import errors listed.

        Args:
            result: The failed import result.
            form: The submitted form.

        Returns:
            The rendered response.
        """
        context = self.get_context_data(form=form, result=result)
        context["about"] = [
            _(
                "The import process encountered errors. Please review the details below and correct any issues in your data file before reuploading."
            )
        ]
        return self.render_to_response(context)

    def form_invalid(self, form):
        """Re-render the invalid form."""
        return super().form_invalid(form)

    def get_import_kwargs(self):
        """Return the keyword arguments passed to the resource's import, for subclasses to customise.

        Returns:
            A copy of ``import_kwargs``.
        """
        return self.import_kwargs.copy()


class DataImportView(BaseImportExportView):
    """Import records from an uploaded spreadsheet into the current dataset."""

    name = "import"
    title = _("Import Data")
    heading_config = {
        "title": _("Import Data"),
        "description": _(
            "The data import workflow allows you to upload existing data files in spreadsheet format which are then processed and integrated into the current dataset. To ensure smooth operation, your data are expected to conform to a predetermined template. To download the template, select your data type below and click the 'Download Template' button. After filling in the template, you can upload it here to import your data."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/import"),
                "icon": "documentation",
            }
        ],
    }
    sections = {
        "components.form.default",
    }
    form_class = ImportForm
    template_name = "import_export/import.html"
    import_kwargs = {
        "dry_run": False,
        "raise_errors": False,
        "rollback_on_validation_errors": True,
    }

    @staticmethod
    def check(request, instance, **kwargs):
        """Allow users holding the dataset's import permission."""
        user = request.user
        if not user.is_authenticated:
            return False
        # The object-level permission backend answers False for a codename without its app label.
        return user.has_perm(f"{instance._meta.app_label}.import_data", instance)

    def form_valid(self, form):
        """Import the uploaded file and report success or re-render with the errors."""
        file = form.cleaned_data["file"]
        result = self.handle_import(file)

        if (result and result.has_errors()) or result.has_validation_errors():
            self.messages.error("There were errors in the import.")
            return self.result_has_errors(result, form)
        else:
            self.messages.success("Data imported successfully.")

        return super().form_valid(form)

    def handle_import(self, file):
        """Import the rows of an uploaded file into the current dataset.

        Args:
            file: The uploaded file.

        Returns:
            The import result, or None when the file's format cannot be resolved.
        """
        resource = self.get_resource()
        input_format = self.get_dataset_format(file)
        if not input_format:
            return None

        None if input_format.is_binary() else self.from_encoding
        file_content = file.read()

        dataset = input_format.create_dataset(file_content)
        print(self.get_import_kwargs())
        return resource.import_data(dataset, **self.get_import_kwargs())

    def get_success_url(self):
        """Send the user back to the dataset."""
        return self.get_object().get_absolute_url()


class DatasetPublishConfirm(FairDMModelFormMixin, FormView):
    """Ask the user to confirm publishing a dataset."""

    name = "get-published"
    title = _("Get Published")
    heading_config = {
        "title": _("Publish your dataset"),
        "description": _(
            "Get your dataset formally published and receive a DOI (Digital Object Identifier) for it. This process ensures that your dataset is discoverable and citable in the academic community."
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
        # See DataImportView.check on the app label.
        return user.has_perm(f"{instance._meta.app_label}.can_publish", instance)

    def get_context_data(self, **kwargs):
        """Add an empty confirmation form."""
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class()
        return context


@method_decorator(require_POST, name="dispatch")
class DataExportView(VirtualDownloadView, BaseImportExportView):
    """Download the current dataset's records, or an empty template, in the chosen format."""

    form_class = ExportForm

    def get_file(self):
        """Export the records, or only the column headings when ``template`` is posted."""
        qs = (
            self.resource_model.objects.none()
            if self.request.POST.get("template")
            else self.get_resource_qs()
        )

        tablib_dataset = self.get_resource().export(queryset=qs)
        return ContentFile(
            content=tablib_dataset.export(self.format),
            name=self.get_basename(),
        )

    def post(self, request, *args, **kwargs):
        """Stream the export file in the submitted format.

        Args:
            request: The POST request carrying the format.
            *args: Unused.
            **kwargs: Unused.

        Returns:
            The file response.

        Raises:
            ValueError: The submitted format is not valid.
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            self.format = form.cleaned_data["format"]
            self.format_class = self.get_format()
            return self.render_to_response(
                content_type=self.format_class.get_content_type()
            )

        raise ValueError(f"Unsupported export format {self.request.GET.get('format')}.")

    def get_basename(self):
        """Name the file after the model and the chosen format."""
        return f"{self.resource_model._meta.verbose_name_plural}.{self.format_class.get_extension()}"

    def get_format(self):
        """Return an instance of the chosen export format.

        Returns:
            The export format for the submitted format title.
        """
        return self.export_formats[self.format]()


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


class UploadForm(forms.Form):
    """Form with a single field for an uploaded file."""

    docfile = forms.FileField(label="Select a file")
