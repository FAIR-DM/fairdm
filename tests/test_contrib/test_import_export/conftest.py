"""Fixtures for the import and export tests."""

import pytest

from demo.models import ICP_MS_Measurement, RockSample, XRFMeasurement
from fairdm.contrib.import_export.schema import Column
from fairdm.registry import registry
from fairdm.registry.config import ModelConfiguration


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
    from fairdm.contrib.import_export import definitions

    before = dict(definitions.added)
    yield definitions.added
    definitions.added.clear()
    definitions.added.update(before)


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
