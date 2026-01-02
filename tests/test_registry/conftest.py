"""Shared fixtures for registry tests."""

import pytest

from fairdm.registry import registry


@pytest.fixture
def clean_registry():
    """Fixture to clean the registry before and after each test."""
    # Clear registry before test
    registry._registry.clear()

    yield registry

    # Clear registry after test
    registry._registry.clear()
