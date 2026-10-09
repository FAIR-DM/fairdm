"""Tests for the FairDM application menu (``fairdm/menus/menus.py``)."""

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


class TestDocumentationMenuGroupPresent:
    def test_documentation_group_exists_in_app_menu(self, documentation_menu_group):
        assert documentation_menu_group is not None


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

    def test_api_child_uses_view_name_not_hardcoded_url(self, documentation_menu_group):
        child = next(
            child
            for child in documentation_menu_group.children
            if getattr(child, "view_name", None) == "api:api-docs"
        )
        assert child._url == "", "Internal links must not carry a hardcoded _url"


class TestDocumentationMenuGroupOtherChildren:
    def test_second_child_is_user_guide(self, documentation_menu_group):
        child = documentation_menu_group.children[1]
        assert child._url == "https://fairdm.org/user-guide/"

    def test_third_child_is_admin_guide(self, documentation_menu_group):
        child = documentation_menu_group.children[2]
        assert child._url == "https://fairdm.org/admin-guide/"


@pytest.mark.django_db
class TestTeamMenuItem:
    def test_team_link_appears_in_the_menu(self, client):
        response = client.get(reverse("team"))

        assert response.status_code == 200
        assert f'href="{reverse("team")}"' in response.content.decode()


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
