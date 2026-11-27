"""Tests for the FairDM application menu (``fairdm/menus.py``)."""

import pytest
from django.urls import reverse


@pytest.fixture()
def documentation_menu_group():
    from mvp.menus import AppMenu

    groups = [
        item
        for item in AppMenu.children
        if any(
            getattr(child, "view_name", None) == "api:api-docs"
            for child in getattr(item, "children", [])
        )
    ]
    assert groups, "No menu group holds the API documentation link."
    return groups[0]


class TestAPIMenuItem:
    def test_exactly_one_entry_leads_to_the_api_documentation(self):
        from mvp.menus import AppMenu

        def entries(items):
            for item in items:
                yield item
                yield from entries(getattr(item, "children", []))

        leading = [
            item
            for item in entries(AppMenu.children)
            if getattr(item, "view_name", None) == "api:api-docs"
        ]

        assert len(leading) == 1


@pytest.mark.django_db
class TestAdminGuideLinkVisibility:
    # The link goes to anyone who can reach the admin (CustomAdminSite.has_permission), not only is_staff.
    def test_a_role_holder_without_staff_sees_the_admin_guide_link(
        self, documentation_menu_group, rf
    ):
        from django.contrib.auth.models import Group

        from fairdm.factories import PersonFactory
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        curator = PersonFactory(is_staff=False)
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))

        child = documentation_menu_group.children[2]
        request = rf.get("/")
        request.user = curator

        assert child.check(request) is True

    def test_a_person_with_neither_staff_nor_a_role_does_not_see_the_link(
        self, documentation_menu_group, rf
    ):
        from fairdm.factories import PersonFactory

        child = documentation_menu_group.children[2]
        request = rf.get("/")
        request.user = PersonFactory(is_staff=False)

        assert child.check(request) is False

    def test_a_staff_account_with_no_role_still_sees_the_link(
        self, documentation_menu_group, rf
    ):
        from fairdm.factories import PersonFactory

        child = documentation_menu_group.children[2]
        request = rf.get("/")
        request.user = PersonFactory(is_staff=True)

        assert child.check(request) is True




@pytest.mark.django_db
class TestMenuLinks:
    def test_the_menu_links_to_the_team_the_catalogue_and_the_install_page(
        self, client
    ):
        response = client.get(reverse("team"))
        content = response.content.decode()

        assert response.status_code == 200
        missing = [
            href
            for href in (
                reverse("team"),
                reverse("literature:item-list"),
                reverse("mvp-pwa-install"),
            )
            if f'href="{href}"' not in content
        ]
        assert missing == []

    def test_the_catalogue_opens_for_an_anonymous_visitor(self, client):
        response = client.get(reverse("literature:item-list"))

        assert response.status_code == 200
