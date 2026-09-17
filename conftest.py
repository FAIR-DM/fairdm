"""
Pytest configuration shared by every suite in this repository.

``tests/`` covers the framework and ``demo/tests/`` covers the reference
application. Both define models inside test bodies, and both pay for it the same
way, so the fixtures that deal with that live here rather than in either one.
"""

import uuid

import pytest
from django.apps import apps


@pytest.fixture
def unique_app_label():
    """
    Generate a unique app label for test models.

    This prevents Django model registry conflicts when creating
    models dynamically in tests. Each test gets a unique app label.

    Example usage:
        def test_something(unique_app_label):
            class TestSample(Sample):
                class Meta:
                    app_label = unique_app_label

    Returns:
        str: A unique app label like "test_app_abc123def456"
    """
    return f"test_app_{uuid.uuid4().hex[:12]}"


@pytest.fixture(autouse=True)
def _media_root_under_tmp_path(tmp_path, settings):
    """Every test's ``MEDIA_ROOT``/``STATIC_ROOT`` are this test's own ``tmp_path``.

    ``tests/settings.py`` falls back to a per-process temp directory for code
    that reads these settings outside a test, but every test overrides it with
    this. A model instance saved with a real image writes it under
    ``MEDIA_ROOT``, so a fixed shared path here meant every run of the suite
    wrote into the same directory and nothing ever removed it (issue #323).
    ``tmp_path`` is unique per test and per pytest-xdist worker, and pytest
    prunes old runs' directories on its own, so growth stays bounded the same
    way ``django-literature``'s equivalent fixture already does.
    """
    settings.MEDIA_ROOT = str(tmp_path / "media")
    settings.STATIC_ROOT = str(tmp_path / "static")


@pytest.fixture(autouse=True)
def no_models_left_in_installed_apps():
    """Fail the test that leaves a new model behind in an installed app.

    A model class defined in a test body registers itself in Django's app
    registry for the rest of the process. If its app is installed, the model
    joins its parent's related objects, so every later delete or polymorphic
    read touches a table the test database never built. The failure then lands
    on whichever unrelated test runs next, which is a different test on every
    worker layout. Giving such a model an app label no project installs, as
    ``unique_app_label`` does, keeps it out of the registry Django queries.
    """
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
