"""Fixtures for the import and export tests."""

import csv
import io

import pytest
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
