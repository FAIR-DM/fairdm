"""Fixtures for the autocomplete views, fields and request limits."""

import pytest
from django.contrib.auth.models import Group, Permission

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.sample.models import SampleIdentifier
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    ContributorIdentifierFactory,
    DatasetFactory,
    LiteratureItemFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory


@pytest.fixture
def researcher(db):
    return UserFactory()


@pytest.fixture
def researcher_client(client, researcher):
    client.force_login(researcher)
    return client


@pytest.fixture
def make_dataset(db):
    """Return a function building a dataset, optionally with a level held by one person."""

    def make_dataset(
        name,
        *,
        visibility=Visibility.PRIVATE,
        project_visibility=Visibility.PUBLIC,
        published=False,
        project=None,
        holder=None,
        level=ContributionLevel.EDIT,
    ):
        project = project or ProjectFactory(visibility=project_visibility)
        dataset = DatasetFactory(
            name=name, visibility=visibility, published=published, project=project
        )
        if holder is not None:
            ContributionFactory(content_object=dataset, contributor=holder, level=level)
        return dataset

    return make_dataset


@pytest.fixture
def make_project(db):
    """Return a function building a project, optionally with a level held by one person."""

    def make_project(
        name,
        *,
        visibility=Visibility.PRIVATE,
        holder=None,
        level=ContributionLevel.EDIT,
    ):
        project = ProjectFactory(name=name, visibility=visibility)
        if holder is not None:
            ContributionFactory(content_object=project, contributor=holder, level=level)
        return project

    return make_project


@pytest.fixture
def data_curator(db):
    """Return a person with the portal-wide Data Curator role."""
    person = UserFactory()
    person.groups.add(Group.objects.get(name="Data Curator"))
    return person


@pytest.fixture
def grant_view_everywhere(db):
    """Return a function giving a person the portal-wide right to view every dataset."""

    def grant(person):
        person.user_permissions.add(Permission.objects.get(codename="view_dataset"))

    return grant


@pytest.fixture
def make_record(make_dataset, make_project, make_sample, make_measurement):
    """Return a function building a public record of a kind that one person may edit.

    The record is offered by every address of its kind, whatever the scope.
    """

    def in_public_dataset(name, holder):
        return make_dataset(
            name, visibility=Visibility.PUBLIC, published=True, holder=holder
        )

    def make_record(kind, name, *, holder):
        builders = {
            "project": lambda: make_project(
                name, visibility=Visibility.PUBLIC, holder=holder
            ),
            "dataset": lambda: make_dataset(
                name, visibility=Visibility.PUBLIC, holder=holder
            ),
            "sample": lambda: make_sample(
                name, dataset=in_public_dataset(f"{name} dataset", holder)
            ),
            "measurement": lambda: make_measurement(
                name, dataset=in_public_dataset(f"{name} dataset", holder)
            ),
        }
        return builders[kind]()

    return make_record


@pytest.fixture
def in_request(rf):
    """Return a function that makes a request the current one, as the middleware does.

    A field finds the person through the current request, so a form built in a test is built
    inside one.
    """
    from django_tomselect.middleware import _request_local

    def enter(user, **query):
        request = rf.get("/some/page/", query)
        request.user = user
        _request_local.request = request
        return request

    yield enter
    if hasattr(_request_local, "request"):
        del _request_local.request


@pytest.fixture
def make_organization(db):
    """Return a function building an organization, optionally with a ROR identifier."""

    def make_organization(
        name, *, ror=None, alternative_names=None, city="", country=""
    ):
        organization = OrganizationFactory(
            name=name,
            alternative_names=alternative_names or [],
            city=city,
            country=country,
        )
        if ror:
            ContributorIdentifierFactory(related=organization, type="ROR", value=ror)
        return organization

    return make_organization


@pytest.fixture
def make_person(db):
    """Return a function building a person, optionally with an ORCID and a primary affiliation."""

    def make_person(
        name,
        *,
        orcid=None,
        email=None,
        alternative_names=None,
        claimed=False,
        superuser=False,
        organization=None,
    ):
        extra = {"email": email} if email else {}
        person = PersonFactory(
            name=name,
            alternative_names=alternative_names or [],
            is_claimed=claimed,
            is_superuser=superuser,
            **extra,
        )
        if orcid:
            ContributorIdentifierFactory(related=person, type="ORCID", value=orcid)
        if organization is not None:
            AffiliationFactory(
                person=person, organization=organization, is_primary=True
            )
        return person

    return make_person


@pytest.fixture
def make_sample(db):
    """Return a function building a sample in a dataset, with an optional identifier."""

    def make_sample(name, *, dataset, local_id="", identifier=None):
        sample = ConcreteSampleFactory(name=name, dataset=dataset, local_id=local_id)
        if identifier:
            SampleIdentifier.objects.create(
                related=sample, type="DOI", value=identifier
            )
        return sample

    return make_sample


@pytest.fixture
def make_measurement(db, make_sample):
    """Return a function building a measurement of a new sample in the same dataset."""

    def make_measurement(name, *, dataset, local_id=""):
        sample = make_sample(f"{name} sample", dataset=dataset)
        return ConcreteMeasurementFactory(
            name=name, dataset=dataset, sample=sample, local_id=local_id
        )

    return make_measurement


@pytest.fixture
def make_publication(db):
    """Return a function building a literature item with authors, a DOI and a year."""

    def make_publication(title, *, authors=(), doi="", year=None):
        item = {"type": "article-journal", "title": title}
        if authors:
            item["author"] = [{"family": f, "given": g} for f, g in authors]
        if doi:
            item["DOI"] = doi
        if year:
            item["issued"] = {"date-parts": [[year]]}
        return LiteratureItemFactory(item=item)

    return make_publication


class FakeRor:
    """What ``Ror.search`` answers in a test: the records set, or an error, and the terms asked."""

    def __init__(self):
        self.results = []
        self.error = None
        self.asked = []

    def search(self, term):
        self.asked.append(term)
        if self.error is not None:
            raise self.error
        return {"results": self.results, "more": False}


@pytest.fixture
def fake_ror(monkeypatch):
    """Replace ``Ror.search`` so that no test reaches ROR."""
    from fairdm.contrib.contributors.services.registries import Ror

    fake = FakeRor()
    monkeypatch.setattr(Ror, "search", lambda self, term: fake.search(term))
    return fake
