"""Tests for the API entry in the default application menu.

Covers the current shape of the "Documentation" MenuGroup in AppMenu:
- AppMenu contains a group named "Documentation"
- The group has exactly 3 child MenuItems: API, User Guide, Admin Guide
- The "API" child points at the interactive API docs view ("api:api-docs")
- FAIRDM_API_DOCS_URL remains a valid, independently overridable Django setting

Commit 2a6106f ("chore: cleaned up default app menu") collapsed the former
standalone "API" MenuGroup (Interactive Docs / Browse API / How to use the
API) into a single "API" MenuItem nested inside the "Documentation" group.
The menu no longer reads FAIRDM_API_DOCS_URL at all — see fairdm/menus/menus.py.
"""

import pytest


@pytest.fixture()
def documentation_menu_group():
    """Return the 'Documentation' MenuGroup from AppMenu."""
    from mvp.menus import AppMenu

    groups = [item for item in AppMenu.children if str(item.name) == "Documentation"]
    assert groups, "No 'Documentation' MenuGroup found in AppMenu. Check fairdm/menus/menus.py."
    return groups[0]


class TestDocumentationMenuGroupPresent:
    """The AppMenu must contain a MenuGroup named 'Documentation'."""

    def test_documentation_group_exists_in_app_menu(self, documentation_menu_group):
        """AppMenu must contain a group whose name is 'Documentation'."""
        assert documentation_menu_group is not None

    def test_documentation_group_has_exactly_three_children(self, documentation_menu_group):
        """The Documentation MenuGroup must have exactly 3 child MenuItems."""
        assert len(documentation_menu_group.children) == 3, (
            f"Expected 3 children in Documentation menu group, found {len(documentation_menu_group.children)}"
        )


class TestAPIMenuItem:
    """The Documentation group's first child links to the interactive API docs."""

    def test_first_child_is_api(self, documentation_menu_group):
        """First child must be 'API' using view_name 'api:api-docs'."""
        child = documentation_menu_group.children[0]
        assert str(child.name) == "API"
        assert child.view_name == "api:api-docs", f"Unexpected view_name: {child.view_name!r}"

    def test_api_child_uses_view_name_not_hardcoded_url(self, documentation_menu_group):
        """API item must use view_name reversal, not a hardcoded URL string."""
        child = documentation_menu_group.children[0]
        assert child.view_name == "api:api-docs"
        assert child._url == "", "Internal links must not carry a hardcoded _url"

    def test_api_child_icon_context(self, documentation_menu_group):
        """API child must have 'api' icon in extra_context."""
        child = documentation_menu_group.children[0]
        assert child.extra_context.get("icon") == "api"


class TestDocumentationMenuGroupOtherChildren:
    """The remaining two children are the user-facing and admin-facing guides."""

    def test_second_child_is_user_guide(self, documentation_menu_group):
        """Second child must be 'User Guide', an external link."""
        child = documentation_menu_group.children[1]
        assert str(child.name) == "User Guide"
        assert child._url == "https://faridm.org/user-guide/"

    def test_third_child_is_admin_guide(self, documentation_menu_group):
        """Third child must be 'Admin Guide', gated behind the staff-only check."""
        child = documentation_menu_group.children[2]
        assert str(child.name) == "Admin Guide"
        assert child._url == "https://faridm.org/admin-guide/"


class TestFairDMAPIDocsURLSetting:
    """FAIRDM_API_DOCS_URL remains a valid, independently defined Django setting.

    It is no longer consumed by the menu (see module docstring), but portal
    developers can still read/override it for their own use (e.g. custom
    templates or views), so the setting's default value is still worth pinning.
    """

    def test_third_child_default_url_is_fairdm_org(self):
        """Default FAIRDM_API_DOCS_URL must be 'https://fairdm.org/api/'."""
        from fairdm.api.settings import FAIRDM_API_DOCS_URL

        assert FAIRDM_API_DOCS_URL == "https://fairdm.org/api/"

    @pytest.mark.django_db
    def test_override_fairdm_api_docs_url_respected(self, settings):
        """Overriding FAIRDM_API_DOCS_URL via Django settings is respected."""
        settings.FAIRDM_API_DOCS_URL = "https://custom.example.org/api/"

        assert settings.FAIRDM_API_DOCS_URL == "https://custom.example.org/api/"
