"""The project's own pages: one registered collection, per 013 plan P1.

T063 - the project's own page is a registration against ``Project``, so the portal's per-record
       navigation offers an entry for it, and that entry is selected while on the page.
T064 - its attributes and deletion pages are extra views of that registration, not registrations
       of their own, so the navigation strip gains no entry for either.
T065 - each of those pages states its own permission, since an additional view inherits its
       owner's predicate but never its permission.
T066 - the registration's own visibility check refuses a private project to anyone without
       `project.view_project`, since a registered page resolves its record past the filtered
       manager on the assumption that the page gates itself.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from fairdm import plugins
from fairdm.contrib.plugins.access import can_open
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import Attributes, Delete, Overview
from fairdm.core.utils import assign_perm


def _request_for(user, path="/"):
    request = RequestFactory().get(path)
    request.user = user
    return request


def _entry_labels(model):
    # Rebuilds the menu now, rather than relying on it having been built already by the root
    # urlconf's own import — the same reason ``tests/test_contrib/test_plugins/test_menus.py``
    # calls this before every assertion.
    plugins.registry.get_urls_for_model(model)
    menu = plugins.registry.get_plugin_menu_for_model(model)
    return [item.extra_context.get("label") for item in menu.children]


@pytest.mark.django_db
class TestOverviewIsTheProjectsOwnRegistration:
    """The project's own page used to sit outside the registration namespace, so the per-record
    navigation could never offer an entry for it and no tab was ever selected while on it
    (013 plan P1)."""

    def test_the_project_menu_carries_an_overview_entry(self):
        assert "Overview" in _entry_labels(Project)

    def test_the_overview_entry_is_selected_while_on_the_projects_page(
        self, public_project
    ):
        menu = plugins.registry.get_plugin_menu_for_model(Project)
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        request = _request_for(AnonymousUser(), path=url)
        processed = menu.process(
            request, object=public_project, uuid=public_project.uuid
        )
        overview_item = next(
            child
            for child in processed.children
            if child.extra_context.get("label") == "Overview"
        )
        assert overview_item.selected is True

    def test_the_overview_declares_no_path_segment_of_its_own(self, public_project):
        """It stays the root of the record's include, the same convention the contributor
        pages already use."""
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        # Nothing follows the record's own identifier in the address.
        assert url.split(str(public_project.uuid))[-1] == "/"


@pytest.mark.django_db
class TestAttributesAndDeletionAreExtraViewsNotEntries:
    """A registration carries one menu entry for the whole collection; the attributes and
    deletion pages hang off the overview's registration rather than registering themselves, so
    the strip does not fill with an entry per addon (013 plan P1)."""

    def test_the_attributes_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse(
            "project:overview-attributes", kwargs={"uuid": public_project.uuid}
        )
        assert url.endswith(f"{public_project.uuid}/attributes/")

    def test_the_deletion_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse("project:overview-delete", kwargs={"uuid": public_project.uuid})
        assert url.endswith(f"{public_project.uuid}/delete/")

    def test_the_project_menu_carries_no_entry_for_attributes_or_deletion(self):
        labels = _entry_labels(Project)
        assert "Attributes" not in labels
        assert "Delete" not in labels

    def test_the_project_menu_carries_exactly_one_entry_for_the_collection(self):
        """Superseded ``ProjectConfigure`` (013 plan P1) is retired along with the standalone
        pages it duplicated, so the collection is carried by ``Overview`` alone."""
        labels = _entry_labels(Project)
        assert labels.count("Overview") == 1
        assert "Configure" not in labels


@pytest.mark.django_db
class TestEachExtraViewStatesItsOwnPermission:
    """FR-051 / issue #279: an additional view inherits its owner's ``check`` but never its
    ``permission`` (fairdm/contrib/plugins/access.py ``can_open``), so a page that states none
    is open to everyone, including an anonymous visitor. Each page here names the right it
    needs, matching the standalone pages it replaces (013 plan P1)."""

    def test_attributes_refuses_a_signed_in_user_without_change_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Attributes, request, public_project) is False

    def test_attributes_admits_a_user_holding_change_permission(
        self, user_with_change_permission
    ):
        request = _request_for(user_with_change_permission)
        assert (
            can_open(Attributes, request, user_with_change_permission.project) is True
        )

    def test_attributes_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Attributes, request, public_project) is False

    def test_deletion_refuses_a_signed_in_user_without_delete_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Delete, request, public_project) is False

    def test_deletion_admits_a_user_holding_delete_permission(
        self, user_with_delete_permission
    ):
        request = _request_for(user_with_delete_permission)
        assert can_open(Delete, request, user_with_delete_permission.project) is True

    def test_deletion_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Delete, request, public_project) is False


@pytest.mark.django_db
class TestTheOverviewGuardsAPrivateProjectsVisibility:
    """The regression this restructuring is most likely to introduce (013 plan P1): a
    registered page resolves its record through machinery that reads past the filtered manager,
    on the assumption that the page gates itself. Without the visibility check carried across, a
    private project becomes readable by anyone holding its address."""

    def test_a_private_project_refuses_a_user_who_may_not_view_it(
        self, private_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Overview, request, private_project) is False

    def test_a_private_project_refuses_an_anonymous_request(self, private_project):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, private_project) is False

    def test_a_private_project_admits_a_user_holding_view_permission(
        self, private_project, user_with_no_permission
    ):
        assign_perm("view_project", user_with_no_permission, private_project)
        request = _request_for(user_with_no_permission)
        assert can_open(Overview, request, private_project) is True

    def test_a_public_project_admits_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, public_project) is True

    def test_the_attributes_page_inherits_the_visibility_check_from_its_owner(
        self, private_project, user_with_change_permission
    ):
        """A user holding change rights on a *different* project still cannot reach a private
        project's attributes page: an additional view inherits its owner's `check`, so the
        visibility guard applies there too."""
        request = _request_for(user_with_change_permission)
        assert can_open(Attributes, request, private_project) is False


@pytest.mark.django_db
class TestAPrivateProjectsPageThroughARealRequest:
    """`can_open()` answering False is a claim about the predicate, not about the page. These
    go through the URL and the response, which is the composition a visitor actually meets."""

    def test_an_anonymous_visitor_is_refused_a_private_project(
        self, client, private_project
    ):
        response = client.get(
            reverse("project:overview", kwargs={"uuid": private_project.uuid})
        )
        assert response.status_code in (302, 403, 404)
        if response.status_code == 302:
            assert reverse("account_login") in response.url

    def test_a_signed_in_visitor_without_view_rights_is_refused(
        self, client, private_project, user_with_no_permission
    ):
        client.force_login(user_with_no_permission)
        response = client.get(
            reverse("project:overview", kwargs={"uuid": private_project.uuid})
        )
        assert response.status_code in (403, 404)

    def test_an_anonymous_visitor_reaches_a_public_project(self, client, public_project):
        response = client.get(
            reverse("project:overview", kwargs={"uuid": public_project.uuid})
        )
        assert response.status_code == 200
