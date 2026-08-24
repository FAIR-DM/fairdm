"""The project's own pages: one registered collection, per 013 plan P1.

T063 - the project's own page is a registration against ``Project``, so the portal's per-record
       navigation offers an entry for it, and that entry is selected while on the page.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from fairdm import plugins
from fairdm.core.project.models import Project


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
