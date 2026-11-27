"""Fixtures for the import and export tests."""

import csv
import io

import pytest
import tablib
from django.core.cache.backends.locmem import LocMemCache
from django.urls import reverse

from demo.factories import (
    CustomParentSampleFactory,
    CustomSampleFactory,
    ExampleMeasurementFactory,
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
    WaterSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import (
    CustomParentSample,
    CustomSample,
    ExampleMeasurement,
    ICP_MS_Measurement,
    RockSample,
    SoilSample,
    WaterSample,
    XRFMeasurement,
)
from fairdm.contrib.import_export.schema import Column
from fairdm.core.measurement.models import Measurement
from fairdm.factories import DatasetFactory, ProjectFactory
from fairdm.registry import registry
from fairdm.registry.config import ModelConfiguration
from fairdm.utils.choices import Visibility


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Store uploaded files in a folder of the test, never in the project's media."""
    settings.MEDIA_ROOT = str(tmp_path / "media")


class RecordingCache(LocMemCache):
    """A local cache that notes each whole number it is asked to store."""

    written = []

    def set(self, key, value, *args, **kwargs):
        """Store the value and note it when it is a number."""
        if isinstance(value, int):
            type(self).written.append(value)
        return super().set(key, value, *args, **kwargs)


@pytest.fixture
def recorded_cache(settings):
    """Use a local cache that keeps every whole number written to it, in order."""
    RecordingCache.written = []
    settings.CACHES = {
        "default": {
            "BACKEND": f"{__name__}.RecordingCache",
            "LOCATION": "recorded-cache",
        }
    }
    yield RecordingCache
    RecordingCache.written = []


RECORD_FACTORIES = {
    RockSample: RockSampleFactory,
    SoilSample: SoilSampleFactory,
    WaterSample: WaterSampleFactory,
    CustomParentSample: CustomParentSampleFactory,
    CustomSample: CustomSampleFactory,
    ExampleMeasurement: ExampleMeasurementFactory,
    XRFMeasurement: XRFMeasurementFactory,
    ICP_MS_Measurement: ICP_MS_MeasurementFactory,
}
"""The factory of each registered demo type."""


@pytest.fixture
def rock_config():
    """The registered rock sample configuration, which lists no resource fields."""
    return registry.get_for_model(RockSample)


@pytest.fixture
def xrf_config():
    """The registered XRF measurement configuration."""
    return registry.get_for_model(XRFMeasurement)


@pytest.fixture
def icp_config():
    """The registered ICP-MS measurement configuration, which has quantity fields."""
    return registry.get_for_model(ICP_MS_Measurement)


@pytest.fixture
def rock_config_for():
    """Return a function building an unregistered rock sample configuration."""

    def build(**overrides):
        """Build the configuration.

        Args:
            **overrides: Configuration attributes, such as ``exclude``.

        Returns:
            A configuration of the rock sample.
        """
        return ModelConfiguration(model=RockSample, **overrides)

    return build


@pytest.fixture
def column_of():
    """Return a function giving a registered type's column by its heading."""

    def get(model, name):
        """Find the column.

        Args:
            model: The registered sample or measurement model.
            name: The column's heading.

        Returns:
            The column of the model's table schema.
        """
        return registry.get_for_model(model).get_table_schema().get(name)

    return get


@pytest.fixture
def make_column():
    """Return a function building a column of a kind no demo type has a field for."""

    def build(kind, **overrides):
        """Build the column.

        Args:
            kind: The column's kind.
            **overrides: Column attributes, such as ``allowed``.

        Returns:
            The column.
        """
        return Column(name=f"{kind}_column", label=kind, kind=kind, **overrides)

    return build


@pytest.fixture
def added_definitions():
    """Remove the definitions a test registers once it has finished."""
    from fairdm.contrib.import_export.definitions import import_definitions

    before = dict(import_definitions.added)
    yield import_definitions.added
    import_definitions.added.clear()
    import_definitions.added.update(before)


@pytest.fixture
def factory_for():
    """Return a function giving the factory of a registered demo type."""
    from demo import factories

    by_model = {
        factories.CustomParentSampleFactory._meta.model: (
            factories.CustomParentSampleFactory
        ),
        factories.CustomSampleFactory._meta.model: factories.CustomSampleFactory,
        factories.RockSampleFactory._meta.model: factories.RockSampleFactory,
        factories.SoilSampleFactory._meta.model: factories.SoilSampleFactory,
        factories.WaterSampleFactory._meta.model: factories.WaterSampleFactory,
        factories.ExampleMeasurementFactory._meta.model: (
            factories.ExampleMeasurementFactory
        ),
        factories.XRFMeasurementFactory._meta.model: factories.XRFMeasurementFactory,
        factories.ICP_MS_MeasurementFactory._meta.model: (
            factories.ICP_MS_MeasurementFactory
        ),
    }
    return by_model.__getitem__


@pytest.fixture
def open_dataset():
    """A published dataset anyone may see."""
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.fixture
def make_record(open_dataset):
    """Return a function creating a stored record of any registered type."""

    def build(model, **overrides):
        """Create the record with its type's factory.

        Args:
            model: A registered sample or measurement model.
            **overrides: Field values for the record.

        Returns:
            The stored record. A measurement is made on a new sample in the same
            dataset unless the overrides give one.
        """
        factory_class = RECORD_FACTORIES[model]
        overrides.setdefault("dataset", open_dataset)
        if issubclass(model, Measurement):
            overrides.setdefault(
                "sample", RockSampleFactory(dataset=overrides["dataset"])
            )
        return factory_class(**overrides)

    return build


@pytest.fixture
def named_rocks(open_dataset):
    """Five rocks of the open dataset, three of them granite."""
    names = ["Granite A", "Granite B", "Granite C", "Basalt A", "Basalt B"]
    return [
        RockSampleFactory(dataset=open_dataset, name=name, rock_type=name.split()[0])
        for name in names
    ]


@pytest.fixture
def private_rocks():
    """Rocks no visitor may list: private, unpublished or in a private project."""
    private = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
    unpublished = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
    hidden_project = ProjectFactory(visibility=Visibility.PRIVATE)
    inside = DatasetFactory(
        project=hidden_project, visibility=Visibility.PUBLIC, published=True
    )
    return [
        RockSampleFactory(dataset=dataset, name=f"Secret {number}")
        for number, dataset in enumerate([private, unpublished, inside])
    ]


@pytest.fixture
def listing_url():
    """Return a function giving the address of a type's portal-wide listing."""

    def build(model):
        """Find the address.

        Args:
            model: A registered sample or measurement model.

        Returns:
            The listing's address.
        """
        return reverse(f"{registry.get_for_model(model).get_slug()}-list")

    return build


@pytest.fixture
def tab_url():
    """Return a function giving the address of a record's records tab."""

    def build(holder, kind, model=None):
        """Find the address.

        Args:
            holder: A dataset, project or contributor.
            kind: ``samples`` or ``measurements``.
            model: The registered type beneath the tab, or None for the first.

        Returns:
            The tab's address.
        """
        kwargs = {"uuid": holder.uuid}
        if model is not None:
            kwargs["type"] = registry.get_for_model(model).get_slug()
        namespace = (
            "contributor"
            if hasattr(holder, "is_organization")
            else holder._meta.model_name
        )
        return reverse(f"{namespace}:{kind}", kwargs=kwargs)

    return build


@pytest.fixture
def csv_rows():
    """Return a function reading a CSV response as one dict per row."""

    def read(response):
        """Read the file.

        Args:
            response: The export's response.

        Returns:
            A dict of heading to cell for each row.
        """
        text = response.content.decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text, newline="")))

    return read


@pytest.fixture
def import_job():
    """A checked import job of rock samples in a new dataset, with no file stored."""
    from tests.factories import ImportJobFactory

    return ImportJobFactory()


@pytest.fixture
def import_row(import_job):
    """One row of the import job, left as a new record."""
    from tests.factories import ImportRowFactory

    return ImportRowFactory(job=import_job)


@pytest.fixture
def file_of():
    """Return a function building the bytes of a file of rows in one of five formats."""

    def build(kind, rows):
        """Build the file.

        Args:
            kind: ``csv``, ``semicolon``, ``tsv``, ``xlsx`` or ``ods``.
            rows: The rows, the first of which is the headings.

        Returns:
            The file's bytes.
        """
        if kind in ("csv", "semicolon", "tsv"):
            delimiter = {"csv": ",", "semicolon": ";", "tsv": "\t"}[kind]
            buffer = io.StringIO(newline="")
            csv.writer(buffer, delimiter=delimiter).writerows(rows)
            return buffer.getvalue().encode("utf-8")
        if kind == "xlsx":
            from openpyxl import Workbook

            book = Workbook()
            for row in rows:
                book.active.append(list(row))
            out = io.BytesIO()
            book.save(out)
            return out.getvalue()
        return ods_of([rows])

    return build


def ods_of(sheets, repeated=None):
    """Build an OpenDocument spreadsheet with odfpy.

    Args:
        sheets: A list of sheets, each a list of rows of strings.
        repeated: A ``(sheet, row, column, times)`` tuple naming a cell that is
            written once and repeated across ``times`` columns.

    Returns:
        The file's bytes.
    """
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    doc = OpenDocumentSpreadsheet()
    for number, rows in enumerate(sheets):
        table = Table(name=f"Sheet{number + 1}")
        for row_number, row in enumerate(rows):
            table_row = TableRow()
            for column_number, value in enumerate(row):
                cell = TableCell(valuetype="string")
                if repeated and repeated[:3] == (number, row_number, column_number):
                    cell.setAttribute("numbercolumnsrepeated", str(repeated[3]))
                cell.addElement(P(text=value))
                table_row.addElement(cell)
            table.addElement(table_row)
        doc.spreadsheet.addElement(table)
    out = io.BytesIO()
    doc.write(out)
    return out.getvalue()


@pytest.fixture
def ods_file():
    """Return the function that builds an OpenDocument file from sheets."""
    return ods_of


@pytest.fixture
def run_import(open_dataset):
    """Return a function that imports rows into a dataset through a type's resource."""

    def run(model, rows, dataset=None, dry_run=False, user=None, **options):
        """Import the rows.

        Args:
            model: The registered sample or measurement model.
            rows: One dict of heading to cell for each row.
            dataset: The dataset to import into. Defaults to the open dataset.
            dry_run: Whether to roll everything back.
            user: The person importing, or None for a visitor.
            **options: ``mode`` and ``empty`` for the resource.

        Returns:
            The resource and the result of its import.
        """
        schema = registry.get_for_model(model).get_table_schema()
        headings = list(dict.fromkeys(key for row in rows for key in row))
        resource = schema_resource(
            schema, dataset or open_dataset, headings, user, **options
        )
        data = tablib.Dataset(headers=headings)
        for row in rows:
            data.append([row.get(heading, "") for heading in headings])
        result = resource.import_data(
            data,
            dry_run=dry_run,
            raise_errors=False,
            use_transactions=True,
            retain_instance_in_row_result=True,
        )
        return resource, result

    return run


def schema_resource(schema, dataset, headings, user, **options):
    """Build the resource for a file with these headings.

    Args:
        schema: The type's table schema.
        dataset: The dataset the file is imported into.
        headings: The file's headings.
        user: The person importing, or None for a visitor.
        **options: ``mode`` and ``empty``.

    Returns:
        The resource.
    """
    from fairdm.contrib.import_export.resources import build_resource

    return build_resource(schema, dataset, columns=headings, user=user, **options)


@pytest.fixture
def make_job(open_dataset):
    """Return a function creating an import job over a CSV file of rows."""

    def build(
        rows,
        model=RockSample,
        dataset=None,
        status="checking",
        user=None,
        column_map=None,
        samples=None,
        **options,
    ):
        """Create the job and store its file.

        Args:
            rows: One dict of heading to cell for each row.
            model: The registered type the rows fill.
            dataset: The dataset to import into. Defaults to the open dataset.
            status: The job's status.
            user: The person who uploaded the file.
            column_map: Heading to column. Defaults to each heading meaning the
                column of the same name.
            samples: The example values to store on the job.
            **options: ``mode`` and ``empty_cells`` for the job.

        Returns:
            The stored job.
        """
        from django.core.files.base import ContentFile

        from fairdm.contrib.import_export.models import ImportJob

        headings = list(dict.fromkeys(key for row in rows for key in row))
        body = io.StringIO(newline="")
        writer = csv.writer(body)
        writer.writerow(headings)
        writer.writerows([row.get(heading, "") for heading in headings] for row in rows)
        return ImportJob.objects.create(
            dataset=dataset or open_dataset,
            definition_name=model._meta.model_name,
            created_by=user,
            file=ContentFile(body.getvalue().encode("utf-8"), name="records.csv"),
            filename="records.csv",
            file_format="csv",
            status=status,
            headers=headings,
            samples=samples or {},
            column_map=column_map or {heading: heading for heading in headings},
            **options,
        )

    return build
