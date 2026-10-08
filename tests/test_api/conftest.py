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


def route_name(model, action):
    """Return the API route name of a model's list or detail route."""
    from fairdm.core.models import Measurement, Sample

    if issubclass(model, Sample):
        prefix = "samples-"
    elif issubclass(model, Measurement):
        prefix = "measurements-"
    else:
        return f"api:{model._meta.model_name}-{action}"
    slug = str(model._meta.verbose_name_plural).lower().replace(" ", "-")
    return f"api:{prefix}{slug}-{action}"


@pytest.fixture
def url_of():
    """Return a function giving a record's, or a model's list, route address."""
    from django.urls import reverse

    def url_of(subject, action="detail"):
        if isinstance(subject, type):
            return reverse(route_name(subject, action))
        return reverse(route_name(type(subject), action), kwargs={"uuid": subject.uuid})

    return url_of


@pytest.fixture
def make_record():
    """Return a function building a record of a registered sample or measurement type."""
    import demo.factories as demo_factories
    from demo.factories import RockSampleFactory
    from fairdm.core.models import Measurement

    def make_record(model, dataset, **kwargs):
        factory = getattr(demo_factories, f"{model.__name__}Factory")
        if issubclass(model, Measurement) and "sample" not in kwargs:
            kwargs["sample"] = RockSampleFactory(dataset=dataset)
        return factory(dataset=dataset, **kwargs)

    return make_record


@pytest.fixture
def add_metadata():
    """Return a function recording one of each kind of metadata on a record."""
    from research_vocabs.models import Concept

    from fairdm.contrib.contributors.choices import ContributionLevel
    from fairdm.core.models import Dataset, Measurement, Project, Sample
    from fairdm.factories import (
        ContributionFactory,
        DatasetDateFactory,
        DatasetDescriptionFactory,
        DatasetIdentifierFactory,
        MeasurementDateFactory,
        MeasurementDescriptionFactory,
        MeasurementIdentifierFactory,
        OrganizationFactory,
        PersonFactory,
        ProjectDateFactory,
        ProjectDescriptionFactory,
        ProjectIdentifierFactory,
        SampleDateFactory,
        SampleDescriptionFactory,
        SampleIdentifierFactory,
    )

    factories = {
        Project: (
            ProjectDescriptionFactory,
            ProjectDateFactory,
            ProjectIdentifierFactory,
        ),
        Dataset: (
            DatasetDescriptionFactory,
            DatasetDateFactory,
            DatasetIdentifierFactory,
        ),
        Sample: (SampleDescriptionFactory, SampleDateFactory, SampleIdentifierFactory),
        Measurement: (
            MeasurementDescriptionFactory,
            MeasurementDateFactory,
            MeasurementIdentifierFactory,
        ),
    }

    def add_metadata(record):
        base = next(model for model in factories if isinstance(record, model))
        description, date, identifier = factories[base]
        description(related=record)
        date(related=record)
        identifier(related=record)
        record.keywords.add(
            Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        )
        credit = ContributionFactory(
            content_object=record,
            contributor=PersonFactory(is_active=True),
            affiliation=OrganizationFactory(),
            level=ContributionLevel.VIEW,
        )
        credit.roles.add(
            Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        )
        return record

    return add_metadata
