"""Tests for FairDM API viewsets (Feature 011 â€” US1)."""

import pytest
from django.urls import reverse

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
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
    def test_returns_200(self, api_client):
        response = api_client.get(reverse("api:contributor-list"))
        assert response.status_code == 200

    def test_has_pagination_keys(self, api_client):
        data = api_client.get(reverse("api:contributor-list")).json()
        for key in ("count", "next", "previous", "results"):
            assert key in data

    def test_post_not_allowed(self, authenticated_client):
        response = authenticated_client.post(
            reverse("api:contributor-list"), {"name": "New"}, format="json"
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


@pytest.mark.django_db
class TestRateLimiting:
    # Test settings use DummyCache, which never stores throttle counts, so the throttle gets a real
    # LocMemCache and a patched rate.
    @pytest.fixture(autouse=True)
    def _throttle_setup(self):
        from unittest.mock import patch

        from django.core.cache.backends.locmem import LocMemCache
        from rest_framework.throttling import SimpleRateThrottle

        test_cache = LocMemCache("throttle-test", {})
        test_cache.clear()
        with patch.object(SimpleRateThrottle, "cache", test_cache):
            yield
        test_cache.clear()

    def test_anonymous_throttled_after_limit(self, api_client):
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="2/minute"):
            url = reverse("api:project-list")
            for _ in range(2):
                assert api_client.get(url).status_code == 200
            assert api_client.get(url).status_code == 429

    def test_throttled_response_has_retry_after_header(self, api_client):
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="1/minute"):
            url = reverse("api:project-list")
            api_client.get(url)
            resp = api_client.get(url)
            assert resp.status_code == 429
            assert "Retry-After" in resp

    def test_throttled_response_has_detail_message(self, api_client):
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="1/minute"):
            url = reverse("api:project-list")
            api_client.get(url)
            resp = api_client.get(url)
            assert resp.status_code == 429
            assert "detail" in resp.json()

    def test_authenticated_gets_higher_limit(self, api_client, authenticated_client):
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

        with (
            patch.object(AnonRateThrottle, "get_rate", return_value="1/minute"),
            patch.object(UserRateThrottle, "get_rate", return_value="3/minute"),
        ):
            url = reverse("api:project-list")
            api_client.get(url)
            assert api_client.get(url).status_code == 429
            for _ in range(3):
                assert authenticated_client.get(url).status_code == 200

    def test_throttle_rates_configurable(self, settings):
        rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        assert "anon" in rates
        assert "user" in rates
        assert rates["anon"] == "100/hour"
        assert rates["user"] == "1000/hour"
        settings.REST_FRAMEWORK = {
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": {"anon": "50/hour", "user": "500/hour"},
        }
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] == "50/hour"


@pytest.mark.django_db
class TestCreatedRecordsListTheirCreator:
    @pytest.mark.parametrize("name", ["project", "dataset"])
    def test_a_project_or_dataset_lists_its_creator_at_the_manage_level(
        self, authenticated_client, user, name
    ):
        from guardian.models import UserObjectPermission

        from fairdm.contrib.contributors.access import RecordAccess
        from fairdm.contrib.contributors.choices import ContributionLevel

        response = authenticated_client.post(
            reverse(f"api:{name}-list"), {"name": f"Made by API {name}"}, format="json"
        )

        assert response.status_code == 201
        model = Project if name == "project" else Dataset
        manager = getattr(model, "all_objects", model.objects)
        record = manager.get(uuid=response.json()["uuid"])
        assert RecordAccess(record).own_level(user) == ContributionLevel.MANAGE
        assert not UserObjectPermission.objects.exists()

    def test_a_superuser_creates_without_being_credited(self, db):
        from rest_framework.test import APIClient

        admin = UserFactory(is_superuser=True, is_staff=True)
        client = APIClient()
        client.force_authenticate(admin)

        response = client.post(
            reverse("api:project-list"), {"name": "Admin by API"}, format="json"
        )

        assert response.status_code == 201
        project = Project.objects.get(uuid=response.json()["uuid"])
        assert project.contributors.count() == 0


@pytest.fixture(params=["project", "dataset"])
def private_record(request):
    """A private project or dataset, each in turn, with one person at manage."""
    from fairdm.contrib.contributors.choices import ContributionLevel
    from fairdm.factories import ContributionFactory, PersonFactory

    factory = ProjectFactory if request.param == "project" else DatasetFactory
    record = factory(visibility=Visibility.PRIVATE)
    ContributionFactory(
        content_object=record,
        contributor=PersonFactory(is_active=True, is_claimed=True),
        level=ContributionLevel.MANAGE,
    )
    return record


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


def detail_url(record):
    """Return the API address of a project or dataset."""
    name = "project" if isinstance(record, Project) else "dataset"
    return reverse(f"api:{name}-detail", kwargs={"uuid": record.uuid})


@pytest.mark.django_db
class TestVisibilityNeedsManage:
    def test_an_editor_cannot_change_visibility(self, private_record):
        from fairdm.contrib.contributors.choices import ContributionLevel

        editor = person_at(private_record, ContributionLevel.EDIT)

        response = signed_in_as(editor).patch(
            detail_url(private_record), {"visibility": Visibility.PUBLIC}, format="json"
        )

        assert response.status_code == 403
        private_record.refresh_from_db()
        assert private_record.visibility == Visibility.PRIVATE

    def test_a_manager_can_change_visibility(self, private_record):
        from fairdm.contrib.contributors.choices import ContributionLevel

        manager = person_at(private_record, ContributionLevel.MANAGE)

        response = signed_in_as(manager).patch(
            detail_url(private_record), {"visibility": Visibility.PUBLIC}, format="json"
        )

        assert response.status_code == 200
        private_record.refresh_from_db()
        assert private_record.visibility == Visibility.PUBLIC

    def test_an_editor_can_change_another_field(self, private_record):
        from fairdm.contrib.contributors.choices import ContributionLevel

        editor = person_at(private_record, ContributionLevel.EDIT)

        response = signed_in_as(editor).patch(
            detail_url(private_record), {"name": "Renamed"}, format="json"
        )

        assert response.status_code == 200
        private_record.refresh_from_db()
        assert private_record.name == "Renamed"

    def test_an_editor_can_send_the_visibility_it_already_has(self, private_record):
        from fairdm.contrib.contributors.choices import ContributionLevel

        editor = person_at(private_record, ContributionLevel.EDIT)

        response = signed_in_as(editor).patch(
            detail_url(private_record),
            {"name": "Renamed", "visibility": Visibility.PRIVATE},
            format="json",
        )

        assert response.status_code == 200


def build_record(kind, make_record, add_metadata):
    """Build a public record of a kind, with metadata recorded, and its parents."""
    from demo.models import ExampleMeasurement, RockSample

    project = ProjectFactory(visibility=Visibility.PUBLIC)
    dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
    if kind == "project":
        record = project
    elif kind == "dataset":
        record = dataset
    elif kind == "sample":
        record = make_record(RockSample, dataset)
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

        assert credited["contributor"]["uuid"] == credit.contributor.uuid
        assert credited["affiliation"]["uuid"] == credit.affiliation.uuid
        assert [role["name"] for role in credited["roles"]] == [
            role.name for role in credit.roles.all()
        ]

    def test_a_dataset_carries_its_licence_and_a_project_its_owner(
        self, api_client, url_of, make_record, add_metadata
    ):
        project = build_record("project", make_record, add_metadata)
        dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)

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
        dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
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
            DatasetFactory(visibility=Visibility.PUBLIC),
            sample=sample,
        )
        viewer = person_at(elsewhere, ContributionLevel.VIEW)

        visitor_sees = api_client.get(url_of(measurement)).json()["sample"]
        viewer_sees = signed_in_as(viewer).get(url_of(measurement)).json()["sample"]

        assert visitor_sees is None
        assert viewer_sees["uuid"] == sample.uuid

    def test_a_list_hides_the_parent_it_would_otherwise_name(self, api_client, url_of):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)

        results = api_client.get(url_of(Dataset, "list")).json()["results"]

        assert [row["project"] for row in results] == [None]


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

        sample = make_record(model, DatasetFactory(visibility=Visibility.PUBLIC))
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

        measurement = make_record(model, DatasetFactory(visibility=Visibility.PUBLIC))
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
            DatasetFactory(visibility=Visibility.PUBLIC),
            element="Fe",
            concentration_ppm="123.45",
        )

        data = api_client.get(url_of(measurement)).json()

        assert data["element"] == "Fe"
        assert float(data["concentration_ppm"]) == 123.45


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
            DatasetFactory(project=project, visibility=Visibility.PUBLIC)
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
        addresses.append(reverse("api:contributor-list"))
        for contributor in (PersonFactory(), OrganizationFactory()):
            addresses.append(
                reverse("api:contributor-detail", kwargs={"uuid": contributor.uuid})
            )
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
            reverse("api:contributor-detail", kwargs={"uuid": person.uuid})
        )

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == person.uuid
        assert data["name"] == person.name
        assert data["type"] == "person"
        assert data["profile"] == person.profile
        assert data["links"] == person.links
        assert data["identifiers"][0]["value"] == person.identifiers.get().value
        assert data["affiliation"]["uuid"] == person.primary_organization.uuid

    def test_an_organisation_is_returned_with_what_its_profile_page_shows(
        self, api_client, organisation
    ):
        response = api_client.get(
            reverse("api:contributor-detail", kwargs={"uuid": organisation.uuid})
        )

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == organisation.uuid
        assert data["type"] == "organization"
        assert data["identifiers"][0]["value"] == "03yrm5c26"
        assert data["affiliation"]["uuid"] == organisation.parent.uuid

    def test_no_response_carries_an_account_detail(
        self, api_client, person, organisation
    ):
        responses = [
            api_client.get(reverse("api:contributor-list")),
            api_client.get(
                reverse("api:contributor-detail", kwargs={"uuid": person.uuid})
            ),
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
            for row in api_client.get(reverse("api:contributor-list")).json()["results"]
        ]

        assert person.uuid in listed
        assert administrator.uuid not in listed
        assert anonymous.uuid not in listed

    def test_a_superuser_is_answered_as_a_record_that_does_not_exist(self, api_client):
        from fairdm.factories import PersonFactory

        administrator = PersonFactory(is_superuser=True, is_staff=True)

        response = api_client.get(
            reverse("api:contributor-detail", kwargs={"uuid": administrator.uuid})
        )

        assert response.status_code == 404


def routable_models():
    """Every model with a list and record route: the core kinds and the registered types."""
    from fairdm.contrib.contributors.models import Contributor

    return [
        Project,
        Dataset,
        Contributor,
        *registered("sample"),
        *registered("measurement"),
    ]


@pytest.mark.django_db
class TestListAndRecordRoutes:
    @pytest.fixture
    def a_record_of(self, make_record):
        """Return a function building a public record of a routable model."""
        from fairdm.contrib.contributors.models import Contributor
        from fairdm.factories import OrganizationFactory

        def a_record_of(model):
            if model is Project:
                return ProjectFactory(visibility=Visibility.PUBLIC)
            if model is Dataset:
                return DatasetFactory(visibility=Visibility.PUBLIC)
            if model is Contributor:
                return OrganizationFactory()
            return make_record(model, DatasetFactory(visibility=Visibility.PUBLIC))

        return a_record_of

    @staticmethod
    def address(model, action, uuid=None):
        from fairdm.contrib.contributors.models import Contributor
        from tests.test_api.conftest import route_name

        name = (
            f"api:contributor-{action}"
            if model is Contributor
            else route_name(model, action)
        )
        return reverse(name, kwargs={"uuid": uuid} if uuid else None)

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

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        clay = make_record(SoilSample, dataset, soil_type="clay")
        make_record(SoilSample, dataset, soil_type="sand")

        found = self.listed(api_client, url_of(SoilSample, "list"), soil_type="clay")

        assert found == {clay.uuid}

    def test_a_declared_filter_narrows_a_measurement_list(
        self, api_client, url_of, make_record
    ):
        from demo.models import XRFMeasurement

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        iron = make_record(XRFMeasurement, dataset, element="Fe")
        make_record(XRFMeasurement, dataset, element="Si")

        found = self.listed(api_client, url_of(XRFMeasurement, "list"), element="Fe")

        assert found == {iron.uuid}

    def test_a_filter_declared_by_overriding_the_accessor_narrows_a_list(
        self, api_client, url_of, make_record
    ):
        from demo.models import WaterSample

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
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
        wanted = DatasetFactory(visibility=Visibility.PUBLIC)
        here = make_record(model, wanted)
        make_record(model, DatasetFactory(visibility=Visibility.PUBLIC))

        found = self.listed(api_client, url_of(model, "list"), dataset=wanted.uuid)

        assert found == {here.uuid}

    @pytest.mark.parametrize(
        "model", registered("measurement"), ids=lambda m: m.__name__
    )
    def test_a_measurement_list_is_narrowed_by_the_short_identifier_of_its_sample(
        self, api_client, url_of, make_record, model
    ):
        from demo.factories import RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
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
        make_record(RockSample, DatasetFactory(visibility=Visibility.PUBLIC))

        found = self.listed(
            signed_in_as(viewer), url_of(RockSample, "list"), dataset=private.uuid
        )

        assert found == {here.uuid}

    @pytest.mark.parametrize(
        "model",
        registered("sample") + registered("measurement"),
        ids=lambda m: m.__name__,
    )
    def test_a_database_number_is_refused_for_the_dataset(
        self, api_client, url_of, make_record, model
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
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
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
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

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
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
                DatasetFactory(name=name, visibility=Visibility.PUBLIC)
            else:
                dataset = Dataset.objects.filter(name="Holder").first() or (
                    DatasetFactory(name="Holder", visibility=Visibility.PUBLIC)
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
        dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
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
        public = DatasetFactory(visibility=Visibility.PUBLIC)
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
        from fairdm.contrib.contributors.models import Contributor
        from fairdm.factories import OrganizationFactory

        def a_record_of(model):
            if model is Project:
                return ProjectFactory(visibility=Visibility.PUBLIC)
            if model is Dataset:
                return DatasetFactory(visibility=Visibility.PUBLIC)
            if model is Contributor:
                return OrganizationFactory()
            return make_record(model, DatasetFactory(visibility=Visibility.PUBLIC))

        return a_record_of

    @pytest.fixture
    def address(self, url_of):
        """Return a function giving a record's or a model's list address, contributors too."""
        from fairdm.contrib.contributors.models import Contributor

        def address(subject, action="detail"):
            if subject is Contributor or isinstance(subject, Contributor):
                kwargs = None if isinstance(subject, type) else {"uuid": subject.uuid}
                return reverse(f"api:contributor-{action}", kwargs=kwargs)
            return url_of(subject, action)

        return address

    @pytest.fixture
    def bodies(self, body_for):
        """Return a function giving the bodies to send to the routes of a model, as a dict."""
        from fairdm.contrib.contributors.models import Contributor
        from fairdm.core.models import Measurement
        from fairdm.registry import registry

        def bodies(model, record):
            if model is Contributor:
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
            DatasetFactory(project=record, visibility=Visibility.PUBLIC)
        if held_by_others and issubclass(model, Sample):
            make_record(XRFMeasurement, record.dataset, sample=record)

        response = client.delete(address(record))

        assert response.status_code < 500
