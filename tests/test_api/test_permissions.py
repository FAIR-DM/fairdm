"""Permission enforcement tests for FairDM API (Feature 011 â€” US4)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from tests.test_api.conftest import make_token_client


@pytest.mark.django_db
class TestAnonymousAccess:
    def test_list_returns_200(self):
        response = APIClient().get(reverse("api:project-list"))
        assert response.status_code == 200

    def test_public_project_detail_returns_200(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().get(url).status_code == 200

    def test_private_project_detail_returns_404(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().get(url).status_code == 404

    def test_post_returns_401(self):
        response = APIClient().post(
            reverse("api:project-list"), {"name": "X"}, format="json"
        )
        assert response.status_code == 401

    def test_patch_public_project_returns_401(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        response = APIClient().patch(url, {"name": "Hacked"}, format="json")
        assert response.status_code == 401

    def test_delete_public_project_returns_401(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().delete(url).status_code == 401


@pytest.mark.django_db
class TestAuthenticatedNoPermission:
    def test_private_project_detail_returns_404(self):
        owner = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # different user, no perms
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.get(url).status_code == 404

    def test_patch_public_project_returns_403(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        client = make_token_client(UserFactory())  # no guardian perm
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        response = client.patch(url, {"name": "Hijack"}, format="json")
        assert response.status_code == 403

    def test_patch_private_project_returns_404(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # no guardian perm
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        response = client.patch(url, {"name": "Hijack"}, format="json")
        assert response.status_code == 404

    def test_delete_private_project_returns_404(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.delete(url).status_code == 404

    def test_create_project_succeeds(self):
        client = make_token_client(UserFactory())
        response = client.post(
            reverse("api:project-list"), {"name": "My New Project"}, format="json"
        )
        assert response.status_code == 201


@pytest.mark.django_db
class TestAuthenticatedWithPermission:
    def test_view_perm_allows_private_project_read(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.VIEW
        )
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.get(url).status_code == 200

    def test_change_perm_allows_patch(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.EDIT
        )
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        resp = client.patch(url, {"name": "Updated"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_delete_perm_allows_delete(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.MANAGE
        )
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.delete(url).status_code == 204

    def test_owner_created_object_gets_full_access(self):
        user = UserFactory()
        client = make_token_client(user)

        post_resp = client.post(
            reverse("api:project-list"), {"name": "Owner Project"}, format="json"
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]
        url = reverse("api:project-detail", kwargs={"uuid": uuid})

        patch_resp = client.patch(url, {"name": "Renamed"}, format="json")
        assert patch_resp.status_code == 200

        del_resp = client.delete(url)
        assert del_resp.status_code == 204

    def test_viewer_cannot_patch_private_project(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.VIEW
        )  # view but not change
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        resp = client.patch(url, {"name": "No Access"}, format="json")
        assert resp.status_code == 403

    def test_private_project_appears_in_list_for_permitted_user(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.VIEW
        )
        client = make_token_client(user)
        response = client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_private_project_excluded_from_list_without_perm(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # no perm
        response = client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(proj.uuid) not in uuids


@pytest.mark.django_db
class TestDatasetPermissions:
    def test_anonymous_cannot_see_private_dataset_detail(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        url = reverse("api:dataset-detail", kwargs={"uuid": ds.uuid})
        assert APIClient().get(url).status_code == 404

    def test_permitted_user_can_see_private_dataset(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        user = UserFactory()
        ContributionFactory(
            content_object=ds, contributor=user, level=ContributionLevel.VIEW
        )
        client = make_token_client(user)
        url = reverse("api:dataset-detail", kwargs={"uuid": ds.uuid})
        assert client.get(url).status_code == 200


@pytest.mark.django_db
class TestReadingASampleOrMeasurement:
    @pytest.fixture(params=["dataset", "sample", "measurement"])
    def private(self, request, make_record, url_of):
        """A private dataset, or a sample or measurement in one, and its address."""
        from types import SimpleNamespace

        from demo.models import ExampleMeasurement, RockSample

        dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        record = {
            "dataset": lambda: dataset,
            "sample": lambda: make_record(RockSample, dataset),
            "measurement": lambda: make_record(ExampleMeasurement, dataset),
        }[request.param]()
        return SimpleNamespace(dataset=dataset, address=url_of(record))

    def test_a_visitor_is_answered_as_for_a_record_that_does_not_exist(self, private):
        assert APIClient().get(private.address).status_code == 404

    def test_a_signed_in_person_with_no_level_is_answered_the_same_way(self, private):
        client = APIClient()
        client.force_authenticate(UserFactory())

        assert client.get(private.address).status_code == 404

    def test_a_person_at_the_view_level_on_the_dataset_receives_the_record(
        self, private
    ):
        viewer = UserFactory()
        ContributionFactory(
            content_object=private.dataset,
            contributor=viewer,
            level=ContributionLevel.VIEW,
        )
        client = APIClient()
        client.force_authenticate(viewer)

        response = client.get(private.address)

        assert response.status_code == 200


@pytest.mark.django_db
class TestWhoMayWriteSamplesAndMeasurements:
    @pytest.fixture(params=["sample", "measurement"])
    def kind(self, request):
        return request.param

    @pytest.fixture
    def a_record_in(self, kind, make_record):
        """Return a function building a sample or measurement in a dataset of a visibility."""
        from demo.models import ExampleMeasurement, RockSample

        def a_record_in(visibility):
            dataset = DatasetFactory(visibility=visibility)
            model = RockSample if kind == "sample" else ExampleMeasurement
            return dataset, make_record(model, dataset)

        return a_record_in

    @pytest.fixture(params=["patch", "put", "delete"])
    def send(self, request):
        """Return a function sending a change or a delete to a record's address."""

        def send(client, address):
            body = (
                {"name": "Changed by a script"} if request.param != "delete" else None
            )
            if request.param == "put":
                return client.put(address, body, format="json")
            if request.param == "patch":
                return client.patch(address, body, format="json")
            return client.delete(address)

        return send

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.PRIVATE])
    def test_no_authentication_is_answered_401(
        self, a_record_in, url_of, send, visibility
    ):
        _dataset, record = a_record_in(visibility)

        assert send(APIClient(), url_of(record)).status_code == 401

    def test_no_level_on_a_public_record_is_answered_403(
        self, a_record_in, url_of, send, signed_in
    ):
        _dataset, record = a_record_in(Visibility.PUBLIC)

        response = send(signed_in(UserFactory()), url_of(record))

        assert response.status_code == 403

    def test_no_level_on_a_private_record_is_answered_404(
        self, a_record_in, url_of, send, signed_in
    ):
        _dataset, record = a_record_in(Visibility.PRIVATE)

        response = send(signed_in(UserFactory()), url_of(record))

        assert response.status_code == 404

    def test_the_view_level_on_a_private_record_is_answered_403(
        self, a_record_in, url_of, send, signed_in, member_at
    ):
        dataset, record = a_record_in(Visibility.PRIVATE)
        viewer = member_at(dataset, ContributionLevel.VIEW)

        response = send(signed_in(viewer), url_of(record))

        assert response.status_code == 403

    def test_a_refused_change_leaves_the_record_as_it_was(
        self, a_record_in, url_of, signed_in, member_at, kind
    ):
        dataset, record = a_record_in(Visibility.PRIVATE)
        viewer = member_at(dataset, ContributionLevel.VIEW)
        name = record.name

        signed_in(viewer).patch(url_of(record), {"name": "Hijack"}, format="json")
        signed_in(viewer).delete(url_of(record))

        stored = type(record).objects.get(pk=record.pk)
        assert stored.name == name

    def test_no_authentication_cannot_create(self, url_of, body_for, kind):
        from demo.models import RockSample, XRFMeasurement

        model = RockSample if kind == "sample" else XRFMeasurement
        body, _stored = body_for(model)
        body["dataset"] = DatasetFactory(visibility=Visibility.PUBLIC).uuid

        response = APIClient().post(url_of(model, "list"), body, format="json")

        assert response.status_code == 401
        assert model.objects.count() == 1

    @pytest.mark.parametrize("level", [ContributionLevel.VIEW, None])
    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.PRIVATE])
    def test_without_the_edit_level_on_the_dataset_nothing_is_created_in_it(
        self, url_of, body_for, signed_in, member_at, kind, level, visibility
    ):
        from demo.factories import RockSampleFactory
        from demo.models import RockSample, XRFMeasurement
        from fairdm.factories import PersonFactory

        model = RockSample if kind == "sample" else XRFMeasurement
        dataset = DatasetFactory(visibility=visibility)
        person = PersonFactory(is_active=True, is_claimed=True)
        if level is not None:
            member_at(dataset, level, person)
        body, _stored = body_for(model)
        stored_before = model.objects.count()
        body["dataset"] = dataset.uuid
        if kind == "measurement":
            body["sample"] = RockSampleFactory(dataset=dataset).uuid

        response = signed_in(person).post(url_of(model, "list"), body, format="json")

        assert response.status_code == 400
        assert "dataset" in response.json()
        assert model.objects.count() == stored_before


@pytest.mark.django_db
class TestManageLevel:
    MOVES = ["dataset", "sample", "measurement"]

    @staticmethod
    def stored(record):
        """Return the record as stored, whether or not the default manager hides it."""
        model = type(record)
        return getattr(model, "all_objects", model.objects).get(pk=record.pk)

    @pytest.fixture
    def scene(self, make_record):
        """Return a function building a record with a parent to move it to."""
        from types import SimpleNamespace

        from demo.factories import RockSampleFactory
        from demo.models import ExampleMeasurement, RockSample

        def scene(kind):
            if kind == "dataset":
                project = ProjectFactory(visibility=Visibility.PRIVATE)
                record = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
                return SimpleNamespace(
                    record=record,
                    above=project,
                    field="project",
                    current=project,
                    other=ProjectFactory(visibility=Visibility.PRIVATE),
                )
            dataset = DatasetFactory(visibility=Visibility.PRIVATE)
            if kind == "sample":
                return SimpleNamespace(
                    record=make_record(RockSample, dataset),
                    above=dataset,
                    field="dataset",
                    current=dataset,
                    other=DatasetFactory(visibility=Visibility.PRIVATE),
                )
            sample = RockSampleFactory(dataset=dataset)
            return SimpleNamespace(
                record=make_record(ExampleMeasurement, dataset, sample=sample),
                above=dataset,
                field="sample",
                current=sample,
                other=RockSampleFactory(dataset=dataset),
            )

        return scene

    @pytest.fixture(params=["project", "dataset"])
    def private_record(self, request):
        """A private project or dataset, each in turn."""
        factory = ProjectFactory if request.param == "project" else DatasetFactory
        return factory(visibility=Visibility.PRIVATE)

    def test_someone_at_the_edit_level_cannot_change_visibility(
        self, private_record, url_of, member_at, signed_in
    ):
        editor = member_at(private_record, ContributionLevel.EDIT)

        response = signed_in(editor).patch(
            url_of(private_record), {"visibility": Visibility.PUBLIC}, format="json"
        )

        assert response.status_code == 403
        private_record = self.stored(private_record)
        assert private_record.visibility == Visibility.PRIVATE

    def test_someone_at_the_manage_level_can_change_visibility(
        self, private_record, url_of, member_at, signed_in
    ):
        manager = member_at(private_record, ContributionLevel.MANAGE)

        response = signed_in(manager).patch(
            url_of(private_record), {"visibility": Visibility.PUBLIC}, format="json"
        )

        assert response.status_code == 200
        private_record = self.stored(private_record)
        assert private_record.visibility == Visibility.PUBLIC

    def test_someone_at_the_edit_level_can_change_another_field(
        self, private_record, url_of, member_at, signed_in
    ):
        editor = member_at(private_record, ContributionLevel.EDIT)

        response = signed_in(editor).patch(
            url_of(private_record), {"name": "Renamed"}, format="json"
        )

        assert response.status_code == 200

    def test_sending_the_visibility_a_record_has_needs_only_the_edit_level(
        self, private_record, url_of, member_at, signed_in
    ):
        editor = member_at(private_record, ContributionLevel.EDIT)

        response = signed_in(editor).patch(
            url_of(private_record),
            {"name": "Renamed", "visibility": Visibility.PRIVATE},
            format="json",
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("kind", MOVES)
    def test_someone_at_the_edit_level_cannot_move_a_record(
        self, scene, kind, url_of, member_at, signed_in
    ):
        found = scene(kind)
        editor = member_at(found.above, ContributionLevel.EDIT)
        member_at(found.other, ContributionLevel.EDIT, editor)

        response = signed_in(editor).patch(
            url_of(found.record), {found.field: found.other.uuid}, format="json"
        )

        assert response.status_code == 403
        stored = self.stored(found.record)
        assert getattr(stored, f"{found.field}_id") == found.current.pk

    @pytest.mark.parametrize("kind", MOVES)
    def test_someone_at_the_manage_level_can_move_a_record(
        self, scene, kind, url_of, member_at, signed_in
    ):
        found = scene(kind)
        manager = member_at(found.record, ContributionLevel.MANAGE)
        member_at(found.other, ContributionLevel.EDIT, manager)

        response = signed_in(manager).patch(
            url_of(found.record), {found.field: found.other.uuid}, format="json"
        )

        assert response.status_code == 200, response.content
        stored = self.stored(found.record)
        assert getattr(stored, f"{found.field}_id") == found.other.pk

    @pytest.mark.parametrize("kind", ["dataset", "sample"])
    def test_a_move_that_leaves_nobody_able_to_manage_the_record_is_refused(
        self, scene, kind, url_of, member_at, signed_in
    ):
        found = scene(kind)
        manager = member_at(found.above, ContributionLevel.MANAGE)
        member_at(found.other, ContributionLevel.EDIT, manager)

        response = signed_in(manager).patch(
            url_of(found.record), {found.field: found.other.uuid}, format="json"
        )

        assert response.status_code == 400
        assert found.field in response.json()
        stored = self.stored(found.record)
        assert getattr(stored, f"{found.field}_id") == found.current.pk

    @pytest.mark.parametrize("kind", MOVES)
    def test_sending_the_parent_a_record_has_needs_only_the_edit_level(
        self, scene, kind, url_of, member_at, signed_in
    ):
        found = scene(kind)
        editor = member_at(found.above, ContributionLevel.EDIT)

        response = signed_in(editor).patch(
            url_of(found.record),
            {"name": "Renamed", found.field: found.current.uuid},
            format="json",
        )

        assert response.status_code == 200, response.content
        assert response.json()["name"] == "Renamed"
