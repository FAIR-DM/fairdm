"""Pytest fixtures for the FairDM REST API test suite (Feature 011).

Provides DRF APIClient instances in various authentication states and
convenience fixtures for core model instances used across all API tests.
"""

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def user(db):
    """A regular (authenticated, no special permissions) test user."""
    return UserFactory()


@pytest.fixture
def other_user(db):
    """A second user for isolation tests."""
    return UserFactory()


@pytest.fixture
def token(user):
    """DRF authentication token for *user*."""
    token, _ = Token.objects.get_or_create(user=user)
    return token


@pytest.fixture
def authenticated_client(user, token) -> APIClient:
    """APIClient authenticated with Token auth as *user*."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def editor_client(authenticated_client):
    """Alias for authenticated_client (permissions are granted per-test via guardian)."""
    return authenticated_client


@pytest.fixture
def public_project(db):
    """A Project with ``visibility=PUBLIC``."""
    return ProjectFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_project(db):
    """A Project with ``visibility=PRIVATE``."""
    return ProjectFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def public_dataset(db, public_project):
    """A Dataset with ``visibility=PUBLIC`` linked to a public project."""
    return DatasetFactory(project=public_project, visibility=Visibility.PUBLIC)


@pytest.fixture
def private_dataset(db, public_project):
    """A Dataset with ``visibility=PRIVATE`` linked to a public project."""
    return DatasetFactory(project=public_project, visibility=Visibility.PRIVATE)
