"""Fixtures for the import and export tests."""

import pytest

from demo.models import ICP_MS_Measurement, RockSample, XRFMeasurement
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
