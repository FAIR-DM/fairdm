"""Record pages served end to end, through the URL configuration.

The suite had 70 passing plugin tests while every sample page returned 500, because every one of
them tested a unit. A predicate written to a signature the navigation package does not call raises
inside template rendering, which no unit test reaches. These do.
"""

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from fairdm.factories import (
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from fairdm_demo.factories import RockSampleFactory


@pytest.mark.django_db
class TestRecordPagesServe:
    def test_sample_overview(self, client):
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        assert response.status_code == 200

    def test_dataset_plugin_page(self, client):
        """Dataset's descriptions page - a registration of its own until US-4 folds
        it into the overview's extra_views (014 plan Order step 3)."""
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        response = client.get(
            reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})
        )
        assert response.status_code == 200

    def test_dataset_overview(self, client):
        """The dataset's own page, now a registration like every other core
        record's (014 T056)."""
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))
        assert response.status_code == 200

    def test_dataset_overview_refuses_an_anonymous_visitor_to_a_private_record_not_found(
        self, client
    ):
        """A private dataset the visitor may not see answers 404, not a
        redirect to sign in, so the address does not confirm the record
        exists (014 plan P1)."""
        dataset = DatasetFactory()  # private, per the model default
        response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))
        assert response.status_code == 404

    def test_dataset_overview_refuses_a_signed_in_stranger_to_a_private_record_not_found(
        self, client
    ):
        """A private dataset a signed-in user has no rights over answers 404,
        not 403, for the same reason (014 plan P1)."""
        dataset = DatasetFactory()  # private, per the model default
        client.force_login(UserFactory())
        response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))
        assert response.status_code == 404

    def test_dataset_overview_admits_a_holder_of_view_permission(self, client):
        """A private dataset is still open to a user granted view_dataset on
        it at record level."""
        dataset = DatasetFactory()
        user = UserFactory()
        assign_perm("view_dataset", user, dataset)
        client.force_login(user)
        response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))
        assert response.status_code == 200

    def test_dataset_plugin_page_is_closed_to_a_visitor(self, client):
        """The dataset management pages edit the record, so they are not open to
        someone holding only its address. Before they declared a permission the
        plugin machinery admitted every request, anonymous included, and served a
        private dataset's descriptions to it.
        """
        dataset = DatasetFactory()
        url = reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})

        anonymous = client.get(url)
        assert anonymous.status_code == 302

        client.force_login(UserFactory())
        assert client.get(url).status_code == 403

    def test_project_plugin_page(self, client):
        project = ProjectFactory()
        response = client.get(
            reverse("project:dataset-list", kwargs={"uuid": project.uuid})
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestNavigationRenders:
    """A page with no navigation still returns 200, so status is not enough."""

    def test_sample_page_renders_its_local_navigation(self, client):
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        content = response.content.decode()
        assert "Overview" in content

    def test_every_visible_entry_points_somewhere(self, client):
        """An entry whose address will not reverse is hidden rather than raised.

        That is the correct fail-safe, and it is also how a broken menu hides instead of
        announcing itself — so the test asserts entries are present, not merely that nothing blew up.
        """
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        content = response.content.decode()
        assert f"/samples/{sample.uuid}/" in content


@pytest.mark.django_db
class TestPredicateFailureDoesNotBreakThePage:
    def test_a_predicate_written_to_the_wrong_signature_hides_its_entry(
        self, client, monkeypatch
    ):
        """The defect that took every sample page down.

        A predicate declared ``(request, instance, **kwargs)`` cannot be satisfied by the navigation
        package, which calls ``check(request, **kwargs)``. Before the adapter, the resulting
        TypeError escaped template rendering as a 500.
        """
        from fairdm.contrib.plugins import registry
        from fairdm.core.sample.models import Sample

        registered = registry.get_plugins_for_model(Sample)
        assert registered, "expected sample plugins to be registered"

        def wrong_signature(request, instance, **kwargs):
            return True

        plugin_class = registered[0][0]
        monkeypatch.setattr(plugin_class, "check", wrong_signature, raising=False)

        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        assert response.status_code == 200
