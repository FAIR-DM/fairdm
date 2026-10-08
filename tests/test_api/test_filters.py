"""Visibility filter tests for FairDM API (Feature 011 â€” US4)."""

import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


def make_token_client(user) -> APIClient:
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
class TestVisibilityFilterProjects:
    def test_public_project_visible_to_anonymous(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        resp = APIClient().get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_private_project_hidden_from_anonymous(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        resp = APIClient().get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) not in uuids

    def test_private_project_hidden_from_authenticated_without_perm(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        resp = make_token_client(UserFactory()).get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) not in uuids

    def test_private_project_visible_to_user_with_view_perm(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.VIEW
        )
        resp = make_token_client(user).get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_a_stored_guardian_row_alone_does_not_list_a_private_project(self):
        from fairdm.core.utils import assign_perm

        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        resp = make_token_client(user).get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) not in uuids

    def test_mixed_queryset_no_duplicates(self):
        user = UserFactory()
        pub = ProjectFactory(visibility=Visibility.PUBLIC)
        priv = ProjectFactory(visibility=Visibility.PRIVATE)
        # Grant view on the public project via guardian too (both filter branches apply)
        ContributionFactory(
            content_object=pub, contributor=user, level=ContributionLevel.VIEW
        )
        ContributionFactory(
            content_object=priv, contributor=user, level=ContributionLevel.VIEW
        )

        resp = make_token_client(user).get(reverse("api:project-list"))
        results = resp.json()["results"]
        all_uuids = [p["uuid"] for p in results]
        assert len(all_uuids) == len(set(all_uuids))
        assert str(pub.uuid) in all_uuids
        assert str(priv.uuid) in all_uuids

    def test_anonymous_sees_multiple_public_projects(self):
        proj1 = ProjectFactory(visibility=Visibility.PUBLIC)
        proj2 = ProjectFactory(visibility=Visibility.PUBLIC)
        resp = APIClient().get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj1.uuid) in uuids
        assert str(proj2.uuid) in uuids


@pytest.mark.django_db
class TestVisibilityFilterDatasets:
    def test_public_dataset_visible_to_anonymous(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PUBLIC)
        resp = APIClient().get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) in uuids

    def test_a_level_on_the_project_above_lists_its_private_dataset(self):
        user = UserFactory()
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        ds = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.VIEW
        )
        resp = make_token_client(user).get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) in uuids

    def test_private_dataset_hidden_without_perm(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        resp = make_token_client(UserFactory()).get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) not in uuids

    def test_private_dataset_visible_with_perm(self):
        user = UserFactory()
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=ds, contributor=user, level=ContributionLevel.VIEW
        )
        resp = make_token_client(user).get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) in uuids


@pytest.mark.django_db
class TestVisibilityFilterContributors:
    def test_all_contributors_visible_to_anonymous(self):
        resp = APIClient().get(reverse("api:contributor-list"))
        assert resp.status_code == 200

    def test_contributor_list_returns_200_for_authenticated(self):
        resp = make_token_client(UserFactory()).get(reverse("api:contributor-list"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestVisibilityOfSamplesAndMeasurements:
    @pytest.fixture(params=["sample", "measurement"])
    def case(self, request, make_record, url_of):
        """A public and a private record of a kind, with the address of their list."""
        from types import SimpleNamespace

        from demo.models import ExampleMeasurement, RockSample

        model = RockSample if request.param == "sample" else ExampleMeasurement
        private = DatasetFactory(visibility=Visibility.PRIVATE)
        public = DatasetFactory(visibility=Visibility.PUBLIC)
        return SimpleNamespace(
            private_dataset=private,
            hidden=make_record(model, private),
            shown=make_record(model, public),
            address=url_of(model, "list"),
        )

    @staticmethod
    def listed_by(client, address):
        data = client.get(address).json()
        return {row["uuid"] for row in data["results"]}, data["count"]

    def test_a_person_with_a_level_on_the_dataset_receives_its_records(self, case):
        from rest_framework.test import APIClient

        viewer = UserFactory()
        ContributionFactory(
            content_object=case.private_dataset,
            contributor=viewer,
            level=ContributionLevel.VIEW,
        )
        client = APIClient()
        client.force_authenticate(viewer)

        listed, count = self.listed_by(client, case.address)

        assert listed == {case.hidden.uuid, case.shown.uuid}
        assert count == 2

    def test_a_signed_in_person_with_no_level_receives_only_public_records(self, case):
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(UserFactory())

        listed, count = self.listed_by(client, case.address)

        assert listed == {case.shown.uuid}
        assert count == 1

    def test_a_visitor_receives_only_public_records(self, case):
        from rest_framework.test import APIClient

        listed, count = self.listed_by(APIClient(), case.address)

        assert listed == {case.shown.uuid}
        assert count == 1
