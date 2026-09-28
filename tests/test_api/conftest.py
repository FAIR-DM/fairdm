"""Pytest fixtures for the FairDM REST API test suite (Feature 011)."""

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def token(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token


@pytest.fixture
def authenticated_client(user, token) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def editor_client(authenticated_client):
    return authenticated_client


@pytest.fixture
def public_project(db):
    return ProjectFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_project(db):
    return ProjectFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def public_dataset(db, public_project):
    return DatasetFactory(project=public_project, visibility=Visibility.PUBLIC)


@pytest.fixture
def private_dataset(db, public_project):
    return DatasetFactory(project=public_project, visibility=Visibility.PRIVATE)
