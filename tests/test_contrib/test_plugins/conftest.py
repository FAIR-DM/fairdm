"""Fixtures for the plugin tests."""

import pytest
from django.contrib.auth import get_user_model

from demo.factories import RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import ContributionFactory

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
    from fairdm.factories.contributors import UserFactory

    user = UserFactory(email="object-perm@example.com")
    ContributionFactory(
        content_object=sample, contributor=user, level=ContributionLevel.EDIT
    )
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
    """Give each test the registry, record menus and URL caches it found."""
    from django.urls import clear_url_caches
    from flex_menu import root

    from fairdm import plugins

    registry = plugins.registry
    saved_registry = {
        model: list(entries) for model, entries in registry._registry.items()
    }
    saved_addressing = dict(registry._addressing)
    saved_root = list(root.children)
    saved_menus = {id(menu): (menu, list(menu.children)) for menu in saved_root}
    yield
    registry_changed = registry._registry != saved_registry
    registry._registry.clear()
    registry._registry.update(saved_registry)
    registry._addressing.clear()
    registry._addressing.update(saved_addressing)
    for menu, children in saved_menus.values():
        menu.children = type(menu.children)(children)
    root.children = type(root.children)(saved_root)
    if registry_changed:
        clear_url_caches()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client
