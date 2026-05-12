"""
Integration tests for fairdm.core.dataset views.

Tests the interaction between views, forms, and models, verifying complete
request/response cycles for dataset CRUD operations.

Phases 3-8 map to User Stories 1-6 from spec/014-dataset-crud-views.
"""

import time

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from fairdm.factories import DatasetFactory, UserFactory
from fairdm.utils.choices import Visibility

# ---------------------------------------------------------------------------
# Phase 3 — User Story 1: Browse and Search the Dataset List
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetListView:
    """Smoke tests and behaviour tests for DatasetListView (US1)."""

    def test_anonymous_get(self, client):
        """T004 — GET /datasets/ returns 200 for anonymous users."""
        url = reverse("dataset-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_shows_only_public_datasets(self, client):
        """T005 — List shows only PUBLIC datasets; PRIVATE datasets are hidden."""
        public = DatasetFactory(name="Public Dataset", visibility=Visibility.PUBLIC)
        DatasetFactory(name="Private Dataset", visibility=Visibility.PRIVATE)

        url = reverse("dataset-list")
        response = client.get(url)

        assert response.status_code == 200
        assert public.name in str(response.content)
        assert "Private Dataset" not in str(response.content)

    def test_order_by_added(self, client):
        """T006 — ?o=added and ?o=-added return results in expected chronological order."""
        older = DatasetFactory(name="Older Dataset", visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = DatasetFactory(name="Newer Dataset", visibility=Visibility.PUBLIC)

        url = reverse("dataset-list")

        response_asc = client.get(url, {"o": "added"})
        assert response_asc.status_code == 200
        content_asc = str(response_asc.content)
        assert content_asc.index(older.name) < content_asc.index(newer.name)

        response_desc = client.get(url, {"o": "-added"})
        assert response_desc.status_code == 200
        content_desc = str(response_desc.content)
        assert content_desc.index(newer.name) < content_desc.index(older.name)


# ---------------------------------------------------------------------------
# Phase 4 — User Story 2: Create a New Dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetCreateView:
    """Smoke tests and behaviour tests for DatasetCreateView (US2)."""

    def test_anonymous_redirects_to_login(self, client):
        """T011 — GET /datasets/create/ by anonymous client returns 302 to login."""
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_authenticated_get_200(self, client):
        """T012 — GET /datasets/create/ by authenticated client returns 200."""
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 200

    def test_valid_post_redirects_to_detail(self, client):
        """T013 — Valid POST redirects to dataset-detail URL.

        MUST FAIL before T015 (DatasetCreateForm) because DatasetForm requires
        additional fields that make a minimal POST fail form validation.
        """
        from licensing.models import License

        from fairdm.factories import ProjectFactory

        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        # User must be a contributor of the project for it to appear in the
        # project queryset (DatasetForm filters to user.projects.all())
        project.add_contributor(user)
        license_obj = License.objects.first()

        url = reverse("dataset-create")
        response = client.post(
            url,
            data={
                "name": "New Test Dataset",
                "project": project.pk,
                "license": license_obj.pk,
            },
        )

        assert response.status_code == 302, (
            f"Form errors: {response.context['form'].errors if 'form' in response.context else 'no form in context'}"
        )

        from fairdm.core.dataset.models import Dataset

        dataset = Dataset.objects.get(name="New Test Dataset")
        expected_url = reverse("dataset-detail", kwargs={"uuid": dataset.uuid})
        assert response.url == expected_url

    def test_assigns_permissions_and_roles(self, client):
        """T014 — After valid POST, creating user holds all 5 permissions and correct roles.

        FR-012, FR-013.
        """
        from licensing.models import License

        from fairdm.factories import ProjectFactory

        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        # User must be a contributor of the project for it to appear in the
        # project queryset (DatasetForm filters to user.projects.all())
        project.add_contributor(user)
        license_obj = License.objects.first()

        url = reverse("dataset-create")
        response = client.post(
            url,
            data={
                "name": "Permission Test Dataset",
                "project": project.pk,
                "license": license_obj.pk,
            },
        )

        assert response.status_code == 302, (
            f"Form errors: {response.context['form'].errors if 'form' in response.context else 'no form in context'}"
        )

        from fairdm.core.dataset.models import Dataset

        dataset = Dataset.objects.get(name="Permission Test Dataset")

        expected_perms = [
            "view_dataset",
            "change_dataset",
            "delete_dataset",
            "change_dataset_metadata",
            "change_dataset_settings",
        ]
        for perm in expected_perms:
            assert user.has_perm(perm, dataset), f"Missing permission: {perm}"

        contributor = dataset.contributors.filter(contributor=user).first()
        assert contributor is not None, "User should be a contributor"
        role_names = list(contributor.roles.values_list("name", flat=True))
        for role in ["Creator", "ProjectMember", "ContactPerson"]:
            assert role in role_names, f"Missing contributor role: {role}"


# ---------------------------------------------------------------------------
# Phase 5 — User Story 3: Edit Dataset Core Attributes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetUpdateView:
    """Smoke tests and behaviour tests for DatasetUpdateView (US3)."""

    def test_anonymous_redirects_to_login(self, client):
        """T019 — GET /datasets/<uuid>/update/ by anonymous client returns 302."""
        dataset = DatasetFactory()
        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_no_permission_returns_403(self, client):
        """T020 — Authenticated client without change_dataset returns 403."""
        user = UserFactory()
        dataset = DatasetFactory()
        client.force_login(user)
        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_with_permission_returns_200(self, client):
        """T021 — Client with change_dataset permission GET returns 200."""
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_valid_post_redirects_to_detail(self, client):
        """T022 — Valid POST by permitted user returns 302 to dataset-detail URL. FR-018a."""
        from licensing.models import License

        user = UserFactory()
        dataset = DatasetFactory(name="Original Name")
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        # User must be a contributor of the dataset's project for it to appear
        # in the project queryset (DatasetForm filters to user.projects.all())
        project = dataset.project
        project.add_contributor(user)
        license_obj = dataset.license if dataset.license else License.objects.first()

        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.post(
            url,
            data={
                "name": "Updated Name",
                "project": project.pk,
                "license": license_obj.pk,
            },
        )

        assert response.status_code == 302, (
            f"Form errors: {response.context['form'].errors if 'form' in response.context else 'no form in context'}"
        )
        expected_url = reverse("dataset-detail", kwargs={"uuid": dataset.uuid})
        assert response.url == expected_url


# ---------------------------------------------------------------------------
# Phase 6 — User Story 4: Delete a Dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetDeleteView:
    """Smoke tests and behaviour tests for DatasetDeleteView (US4)."""

    def test_anonymous_redirects_to_login(self, client):
        """T027 — GET /datasets/<uuid>/delete/ by anonymous client returns 302."""
        dataset = DatasetFactory()
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_no_permission_returns_403(self, client):
        """T028 — Authenticated client without delete_dataset returns 403."""
        user = UserFactory()
        dataset = DatasetFactory()
        client.force_login(user)
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_with_permission_returns_200(self, client):
        """T029 — Client with delete_dataset permission GET returns 200."""
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_wrong_name_shows_error(self, client):
        """T030 — POST with mismatched confirmation returns 200 with form error; dataset not deleted."""
        from fairdm.core.dataset.models import Dataset

        user = UserFactory()
        dataset = DatasetFactory(name="My Dataset")
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "Wrong Name"})
        assert response.status_code == 200
        assert "confirmation" in response.context["form"].errors
        assert Dataset.objects.filter(pk=dataset.pk).exists()

    def test_correct_name_redirects_to_list(self, client):
        """T030a — POST with correct name redirects to dataset-list; dataset deleted."""
        from fairdm.core.dataset.models import Dataset

        user = UserFactory()
        dataset = DatasetFactory(name="Delete Me Dataset")
        pk = dataset.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "Delete Me Dataset"})
        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Dataset.objects.filter(pk=pk).exists()
