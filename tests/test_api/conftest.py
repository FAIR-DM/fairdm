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


def make_token_client(user, **kwargs) -> APIClient:
    """Return an APIClient that sends a new token of the person's in each request."""
    from knox.models import AuthToken

    _record, value = AuthToken.objects.create(user=user, **kwargs)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {value}")
    return client


@pytest.fixture
def make_token():
    """Return a function creating a token for a person, giving the record and its value.

    The value is the secret a script sends. Only the record's digest is stored.
    """
    from knox.models import AuthToken

    def make_token(user, **kwargs):
        return AuthToken.objects.create(user=user, **kwargs)

    return make_token


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


def plain(value):
    """Return a stored value as plain data: a vocabulary concept becomes its name."""
    return getattr(value, "name", value)


@pytest.fixture
def member_at():
    """Return a function crediting a person who can sign in on a record at a level."""
    from fairdm.factories import ContributionFactory, PersonFactory

    def member_at(record, level, person=None):
        person = person or PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(content_object=record, contributor=person, level=level)
        return person

    return member_at


@pytest.fixture
def signed_in():
    """Return a function giving an API client signed in as a person."""

    def signed_in(person):
        client = APIClient()
        client.force_authenticate(person)
        return client

    return signed_in


@pytest.fixture
def body_for(make_record):
    """Return a function giving a valid request body for a registered type, with its values.

    The values come from a record the type's factory builds. The body holds what the type's
    serializer lets a caller write, without the parents, and the second item holds the values
    as the model stores them, to compare with what a create or a replacement saved. Compare
    them through ``saved``.
    """
    from fairdm.core.models import Measurement

    def body_for(model, name="Sent by a script"):
        from fairdm.factories import DatasetFactory
        from fairdm.registry import registry

        template = make_record(model, DatasetFactory(visibility=Visibility.PUBLIC))
        template.refresh_from_db()
        fields = registry.get_for_model(model).get_serializer_class()().fields
        parents = (
            {"dataset", "sample"} if issubclass(model, Measurement) else {"dataset"}
        )
        body = {}
        for key, field in fields.items():
            value = getattr(template, key, None)
            if field.read_only or key in parents or value in (None, "", {}):
                continue
            body[key] = field.to_representation(value)
        body["name"] = name
        stored = {key: plain(getattr(template, key)) for key in body}
        stored["name"] = name
        return body, stored

    return body_for


@pytest.fixture
def saved():
    """Return a function reading the named fields of a stored record as plain data."""

    def saved(record, fields):
        return {key: plain(getattr(record, key)) for key in fields}

    return saved


@pytest.fixture
def on_the_router():
    """Return a function that registers a viewset on the API router for one test.

    The router's addresses are read once, when the URL modules are imported, so the
    modules are loaded again after every change. Both the registration and the reload
    are undone at the end of the test.
    """
    import importlib

    from django.urls import clear_url_caches

    import fairdm.api.urls
    import fairdm.conf.urls
    from fairdm.api.router import fairdm_api_router

    added = []

    def reload_urls():
        if hasattr(fairdm_api_router, "_urls"):
            del fairdm_api_router._urls
        importlib.reload(fairdm.api.urls)
        importlib.reload(fairdm.conf.urls)
        clear_url_caches()

    def register(prefix, viewset, basename):
        fairdm_api_router.register(prefix, viewset, basename=basename)
        added.append((prefix, viewset, basename))
        reload_urls()

    yield register

    if added:
        for entry in added:
            fairdm_api_router.registry.remove(entry)
        reload_urls()
