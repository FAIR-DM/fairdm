"""Format lookups, metadata rendering and ZIP packaging for exports."""

import io
import zipfile

from defusedxml.minidom import parseString
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from import_export.formats.base_formats import DEFAULT_FORMATS

from fairdm.core.dataset.models import DatasetDate
from fairdm.core.vocabularies import DATE_TYPES

DATACITE_DATE_TYPES = {
    f"{DATE_TYPES}/available": "Available",
    f"{DATE_TYPES}/published": "Issued",
    f"{DATE_TYPES}/submitted": "Submitted",
    f"{DATE_TYPES}/withdrawn": "Withdrawn",
}

SPDX_IDENTIFIERS = {
    "https://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "https://creativecommons.org/licenses/by-nc/4.0/": "CC-BY-NC-4.0",
    "https://creativecommons.org/licenses/by-nc-nd/4.0/": "CC-BY-NC-ND-4.0",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/": "CC-BY-NC-SA-4.0",
    "https://creativecommons.org/licenses/by-nd/4.0/": "CC-BY-ND-4.0",
    "https://creativecommons.org/licenses/by-sa/4.0/": "CC-BY-SA-4.0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC0-1.0",
}


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


def datacite_dates(dataset):
    """Write a dataset's dates with types from DataCite's ``dateType`` list.

    DataCite has one ``Collected`` date, so the collection start and end become one range, open
    at the side with no date. A type with no DataCite match is written as ``Other``.

    Args:
        dataset: The dataset whose dates to write.

    Returns:
        A list of dicts, each with the date's ``type`` and its ``value``.
    """
    values = {date.type_id: str(date.value) for date in dataset.dates.all()}
    start = values.pop(DatasetDate.START_TYPE, "")
    end = values.pop(DatasetDate.END_TYPE, "")
    dates = [{"type": "Collected", "value": f"{start}/{end}"}] if start or end else []
    return dates + [
        {"type": DATACITE_DATE_TYPES.get(type_id, "Other"), "value": value}
        for type_id, value in values.items()
    ]


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
    license_url = dataset.license.canonical_url if dataset.license else None
    context = {
        "dataset": dataset,
        "uri": uri,
        "dates": datacite_dates(dataset),
        "spdx_identifier": SPDX_IDENTIFIERS.get(license_url),
    }
    xml = render_to_string(template_name, context, request=request)
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
