"""Format lookups, metadata rendering and ZIP packaging for exports."""

import io
import zipfile

from defusedxml.minidom import parseString
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from import_export.formats.base_formats import DEFAULT_FORMATS


def get_formats():
    """Return the available import and export formats.

    Returns:
        The ``IMPORT_EXPORT_FORMATS`` setting, or the library defaults.
    """
    return getattr(settings, "IMPORT_EXPORT_FORMATS", DEFAULT_FORMATS)


def get_export_formats():
    """Return the available export formats.

    Returns:
        The ``EXPORT_FORMATS`` setting, or all available formats.
    """
    return getattr(settings, "EXPORT_FORMATS", get_formats())


def get_import_formats():
    """Return the formats that can be imported.

    Returns:
        A map of format title to format class.
    """
    formats = getattr(settings, "IMPORT_FORMATS", get_formats())
    return {f().get_title(): f for f in formats if f().can_import()}


export_choices = {
    f().get_title(): f().get_title() for f in get_export_formats() if f().can_export()
}

import_choices = {f: f for f in get_import_formats()}


def build_metadata(dataset, request):
    """Render a dataset's DataCite metadata as indented XML.

    Args:
        dataset: The dataset to describe.
        request: The current request, used to build the dataset's absolute URL.

    Returns:
        The pretty-printed XML.
    """
    template_name = "publishing/datacite44.xml"
    uri = request.build_absolute_uri(dataset.get_absolute_url())
    xml = render_to_string(
        template_name, {"dataset": dataset, "uri": uri}, request=request
    )
    dom = parseString(xml)
    return dom.toprettyxml(indent="  ")


def build_export_for_datatype(dataset, queryset, fmt="csv"):
    """Export a queryset of one data type for inclusion in a ZIP file.

    Args:
        dataset: The dataset the records belong to.
        queryset: The records to export.
        fmt: The tablib export format.

    Returns:
        The exported data.
    """
    from fairdm.registry import registry

    model = queryset.model
    resource = registry.get_for_model(model).get_resource_class()(dataset=dataset)
    tablib_dataset = resource.export(queryset=queryset)
    return tablib_dataset.export(fmt)


class DataPackage:
    """Build a ZIP package holding a dataset's licence, readme, metadata and records.

    Args:
        dataset: The dataset to package.
        request: The current request.
    """

    def __init__(self, dataset, request):
        self.dataset = dataset
        self.request = request

    def build_package(self):
        """Build the ZIP package.

        Returns:
            A rewound buffer holding the ZIP.
        """
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            self.add_license(zip_file)
            self.add_readme(zip_file)
            self.add_metadata(zip_file)
            self.add_samples(zip_file)
            self.add_measurements(zip_file)

        buffer.seek(0)
        return buffer

    def add_license(self, zip_file):
        """Add the dataset's licence text, if it has a licence.

        Args:
            zip_file: The open ZIP file.
        """
        if self.dataset.license:
            zip_file.writestr("license.txt", self.dataset.license.text)

    def add_readme(self, zip_file):
        """Add a readme file.

        Args:
            zip_file: The open ZIP file.
        """
        zip_file.writestr("readme.txt", "This is a dynamically generated ZIP file.")

    def add_metadata(self, zip_file):
        """Add the dataset's XML metadata.

        Args:
            zip_file: The open ZIP file.
        """
        zip_file.writestr("metadata.xml", build_metadata(self.dataset, self.request))

    def add_samples(self, zip_file):
        """Add one CSV per sample type in the dataset.

        Args:
            zip_file: The open ZIP file.
        """
        sample_types = self.dataset.samples.values_list("polymorphic_ctype", flat=True)

        ctypes = ContentType.objects.filter(id__in=sample_types)

        for model_ctype in ctypes:
            model = model_ctype.model_class()
            qs = model.objects.filter(dataset=self.dataset)
            export = build_export_for_datatype(self.dataset, qs)
            zip_file.writestr(f"samples/{model._meta.verbose_name_plural}.csv", export)

    def add_measurements(self, zip_file):
        """Add one CSV per measurement type in the dataset.

        Args:
            zip_file: The open ZIP file.
        """
        measurements = self.dataset.measurements.values_list(
            "polymorphic_ctype", flat=True
        )

        ctypes = ContentType.objects.filter(id__in=measurements)

        for model_ctype in ctypes:
            model = model_ctype.model_class()
            qs = model.objects.filter(dataset=self.dataset)
            export = build_export_for_datatype(self.dataset, qs)
            zip_file.writestr(
                f"measurements/{model._meta.verbose_name_plural}.csv", export
            )
