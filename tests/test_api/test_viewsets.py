"""Tests for FairDM API viewsets (Feature 011 â€” US1)."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from django.urls import reverse

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization, Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import (
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectListEndpoint:
    def test_returns_200(self, api_client):
        response = api_client.get(reverse("api:project-list"))
        assert response.status_code == 200

    def test_response_has_pagination_keys(self, api_client):
        response = api_client.get(reverse("api:project-list"))
        data = response.json()
        for key in ("count", "next", "previous", "results"):
            assert key in data

    def test_public_project_visible_to_anonymous(self, api_client, public_project):
        response = api_client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(public_project.uuid) in uuids

    def test_private_project_hidden_from_anonymous(self, api_client, private_project):
        response = api_client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(private_project.uuid) not in uuids

    def test_authenticated_sees_public_project(
        self, authenticated_client, public_project
    ):
        response = authenticated_client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(public_project.uuid) in uuids

    def test_authenticated_still_hidden_from_private_without_permission(
        self, authenticated_client, private_project
    ):
        response = authenticated_client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(private_project.uuid) not in uuids

    def test_ordering_ascending(self, api_client, db):
        ProjectFactory(name="Zeta Project", visibility=Visibility.PUBLIC)
        ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("api:project-list"), {"ordering": "name"})
        assert response.status_code == 200
        names = [p["name"] for p in response.json()["results"]]
        assert names == sorted(names)

    def test_ordering_descending(self, api_client, db):
        ProjectFactory(name="Zeta Project", visibility=Visibility.PUBLIC)
        ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("api:project-list"), {"ordering": "-name"})
        assert response.status_code == 200
        names = [p["name"] for p in response.json()["results"]]
        assert names == sorted(names, reverse=True)

    def test_unauthenticated_post_returns_401(self, api_client):
        response = api_client.post(
            reverse("api:project-list"), {"name": "New Project"}, format="json"
        )
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestProjectDetailEndpoint:
    def test_public_project_returns_200(self, api_client, public_project):
        url = reverse("api:project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_public_project_uuid_in_response(self, api_client, public_project):
        url = reverse("api:project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.get(url)
        assert response.json()["uuid"] == str(public_project.uuid)

    def test_public_project_has_expected_fields(self, api_client, public_project):
        url = reverse("api:project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.get(url)
        data = response.json()
        for field in ("uuid", "name", "visibility"):
            assert field in data

    def test_private_project_returns_404_to_anonymous(
        self, api_client, private_project
    ):
        url = reverse("api:project-detail", kwargs={"uuid": private_project.uuid})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_nonexistent_uuid_returns_404(self, api_client):
        url = reverse("api:project-detail", kwargs={"uuid": "nonexistentid"})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_unauthenticated_patch_returns_401(self, api_client, public_project):
        url = reverse("api:project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.patch(url, {"name": "Hacked"}, format="json")
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestDatasetListEndpoint:
    def test_returns_200(self, api_client):
        response = api_client.get(reverse("api:dataset-list"))
        assert response.status_code == 200

    def test_public_dataset_visible_to_anonymous(self, api_client, public_dataset):
        response = api_client.get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in response.json()["results"]]
        assert str(public_dataset.uuid) in uuids

    def test_private_dataset_hidden_from_anonymous(self, api_client, private_dataset):
        response = api_client.get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in response.json()["results"]]
        assert str(private_dataset.uuid) not in uuids

    def test_response_has_expected_fields(self, api_client, public_dataset):
        response = api_client.get(reverse("api:dataset-list"))
        results = response.json()["results"]
        ds = next((d for d in results if d["uuid"] == str(public_dataset.uuid)), None)
        assert ds is not None
        for field in ("uuid", "name", "visibility"):
            assert field in ds

    def test_dataset_ordering_ascending(self, api_client, public_project, db):
        DatasetFactory(
            project=public_project, name="A Dataset", visibility=Visibility.PUBLIC
        )
        DatasetFactory(
            project=public_project, name="Z Dataset", visibility=Visibility.PUBLIC
        )
        response = api_client.get(reverse("api:dataset-list"), {"ordering": "name"})
        assert response.status_code == 200
        names = [d["name"] for d in response.json()["results"]]
        assert names == sorted(names)


@pytest.mark.django_db
class TestDatasetDetailEndpoint:
    def test_public_dataset_returns_200(self, api_client, public_dataset):
        url = reverse("api:dataset-detail", kwargs={"uuid": public_dataset.uuid})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_private_dataset_returns_404_to_anonymous(
        self, api_client, private_dataset
    ):
        url = reverse("api:dataset-detail", kwargs={"uuid": private_dataset.uuid})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_nonexistent_uuid_returns_404(self, api_client):
        url = reverse("api:dataset-detail", kwargs={"uuid": "doesnotexist"})
        response = api_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestDatasetCreatorParity:
    def test_created_by_is_set_server_side_and_cannot_be_spoofed(
        self, authenticated_client, user
    ):
        other_user = UserFactory()

        response = authenticated_client.post(
            reverse("api:dataset-list"),
            {"name": "Spoofed Creator Dataset", "created_by": other_user.pk},
            format="json",
        )

        assert response.status_code == 201
        assert "created_by" not in response.json()

        # Use `all_objects`: a dataset created with no visibility stated is PRIVATE, so the privacy-first
        # default manager would exclude it here.
        dataset = Dataset.all_objects.get(uuid=response.json()["uuid"])
        assert dataset.created_by == user
        assert dataset.created_by != other_user


@pytest.mark.django_db
class TestContributorListEndpoint:
    ROUTES = ("api:person-list", "api:organization-list")

    @pytest.mark.parametrize("route", ROUTES)
    def test_returns_200(self, api_client, route):
        response = api_client.get(reverse(route))
        assert response.status_code == 200

    @pytest.mark.parametrize("route", ROUTES)
    def test_has_pagination_keys(self, api_client, route):
        data = api_client.get(reverse(route)).json()
        for key in ("count", "next", "previous", "results"):
            assert key in data

    @pytest.mark.parametrize("route", ROUTES)
    def test_post_not_allowed(self, authenticated_client, route):
        response = authenticated_client.post(
            reverse(route), {"name": "New"}, format="json"
        )
        # DRF may return 403 (permission denied) before 405 (method not allowed)
        # when object-level permissions fire before method routing.
        assert response.status_code in (403, 405)


@pytest.mark.django_db
class TestProjectCRUD:
    def test_authenticated_post_creates_project(self, authenticated_client):
        response = authenticated_client.post(
            reverse("api:project-list"),
            {"name": "New API Project"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New API Project"
        assert "uuid" in data

    def test_created_project_appears_in_list(self, authenticated_client):
        post_resp = authenticated_client.post(
            reverse("api:project-list"),
            {"name": "Listed Project"},
            format="json",
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]
        list_resp = authenticated_client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in list_resp.json()["results"]]
        assert uuid in uuids

    def test_authenticated_patch_updates_project(self, authenticated_client, user):
        post_resp = authenticated_client.post(
            reverse("api:project-list"),
            {"name": "Patch Target"},
            format="json",
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]

        url = reverse("api:project-detail", kwargs={"uuid": uuid})
        patch_resp = authenticated_client.patch(
            url, {"name": "Updated Name"}, format="json"
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == "Updated Name"

    def test_authenticated_delete_removes_project(self, authenticated_client, user):
        post_resp = authenticated_client.post(
            reverse("api:project-list"),
            {"name": "Delete Target"},
            format="json",
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]

        url = reverse("api:project-detail", kwargs={"uuid": uuid})
        del_resp = authenticated_client.delete(url)
        assert del_resp.status_code == 204

        get_resp = authenticated_client.get(url)
        assert get_resp.status_code == 404

    def test_unauthenticated_post_returns_401(self, api_client):
        response = api_client.post(
            reverse("api:project-list"),
            {"name": "Should Fail"},
            format="json",
        )
        assert response.status_code == 401

    def test_post_missing_required_field_returns_400(self, authenticated_client):
        response = authenticated_client.post(
            reverse("api:project-list"),
            {},
            format="json",
        )
        assert response.status_code == 400
        assert "name" in response.json()

    def test_created_by_is_set_server_side_and_cannot_be_spoofed(
        self, authenticated_client, user
    ):
        other_user = UserFactory()

        response = authenticated_client.post(
            reverse("api:project-list"),
            {"name": "Spoofed Creator Project", "created_by": other_user.pk},
            format="json",
        )

        assert response.status_code == 201
        assert "created_by" not in response.json()

        project = Project.objects.get(uuid=response.json()["uuid"])
        assert project.created_by == user
        assert project.created_by != other_user


def person_at(record, level, person=None):
    """Return a person who can sign in, credited on the record at the level."""
    from fairdm.factories import ContributionFactory, PersonFactory

    person = person or PersonFactory(is_active=True, is_claimed=True)
    ContributionFactory(content_object=record, contributor=person, level=level)
    return person


def signed_in_as(person):
    """Return an API client signed in as the person."""
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(person)
    return client


def build_record(kind, make_record, add_metadata):
    """Build a public record of a kind, with metadata recorded, and its parents."""
    from demo.models import ExampleMeasurement, RockSample

    project = ProjectFactory(visibility=Visibility.PUBLIC)
    dataset = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=True
    )
    if kind == "project":
        record = project
    elif kind == "dataset":
        record = dataset
    elif kind == "sample":
        record = make_record(RockSample, dataset)
    elif kind == "located sample":
        from demo.models import CustomSample
        from fairdm.factories import PointFactory

        record = make_record(CustomSample, dataset, location=PointFactory())
    else:
        record = make_record(ExampleMeasurement, dataset)
    return add_metadata(record)


@pytest.mark.django_db
class TestCompleteRecord:
    METADATA = ("descriptions", "dates", "identifiers", "keywords", "contributors")

    @pytest.mark.parametrize("kind", ["project", "dataset", "sample", "measurement"])
    def test_a_record_carries_its_own_fields_and_its_metadata(
        self, api_client, url_of, make_record, add_metadata, kind
    ):
        record = build_record(kind, make_record, add_metadata)

        response = api_client.get(url_of(record))

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == record.uuid
        assert data["name"] == record.name
        for name in self.METADATA:
            assert len(data[name]) == 1, name
        description = record.descriptions.get()
        assert data["descriptions"][0]["type"] == description.type
        assert data["descriptions"][0]["value"] == description.value
        assert data["dates"][0]["type"] == record.dates.get().type
        assert data["identifiers"][0]["value"] == record.identifiers.get().value
        assert data["keywords"][0]["name"] == record.keywords.get().name

    @pytest.mark.parametrize("kind", ["project", "dataset", "sample", "measurement"])
    def test_a_credited_contributor_is_named_with_roles_and_affiliation(
        self, api_client, url_of, make_record, add_metadata, kind
    ):
        record = build_record(kind, make_record, add_metadata)
        credit = record.contributors.get()

        credited = api_client.get(url_of(record)).json()["contributors"][0]

        assert credited["uuid"] == credit.contributor.uuid
        assert credited["affiliation"][0]["uuid"] == credit.affiliation.uuid
        assert [role["name"] for role in credited["roles"]] == [
            role.name for role in credit.roles.all()
        ]

    def test_a_dataset_carries_its_licence_and_a_project_its_owner(
        self, api_client, url_of, make_record, add_metadata
    ):
        project = build_record("project", make_record, add_metadata)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )

        project_data = api_client.get(url_of(project)).json()
        dataset_data = api_client.get(url_of(dataset)).json()

        assert project_data["owner"]["uuid"] == project.owner.uuid
        assert dataset_data["license"]["name"] == dataset.license.name

    @pytest.mark.parametrize("kind", ["dataset", "sample", "measurement"])
    def test_the_address_of_a_parent_returns_the_parent(
        self, api_client, url_of, make_record, add_metadata, kind
    ):
        record = build_record(kind, make_record, add_metadata)
        data = api_client.get(url_of(record)).json()
        parent_name = "project" if kind == "dataset" else "dataset"

        parent = api_client.get(data[parent_name]["url"])

        assert parent.status_code == 200
        assert parent.json()["uuid"] == data[parent_name]["uuid"]

    def test_a_measurement_names_its_sample_and_the_sample_address_returns_it(
        self, api_client, url_of, make_record, add_metadata
    ):
        measurement = build_record("measurement", make_record, add_metadata)
        data = api_client.get(url_of(measurement)).json()

        sample = api_client.get(data["sample"]["url"])

        assert data["sample"]["uuid"] == measurement.sample.uuid
        assert sample.status_code == 200
        assert sample.json()["uuid"] == measurement.sample.uuid

    def test_a_public_dataset_in_a_private_project_hides_the_project_from_a_visitor(
        self, api_client, url_of
    ):
        from fairdm.contrib.contributors.choices import ContributionLevel

        project = ProjectFactory(visibility=Visibility.PRIVATE)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        viewer = person_at(project, ContributionLevel.VIEW)

        visitor_sees = api_client.get(url_of(dataset)).json()["project"]
        viewer_sees = signed_in_as(viewer).get(url_of(dataset)).json()["project"]

        assert visitor_sees is None
        assert viewer_sees["uuid"] == project.uuid

    def test_a_sample_in_a_private_dataset_is_hidden_from_a_measurement_that_names_it(
        self, api_client, url_of, make_record
    ):
        from demo.models import ExampleMeasurement, RockSample
        from fairdm.contrib.contributors.choices import ContributionLevel

        elsewhere = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = make_record(RockSample, elsewhere)
        measurement = make_record(
            ExampleMeasurement,
            DatasetFactory(visibility=Visibility.PUBLIC, published=True),
            sample=sample,
        )
        viewer = person_at(elsewhere, ContributionLevel.VIEW)

        visitor_sees = api_client.get(url_of(measurement)).json()["sample"]
        viewer_sees = signed_in_as(viewer).get(url_of(measurement)).json()["sample"]

        assert visitor_sees is None
        assert viewer_sees["uuid"] == sample.uuid

    def test_a_list_hides_the_parent_it_would_otherwise_name(self, api_client, url_of):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC, published=True)

        results = api_client.get(url_of(Dataset, "list")).json()["results"]

        assert [row["project"] for row in results] == [None]


CREDIT_KINDS = ("project", "dataset", "sample", "measurement")

CREDIT_KEYS = {
    "uuid",
    "url",
    "name",
    "name_type",
    "given_name",
    "family_name",
    "name_identifiers",
    "affiliation",
    "roles",
}


def add_credit(record, contributor, affiliation=None, roles=1):
    """Credit a contributor on a record, with the first roles of the roles vocabulary."""
    from research_vocabs.models import Concept

    from fairdm.factories import ContributionFactory

    credit = ContributionFactory(
        content_object=record,
        contributor=contributor,
        affiliation=affiliation,
        level=None if contributor.is_organization else ContributionLevel.VIEW,
    )
    credit.roles.add(*Concept.objects.filter(vocabulary__name="fairdm-roles")[:roles])
    return credit


@pytest.mark.django_db
class TestCredit:
    @pytest.fixture
    def author(self):
        """A person with an ORCID iD, credited from an organization with a ROR ID."""
        from fairdm.factories import (
            ContributorIdentifierFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory(first_name="Ada", last_name="Lovelace")
        ContributorIdentifierFactory(
            related=person, type="ORCID", value="0000-0002-1825-0097"
        )
        institute = OrganizationFactory(name="Analytical Institute")
        ContributorIdentifierFactory(related=institute, type="ROR", value="03yrm5c26")
        return person, institute

    @pytest.fixture
    def add_team(self, author):
        """Return a function crediting the three kinds of credit on a record."""
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person, institute = author

        def add_team(record):
            bare = PersonFactory(first_name="Grace", last_name="Hopper")
            AffiliationFactory(
                person=bare, organization=OrganizationFactory(), is_primary=True
            )
            return {
                "author": add_credit(record, person, institute, roles=2),
                "bare": add_credit(record, bare),
                "organization": add_credit(record, OrganizationFactory()),
            }

        return add_team

    @pytest.fixture
    def record_of(self, make_record):
        """Return a function building a public record of a kind with no add_team."""
        return lambda kind: build_record(kind, make_record, lambda record: record)

    @staticmethod
    def credits_of(client, url_of, record):
        response = client.get(url_of(record))
        assert response.status_code == 200
        return response.json()["contributors"]

    @pytest.mark.parametrize("kind", CREDIT_KINDS)
    def test_a_credit_carries_what_datacite_asks_of_a_creator(
        self, api_client, url_of, record_of, add_team, author, kind
    ):
        person, institute = author
        record = record_of(kind)
        made = add_team(record)

        credit = self.credits_of(api_client, url_of, record)[0]

        assert set(credit) == CREDIT_KEYS
        assert credit["uuid"] == person.uuid
        assert credit["url"].endswith(
            reverse("api:person-detail", kwargs={"uuid": person.uuid})
        )
        assert credit["name"] == "Lovelace, Ada"
        assert credit["name_type"] == "Personal"
        assert credit["given_name"] == "Ada"
        assert credit["family_name"] == "Lovelace"
        assert credit["name_identifiers"] == [
            {
                "name_identifier": "https://orcid.org/0000-0002-1825-0097",
                "name_identifier_scheme": "ORCID",
                "scheme_uri": "https://orcid.org/",
            }
        ]
        assert credit["affiliation"] == [
            {
                "uuid": institute.uuid,
                "url": credit["affiliation"][0]["url"],
                "name": "Analytical Institute",
                "affiliation_identifier": "https://ror.org/03yrm5c26",
                "affiliation_identifier_scheme": "ROR",
                "scheme_uri": "https://ror.org/",
            }
        ]
        assert credit["affiliation"][0]["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": institute.uuid})
        )
        held = made["author"].roles.all()
        assert len(held) == 2
        assert {(role["name"], role["label"]) for role in credit["roles"]} == {
            (role.name, str(role.label)) for role in held
        }

    @pytest.mark.parametrize("kind", CREDIT_KINDS)
    def test_a_person_with_no_identifier_and_no_credited_affiliation_has_neither(
        self, api_client, url_of, record_of, add_team, kind
    ):
        record = record_of(kind)
        add_team(record)

        credit = self.credits_of(api_client, url_of, record)[1]

        assert credit["name"] == "Hopper, Grace"
        assert credit["name_identifiers"] == []
        assert credit["affiliation"] == []

    @pytest.mark.parametrize("kind", CREDIT_KINDS)
    def test_an_organizations_credit_is_organizational_with_no_personal_names(
        self, api_client, url_of, record_of, add_team, kind
    ):
        record = record_of(kind)
        made = add_team(record)
        organization = made["organization"].contributor

        credit = self.credits_of(api_client, url_of, record)[2]

        assert set(credit) == CREDIT_KEYS
        assert credit["name"] == organization.name
        assert credit["name_type"] == "Organizational"
        assert credit["given_name"] is None
        assert credit["family_name"] is None
        assert credit["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": organization.uuid})
        )

    def test_the_address_of_a_credit_returns_that_contributor(
        self, api_client, url_of, record_of, add_team
    ):
        record = record_of("dataset")
        add_team(record)

        for credit in self.credits_of(api_client, url_of, record):
            response = api_client.get(credit["url"])

            assert response.status_code == 200
            assert response.json()["uuid"] == credit["uuid"]

    def test_credits_come_in_the_order_the_record_keeps_them(
        self, api_client, url_of, record_of, add_team
    ):
        record = record_of("dataset")
        made = add_team(record)
        made["organization"].top()

        names = [
            credit["name"] for credit in self.credits_of(api_client, url_of, record)
        ]

        assert names == [
            made["organization"].contributor.name,
            "Lovelace, Ada",
            "Hopper, Grace",
        ]

    @pytest.mark.parametrize("kind", CREDIT_KINDS)
    def test_a_record_with_no_credits_returns_an_empty_list(
        self, api_client, url_of, record_of, kind
    ):
        record = record_of(kind)

        assert self.credits_of(api_client, url_of, record) == []

    def test_a_credit_whose_contributor_was_deleted_is_absent(
        self, api_client, url_of, record_of, add_team
    ):
        record = record_of("dataset")
        made = add_team(record)
        made["bare"].contributor.delete()

        names = [
            credit["name"] for credit in self.credits_of(api_client, url_of, record)
        ]

        assert "Hopper, Grace" not in names
        assert len(names) == 2

    def test_a_credit_whose_affiliation_was_deleted_shows_none(
        self, api_client, url_of, record_of, add_team, author
    ):
        _person, institute = author
        record = record_of("dataset")
        add_team(record)
        institute.delete()

        credit = self.credits_of(api_client, url_of, record)[0]

        assert credit["affiliation"] == []

    def test_a_person_holding_two_identifiers_carries_both(
        self, api_client, url_of, record_of, author
    ):
        from fairdm.factories import ContributorIdentifierFactory

        person, _institute = author
        ContributorIdentifierFactory(
            related=person, type="ISNI", value="0000 0001 2281 955X"
        )
        ContributorIdentifierFactory(related=person, type="Wikidata", value="Q7259")
        record = record_of("dataset")
        add_credit(record, person)

        credit = self.credits_of(api_client, url_of, record)[0]

        assert {
            entry["name_identifier_scheme"] for entry in credit["name_identifiers"]
        } == {
            "ORCID",
            "ISNI",
            "Wikidata",
        }

    def test_an_identifier_with_no_resolver_has_its_value_and_no_scheme_address(
        self, api_client, url_of, record_of
    ):
        from fairdm.factories import ContributorIdentifierFactory, PersonFactory

        person = PersonFactory()
        unresolved = ContributorIdentifierFactory(related=person, type="Local")
        record = record_of("dataset")
        add_credit(record, person)

        credit = self.credits_of(api_client, url_of, record)[0]

        assert credit["name_identifiers"] == [
            {
                "name_identifier": unresolved.value,
                "name_identifier_scheme": "Local",
                "scheme_uri": None,
            }
        ]

    def test_an_affiliation_with_two_identifiers_gives_its_ror_id(
        self, api_client, url_of, record_of, author
    ):
        from fairdm.factories import ContributorIdentifierFactory, OrganizationFactory

        person, _ = author
        institute = OrganizationFactory(name="Difference Works")
        ContributorIdentifierFactory(related=institute, type="Wikidata", value="Q1")
        ContributorIdentifierFactory(related=institute, type="ROR", value="04aj4c181")
        record = record_of("dataset")
        add_credit(record, person, institute)

        affiliation = self.credits_of(api_client, url_of, record)[0]["affiliation"][0]

        assert affiliation["affiliation_identifier_scheme"] == "ROR"
        assert affiliation["affiliation_identifier"] == "https://ror.org/04aj4c181"

    def test_a_person_with_one_name_has_null_for_the_names_they_lack(
        self, api_client, url_of, record_of
    ):
        from fairdm.factories import PersonFactory

        person = PersonFactory(first_name="", last_name="", name="Mononym")
        record = record_of("dataset")
        add_credit(record, person, None)

        credit = self.credits_of(api_client, url_of, record)[0]

        assert credit["name"] == "Mononym"
        assert credit["given_name"] is None
        assert credit["family_name"] is None

    def test_an_affiliation_with_no_identifier_gives_null_for_the_three_keys(
        self, api_client, url_of, record_of
    ):
        from fairdm.factories import OrganizationFactory, PersonFactory

        record = record_of("dataset")
        add_credit(record, PersonFactory(), OrganizationFactory())

        entry = self.credits_of(api_client, url_of, record)[0]["affiliation"][0]

        assert entry["affiliation_identifier"] is None
        assert entry["affiliation_identifier_scheme"] is None
        assert entry["scheme_uri"] is None

    @pytest.mark.parametrize("kind", CREDIT_KINDS)
    def test_the_body_answering_a_create_carries_the_creators_credit(
        self, url_of, member_at, signed_in, body_for, kind
    ):
        from fairdm.factories import PersonFactory

        creator = PersonFactory(
            first_name="Ada", last_name="Lovelace", is_active=True, is_claimed=True
        )

        response = create_through_the_api(
            kind, url_of, member_at, signed_in, body_for, creator
        )

        assert response.status_code == 201, response.content
        credit = next(
            credit
            for credit in response.json()["contributors"]
            if credit["uuid"] == creator.uuid
        )
        assert set(credit) == CREDIT_KEYS
        assert credit["name"] == "Lovelace, Ada"
        assert credit["given_name"] == "Ada"
        assert credit["family_name"] == "Lovelace"

    def test_the_body_answering_a_partial_change_carries_the_same_keys(
        self, url_of, member_at, signed_in
    ):
        from fairdm.factories import PersonFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        editor = PersonFactory(
            first_name="Ada", last_name="Lovelace", is_active=True, is_claimed=True
        )
        member_at(project, ContributionLevel.EDIT, editor)

        response = signed_in(editor).patch(
            url_of(project), {"name": "Renamed"}, format="json"
        )

        assert response.status_code == 200, response.content
        credit = response.json()["contributors"][0]
        assert set(credit) == CREDIT_KEYS
        assert credit["given_name"] == "Ada"
        assert credit["family_name"] == "Lovelace"


def registered(kind):
    """Return the registered sample or measurement types, in a stable order."""
    from fairdm.registry import registry

    models = registry.samples if kind == "sample" else registry.measurements
    return sorted(models, key=lambda model: model.__name__)


COMMON_SAMPLE_FIELDS = (
    "url",
    "uuid",
    "name",
    "local_id",
    "status",
    "dataset",
    "added",
    "modified",
)
COMMON_MEASUREMENT_FIELDS = (
    "url",
    "uuid",
    "name",
    "sample",
    "dataset",
    "added",
    "modified",
)


@pytest.mark.django_db
class TestCommonFields:
    @pytest.mark.parametrize("model", registered("sample"), ids=lambda m: m.__name__)
    def test_a_sample_carries_the_common_fields_and_every_declared_field(
        self, api_client, url_of, make_record, model
    ):
        from fairdm.registry import registry
        from fairdm.registry.config import flatten_fields

        sample = make_record(
            model, DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        declared = flatten_fields(
            registry.get_for_model(model).resolve_fields("serializer")
        )

        data = api_client.get(url_of(sample)).json()

        assert set(COMMON_SAMPLE_FIELDS) <= set(data)
        assert set(declared) <= set(data)
        assert data["dataset"]["uuid"] == sample.dataset.uuid

    @pytest.mark.parametrize(
        "model", registered("measurement"), ids=lambda m: m.__name__
    )
    def test_a_measurement_carries_the_common_fields_and_its_measured_values(
        self, api_client, url_of, make_record, model
    ):
        from fairdm.registry import registry
        from fairdm.registry.config import flatten_fields

        measurement = make_record(
            model, DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        declared = flatten_fields(
            registry.get_for_model(model).resolve_fields("serializer")
        )

        data = api_client.get(url_of(measurement)).json()

        assert set(COMMON_MEASUREMENT_FIELDS) <= set(data)
        assert set(declared) <= set(data)
        assert data["sample"]["uuid"] == measurement.sample.uuid

    def test_a_measured_value_is_returned_as_recorded(
        self, api_client, url_of, make_record
    ):
        from demo.models import XRFMeasurement

        measurement = make_record(
            XRFMeasurement,
            DatasetFactory(visibility=Visibility.PUBLIC, published=True),
            element="Fe",
            concentration_ppm="123.45",
        )

        data = api_client.get(url_of(measurement)).json()

        assert data["element"] == "Fe"
        assert float(data["concentration_ppm"]) == 123.45


KINDS_WITH_A_PAGE = (
    "project",
    "dataset",
    "sample",
    "measurement",
    "person",
    "organisation",
)


@pytest.mark.django_db
class TestPageOnThePortal:
    @staticmethod
    def build(kind, make_record):
        """Build a record of a kind that anyone may see, and return it."""
        from demo.models import ExampleMeasurement, RockSample
        from fairdm.factories import OrganizationFactory, PersonFactory

        if kind == "person":
            return PersonFactory(is_claimed=True)
        if kind == "organisation":
            return OrganizationFactory()
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        if kind == "project":
            return project
        if kind == "dataset":
            return dataset
        return make_record(
            RockSample if kind == "sample" else ExampleMeasurement, dataset
        )

    @staticmethod
    def routes(record, url_of):
        """Return the list and record addresses that serve a record."""
        return url_of(type(record), "list"), url_of(record)

    @pytest.mark.parametrize("kind", KINDS_WITH_A_PAGE)
    def test_a_record_carries_the_absolute_address_of_its_page(
        self, api_client, url_of, make_record, kind
    ):
        record = self.build(kind, make_record)
        _list, detail = self.routes(record, url_of)

        data = api_client.get(detail).json()

        assert data["html_url"] == f"http://testserver{record.get_absolute_url()}"

    @pytest.mark.parametrize("kind", KINDS_WITH_A_PAGE)
    def test_a_list_carries_it_too(self, api_client, url_of, make_record, kind):
        record = self.build(kind, make_record)
        listing, _detail = self.routes(record, url_of)

        rows = api_client.get(listing, {"page_size": 1000}).json()["results"]

        row = next(row for row in rows if row["uuid"] == record.uuid)
        assert row["html_url"] == f"http://testserver{record.get_absolute_url()}"

    @pytest.mark.parametrize("kind", KINDS_WITH_A_PAGE)
    def test_the_address_returns_the_page(
        self, api_client, client, url_of, make_record, kind
    ):
        from urllib.parse import urlsplit

        record = self.build(kind, make_record)
        _list, detail = self.routes(record, url_of)
        address = api_client.get(detail).json()["html_url"]

        response = client.get(urlsplit(address).path)

        assert response.status_code == 200

    @pytest.mark.parametrize("kind", KINDS_WITH_A_PAGE)
    def test_it_follows_the_address_of_the_record_in_the_api(
        self, api_client, url_of, make_record, kind
    ):
        record = self.build(kind, make_record)
        _list, detail = self.routes(record, url_of)

        data = api_client.get(detail).json()

        keys = list(data)
        assert keys[keys.index("url") + 1] == "html_url"

    @pytest.mark.parametrize("kind", ("project", "dataset", "sample"))
    def test_a_value_sent_for_it_is_ignored(
        self, url_of, make_record, member_at, signed_in, kind
    ):
        record = self.build(kind, make_record)
        client = signed_in(member_at(record, ContributionLevel.EDIT))

        response = client.patch(
            url_of(record),
            {"name": "Renamed", "html_url": "https://example.org/elsewhere"},
            format="json",
        )

        assert response.status_code == 200, response.content
        assert response.json()["name"] == "Renamed"
        assert response.json()["html_url"] == (
            f"http://testserver{record.get_absolute_url()}"
        )


@pytest.mark.django_db
class TestNoDatabaseNumbers:
    RELATIONS = (
        "project",
        "dataset",
        "sample",
        "owner",
        "license",
        "contributor",
        "affiliation",
        "location",
        "polymorphic_ctype",
        "created_by",
    )

    @staticmethod
    def walk(value, path=""):
        """Yield the path of every key that is a database number or holds one."""
        if isinstance(value, dict):
            for key, inner in value.items():
                where = f"{path}.{key}"
                if key in ("id", "pk") or (
                    key in TestNoDatabaseNumbers.RELATIONS and isinstance(inner, int)
                ):
                    yield where
                yield from TestNoDatabaseNumbers.walk(inner, where)
        elif isinstance(value, list):
            for position, inner in enumerate(value):
                yield from TestNoDatabaseNumbers.walk(inner, f"{path}[{position}]")

    @pytest.fixture
    def every_address(self, url_of, make_record, add_metadata):
        """The list and record address of every kind of record and registered type."""
        from fairdm.factories import OrganizationFactory, PersonFactory

        project = add_metadata(ProjectFactory(visibility=Visibility.PUBLIC))
        dataset = add_metadata(
            DatasetFactory(
                project=project, visibility=Visibility.PUBLIC, published=True
            )
        )
        records = [project, dataset]
        records += [
            add_metadata(make_record(model, dataset))
            for model in registered("sample") + registered("measurement")
        ]
        addresses = [
            address
            for record in records
            for address in (url_of(type(record), "list"), url_of(record))
        ]
        addresses += [
            reverse("api:person-list"),
            reverse("api:organization-list"),
        ]
        for contributor in (PersonFactory(), OrganizationFactory()):
            addresses.append(url_of(contributor))
        return addresses

    def test_no_list_or_record_response_carries_a_database_number(
        self, api_client, every_address
    ):
        found = []
        for address in every_address:
            response = api_client.get(address)
            assert response.status_code == 200, address
            found += [f"{address}{where}" for where in self.walk(response.json())]

        assert found == []


@pytest.mark.django_db
class TestContributor:
    ACCOUNT_KEYS = (
        "email",
        "password",
        "is_staff",
        "is_superuser",
        "is_active",
        "last_login",
        "date_joined",
        "groups",
        "user_permissions",
        "is_claimed",
    )

    @pytest.fixture
    def person(self):
        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory(
            email="private.address@example.org",
            is_claimed=True,
            links=["https://example.org/me"],
            lang=["en"],
        )
        ContributorIdentifierFactory(related=person, type="ORCID")
        AffiliationFactory(
            person=person, organization=OrganizationFactory(), is_primary=True
        )
        return person

    @pytest.fixture
    def organisation(self):
        from fairdm.factories import ContributorIdentifierFactory, OrganizationFactory

        organisation = OrganizationFactory(parent=OrganizationFactory())
        ContributorIdentifierFactory(
            related=organisation, type="ROR", value="03yrm5c26"
        )
        return organisation

    @staticmethod
    def keys_of(value):
        """Return every key that appears anywhere in a response."""
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from TestContributor.keys_of(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from TestContributor.keys_of(inner)

    def test_a_person_is_returned_with_what_their_profile_page_shows(
        self, api_client, person
    ):
        response = api_client.get(
            reverse("api:person-detail", kwargs={"uuid": person.uuid})
        )

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == person.uuid
        assert data["name"] == person.name
        assert data["identifiers"][0]["value"] == person.identifiers.get().value
        assert data["primary_organization"]["uuid"] == person.primary_organization.uuid

    def test_an_organisation_is_returned_with_what_its_profile_page_shows(
        self, api_client, organisation
    ):
        response = api_client.get(
            reverse("api:organization-detail", kwargs={"uuid": organisation.uuid})
        )

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == organisation.uuid
        assert data["name"] == organisation.name
        assert data["identifiers"][0]["value"] == "03yrm5c26"

    def test_no_response_carries_an_account_detail(
        self, api_client, person, organisation
    ):
        responses = [
            api_client.get(reverse("api:person-list")),
            api_client.get(reverse("api:organization-list")),
            api_client.get(reverse("api:person-detail", kwargs={"uuid": person.uuid})),
        ]

        for response in responses:
            assert response.status_code == 200
            assert set(self.keys_of(response.json())).isdisjoint(self.ACCOUNT_KEYS)
            assert person.email not in response.content.decode()

    def test_a_superuser_and_the_anonymous_account_are_not_listed(
        self, api_client, person
    ):
        from fairdm.factories import PersonFactory

        administrator = PersonFactory(is_superuser=True, is_staff=True)
        anonymous = PersonFactory(email="AnonymousUser")

        listed = [
            row["uuid"]
            for row in api_client.get(reverse("api:person-list")).json()["results"]
        ]

        assert person.uuid in listed
        assert administrator.uuid not in listed
        assert anonymous.uuid not in listed

    def test_a_superuser_is_answered_as_a_record_that_does_not_exist(self, api_client):
        from fairdm.factories import PersonFactory

        administrator = PersonFactory(is_superuser=True, is_staff=True)

        response = api_client.get(
            reverse("api:person-detail", kwargs={"uuid": administrator.uuid})
        )

        assert response.status_code == 404


PERSON_LIST_KEYS = {
    "url",
    "html_url",
    "uuid",
    "name",
    "given_name",
    "family_name",
    "identifiers",
    "primary_organization",
}

ORGANIZATION_LIST_KEYS = {
    "url",
    "html_url",
    "uuid",
    "name",
    "type",
    "country",
    "identifiers",
}

#: What only a single record carries, or nothing in the API: never a list entry.
LEFT_OUT_OF_A_LIST = {
    "alternative_names",
    "profile",
    "links",
    "languages",
    "image",
    "affiliations",
    "projects",
    "datasets",
    "city",
    "parent",
    "sub_organizations",
    "members",
    "added",
    "modified",
}


@pytest.mark.django_db
class TestPeopleList:
    @pytest.fixture
    def listed(self, api_client):
        """Return a function giving the entries of the people list, by identifier."""

        def listed(**query):
            response = api_client.get(
                reverse("api:person-list"), {"page_size": 1000, **query}
            )
            assert response.status_code == 200, response.content
            return {row["uuid"]: row for row in response.json()["results"]}

        return listed

    def test_the_list_holds_people_only(self, listed):
        person = PersonFactory()
        organization = OrganizationFactory()

        entries = listed()

        assert person.uuid in entries
        assert organization.uuid not in entries

    def test_an_entry_carries_the_keys_of_the_list_shape_and_no_others(self, listed):
        person = PersonFactory()

        entry = listed()[person.uuid]

        assert set(entry) == PERSON_LIST_KEYS

    def test_an_entry_leaves_out_what_a_single_record_carries(self, listed):
        person = PersonFactory(links=["https://example.org/me"], lang=["en"])

        entry = listed()[person.uuid]

        assert set(entry).isdisjoint(LEFT_OUT_OF_A_LIST)

    def test_an_entry_names_the_person_and_their_identifiers(self, listed):
        from fairdm.factories import ContributorIdentifierFactory

        person = PersonFactory(first_name="Ada", last_name="Lovelace")
        identifier = ContributorIdentifierFactory(related=person, type="ORCID")

        entry = listed()[person.uuid]

        assert entry["name"] == person.name
        assert entry["given_name"] == "Ada"
        assert entry["family_name"] == "Lovelace"
        assert entry["identifiers"] == [
            {
                "type": "ORCID",
                "value": identifier.value,
                "link": f"https://orcid.org/{identifier.value}",
            }
        ]

    def test_an_entry_carries_the_address_of_the_person_in_the_api_and_on_the_portal(
        self, listed
    ):
        person = PersonFactory(is_claimed=True)

        entry = listed()[person.uuid]

        assert entry["url"].endswith(
            reverse("api:person-detail", kwargs={"uuid": person.uuid})
        )
        assert entry["html_url"] == f"http://testserver{person.get_absolute_url()}"

    def test_a_verified_current_primary_affiliation_is_the_primary_organization(
        self, listed
    ):
        from fairdm.factories import AffiliationFactory

        person = PersonFactory()
        institute = OrganizationFactory()
        AffiliationFactory(person=person, organization=institute, is_primary=True)

        entry = listed()[person.uuid]

        assert entry["primary_organization"] == {
            "uuid": institute.uuid,
            "url": entry["primary_organization"]["url"],
            "name": institute.name,
        }
        assert entry["primary_organization"]["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": institute.uuid})
        )

    @pytest.mark.parametrize("state", ["pending", "ended"])
    def test_a_primary_affiliation_that_is_pending_or_ended_gives_no_primary_organization(
        self, listed, state
    ):
        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.factories import AffiliationFactory

        person = PersonFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=OrganizationFactory(),
            is_primary=True,
            **(
                {"type": Affiliation.MembershipType.PENDING}
                if state == "pending"
                else {"end_date": "2021"}
            ),
        )

        entry = listed()[person.uuid]

        assert affiliation.is_primary
        assert entry["primary_organization"] is None

    def test_a_person_with_no_affiliation_has_no_primary_organization(self, listed):
        person = PersonFactory()

        assert listed()[person.uuid]["primary_organization"] is None

    @pytest.mark.parametrize("name", ["added", "modified"])
    def test_added_and_modified_are_not_returned_but_can_order_the_list(
        self, api_client, name
    ):
        PersonFactory.create_batch(2)

        for ordering in (name, f"-{name}"):
            response = api_client.get(
                reverse("api:person-list"), {"ordering": ordering}
            )

            assert response.status_code == 200
            assert all(name not in row for row in response.json()["results"])

    def test_an_unclaimed_profile_is_listed_like_any_other_person(self, listed):
        person = PersonFactory(is_claimed=False)

        assert person.uuid in listed()

    @pytest.mark.parametrize(
        "account",
        [
            {"is_superuser": True, "is_staff": True},
            {"email": "AnonymousUser"},
        ],
        ids=["superuser", "anonymous"],
    )
    def test_an_account_the_portal_leaves_out_is_absent_and_answered_404_by_address(
        self, api_client, listed, account
    ):
        visible = PersonFactory()
        hidden = PersonFactory(**account)

        entries = listed()

        assert visible.uuid in entries
        assert hidden.uuid not in entries
        response = api_client.get(
            reverse("api:person-detail", kwargs={"uuid": hidden.uuid})
        )
        assert response.status_code == 404

    def test_the_list_is_paged(self, api_client):
        PersonFactory.create_batch(3)

        first = api_client.get(reverse("api:person-list"), {"page_size": 2}).json()
        second = api_client.get(
            reverse("api:person-list"), {"page_size": 2, "page": 2}
        ).json()

        assert first["count"] == 3
        assert len(first["results"]) == 2
        assert first["next"] is not None
        assert len(second["results"]) == 1
        assert second["next"] is None

    @pytest.mark.parametrize("direction", ["", "-"])
    def test_the_list_sorts_by_name_in_either_direction(self, api_client, direction):
        for name in ("Charlie Chan", "Alpha Adams", "Bravo Brown"):
            PersonFactory(name=name)

        response = api_client.get(
            reverse("api:person-list"), {"ordering": f"{direction}name"}
        )

        assert response.status_code == 200
        names = [row["name"] for row in response.json()["results"]]
        assert names == sorted(names, reverse=direction == "-")
        assert len(names) == 3

    def test_the_list_is_in_name_order_when_no_order_is_asked_for(self, api_client):
        for name in ("Charlie Chan", "Alpha Adams", "Bravo Brown"):
            PersonFactory(name=name)

        response = api_client.get(reverse("api:person-list"))

        names = [row["name"] for row in response.json()["results"]]
        assert names == ["Alpha Adams", "Bravo Brown", "Charlie Chan"]

    def test_the_list_narrows_by_the_moment_a_person_was_changed(self, api_client):
        from datetime import UTC, datetime

        old = PersonFactory()
        recent = PersonFactory()
        Person.objects.filter(pk=old.pk).update(
            modified=datetime(2024, 1, 15, 12, tzinfo=UTC)
        )
        Person.objects.filter(pk=recent.pk).update(
            modified=datetime(2026, 1, 15, 12, tzinfo=UTC)
        )

        response = api_client.get(
            reverse("api:person-list"), {"modified_after": "2025-01-01T00:00:00Z"}
        )

        assert response.status_code == 200
        found = {row["uuid"] for row in response.json()["results"]}
        assert recent.uuid in found
        assert old.uuid not in found


#: What the people responses must never carry, at any depth.
ACCOUNT_STATE_KEYS = {
    "email",
    "password",
    "is_staff",
    "is_superuser",
    "is_active",
    "is_claimed",
    "last_login",
    "date_joined",
    "groups",
    "user_permissions",
    "portal_roles",
    "config",
    "synced_data",
    "last_synced",
    "added",
    "modified",
}

PERSON_KEYS = PERSON_LIST_KEYS | {
    "alternative_names",
    "profile",
    "links",
    "languages",
    "image",
    "affiliations",
    "projects",
    "datasets",
}


@pytest.mark.django_db
class TestPerson:
    @pytest.fixture
    def person(self):
        return PersonFactory(
            first_name="Ada",
            last_name="Lovelace",
            profile="Wrote the first program.",
            alternative_names=["A. A. King", "Countess of Lovelace"],
            links=["https://example.org/ada", "javascript:alert(1)"],
            lang=["en", "de"],
            is_claimed=True,
        )

    @staticmethod
    def record(client, person):
        response = client.get(
            reverse("api:person-detail", kwargs={"uuid": person.uuid})
        )
        assert response.status_code == 200, response.content
        data: dict = response.json()
        return data

    @staticmethod
    def keys_of(value):
        """Return every key that appears anywhere in a response."""
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from TestPerson.keys_of(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from TestPerson.keys_of(inner)

    def test_a_person_carries_the_list_keys_and_what_only_a_record_carries(
        self, api_client, person
    ):
        data = self.record(api_client, person)

        assert set(data) == PERSON_KEYS

    def test_a_person_carries_everything_their_list_entry_does(
        self, api_client, person
    ):
        from fairdm.factories import AffiliationFactory

        AffiliationFactory(
            person=person, organization=OrganizationFactory(), is_primary=True
        )
        entry = next(
            row
            for row in api_client.get(reverse("api:person-list")).json()["results"]
            if row["uuid"] == person.uuid
        )

        data = self.record(api_client, person)

        assert {key: data[key] for key in PERSON_LIST_KEYS} == entry

    def test_a_person_carries_the_profile_the_page_shows(self, api_client, person):
        data = self.record(api_client, person)

        assert data["profile"] == "Wrote the first program."
        assert data["alternative_names"] == ["A. A. King", "Countess of Lovelace"]

    def test_links_are_the_web_addresses_the_page_draws(self, api_client, person):
        data = self.record(api_client, person)

        assert data["links"] == ["https://example.org/ada"]

    def test_languages_are_named_as_the_page_names_them(self, api_client, person):
        data = self.record(api_client, person)

        assert data["languages"] == [str(name) for name in person.get_language_names()]
        assert len(data["languages"]) == 2

    def test_a_person_with_no_links_languages_or_other_names_returns_empty_lists(
        self, api_client
    ):
        person = PersonFactory(links=[], lang=[], alternative_names=[])

        data = self.record(api_client, person)

        assert data["links"] == []
        assert data["languages"] == []
        assert data["alternative_names"] == []

    def test_a_person_with_no_image_has_a_null_image(self, api_client, person):
        assert self.record(api_client, person)["image"] is None

    def test_an_image_is_given_as_an_address(self, api_client):
        person = PersonFactory(with_image=True)

        image = self.record(api_client, person)["image"]

        assert image.startswith("http://testserver/")

    def test_an_affiliation_names_its_organization_and_gives_its_kind_and_dates(
        self, api_client, person
    ):
        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.factories import AffiliationFactory

        institute = OrganizationFactory()
        AffiliationFactory(
            person=person,
            organization=institute,
            type=Affiliation.MembershipType.ADMIN,
            is_primary=True,
            start_date="2019",
        )

        (entry,) = self.record(api_client, person)["affiliations"]

        assert set(entry) == {"organization", "type", "start", "end", "is_primary"}
        assert entry["organization"] == {
            "uuid": institute.uuid,
            "url": entry["organization"]["url"],
            "name": institute.name,
        }
        assert entry["organization"]["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": institute.uuid})
        )
        assert entry["type"] == "admin"
        assert entry["start"] == "2019"
        assert entry["end"] is None
        assert entry["is_primary"] is True

    @pytest.mark.parametrize(
        ("level", "name"),
        [(1, "member"), (2, "admin"), (3, "owner")],
    )
    def test_the_kind_of_an_affiliation_is_the_lower_case_name_of_its_level(
        self, api_client, person, level, name
    ):
        from fairdm.factories import AffiliationFactory

        AffiliationFactory(
            person=person, organization=OrganizationFactory(), type=level
        )

        (entry,) = self.record(api_client, person)["affiliations"]

        assert entry["type"] == name

    def test_an_affiliation_with_no_dates_returns_null_for_both(
        self, api_client, person
    ):
        from fairdm.factories import AffiliationFactory

        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(),
            start_date=None,
            end_date=None,
        )

        (entry,) = self.record(api_client, person)["affiliations"]

        assert entry["start"] is None
        assert entry["end"] is None

    def test_a_pending_affiliation_is_absent(self, api_client, person):
        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.factories import AffiliationFactory

        verified = OrganizationFactory()
        pending = OrganizationFactory()
        AffiliationFactory(person=person, organization=verified)
        AffiliationFactory(
            person=person,
            organization=pending,
            type=Affiliation.MembershipType.PENDING,
        )

        shown = {
            entry["organization"]["uuid"]
            for entry in self.record(api_client, person)["affiliations"]
        }

        assert shown == {verified.uuid}

    def test_an_ended_affiliation_is_present_with_its_end_after_the_current_ones(
        self, api_client, person
    ):
        from fairdm.factories import AffiliationFactory

        former = OrganizationFactory()
        current = OrganizationFactory()
        AffiliationFactory(
            person=person, organization=former, start_date="2015", end_date="2018"
        )
        AffiliationFactory(person=person, organization=current, is_primary=True)

        entries = self.record(api_client, person)["affiliations"]

        assert [entry["organization"]["uuid"] for entry in entries] == [
            current.uuid,
            former.uuid,
        ]
        assert entries[0]["end"] is None
        assert entries[1]["start"] == "2015"
        assert entries[1]["end"] == "2018"
        assert entries[1]["is_primary"] is False

    def test_a_person_with_no_affiliation_has_an_empty_list(self, api_client, person):
        assert self.record(api_client, person)["affiliations"] == []

    def test_the_primary_affiliation_comes_first_among_the_current_ones(
        self, api_client, person
    ):
        from fairdm.factories import AffiliationFactory

        other = OrganizationFactory(name="Aardvark Institute")
        primary = OrganizationFactory(name="Zebra Institute")
        AffiliationFactory(person=person, organization=other)
        AffiliationFactory(person=person, organization=primary, is_primary=True)

        entries = self.record(api_client, person)["affiliations"]

        assert [entry["organization"]["uuid"] for entry in entries] == [
            primary.uuid,
            other.uuid,
        ]

    def test_an_unclaimed_profile_is_returned_like_any_other_person(self, api_client):
        person = PersonFactory(is_claimed=False)

        assert self.record(api_client, person)["uuid"] == person.uuid

    def test_no_response_about_a_person_has_a_key_for_account_state(
        self, api_client, person
    ):
        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
        )

        ContributorIdentifierFactory(related=person, type="ORCID")
        AffiliationFactory(
            person=person, organization=OrganizationFactory(), is_primary=True
        )
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(),
            start_date="2010",
            end_date="2012",
        )
        responses = [
            api_client.get(reverse("api:person-list")),
            api_client.get(reverse("api:person-detail", kwargs={"uuid": person.uuid})),
        ]

        for response in responses:
            assert response.status_code == 200
            assert set(self.keys_of(response.json())).isdisjoint(ACCOUNT_STATE_KEYS)
            assert person.email not in response.content.decode()

    def test_a_record_runs_the_queries_of_one_with_fewer_affiliations(self, api_client):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm.factories import AffiliationFactory

        def queries(person):
            address = reverse("api:person-detail", kwargs={"uuid": person.uuid})
            with CaptureQueriesContext(connection) as captured:
                assert api_client.get(address).status_code == 200
            return len(captured)

        few = PersonFactory()
        many = PersonFactory()
        for person, number in ((few, 2), (many, 12)):
            for _ in range(number):
                AffiliationFactory(person=person, organization=OrganizationFactory())
        queries(few)

        assert queries(many) == queries(few)


@pytest.mark.django_db
class TestOrganizationsList:
    @pytest.fixture
    def listed(self, api_client):
        """Return a function giving the entries of the organizations list, by identifier."""

        def listed(**query):
            response = api_client.get(
                reverse("api:organization-list"), {"page_size": 1000, **query}
            )
            assert response.status_code == 200, response.content
            return {row["uuid"]: row for row in response.json()["results"]}

        return listed

    def test_the_list_holds_organizations_only(self, listed):
        person = PersonFactory()
        organization = OrganizationFactory()

        entries = listed()

        assert organization.uuid in entries
        assert person.uuid not in entries

    def test_an_entry_carries_the_keys_of_the_list_shape_and_no_others(self, listed):
        organization = OrganizationFactory()

        entry = listed()[organization.uuid]

        assert set(entry) == ORGANIZATION_LIST_KEYS

    def test_an_entry_leaves_out_what_a_single_record_carries(self, listed):
        organization = OrganizationFactory(
            parent=OrganizationFactory(), links=["https://example.org"]
        )

        entry = listed()[organization.uuid]

        assert set(entry).isdisjoint(LEFT_OUT_OF_A_LIST)

    def test_type_and_country_are_the_stored_codes(self, listed):
        from fairdm.contrib.contributors.choices import OrganizationType

        organization = OrganizationFactory(
            type=OrganizationType.EDUCATION, country="AU"
        )

        entry = listed()[organization.uuid]

        assert entry["type"] == "education"
        assert entry["country"] == "AU"

    def test_an_organization_with_neither_type_nor_country_returns_null_for_both(
        self, listed
    ):
        organization = OrganizationFactory(type=None, country=None)

        entry = listed()[organization.uuid]

        assert entry["type"] is None
        assert entry["country"] in (None, "")

    def test_an_entry_carries_its_identifiers_and_addresses(self, listed):
        from fairdm.factories import ContributorIdentifierFactory

        organization = OrganizationFactory()
        ContributorIdentifierFactory(
            related=organization, type="ROR", value="03yrm5c26"
        )

        entry = listed()[organization.uuid]

        assert entry["identifiers"] == [
            {
                "type": "ROR",
                "value": "03yrm5c26",
                "link": "https://ror.org/03yrm5c26",
            }
        ]
        assert entry["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": organization.uuid})
        )
        assert entry["html_url"] == (
            f"http://testserver{organization.get_absolute_url()}"
        )

    @pytest.mark.parametrize("name", ["added", "modified"])
    def test_added_and_modified_are_not_returned_but_can_order_the_list(
        self, api_client, name
    ):
        OrganizationFactory.create_batch(2)

        for ordering in (name, f"-{name}"):
            response = api_client.get(
                reverse("api:organization-list"), {"ordering": ordering}
            )

            assert response.status_code == 200
            assert all(name not in row for row in response.json()["results"])

    def test_the_list_is_paged(self, api_client):
        OrganizationFactory.create_batch(3)

        first = api_client.get(
            reverse("api:organization-list"), {"page_size": 2}
        ).json()
        second = api_client.get(
            reverse("api:organization-list"), {"page_size": 2, "page": 2}
        ).json()

        assert first["count"] == 3
        assert len(first["results"]) == 2
        assert first["next"] is not None
        assert len(second["results"]) == 1
        assert second["next"] is None

    @pytest.mark.parametrize("direction", ["", "-"])
    def test_the_list_sorts_by_name_in_either_direction(self, api_client, direction):
        for name in ("Charlie Institute", "Alpha Institute", "Bravo Institute"):
            OrganizationFactory(name=name)

        response = api_client.get(
            reverse("api:organization-list"), {"ordering": f"{direction}name"}
        )

        assert response.status_code == 200
        names = [row["name"] for row in response.json()["results"]]
        assert names == sorted(names, reverse=direction == "-")
        assert len(names) == 3

    def test_the_list_is_in_name_order_when_no_order_is_asked_for(self, api_client):
        for name in ("Charlie Institute", "Alpha Institute", "Bravo Institute"):
            OrganizationFactory(name=name)

        response = api_client.get(reverse("api:organization-list"))

        names = [row["name"] for row in response.json()["results"]]
        assert names == ["Alpha Institute", "Bravo Institute", "Charlie Institute"]

    def test_the_list_narrows_by_the_moment_an_organization_was_changed(
        self, api_client
    ):
        old = OrganizationFactory()
        recent = OrganizationFactory()
        Organization.objects.filter(pk=old.pk).update(
            modified=datetime(2024, 1, 15, 12, tzinfo=UTC)
        )
        Organization.objects.filter(pk=recent.pk).update(
            modified=datetime(2026, 1, 15, 12, tzinfo=UTC)
        )

        response = api_client.get(
            reverse("api:organization-list"),
            {"modified_after": "2025-01-01T00:00:00Z"},
        )

        assert response.status_code == 200
        found = {row["uuid"] for row in response.json()["results"]}
        assert recent.uuid in found
        assert old.uuid not in found


ORGANIZATION_KEYS = ORGANIZATION_LIST_KEYS | {
    "alternative_names",
    "profile",
    "city",
    "links",
    "image",
    "parent",
    "sub_organizations",
    "members",
    "projects",
    "datasets",
}


@pytest.mark.django_db
class TestOrganization:
    @pytest.fixture
    def organization(self):
        return OrganizationFactory(
            name="Institute of Marine Science",
            profile="Studies the sea.",
            alternative_names=["IMS", "Marine Science Institute"],
            city="Hobart",
            country="AU",
            links=["https://example.org/ims", "javascript:alert(1)"],
        )

    @staticmethod
    def record(client, organization):
        response = client.get(
            reverse("api:organization-detail", kwargs={"uuid": organization.uuid})
        )
        assert response.status_code == 200, response.content
        data: dict = response.json()
        return data

    @staticmethod
    def keys_of(value):
        """Return every key that appears anywhere in a response."""
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from TestOrganization.keys_of(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from TestOrganization.keys_of(inner)

    @staticmethod
    def join(organization, **kwargs):
        """Affiliate a new person with an organization, giving the person."""
        from fairdm.factories import AffiliationFactory

        return AffiliationFactory(organization=organization, **kwargs).person

    def test_an_organization_carries_the_list_keys_and_what_only_a_record_carries(
        self, api_client, organization
    ):
        data = self.record(api_client, organization)

        assert set(data) == ORGANIZATION_KEYS

    def test_an_organization_carries_everything_its_list_entry_does(
        self, api_client, organization
    ):
        from fairdm.factories import ContributorIdentifierFactory

        ContributorIdentifierFactory(
            related=organization, type="ROR", value="03yrm5c26"
        )
        entry = next(
            row
            for row in api_client.get(reverse("api:organization-list")).json()[
                "results"
            ]
            if row["uuid"] == organization.uuid
        )

        data = self.record(api_client, organization)

        assert {key: data[key] for key in ORGANIZATION_LIST_KEYS} == entry

    def test_an_organization_carries_the_profile_the_other_names_and_the_city(
        self, api_client, organization
    ):
        data = self.record(api_client, organization)

        assert data["profile"] == "Studies the sea."
        assert data["alternative_names"] == ["IMS", "Marine Science Institute"]
        assert data["city"] == "Hobart"

    def test_links_are_the_web_addresses_the_page_draws(self, api_client, organization):
        assert self.record(api_client, organization)["links"] == [
            "https://example.org/ims"
        ]

    def test_an_organization_with_no_links_or_other_names_returns_empty_lists(
        self, api_client
    ):
        data = self.record(
            api_client, OrganizationFactory(links=[], alternative_names=[])
        )

        assert data["links"] == []
        assert data["alternative_names"] == []

    def test_an_organization_with_no_image_has_a_null_image(
        self, api_client, organization
    ):
        assert self.record(api_client, organization)["image"] is None

    def test_the_parent_is_named_by_identifier_address_and_name(self, api_client):
        university = OrganizationFactory(name="University of Tasmania")
        department = OrganizationFactory(parent=university)

        data = self.record(api_client, department)

        assert data["parent"] == {
            "uuid": university.uuid,
            "url": data["parent"]["url"],
            "name": "University of Tasmania",
        }
        assert data["parent"]["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": university.uuid})
        )

    def test_an_organization_with_no_parent_has_a_null_parent(
        self, api_client, organization
    ):
        assert self.record(api_client, organization)["parent"] is None

    def test_sub_organizations_are_named_by_identifier_address_and_name_by_name(
        self, api_client, organization
    ):
        zoology = OrganizationFactory(name="Zoology", parent=organization)
        acoustics = OrganizationFactory(name="Acoustics", parent=organization)
        OrganizationFactory(name="Elsewhere", parent=OrganizationFactory())

        entries = self.record(api_client, organization)["sub_organizations"]

        assert [entry["name"] for entry in entries] == ["Acoustics", "Zoology"]
        assert [entry["uuid"] for entry in entries] == [acoustics.uuid, zoology.uuid]
        assert entries[0]["url"].endswith(
            reverse("api:organization-detail", kwargs={"uuid": acoustics.uuid})
        )
        assert all(set(entry) == {"uuid", "url", "name"} for entry in entries)

    def test_an_organization_with_no_sub_organizations_or_members_has_empty_lists(
        self, api_client, organization
    ):
        data = self.record(api_client, organization)

        assert data["sub_organizations"] == []
        assert data["members"] == []

    def test_a_member_names_the_person_and_gives_the_kind_of_affiliation(
        self, api_client, organization
    ):
        from fairdm.contrib.contributors.models import Affiliation

        person = self.join(organization, type=Affiliation.MembershipType.ADMIN)

        (entry,) = self.record(api_client, organization)["members"]

        assert set(entry) == {"person", "type"}
        assert entry["person"] == {
            "uuid": person.uuid,
            "url": entry["person"]["url"],
            "name": person.name,
        }
        assert entry["person"]["url"].endswith(
            reverse("api:person-detail", kwargs={"uuid": person.uuid})
        )
        assert entry["type"] == "admin"

    @pytest.mark.parametrize(
        ("level", "name"),
        [(1, "member"), (2, "admin"), (3, "owner")],
    )
    def test_the_kind_of_a_member_is_the_lower_case_name_of_their_level(
        self, api_client, organization, level, name
    ):
        self.join(organization, type=level)

        (entry,) = self.record(api_client, organization)["members"]

        assert entry["type"] == name

    def test_the_people_who_run_the_organization_come_first_then_by_name(
        self, api_client, organization
    ):
        from fairdm.contrib.contributors.models import Affiliation

        MemberType = Affiliation.MembershipType
        for name, level in (
            ("Zoe Member", MemberType.MEMBER),
            ("Abe Member", MemberType.MEMBER),
            ("Yan Admin", MemberType.ADMIN),
            ("Mia Owner", MemberType.OWNER),
            ("Bea Admin", MemberType.ADMIN),
        ):
            self.join(organization, type=level, person__name=name)

        entries = self.record(api_client, organization)["members"]

        assert [(entry["person"]["name"], entry["type"]) for entry in entries] == [
            ("Mia Owner", "owner"),
            ("Bea Admin", "admin"),
            ("Yan Admin", "admin"),
            ("Abe Member", "member"),
            ("Zoe Member", "member"),
        ]

    def test_a_pending_member_is_absent(self, api_client, organization):
        from fairdm.contrib.contributors.models import Affiliation

        verified = self.join(organization)
        pending = self.join(organization, type=Affiliation.MembershipType.PENDING)

        shown = {
            entry["person"]["uuid"]
            for entry in self.record(api_client, organization)["members"]
        }

        assert shown == {verified.uuid}
        assert pending.uuid not in shown

    def test_a_member_whose_affiliation_has_ended_is_absent(
        self, api_client, organization
    ):
        current = self.join(organization)
        former = self.join(organization, start_date="2015", end_date="2018")

        shown = {
            entry["person"]["uuid"]
            for entry in self.record(api_client, organization)["members"]
        }

        assert shown == {current.uuid}
        assert former.uuid not in shown

    @pytest.mark.parametrize(
        "account",
        [
            {"is_superuser": True, "is_staff": True},
            {"email": "AnonymousUser"},
        ],
        ids=["superuser", "anonymous"],
    )
    def test_a_member_the_people_list_leaves_out_is_absent(
        self, api_client, organization, account
    ):
        visible = self.join(organization)
        hidden = self.join(
            organization, **{f"person__{field}": v for field, v in account.items()}
        )

        shown = {
            entry["person"]["uuid"]
            for entry in self.record(api_client, organization)["members"]
        }

        assert shown == {visible.uuid}

    def test_no_response_about_an_organization_has_a_key_for_account_state(
        self, api_client, organization
    ):
        person = self.join(organization, person__email="private.address@example.org")
        OrganizationFactory(parent=organization)
        responses = [
            api_client.get(reverse("api:organization-list")),
            api_client.get(
                reverse("api:organization-detail", kwargs={"uuid": organization.uuid})
            ),
        ]

        for response in responses:
            assert response.status_code == 200
            assert set(self.keys_of(response.json())).isdisjoint(ACCOUNT_STATE_KEYS)
            assert person.email not in response.content.decode()


@pytest.mark.django_db
class TestOrganizationQueries:
    def test_a_record_runs_the_queries_of_one_with_fewer_members(self, api_client):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm.factories import AffiliationFactory

        def read(organization):
            address = reverse(
                "api:organization-detail", kwargs={"uuid": organization.uuid}
            )
            with CaptureQueriesContext(connection) as captured:
                response = api_client.get(address)
            assert response.status_code == 200
            return len(captured), len(response.json()["members"])

        few = OrganizationFactory(parent=OrganizationFactory())
        many = OrganizationFactory(parent=OrganizationFactory())
        for organization, number in ((few, 2), (many, 30)):
            for _ in range(number):
                AffiliationFactory(organization=organization)
            OrganizationFactory.create_batch(2, parent=organization)
        read(few)

        queries_few, members_few = read(few)
        queries_many, members_many = read(many)

        assert (members_few, members_many) == (2, 30)
        assert queries_many == queries_few


@pytest.mark.django_db
class TestContributorRecordAddresses:
    @pytest.fixture(params=["person", "organization"])
    def contributor(self, request):
        """A person, and then an organization, each credited on a public project and dataset."""
        from fairdm.factories import ContributionFactory

        contributor = (
            PersonFactory() if request.param == "person" else OrganizationFactory()
        )
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        for record in (project, dataset):
            ContributionFactory(
                content_object=record,
                contributor=contributor,
                level=None if contributor.is_organization else ContributionLevel.VIEW,
            )
        contributor.credited = {"projects": project, "datasets": dataset}
        return contributor

    @staticmethod
    def record(client, contributor):
        route = "person" if isinstance(contributor, Person) else "organization"
        response = client.get(
            reverse(f"api:{route}-detail", kwargs={"uuid": contributor.uuid})
        )
        assert response.status_code == 200, response.content
        data: dict = response.json()
        return data

    @pytest.mark.parametrize("kind", ["projects", "datasets"])
    def test_a_record_gives_the_absolute_address_of_the_narrowed_list(
        self, api_client, contributor, kind
    ):
        from urllib.parse import parse_qs, urlparse

        address = urlparse(self.record(api_client, contributor)[kind])

        assert address.scheme == "http"
        assert address.netloc == "testserver"
        assert address.path == reverse(f"api:{kind[:-1]}-list")
        assert parse_qs(address.query) == {"contributor": [contributor.uuid]}

    @pytest.mark.parametrize("kind", ["projects", "datasets"])
    def test_requesting_the_address_returns_the_records_credited(
        self, api_client, contributor, kind
    ):
        address = self.record(api_client, contributor)[kind]
        other = ProjectFactory(visibility=Visibility.PUBLIC)

        response = api_client.get(address)

        assert response.status_code == 200
        assert {row["uuid"] for row in response.json()["results"]} == {
            contributor.credited[kind].uuid
        }
        assert other.uuid not in {row["uuid"] for row in response.json()["results"]}

    def test_a_list_entry_carries_neither_address(self, api_client, contributor):
        route = "person" if isinstance(contributor, Person) else "organization"

        response = api_client.get(reverse(f"api:{route}-list"))

        [entry] = [
            row for row in response.json()["results"] if row["uuid"] == contributor.uuid
        ]
        assert {"projects", "datasets"}.isdisjoint(entry)

    def test_a_private_record_is_credited_on_its_own_page_and_left_out_of_the_lists(
        self, member_at, signed_in
    ):
        from fairdm.factories import ContributionFactory

        person = PersonFactory()
        dataset = DatasetFactory(
            project=ProjectFactory(visibility=Visibility.PUBLIC),
            visibility=Visibility.PRIVATE,
        )
        ContributionFactory(
            content_object=dataset, contributor=person, level=ContributionLevel.VIEW
        )
        client = signed_in(member_at(dataset, ContributionLevel.VIEW))

        shown = client.get(reverse("api:dataset-detail", kwargs={"uuid": dataset.uuid}))
        listed = client.get(self.record(client, person)["datasets"])

        assert shown.status_code == 200
        assert person.uuid in {
            credit["uuid"] for credit in shown.json()["contributors"]
        }
        assert listed.status_code == 200
        assert listed.json()["results"] == []


def routable_models():
    """Every model with a list and record route: the core kinds and the registered types."""
    from fairdm.contrib.contributors.models import Organization, Person

    return [
        Project,
        Dataset,
        Person,
        Organization,
        *registered("sample"),
        *registered("measurement"),
    ]


@pytest.mark.django_db
class TestListAndRecordRoutes:
    @pytest.fixture
    def a_record_of(self, make_record):
        """Return a function building a public record of a routable model."""
        from fairdm.contrib.contributors.models import Organization, Person

        def a_record_of(model):
            if model is Project:
                return ProjectFactory(visibility=Visibility.PUBLIC)
            if model is Dataset:
                return DatasetFactory(visibility=Visibility.PUBLIC, published=True)
            if model is Person:
                return PersonFactory()
            if model is Organization:
                return OrganizationFactory()
            return make_record(
                model, DatasetFactory(visibility=Visibility.PUBLIC, published=True)
            )

        return a_record_of

    @staticmethod
    def address(model, action, uuid=None):
        from tests.test_api.conftest import route_name

        return reverse(
            route_name(model, action), kwargs={"uuid": uuid} if uuid else None
        )

    @pytest.mark.parametrize("model", routable_models(), ids=lambda m: m.__name__)
    def test_a_list_is_served_to_a_visitor(self, api_client, a_record_of, model):
        record = a_record_of(model)

        response = api_client.get(self.address(model, "list"))

        assert response.status_code == 200
        assert record.uuid in [row["uuid"] for row in response.json()["results"]]

    @pytest.mark.parametrize("model", routable_models(), ids=lambda m: m.__name__)
    def test_a_record_is_found_by_its_short_identifier(
        self, api_client, a_record_of, model
    ):
        record = a_record_of(model)

        response = api_client.get(self.address(model, "detail", record.uuid))

        assert response.status_code == 200
        assert response.json()["uuid"] == record.uuid

    @pytest.mark.parametrize("model", routable_models(), ids=lambda m: m.__name__)
    def test_an_unknown_identifier_is_answered_404(self, api_client, model):
        response = api_client.get(self.address(model, "detail", "xNoSuchRecord"))

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/samples/unregistered-types/",
            "/api/v1/measurements/unregistered-types/",
            "/api/v1/samples/unregistered-types/sNoSuchRecord/",
            "/api/v1/measurements/unregistered-types/mNoSuchRecord/",
        ],
    )
    def test_an_unregistered_type_is_answered_404(self, api_client, path):
        assert api_client.get(path).status_code == 404

    def test_a_sample_type_is_not_served_under_the_measurement_prefix(
        self, api_client, a_record_of
    ):
        from demo.models import RockSample

        record = a_record_of(RockSample)

        response = api_client.get(f"/api/v1/measurements/rock-samples/{record.uuid}/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestFiltering:
    @staticmethod
    def listed(client, address, **query):
        response = client.get(address, query)
        assert response.status_code == 200, response.content
        return {row["uuid"] for row in response.json()["results"]}

    def test_a_declared_filter_narrows_a_sample_list(
        self, api_client, url_of, make_record
    ):
        from demo.models import SoilSample

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        clay = make_record(SoilSample, dataset, soil_type="clay")
        make_record(SoilSample, dataset, soil_type="sand")

        found = self.listed(api_client, url_of(SoilSample, "list"), soil_type="clay")

        assert found == {clay.uuid}

    def test_a_declared_filter_narrows_a_measurement_list(
        self, api_client, url_of, make_record
    ):
        from demo.models import XRFMeasurement

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        iron = make_record(XRFMeasurement, dataset, element="Fe")
        make_record(XRFMeasurement, dataset, element="Si")

        found = self.listed(api_client, url_of(XRFMeasurement, "list"), element="Fe")

        assert found == {iron.uuid}

    def test_a_filter_declared_by_overriding_the_accessor_narrows_a_list(
        self, api_client, url_of, make_record
    ):
        from demo.models import WaterSample

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        river = make_record(WaterSample, dataset, water_source="river")
        make_record(WaterSample, dataset, water_source="well")

        found = self.listed(
            api_client, url_of(WaterSample, "list"), water_source="river"
        )

        assert found == {river.uuid}

    @pytest.mark.parametrize(
        "model",
        registered("sample") + registered("measurement"),
        ids=lambda m: m.__name__,
    )
    def test_a_list_is_narrowed_by_the_short_identifier_of_its_dataset(
        self, api_client, url_of, make_record, model
    ):
        wanted = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        here = make_record(model, wanted)
        make_record(model, DatasetFactory(visibility=Visibility.PUBLIC, published=True))

        found = self.listed(api_client, url_of(model, "list"), dataset=wanted.uuid)

        assert found == {here.uuid}

    @pytest.mark.parametrize(
        "model", registered("measurement"), ids=lambda m: m.__name__
    )
    def test_a_measurement_list_is_narrowed_by_the_short_identifier_of_its_sample(
        self, api_client, url_of, make_record, model
    ):
        from demo.factories import RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = RockSampleFactory(dataset=dataset)
        here = make_record(model, dataset, sample=sample)
        make_record(model, dataset, sample=RockSampleFactory(dataset=dataset))

        found = self.listed(api_client, url_of(model, "list"), sample=sample.uuid)

        assert found == {here.uuid}

    def test_a_person_with_a_level_can_narrow_by_a_private_dataset(
        self, url_of, make_record
    ):
        from demo.models import RockSample
        from fairdm.contrib.contributors.choices import ContributionLevel

        private = DatasetFactory(visibility=Visibility.PRIVATE)
        viewer = person_at(private, ContributionLevel.VIEW)
        here = make_record(RockSample, private)
        make_record(
            RockSample, DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )

        found = self.listed(
            signed_in_as(viewer), url_of(RockSample, "list"), dataset=private.uuid
        )

        assert found == {here.uuid}

    @staticmethod
    def answer_to(client, address, name, sent):
        """Return the status and the body of a refused filter, without the value sent."""
        response = client.get(address, {name: sent})
        return response.status_code, str(response.json()).replace(sent, "<sent>")

    def test_a_visitor_narrowing_by_a_private_dataset_is_answered_as_for_an_unknown_one(
        self, api_client, url_of, make_record
    ):
        from demo.models import RockSample

        private = DatasetFactory(visibility=Visibility.PRIVATE)
        make_record(RockSample, private)
        address = url_of(RockSample, "list")

        answer = self.answer_to(api_client, address, "dataset", private.uuid)

        assert answer[0] == 400
        assert answer == self.answer_to(api_client, address, "dataset", "u" * 23)

    def test_a_visitor_narrowing_by_a_sample_of_a_private_dataset_is_answered_as_for_an_unknown_one(
        self, api_client, url_of, make_record
    ):
        from demo.factories import RockSampleFactory
        from demo.models import ExampleMeasurement

        private = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=private)
        make_record(ExampleMeasurement, private, sample=sample)
        address = url_of(ExampleMeasurement, "list")

        answer = self.answer_to(api_client, address, "sample", sample.uuid)

        assert answer[0] == 400
        assert answer == self.answer_to(api_client, address, "sample", "u" * 23)

    @pytest.mark.parametrize(
        "model",
        registered("sample") + registered("measurement"),
        ids=lambda m: m.__name__,
    )
    def test_a_database_number_is_refused_for_the_dataset(
        self, api_client, url_of, make_record, model
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        make_record(model, dataset)

        response = api_client.get(url_of(model, "list"), {"dataset": dataset.pk})

        assert response.status_code == 400
        assert "dataset" in response.json()

    @pytest.mark.parametrize(
        "model", registered("measurement"), ids=lambda m: m.__name__
    )
    def test_a_database_number_is_refused_for_the_sample(
        self, api_client, url_of, make_record, model
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        measurement = make_record(model, dataset)

        response = api_client.get(
            url_of(model, "list"), {"sample": measurement.sample.pk}
        )

        assert response.status_code == 400
        assert "sample" in response.json()

    @pytest.mark.parametrize(
        "model",
        registered("sample") + registered("measurement"),
        ids=lambda m: m.__name__,
    )
    def test_a_content_type_number_is_not_a_way_to_narrow_a_list(
        self, api_client, url_of, make_record, model
    ):
        from django.contrib.contenttypes.models import ContentType

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        here = make_record(model, dataset)
        other = ContentType.objects.get_for_model(ProjectFactory._meta.model)

        found = self.listed(
            api_client, url_of(model, "list"), polymorphic_ctype=other.pk
        )

        assert here.uuid in found


@pytest.mark.django_db
class TestOrdering:
    NAMES = ("Charlie", "Alpha", "Bravo")

    @pytest.fixture(
        params=[Project, Dataset, *registered("sample"), *registered("measurement")],
        ids=lambda model: model.__name__,
    )
    def model(self, request, make_record):
        """A kind of record, with three public records named out of order."""
        model = request.param
        for name in self.NAMES:
            if model is Project:
                ProjectFactory(name=name, visibility=Visibility.PUBLIC)
            elif model is Dataset:
                DatasetFactory(name=name, visibility=Visibility.PUBLIC, published=True)
            else:
                dataset = Dataset.objects.filter(name="Holder").first() or (
                    DatasetFactory(
                        name="Holder", visibility=Visibility.PUBLIC, published=True
                    )
                )
                make_record(model, dataset, name=name)
        return model

    def names_in(self, client, url_of, model, ordering):
        response = client.get(url_of(model, "list"), {"ordering": ordering})
        assert response.status_code == 200, response.content
        return [row["name"] for row in response.json()["results"]]

    def test_a_list_is_returned_in_ascending_order(self, api_client, url_of, model):
        names = self.names_in(api_client, url_of, model, "name")

        assert names == sorted(self.NAMES)

    def test_a_list_is_returned_in_descending_order(self, api_client, url_of, model):
        names = self.names_in(api_client, url_of, model, "-name")

        assert names == sorted(self.NAMES, reverse=True)

    def test_a_list_is_returned_in_the_order_records_were_added(
        self, api_client, url_of, model
    ):
        oldest_first = self.names_in(api_client, url_of, model, "added")
        newest_first = self.names_in(api_client, url_of, model, "-added")

        assert oldest_first == list(self.NAMES)
        assert newest_first == list(reversed(self.NAMES))


@pytest.mark.django_db
class TestCreating:
    @pytest.mark.parametrize("model", registered("sample"), ids=lambda m: m.__name__)
    def test_someone_at_the_edit_level_creates_a_sample_in_a_dataset(
        self, url_of, member_at, signed_in, body_for, saved, model
    ):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        client = signed_in(member_at(dataset, ContributionLevel.EDIT))
        body, stored = body_for(model)

        response = client.post(
            url_of(model, "list"), {**body, "dataset": dataset.uuid}, format="json"
        )

        assert response.status_code == 201, response.content
        sample = model.objects.get(uuid=response.json()["uuid"])
        assert sample.dataset == dataset
        assert saved(sample, stored) == stored
        assert response.json() == client.get(url_of(sample)).json()

    @pytest.mark.parametrize(
        "model", registered("measurement"), ids=lambda m: m.__name__
    )
    def test_someone_at_the_edit_level_creates_a_measurement_with_its_values(
        self, url_of, member_at, signed_in, body_for, saved, model
    ):
        from demo.factories import RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=dataset)
        client = signed_in(member_at(dataset, ContributionLevel.EDIT))
        body, stored = body_for(model)

        response = client.post(
            url_of(model, "list"),
            {**body, "dataset": dataset.uuid, "sample": sample.uuid},
            format="json",
        )

        assert response.status_code == 201, response.content
        measurement = model.objects.get(uuid=response.json()["uuid"])
        assert measurement.dataset == dataset
        assert measurement.sample_id == sample.pk
        assert saved(measurement, stored) == stored
        assert response.json() == client.get(url_of(measurement)).json()

    def test_someone_at_the_edit_level_creates_a_dataset_in_a_project(
        self, member_at, signed_in
    ):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        client = signed_in(member_at(project, ContributionLevel.EDIT))

        response = client.post(
            reverse("api:dataset-list"),
            {"name": "Sent by a script", "project": project.uuid},
            format="json",
        )

        assert response.status_code == 201, response.content
        dataset = Dataset.all_objects.get(uuid=response.json()["uuid"])
        assert dataset.project == project
        assert dataset.name == "Sent by a script"
        detail = reverse("api:dataset-detail", kwargs={"uuid": dataset.uuid})
        assert response.json() == client.get(detail).json()

    def test_any_signed_in_person_creates_a_project(self, signed_in):
        from fairdm.factories import PersonFactory

        client = signed_in(PersonFactory(is_active=True, is_claimed=True))

        response = client.post(
            reverse("api:project-list"), {"name": "Sent by a script"}, format="json"
        )

        assert response.status_code == 201, response.content
        project = Project.objects.get(uuid=response.json()["uuid"])
        assert project.name == "Sent by a script"
        detail = reverse("api:project-detail", kwargs={"uuid": project.uuid})
        assert response.json() == client.get(detail).json()


def create_through_the_api(
    kind, url_of, member_at, signed_in, body_for, person, **sent
):
    """Create a record of a kind through its route as a person, and return the response.

    The person is given the level the kind needs on its parent first. Anything in ``sent`` is
    added to the body.
    """
    from demo.factories import RockSampleFactory
    from demo.models import RockSample, XRFMeasurement

    client = signed_in(person)
    if kind == "project":
        return client.post(
            reverse("api:project-list"), {"name": "Sent by a script", **sent}, "json"
        )
    if kind == "dataset":
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        member_at(project, ContributionLevel.EDIT, person)
        body = {"name": "Sent by a script", "project": project.uuid, **sent}
        return client.post(reverse("api:dataset-list"), body, format="json")
    dataset = DatasetFactory(visibility=Visibility.PRIVATE)
    member_at(dataset, ContributionLevel.EDIT, person)
    model = RockSample if kind == "sample" else XRFMeasurement
    body, _stored = body_for(model)
    body["dataset"] = dataset.uuid
    if kind == "measurement":
        body["sample"] = RockSampleFactory(dataset=dataset).uuid
    return client.post(url_of(model, "list"), {**body, **sent}, format="json")


def stored_record(kind, uuid):
    """Return the stored project, dataset, sample or measurement with the identifier."""
    from fairdm.core.models import Measurement, Sample

    model = {
        "project": Project,
        "dataset": Dataset,
        "sample": Sample,
        "measurement": Measurement,
    }[kind]
    return getattr(model, "all_objects", model.objects).get(uuid=uuid)


RECORD_KINDS = ["project", "dataset", "sample", "measurement"]


@pytest.mark.django_db
class TestCreatorIsCredited:
    @pytest.mark.parametrize("kind", RECORD_KINDS)
    def test_the_creator_is_listed_at_the_manage_level(
        self, url_of, member_at, signed_in, body_for, kind
    ):
        from fairdm.contrib.contributors.access import RecordAccess
        from fairdm.factories import PersonFactory

        creator = PersonFactory(is_active=True, is_claimed=True)

        response = create_through_the_api(
            kind, url_of, member_at, signed_in, body_for, creator
        )

        assert response.status_code == 201, response.content
        record = stored_record(kind, response.json()["uuid"])
        assert RecordAccess(record).own_level(creator) == ContributionLevel.MANAGE

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_a_created_by_sent_by_the_caller_is_ignored(
        self, url_of, member_at, signed_in, body_for, kind
    ):
        from fairdm.factories import PersonFactory

        creator = PersonFactory(is_active=True, is_claimed=True)
        someone_else = PersonFactory(is_active=True, is_claimed=True)

        response = create_through_the_api(
            kind,
            url_of,
            member_at,
            signed_in,
            body_for,
            creator,
            created_by=someone_else.pk,
        )

        assert response.status_code == 201, response.content
        assert "created_by" not in response.json()
        record = stored_record(kind, response.json()["uuid"])
        assert record.created_by_id == creator.pk

    @pytest.mark.parametrize("kind", RECORD_KINDS)
    def test_a_person_named_as_created_by_is_not_credited(
        self, url_of, member_at, signed_in, body_for, kind
    ):
        from fairdm.contrib.contributors.access import RecordAccess
        from fairdm.factories import PersonFactory

        creator = PersonFactory(is_active=True, is_claimed=True)
        someone_else = PersonFactory(is_active=True, is_claimed=True)

        response = create_through_the_api(
            kind,
            url_of,
            member_at,
            signed_in,
            body_for,
            creator,
            created_by=someone_else.pk,
        )

        record = stored_record(kind, response.json()["uuid"])
        assert RecordAccess(record).own_level(someone_else) is None

    def test_a_superuser_creates_without_being_credited(self, signed_in):
        admin = UserFactory(is_superuser=True, is_staff=True)

        response = signed_in(admin).post(
            reverse("api:project-list"), {"name": "Sent by an admin"}, format="json"
        )

        assert response.status_code == 201
        project = Project.objects.get(uuid=response.json()["uuid"])
        assert project.contributors.count() == 0


def writable_models():
    """Every model the API creates records of: the core kinds with a type and the registered types."""
    return [Project, Dataset, *registered("sample"), *registered("measurement")]


@pytest.fixture
def a_private_record(make_record):
    """Return a function building a private record of a writable model, with its parents."""

    def a_private_record(model):
        if model is Project:
            return ProjectFactory(visibility=Visibility.PRIVATE)
        if model is Dataset:
            return DatasetFactory(
                project=ProjectFactory(visibility=Visibility.PRIVATE),
                visibility=Visibility.PRIVATE,
            )
        return make_record(model, DatasetFactory(visibility=Visibility.PRIVATE))

    return a_private_record


@pytest.fixture
def replacement_for(body_for):
    """Return a function giving a full body that replaces a record, naming the parents it has."""

    def replacement_for(record):
        model = type(record)
        if model is Project:
            other = next(
                value
                for value, _label in Project.STATUS_CHOICES.choices
                if value != record.status
            )
            body = {"name": "Replaced by a script", "status": other}
            return body, dict(body)
        if model is Dataset:
            body = {"name": "Replaced by a script", "project": record.project.uuid}
            return body, {"name": "Replaced by a script"}
        body, stored = body_for(model, name="Replaced by a script")
        body["dataset"] = record.dataset.uuid
        if "sample" in {field.name for field in model._meta.fields}:
            body["sample"] = record.sample.uuid
        return body, stored

    return replacement_for


@pytest.mark.django_db
class TestChanging:
    @staticmethod
    def edited_by_an_editor(record, member_at, signed_in):
        return signed_in(member_at(record, ContributionLevel.EDIT))

    @staticmethod
    def without(data, *names):
        return {key: value for key, value in data.items() if key not in names}

    @pytest.mark.parametrize("model", writable_models(), ids=lambda m: m.__name__)
    def test_a_partial_change_alters_the_named_field_and_nothing_else(
        self, url_of, member_at, signed_in, a_private_record, model
    ):
        record = a_private_record(model)
        client = self.edited_by_an_editor(record, member_at, signed_in)
        before = client.get(url_of(record)).json()

        response = client.patch(url_of(record), {"name": "Renamed"}, format="json")

        assert response.status_code == 200, response.content
        after = client.get(url_of(record)).json()
        assert after["name"] == "Renamed"
        assert self.without(after, "name", "modified") == self.without(
            before, "name", "modified"
        )
        assert response.json() == after

    @pytest.mark.parametrize("model", writable_models(), ids=lambda m: m.__name__)
    def test_a_full_replacement_sets_the_writable_fields(
        self,
        url_of,
        member_at,
        signed_in,
        saved,
        a_private_record,
        replacement_for,
        model,
    ):
        record = a_private_record(model)
        client = self.edited_by_an_editor(record, member_at, signed_in)
        body, stored = replacement_for(record)

        response = client.put(url_of(record), body, format="json")

        assert response.status_code == 200, response.content
        manager = getattr(model, "all_objects", model.objects)
        record = manager.get(uuid=record.uuid)
        assert saved(record, stored) == stored

    @pytest.mark.parametrize("method", ["patch", "put"])
    @pytest.mark.parametrize("model", writable_models(), ids=lambda m: m.__name__)
    def test_a_value_for_a_read_only_field_changes_nothing(
        self,
        url_of,
        member_at,
        signed_in,
        add_metadata,
        a_private_record,
        replacement_for,
        model,
        method,
    ):
        record = add_metadata(a_private_record(model))
        client = self.edited_by_an_editor(record, member_at, signed_in)
        before = client.get(url_of(record)).json()
        body, _stored = replacement_for(record)
        body.update(
            {
                "uuid": "xNotMyIdentifier",
                "added": "2001-01-01T00:00:00Z",
                "modified": "2001-01-01T00:00:00Z",
                "url": "http://example.org/elsewhere/",
                "descriptions": [{"type": "Abstract", "value": "Overwritten"}],
                "dates": [{"type": "Created", "value": "2001-01-01"}],
                "identifiers": [{"type": "DOI", "value": "10.1234/overwritten"}],
                "keywords": [],
                "contributors": [],
            }
        )

        response = getattr(client, method)(url_of(record), body, format="json")

        assert response.status_code == 200, response.content
        after = client.get(url_of(record)).json()
        read_only = ("uuid", "url", "added", "descriptions", "dates", "identifiers")
        for name in (*read_only, "keywords", "contributors"):
            assert after[name] == before[name]


@pytest.mark.django_db
class TestDeleting:
    @pytest.mark.parametrize("model", writable_models(), ids=lambda m: m.__name__)
    def test_a_deleted_record_is_gone_and_then_answered_404(
        self, url_of, member_at, signed_in, a_private_record, model
    ):
        record = a_private_record(model)
        client = signed_in(member_at(record, ContributionLevel.MANAGE))
        address = url_of(record)

        response = client.delete(address)

        assert response.status_code == 204
        assert client.get(address).status_code == 404
        manager = getattr(model, "all_objects", model.objects)
        assert not manager.filter(uuid=record.uuid).exists()

    def test_a_project_with_a_public_dataset_is_refused_with_a_reason(
        self, url_of, member_at, signed_in
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        client = signed_in(member_at(project, ContributionLevel.MANAGE))

        response = client.delete(url_of(project))

        assert response.status_code == 409
        assert response.json()["detail"]
        assert dataset.uuid not in response.content.decode()
        assert Project.objects.filter(pk=project.pk).exists()
        assert Dataset.all_objects.filter(pk=dataset.pk).exists()

    def test_a_sample_with_measurements_is_refused_with_a_reason(
        self, url_of, member_at, signed_in
    ):
        from demo.factories import RockSampleFactory, XRFMeasurementFactory
        from demo.models import RockSample, XRFMeasurement

        dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=dataset)
        measurement = XRFMeasurementFactory(dataset=dataset, sample=sample)
        client = signed_in(member_at(dataset, ContributionLevel.MANAGE))

        response = client.delete(url_of(sample))

        assert response.status_code == 409
        assert response.json()["detail"]
        assert measurement.uuid not in response.content.decode()
        assert RockSample.objects.filter(pk=sample.pk).exists()
        assert XRFMeasurement.objects.filter(pk=measurement.pk).exists()


@pytest.mark.django_db
class TestValidation:
    @pytest.fixture
    def person(self):
        from fairdm.factories import PersonFactory

        return PersonFactory(is_active=True, is_claimed=True)

    @pytest.fixture
    def dataset(self, person, member_at):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        member_at(dataset, ContributionLevel.EDIT, person)
        return dataset

    def test_missing_required_fields_are_named_and_nothing_is_saved(
        self, url_of, signed_in, person, dataset
    ):
        from demo.models import RockSample

        response = signed_in(person).post(
            url_of(RockSample, "list"), {"dataset": dataset.uuid}, format="json"
        )

        assert response.status_code == 400
        assert {"name", "rock_type", "collection_date"} <= set(response.json())
        assert not RockSample.objects.exists()

    def test_missing_required_fields_of_a_measurement_are_named(
        self, url_of, signed_in, person, dataset
    ):
        from demo.models import XRFMeasurement

        response = signed_in(person).post(
            url_of(XRFMeasurement, "list"), {"dataset": dataset.uuid}, format="json"
        )

        assert response.status_code == 400
        assert {"name", "sample", "element", "concentration_ppm"} <= set(
            response.json()
        )
        assert not XRFMeasurement.objects.exists()

    def test_missing_required_fields_of_a_project_and_a_dataset_are_named(
        self, signed_in, person
    ):
        client = signed_in(person)

        project = client.post(reverse("api:project-list"), {}, format="json")
        dataset = client.post(reverse("api:dataset-list"), {}, format="json")

        assert project.status_code == dataset.status_code == 400
        assert "name" in project.json()
        assert "name" in dataset.json()
        assert not Project.objects.exists()
        assert not Dataset.all_objects.exists()

    def test_an_unacceptable_value_is_named_with_every_other_one_at_fault(
        self, url_of, signed_in, person, dataset, body_for
    ):
        from demo.models import RockSample

        body, _stored = body_for(RockSample)
        body.update(
            dataset=dataset.uuid,
            weight_grams="heavy",
            collection_date="not a date",
            name="x" * 1000,
        )

        response = signed_in(person).post(url_of(RockSample, "list"), body, "json")

        assert response.status_code == 400
        assert set(response.json()) == {"weight_grams", "collection_date", "name"}
        assert not RockSample.objects.filter(dataset=dataset).exists()

    def test_an_unacceptable_value_in_a_change_is_named_and_the_record_is_kept(
        self, url_of, signed_in, person, dataset, make_record
    ):
        from demo.models import RockSample

        sample = make_record(RockSample, dataset)
        before = sample.weight_grams

        response = signed_in(person).patch(
            url_of(sample), {"weight_grams": "heavy"}, format="json"
        )

        assert response.status_code == 400
        assert set(response.json()) == {"weight_grams"}
        sample.refresh_from_db()
        assert sample.weight_grams == before

    @pytest.mark.parametrize(
        ("kind", "parent"),
        [("sample", "dataset"), ("measurement", "sample"), ("dataset", "project")],
    )
    def test_a_parent_that_does_not_exist_and_one_the_caller_may_not_add_to_are_answered_alike(
        self, url_of, signed_in, member_at, body_for, person, dataset, kind, parent
    ):
        from demo.factories import RockSampleFactory
        from demo.models import RockSample, XRFMeasurement

        own_project = ProjectFactory(visibility=Visibility.PRIVATE)
        member_at(own_project, ContributionLevel.EDIT, person)
        elsewhere = DatasetFactory(visibility=Visibility.PRIVATE)
        public = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        member_at(public, ContributionLevel.VIEW, person)
        make_parent = {
            "dataset": lambda: DatasetFactory(visibility=Visibility.PRIVATE),
            "sample": lambda: RockSampleFactory(dataset=elsewhere),
            "project": lambda: ProjectFactory(visibility=Visibility.PRIVATE),
        }[parent]
        unseen = make_parent()
        seen = make_parent()
        if parent != "sample":
            seen.visibility = Visibility.PUBLIC
            seen.save()
            member_at(seen, ContributionLevel.VIEW, person)
        else:
            member_at(elsewhere, ContributionLevel.VIEW, person)
        if kind == "dataset":
            model, body = Dataset, {"name": "Sent by a script"}
            url = reverse("api:dataset-list")
        else:
            model = RockSample if kind == "sample" else XRFMeasurement
            body, _stored = body_for(model)
            body["dataset"] = dataset.uuid
            if kind == "measurement":
                body["sample"] = RockSampleFactory(dataset=dataset).uuid
            url = url_of(model, "list")
        manager = getattr(model, "all_objects", model.objects)
        stored_before = manager.count()

        answers = []
        for sent in ("xNoSuchRecord", unseen.uuid, seen.uuid):
            response = signed_in(person).post(
                url, {**body, parent: sent}, format="json"
            )
            assert response.status_code == 400, response.content
            assert set(response.json()) == {parent}
            answers.append(
                [message.replace(sent, "<sent>") for message in response.json()[parent]]
            )

        assert answers[0] == answers[1] == answers[2]
        assert manager.count() == stored_before

    @pytest.mark.parametrize("name", ["project", "dataset"])
    def test_a_body_that_cannot_be_parsed_is_answered_400(
        self, signed_in, person, name
    ):
        response = signed_in(person).post(
            reverse(f"api:{name}-list"),
            data=b'{"name": "unfinished',
            content_type="application/json",
        )

        assert response.status_code == 400
        assert not Project.objects.exists()
        assert not Dataset.all_objects.exists()


@pytest.mark.django_db
class TestNoServerErrors:
    @pytest.fixture(params=["superuser", "stranger"])
    def client(self, request, signed_in):
        """A client signed in as a superuser, and as a person with no level on anything."""
        from fairdm.factories import PersonFactory

        if request.param == "superuser":
            return signed_in(UserFactory(is_superuser=True, is_staff=True))
        return signed_in(PersonFactory(is_active=True, is_claimed=True))

    @pytest.fixture
    def a_record_of(self, make_record):
        """Return a function building a public record of a routable model."""
        from fairdm.contrib.contributors.models import Organization, Person

        def a_record_of(model):
            if model is Project:
                return ProjectFactory(visibility=Visibility.PUBLIC)
            if model is Dataset:
                return DatasetFactory(visibility=Visibility.PUBLIC, published=True)
            if model is Person:
                return PersonFactory()
            if model is Organization:
                return OrganizationFactory()
            return make_record(
                model, DatasetFactory(visibility=Visibility.PUBLIC, published=True)
            )

        return a_record_of

    @pytest.fixture
    def address(self, url_of):
        """Return a function giving a record's or a model's list address, contributors too."""
        return url_of

    @pytest.fixture
    def bodies(self, body_for):
        """Return a function giving the bodies to send to the routes of a model, as a dict."""
        from fairdm.contrib.contributors.models import Organization, Person
        from fairdm.core.models import Measurement
        from fairdm.registry import registry

        def bodies(model, record):
            if model in (Person, Organization):
                valid = {"name": "Sent by a script"}
                fields = ["name", "type"]
            elif model in (Project, Dataset):
                valid = {"name": "Sent by a script"}
                fields = ["name", "status", "visibility", "project", "funding", "owner"]
            else:
                valid, _stored = body_for(model)
                valid["dataset"] = record.dataset.uuid
                if issubclass(model, Measurement):
                    valid["sample"] = record.sample.uuid
                fields = list(
                    registry.get_for_model(model).get_serializer_class()().fields
                )
            return {
                "empty": {},
                "wrong types": {name: {"nested": [1, None]} for name in fields},
                "a list": ["not", "an", "object"],
                "valid": valid,
            }

        return bodies

    @pytest.mark.parametrize("model", routable_models(), ids=lambda m: m.__name__)
    @pytest.mark.parametrize("sent", ["empty", "wrong types", "a list", "valid"])
    def test_a_create_is_answered_below_500(
        self, client, a_record_of, bodies, address, model, sent
    ):
        record = a_record_of(model)

        response = client.post(
            address(model, "list"), bodies(model, record)[sent], format="json"
        )

        assert response.status_code < 500

    @pytest.mark.parametrize("model", routable_models(), ids=lambda m: m.__name__)
    @pytest.mark.parametrize("method", ["put", "patch"])
    @pytest.mark.parametrize("sent", ["empty", "wrong types", "a list", "valid"])
    def test_a_change_is_answered_below_500(
        self, client, a_record_of, bodies, address, model, method, sent
    ):
        record = a_record_of(model)

        response = getattr(client, method)(
            address(record), bodies(model, record)[sent], format="json"
        )

        assert response.status_code < 500

    @pytest.mark.parametrize("model", routable_models(), ids=lambda m: m.__name__)
    @pytest.mark.parametrize("held_by_others", [False, True])
    def test_a_delete_is_answered_below_500(
        self, client, a_record_of, address, make_record, model, held_by_others
    ):
        from demo.models import XRFMeasurement
        from fairdm.core.models import Sample

        record = a_record_of(model)
        if held_by_others and model is Project:
            DatasetFactory(project=record, visibility=Visibility.PUBLIC, published=True)
        if held_by_others and issubclass(model, Sample):
            make_record(XRFMeasurement, record.dataset, sample=record)

        response = client.delete(address(record))

        assert response.status_code < 500


def marked_serializer(base, model, marker):
    """Return a serializer on ``base`` that carries one extra field holding ``marker``."""
    from rest_framework import serializers

    class MarkedSerializer(base):
        marked_by = serializers.SerializerMethodField()

        def get_marked_by(self, obj):
            return marker

        class Meta(base.Meta):
            fields = [*base.Meta.fields, "marked_by"]

    MarkedSerializer.Meta.model = model
    return MarkedSerializer


@pytest.mark.django_db
class TestRegisteredSerializerIsUsed:
    @pytest.fixture
    def rock(self):
        from demo.factories import RockSampleFactory

        return RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )

    def test_a_serializer_named_in_the_registration_is_the_routes_serializer(
        self, api_client, on_the_router, rock
    ):
        from demo.models import RockSample
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import ModelConfiguration

        config = ModelConfiguration(
            model=RockSample,
            serializer_class=marked_serializer(
                BaseSampleSerializer, RockSample, "the named class"
            ),
        )
        on_the_router(
            "samples/named-serializer", generate_viewset(config), "samples-named"
        )

        results = api_client.get(reverse("api:samples-named-list")).json()["results"]

        assert [row["marked_by"] for row in results] == ["the named class"]

    def test_a_serializer_from_an_overridden_accessor_is_the_routes_serializer(
        self, api_client, on_the_router, rock
    ):
        from demo.models import RockSample
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import ModelConfiguration

        serializer_class = marked_serializer(
            BaseSampleSerializer, RockSample, "the accessor"
        )

        class OverridingConfig(ModelConfiguration):
            def get_serializer_class(self):
                return serializer_class

        on_the_router(
            "samples/accessor-serializer",
            generate_viewset(OverridingConfig(model=RockSample)),
            "samples-accessor",
        )

        results = api_client.get(reverse("api:samples-accessor-list")).json()["results"]

        assert [row["marked_by"] for row in results] == ["the accessor"]

    def test_a_measurement_route_uses_the_serializer_its_configuration_returns(
        self, api_client, on_the_router, rock
    ):
        from demo.factories import XRFMeasurementFactory
        from demo.models import XRFMeasurement
        from fairdm.api.serializers import BaseMeasurementSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import ModelConfiguration

        XRFMeasurementFactory(dataset=rock.dataset, sample=rock)
        config = ModelConfiguration(
            model=XRFMeasurement,
            serializer_class=marked_serializer(
                BaseMeasurementSerializer, XRFMeasurement, "the measurement class"
            ),
        )
        on_the_router(
            "measurements/named-serializer",
            generate_viewset(config),
            "measurements-named",
        )

        results = api_client.get(reverse("api:measurements-named-list")).json()[
            "results"
        ]

        assert [row["marked_by"] for row in results] == ["the measurement class"]


@pytest.mark.django_db
class TestRelationFiltersUseIdentifiers:
    """A filter a type declares on a relation matches the related record's short identifier."""

    @pytest.fixture
    def portal_filters(self):
        """Return the filter set a type declares, the one the portal's pages would use."""
        import django_filters
        from django.contrib.contenttypes.models import ContentType

        from demo.models import RockSample

        class RockFilters(django_filters.FilterSet):
            project = django_filters.ModelChoiceFilter(
                field_name="dataset__project", queryset=Project.objects.all()
            )
            projects = django_filters.ModelMultipleChoiceFilter(
                field_name="dataset__project", queryset=Project.objects.all()
            )
            kind = django_filters.ModelChoiceFilter(
                field_name="polymorphic_ctype", queryset=ContentType.objects.all()
            )

            class Meta:
                model = RockSample
                fields = []

        return RockFilters

    @pytest.fixture
    def filtered_route(self, on_the_router, portal_filters):
        from demo.models import RockSample
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import ModelConfiguration

        config = ModelConfiguration(model=RockSample, filterset_class=portal_filters)
        on_the_router(
            "samples/filtered-rocks", generate_viewset(config), "samples-filtered"
        )
        return reverse("api:samples-filtered-list")

    @pytest.fixture
    def rocks(self, make_record):
        from demo.models import RockSample

        first = ProjectFactory(visibility=Visibility.PUBLIC)
        second = ProjectFactory(visibility=Visibility.PUBLIC)
        return {
            project: make_record(
                RockSample,
                DatasetFactory(
                    project=project, visibility=Visibility.PUBLIC, published=True
                ),
            )
            for project in (first, second)
        }

    @staticmethod
    def listed(client, address, **query):
        response = client.get(address, query)
        assert response.status_code == 200, response.content
        return {row["uuid"] for row in response.json()["results"]}

    def test_a_relation_filter_matches_the_short_identifier(
        self, api_client, filtered_route, rocks
    ):
        project, record = next(iter(rocks.items()))

        found = self.listed(api_client, filtered_route, project=project.uuid)

        assert found == {record.uuid}

    def test_a_relation_filter_refuses_a_database_number(
        self, api_client, filtered_route, rocks
    ):
        project = next(iter(rocks))

        response = api_client.get(filtered_route, {"project": project.pk})

        assert response.status_code == 400
        assert "project" in response.json()

    def test_a_filter_for_several_related_records_matches_their_identifiers(
        self, api_client, filtered_route, rocks
    ):
        found = self.listed(
            api_client,
            filtered_route,
            projects=[project.uuid for project in rocks],
        )

        assert found == {record.uuid for record in rocks.values()}

    def test_a_filter_on_a_relation_with_no_identifier_is_left_out(
        self, api_client, filtered_route, rocks
    ):
        from django.contrib.contenttypes.models import ContentType

        kind = ContentType.objects.get_for_model(Project)

        found = self.listed(api_client, filtered_route, kind=kind.pk)

        assert found == {record.uuid for record in rocks.values()}

    def test_the_filter_set_the_portal_uses_is_left_as_declared(
        self, api_client, filtered_route, portal_filters
    ):
        api_client.get(filtered_route)

        assert "to_field_name" not in portal_filters.base_filters["project"].extra
        assert "kind" in portal_filters.base_filters


class TestSerializerMustBuildOnBase:
    @pytest.fixture
    def off_the_base(self):
        from rest_framework import serializers

        def build(model):
            class OffTheBase(serializers.ModelSerializer):
                class Meta:
                    pass

            OffTheBase.Meta.model = model
            OffTheBase.Meta.fields = ["name"]
            return OffTheBase

        return build

    @pytest.mark.parametrize("kind", ["sample", "measurement"])
    def test_an_overridden_accessor_returning_a_serializer_off_the_base_is_refused(
        self, off_the_base, kind
    ):
        from django.core.exceptions import ImproperlyConfigured

        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import ModelConfiguration

        model = registered(kind)[0]
        serializer_class = off_the_base(model)

        class OverridingConfig(ModelConfiguration):
            def get_serializer_class(self):
                return serializer_class

        with pytest.raises(ImproperlyConfigured):
            generate_viewset(OverridingConfig(model=model))

    @pytest.mark.parametrize("kind", ["sample", "measurement"])
    def test_a_named_serializer_off_the_base_is_refused(self, off_the_base, kind):
        from django.core.exceptions import ImproperlyConfigured

        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import ModelConfiguration

        model = registered(kind)[0]

        with pytest.raises(ImproperlyConfigured):
            generate_viewset(
                ModelConfiguration(model=model, serializer_class=off_the_base(model))
            )


@pytest.mark.django_db
class TestQueryCount:
    KINDS = (
        "project",
        "dataset",
        "people",
        "organizations",
        "sample",
        "located sample",
        "measurement",
    )

    @staticmethod
    def add_person():
        """Add a person with an identifier and two affiliations, one of them primary."""
        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory(is_active=True, is_claimed=True)
        ContributorIdentifierFactory(related=person, type="ORCID")
        AffiliationFactory(
            person=person, organization=OrganizationFactory(), is_primary=True
        )
        AffiliationFactory(person=person, organization=OrganizationFactory())

    @staticmethod
    def add_organization():
        """Add an organisation with a parent and an identifier."""
        from fairdm.factories import ContributorIdentifierFactory, OrganizationFactory

        organisation = OrganizationFactory(parent=OrganizationFactory())
        ContributorIdentifierFactory(related=organisation, type="ROR")

    @pytest.fixture
    def grow(self, make_record, add_metadata):
        """Return a function adding records of a kind, each with its metadata recorded."""

        def grow(kind, number):
            for _ in range(number):
                if kind == "people":
                    self.add_person()
                elif kind == "organizations":
                    self.add_organization()
                else:
                    build_record(kind, make_record, add_metadata)

        return grow

    @staticmethod
    def address(kind, url_of):
        from demo.models import CustomSample, ExampleMeasurement, RockSample

        return {
            "project": lambda: reverse("api:project-list"),
            "dataset": lambda: reverse("api:dataset-list"),
            "people": lambda: reverse("api:person-list"),
            "organizations": lambda: reverse("api:organization-list"),
            "sample": lambda: url_of(RockSample, "list"),
            "located sample": lambda: url_of(CustomSample, "list"),
            "measurement": lambda: url_of(ExampleMeasurement, "list"),
        }[kind]()

    @staticmethod
    def queries_for(client, address):
        """Return the number of queries behind a list, and the number of records it holds."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as captured:
            response = client.get(address, {"page_size": 100})
        assert response.status_code == 200
        return len(captured), len(response.json()["results"])

    @pytest.mark.parametrize("caller", ["anonymous", "token"])
    @pytest.mark.parametrize("kind", KINDS)
    def test_a_list_of_twelve_runs_the_queries_of_a_list_of_two(
        self, api_client, authenticated_client, url_of, grow, kind, caller
    ):
        client = api_client if caller == "anonymous" else authenticated_client
        address = self.address(kind, url_of)
        grow(kind, 2)
        self.queries_for(client, address)
        few, held_few = self.queries_for(client, address)

        grow(kind, 10)
        many, held_many = self.queries_for(client, address)

        assert held_many >= held_few + 10
        assert many == few


@pytest.mark.django_db
class TestCreditQueries:
    @staticmethod
    def add_credits(record, people=1):
        """Credit people each with an identifier and an affiliation that has one, and an organization."""
        from fairdm.factories import (
            ContributorIdentifierFactory,
            OrganizationFactory,
            PersonFactory,
        )

        for _ in range(people):
            person = PersonFactory()
            ContributorIdentifierFactory(related=person, type="ORCID")
            institute = OrganizationFactory()
            ContributorIdentifierFactory(related=institute, type="ROR")
            add_credit(record, person, institute, roles=2)
        add_credit(record, OrganizationFactory())

    @pytest.mark.parametrize("kind", CREDIT_KINDS)
    def test_a_page_of_twelve_runs_the_queries_of_a_page_of_two(
        self, api_client, url_of, make_record, kind
    ):
        from demo.models import ExampleMeasurement, RockSample

        model = {
            "project": Project,
            "dataset": Dataset,
            "sample": RockSample,
            "measurement": ExampleMeasurement,
        }[kind]

        def grow(number, people):
            for _ in range(number):
                record = build_record(kind, make_record, lambda record: record)
                self.add_credits(record, people)

        address = url_of(model, "list")
        grow(2, people=1)
        TestQueryCount.queries_for(api_client, address)
        few, held_few = TestQueryCount.queries_for(api_client, address)

        grow(10, people=3)
        many, held_many = TestQueryCount.queries_for(api_client, address)

        assert held_many >= held_few + 10
        assert many == few


@pytest.mark.django_db
class TestEveryListedFilter:
    VALUES = {
        "text": "abc",
        "number": "1",
        "date": "2020-01-01",
        "identifier": "00000000-0000-0000-0000-000000000000",
    }

    @pytest.fixture
    def client(self):
        from rest_framework.test import APIClient

        return APIClient(raise_request_exception=False)

    def listed(self, rf, kind, url_of):
        """Return each type's list address and the filter names the API builds for it."""
        from django.contrib.auth.models import AnonymousUser
        from django.urls import resolve
        from rest_framework.request import Request

        from fairdm.api.filters import FairDMFilterBackend

        types = []
        for model in registered(kind[:-1]):
            address = url_of(model, "list")
            viewset = resolve(address).func.cls
            request = Request(rf.get(address))
            request.user = AnonymousUser()
            view = viewset(request=request, format_kwarg=None, action="list")
            queryset = viewset.queryset.all()
            filterset_class = FairDMFilterBackend().get_filterset_class(view, queryset)
            filterset = filterset_class(data={}, queryset=queryset, request=request)
            types.append((address, list(filterset.filters)))
        return types

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    @pytest.mark.parametrize("value", sorted(VALUES))
    def test_a_listed_filter_is_answered_below_500(
        self, client, rf, url_of, kind, value
    ):
        types = self.listed(rf, kind, url_of)
        assert any(names for _address, names in types)

        for address, names in types:
            for name in names:
                response = client.get(address, {name: self.VALUES[value]})

                assert response.status_code < 500, (address, name)


@pytest.mark.django_db
class TestReferencesFollowTheLists:
    @pytest.fixture(params=["superuser", "anonymous account"])
    def unlisted(self, request):
        """A contributor the contributor list leaves out."""
        from fairdm.factories import PersonFactory

        if request.param == "superuser":
            return PersonFactory(is_active=True, is_superuser=True)
        return PersonFactory(email="AnonymousUser")

    def test_the_contributor_list_leaves_the_account_out(self, api_client, unlisted):
        response = api_client.get(
            reverse("api:person-detail", kwargs={"uuid": unlisted.uuid})
        )

        assert response.status_code == 404

    def test_a_credit_to_that_contributor_names_them_and_gives_no_address(
        self, api_client, unlisted
    ):
        from fairdm.factories import ContributorIdentifierFactory

        ContributorIdentifierFactory(
            related=unlisted, type="ORCID", value="0000-0003-1415-9269"
        )
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        credit = add_credit(dataset, unlisted, roles=2)

        response = api_client.get(
            reverse("api:dataset-detail", kwargs={"uuid": dataset.uuid})
        )

        assert response.status_code == 200
        [returned] = response.json()["contributors"]
        assert returned["uuid"] is None
        assert returned["url"] is None
        assert returned["name"] == unlisted.get_full_name_display("family_given")
        assert returned["name_identifiers"] == [
            {
                "name_identifier": "https://orcid.org/0000-0003-1415-9269",
                "name_identifier_scheme": "ORCID",
                "scheme_uri": "https://orcid.org/",
            }
        ]
        assert {role["name"] for role in returned["roles"]} == {
            role.name for role in credit.roles.all()
        }
        assert len(returned["roles"]) == 2

    def test_a_credit_to_a_listed_contributor_is_a_reference(self, api_client):
        from fairdm.factories import ContributionFactory, PersonFactory

        person = PersonFactory(is_active=True)
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        ContributionFactory(content_object=dataset, contributor=person)

        response = api_client.get(
            reverse("api:dataset-detail", kwargs={"uuid": dataset.uuid})
        )

        referred = [row["uuid"] for row in response.json()["contributors"]]
        assert referred == [person.uuid]

    @pytest.fixture
    def related_samples(self, on_the_router):
        """Register a rock sample type listing its relation to other samples; return it."""
        from demo.factories import RockSampleFactory
        from demo.models import RockSample
        from fairdm.api.viewsets import generate_viewset
        from fairdm.core.sample.models import SampleRelation
        from fairdm.registry import ModelConfiguration

        config = ModelConfiguration(
            model=RockSample, serializer_fields=["name", "related"]
        )
        on_the_router(
            "samples/with-relations", generate_viewset(config), "samples-related"
        )
        public = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        shown = RockSampleFactory(dataset=public)
        hidden = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PRIVATE)
        )
        source = RockSampleFactory(dataset=public)
        for target in (shown, hidden):
            SampleRelation.objects.create(source=source, target=target, type="child_of")
        return source, shown

    def test_a_declared_relation_to_a_sample_is_a_reference_null_when_hidden(
        self, api_client, related_samples
    ):
        source, shown = related_samples

        response = api_client.get(
            reverse("api:samples-related-detail", kwargs={"uuid": source.uuid})
        )

        assert response.status_code == 200
        related = response.json()["related"]
        assert len(related) == 2
        assert None in related
        assert [row["uuid"] for row in related if row] == [shown.uuid]

    def test_a_list_of_twelve_runs_the_queries_of_a_list_of_two(
        self, api_client, related_samples
    ):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import SampleRelation

        source, _shown = related_samples
        address = reverse("api:samples-related-list")

        def relate(number):
            for _ in range(number):
                SampleRelation.objects.create(
                    source=RockSampleFactory(dataset=source.dataset),
                    target=RockSampleFactory(
                        dataset=DatasetFactory(visibility=Visibility.PRIVATE)
                    ),
                    type="child_of",
                )

        def queries():
            from django.db import connection
            from django.test.utils import CaptureQueriesContext

            with CaptureQueriesContext(connection) as captured:
                response = api_client.get(address, {"page_size": 100})
            assert response.status_code == 200
            return len(captured)

        relate(2)
        queries()
        few = queries()
        relate(10)

        assert queries() == few


@pytest.mark.django_db
class TestChangedSince:
    MOMENTS = (
        datetime(2024, 1, 15, 12, tzinfo=UTC),
        datetime(2025, 1, 15, 12, tzinfo=UTC),
        datetime(2026, 1, 15, 12, tzinfo=UTC),
    )

    @pytest.fixture(
        params=[
            Project,
            Dataset,
            Person,
            Organization,
            *registered("sample"),
            *registered("measurement"),
        ],
        ids=lambda model: model.__name__,
    )
    def records(self, request, make_record, public_dataset):
        """Three public records of a kind, last changed in 2024, 2025 and 2026 in that order."""
        model = request.param
        made = []
        for _ in range(3):
            if model is Project:
                made.append(ProjectFactory(visibility=Visibility.PUBLIC))
            elif model is Dataset:
                made.append(
                    DatasetFactory(visibility=Visibility.PUBLIC, published=True)
                )
            elif model is Person:
                made.append(PersonFactory(is_active=True, is_claimed=True))
            elif model is Organization:
                made.append(OrganizationFactory())
            else:
                made.append(make_record(model, public_dataset))
        for record, moment in zip(made, self.MOMENTS, strict=True):
            type(record).objects.filter(pk=record.pk).update(modified=moment)
        return SimpleNamespace(model=model, made=made)

    def listed(self, client, url_of, records, **query):
        response = client.get(url_of(records.model, "list"), query)
        assert response.status_code == 200, response.content
        return {row["uuid"] for row in response.json()["results"]}

    def uuids(self, records, *positions):
        return {records.made[position].uuid for position in positions}

    def test_modified_after_returns_what_changed_after_the_moment(
        self, api_client, url_of, records
    ):
        listed = self.listed(
            api_client, url_of, records, modified_after="2024-06-01T00:00:00Z"
        )

        assert listed >= self.uuids(records, 1, 2)
        assert not listed & self.uuids(records, 0)

    def test_modified_before_returns_what_changed_before_the_moment(
        self, api_client, url_of, records
    ):
        listed = self.listed(
            api_client, url_of, records, modified_before="2025-06-01T00:00:00Z"
        )

        assert listed >= self.uuids(records, 0, 1)
        assert not listed & self.uuids(records, 2)

    def test_the_two_together_return_what_changed_between_them(
        self, api_client, url_of, records
    ):
        listed = self.listed(
            api_client,
            url_of,
            records,
            modified_after="2024-06-01T00:00:00Z",
            modified_before="2025-06-01T00:00:00Z",
        )

        assert listed & self.uuids(records, 0, 1, 2) == self.uuids(records, 1)

    def test_a_record_changed_at_the_moment_given_is_returned_by_both(
        self, api_client, url_of, records
    ):
        moment = self.MOMENTS[1].isoformat()

        after = self.listed(api_client, url_of, records, modified_after=moment)
        before = self.listed(api_client, url_of, records, modified_before=moment)

        assert after & self.uuids(records, 0, 1, 2) == self.uuids(records, 1, 2)
        assert before & self.uuids(records, 0, 1, 2) == self.uuids(records, 0, 1)

    def test_a_date_alone_is_a_moment(self, api_client, url_of, records):
        listed = self.listed(api_client, url_of, records, modified_after="2025-06-01")

        assert listed & self.uuids(records, 0, 1, 2) == self.uuids(records, 2)

    def test_a_moment_with_an_offset_is_read_in_that_offset(
        self, api_client, url_of, records
    ):
        # 14:00 at +03:00 is 11:00 UTC, an hour before the middle record changed.
        listed = self.listed(
            api_client, url_of, records, modified_after="2025-01-15T14:00:00+03:00"
        )

        assert listed & self.uuids(records, 0, 1, 2) == self.uuids(records, 1, 2)

    @pytest.mark.parametrize("name", ["modified_after", "modified_before"])
    @pytest.mark.parametrize("value", ["yesterday", "2025-13-45", "12"])
    def test_a_moment_that_cannot_be_read_is_refused_naming_the_parameter(
        self, api_client, url_of, records, name, value
    ):
        response = api_client.get(url_of(records.model, "list"), {name: value})

        assert response.status_code == 400
        assert name in response.json()

    def test_both_are_among_the_list_parameters_of_the_documentation(
        self, api_client, url_of, records
    ):
        schema = api_client.get(reverse("api:api-schema"), {"format": "json"}).json()

        parameters = schema["paths"][url_of(records.model, "list")]["get"]["parameters"]

        offered = {parameter["name"] for parameter in parameters}
        assert {"modified_after", "modified_before"} <= offered
