"""Fixtures for the plugin tests."""

import contextlib

import pytest
from django.contrib.auth import get_user_model

from demo.factories import RockSampleFactory
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project

User = get_user_model()


@pytest.fixture
def user(db):
    from fairdm.factories.contributors import UserFactory

    return UserFactory(email="test@example.com")


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Test Project",
        visibility=Project.VISIBILITY.PUBLIC,
        status=Project.STATUS_CHOICES.IN_PROGRESS,
    )


@pytest.fixture
def dataset(db, project):
    return Dataset.objects.create(name="Test Dataset", project=project)


@pytest.fixture
def sample(db, dataset):
    return RockSampleFactory(dataset=dataset, local_id="TEST-001")


@pytest.fixture
def admin_user(db):
    from fairdm.factories.contributors import UserFactory

    return UserFactory(email="admin@example.com", is_staff=True, is_superuser=True)


@pytest.fixture
def anonymous_user():
    from django.contrib.auth.models import AnonymousUser

    return AnonymousUser()


@pytest.fixture
def plain_user(db):
    from fairdm.factories.contributors import UserFactory

    return UserFactory(email="plain@example.com")


@pytest.fixture
def model_perm_user(db):
    from guardian.shortcuts import assign_perm

    from fairdm.factories.contributors import UserFactory

    user = UserFactory(email="model-perm@example.com")
    assign_perm("sample.change_sample", user)
    return user


@pytest.fixture
def object_perm_user(db, sample):
    from fairdm.core.utils import assign_perm
    from fairdm.factories.contributors import UserFactory

    user = UserFactory(email="object-perm@example.com")
    assign_perm("change_sample", user, sample)
    return user


@pytest.fixture
def as_user(rf):

    def build(user, path="/"):
        request = rf.get(path)
        request.user = user
        return request

    return build


@pytest.fixture(autouse=True)
def isolate_registry():
    from fairdm import plugins

    saved = {
        model: list(entries) for model, entries in plugins.registry._registry.items()
    }
    yield
    plugins.registry._registry.clear()
    plugins.registry._registry.update(saved)


@pytest.fixture
def clear_registry():
    import sys
    from importlib import import_module, reload

    from fairdm import plugins

    plugins.registry._registry.clear()
    yield
    plugins.registry._registry.clear()

    plugin_modules = [name for name in sys.modules if name.endswith(".plugins")]

    for module_name in plugin_modules:
        if module_name in sys.modules:
            try:
                reload(sys.modules[module_name])
            except Exception:
                with contextlib.suppress(Exception):
                    import_module(module_name)


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client
