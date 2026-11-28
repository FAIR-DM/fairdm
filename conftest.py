"""Pytest configuration shared by every suite in this repository."""

import random
import uuid
import zlib

import factory.random
import faker
import pytest
from django.apps import apps


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Seed every random source from the test's id before any fixture builds data.

    Faker, factory_boy and ``random`` draw the same values on every run of a test and
    different values from one test to the next, so a failure reproduces and tests do
    not collide on a unique field. This runs ahead of fixture setup, which includes the
    class- and module-scoped fixtures.
    """
    seed = zlib.crc32(item.nodeid.encode())
    factory.random.reseed_random(seed)
    faker.Faker.seed(seed)
    random.seed(seed)


@pytest.fixture
def unique_app_label():
    return f"test_app_{uuid.uuid4().hex[:12]}"


@pytest.fixture(autouse=True)
def _media_root_under_tmp_path(tmp_path, settings):
    # A test's files land in its own tmp_path, never in a path shared across runs and xdist workers.
    settings.MEDIA_ROOT = str(tmp_path / "media")
    settings.STATIC_ROOT = str(tmp_path / "static")


@pytest.fixture(autouse=True)
def no_models_left_in_installed_apps():
    # A model class defined in a test body stays in the app registry, and later unrelated tests
    # fail on its missing table when its app is installed.
    installed = {config.label for config in apps.get_app_configs()}
    before = {label: set(apps.all_models[label]) for label in installed}

    yield

    leaked = sorted(
        f"{label}.{name}"
        for label in installed
        for name in set(apps.all_models[label]) - before[label]
    )
    assert not leaked, (
        f"This test registered {', '.join(leaked)} in an installed app and left it "
        "there. Use the unique_app_label fixture so the model lands in an app "
        "nothing installs."
    )
