"""The permalink: a record's portal ID at the portal's root opens the record's page."""

import re

import pytest
from django.urls import resolve, reverse
from shortuuid import ShortUUID

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility
from fairdm.views.permalink import PORTAL_ID_PATTERN, get_permalink

pytestmark = pytest.mark.django_db


def public_dataset():
    """Build a public dataset in a public project."""
    project = ProjectFactory(visibility=Visibility.PUBLIC)
    return DatasetFactory(project=project, visibility=Visibility.PUBLIC)


def unknown_id(letter):
    """Return a well-formed portal ID with the given letter that belongs to no record."""
    return letter + ShortUUID().random(length=22)


def steps(response, portal_id):
    """Return the status of each step a followed request took, with the ID masked."""
    chain = [
        (url.replace(portal_id, "<id>"), status)
        for url, status in response.redirect_chain
    ]
    return [*chain, (response.status_code,)]


def public_records():
    """Build one public record of every kind the permalink opens."""
    dataset = public_dataset()
    sample = RockSampleFactory(dataset=dataset)
    return {
        "project": ProjectFactory(visibility=Visibility.PUBLIC),
        "dataset": dataset,
        "sample": sample,
        "measurement": ExampleMeasurementFactory(dataset=dataset, sample=sample),
        "person": PersonFactory(),
        "unclaimed person": PersonFactory(is_claimed=False),
        "deactivated person": PersonFactory(is_active=False),
        "organization": OrganizationFactory(),
    }


class TestPermalinkRedirect:
    @pytest.mark.parametrize(
        "kind",
        [
            "project",
            "dataset",
            "sample",
            "measurement",
            "person",
            "unclaimed person",
            "deactivated person",
            "organization",
        ],
    )
    def test_a_record_s_portal_id_redirects_to_its_page(self, client, kind):
        record = public_records()[kind]

        response = client.get(f"/{record.uuid}/")

        assert response.status_code == 302
        assert response.url == record.get_absolute_url()

    @pytest.mark.parametrize(
        "kind", ["project", "dataset", "sample", "measurement", "person"]
    )
    def test_following_the_link_renders_the_page_of_the_record(self, client, kind):
        record = public_records()[kind]

        response = client.get(f"/{record.uuid}/", follow=True)

        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == record.get_absolute_url()

    def test_the_redirect_is_temporary(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = client.get(f"/{project.uuid}/")

        assert response.status_code == 302
        assert response.status_code != 301

    def test_a_query_string_is_carried_to_the_page(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = client.get(f"/{project.uuid}/?tab=data")

        assert response.url == f"{project.get_absolute_url()}?tab=data"

    def test_an_id_with_no_closing_slash_reaches_the_record(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = client.get(f"/{project.uuid}", follow=True)

        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == project.get_absolute_url()


class TestPermalinkNotFound:
    def test_an_id_that_belongs_to_no_record_ends_at_not_found(self, client):
        response = client.get(f"/{unknown_id('p')}/", follow=True)

        assert response.status_code == 404

    def test_the_id_of_a_deleted_record_ends_at_not_found(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        portal_id = project.uuid
        project.delete()

        response = client.get(f"/{portal_id}/", follow=True)

        assert response.status_code == 404

    def test_an_id_that_differs_from_a_real_one_only_in_case_ends_at_not_found(
        self, client
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        changed = project.uuid[0] + project.uuid[1:].swapcase()
        assert changed != project.uuid

        response = client.get(f"/{changed}/", follow=True)

        assert response.status_code == 404


class TestPermalinkAccess:
    @pytest.fixture(params=["project", "dataset"])
    def private(self, request):
        if request.param == "project":
            return ProjectFactory(visibility=Visibility.PRIVATE)
        return DatasetFactory(visibility=Visibility.PRIVATE)

    def test_an_anonymous_visitor_cannot_tell_a_private_record_from_no_record(
        self, client, private
    ):
        letter = private.uuid[0]
        absent = unknown_id(letter)

        known = client.get(f"/{private.uuid}/", follow=True)
        unknown = client.get(f"/{absent}/", follow=True)

        assert steps(known, private.uuid) == steps(unknown, absent)
        assert known.status_code == 404

    def test_someone_holding_a_level_reaches_the_page(self, client, private):
        user = PersonFactory(is_active=True, is_claimed=True, password="x")
        ContributionFactory(
            content_object=private, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        response = client.get(f"/{private.uuid}/", follow=True)

        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == private.get_absolute_url()


class TestPermalinkAddress:
    @pytest.mark.parametrize(
        "factory",
        [
            ProjectFactory,
            DatasetFactory,
            RockSampleFactory,
            ExampleMeasurementFactory,
            PersonFactory,
            OrganizationFactory,
        ],
    )
    def test_the_uuid_each_model_makes_resolves_to_the_permalink_route(self, factory):
        record = factory()

        match = resolve(f"/{record.uuid}/")

        assert match.url_name == "permalink"
        assert match.kwargs == {"portal_id": record.uuid}

    def test_get_permalink_returns_the_path(self):
        project = ProjectFactory()

        assert get_permalink(project) == f"/{project.uuid}/"
        assert reverse("permalink", kwargs={"portal_id": project.uuid}) == (
            f"/{project.uuid}/"
        )

    def test_get_permalink_with_a_request_returns_the_absolute_link(self, rf):
        project = ProjectFactory()
        request = rf.get("/", HTTP_HOST="portal.example.org")

        assert get_permalink(project, request) == (
            f"http://portal.example.org/{project.uuid}/"
        )

    def test_the_portal_id_pattern_matches_the_uuid_a_model_makes(self):
        project = ProjectFactory()

        assert re.fullmatch(PORTAL_ID_PATTERN, project.uuid)
