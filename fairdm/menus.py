"""For information on how menus work, see django-flex-menu documentation: https://django-flex-menu.readthedocs.io/en/latest/"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem, checks

from fairdm import plugins
from fairdm.registry import registry


def resolve_collection_view(view_name):
    """
    Resolve the collection view for the given instance.
    This function is used to determine the view name for the collection of a specific type.
    """

    def func(request, instance=None, **kwargs):
        if not instance:
            return reverse(view_name)
        return plugins.reverse(instance, view_name)

    return func


def generate_menu_items(items):
    return [
        SubMenuItem(
            item["verbose_name_plural"],
            url=resolve_collection_view(f"{item['slug']}-collection"),
        )
        for item in items
    ]


def get_sample_menu_items():
    """Get sample menu items based on the sample type."""
    return generate_menu_items(registry.samples)


def get_measurement_menu_items():
    """Get measurement menu items based on the measurement type."""
    return generate_menu_items(registry.measurements)


class NavLink(MenuItem):
    """A simple navigation link item."""

    template = "cotton/sections/navbar/test/nav-link.html"


class SubMenu(Menu):
    """A submenu that can contain other menu items."""

    root_template = "cotton/sections/navbar/test/nav-dropdown.html"
    template = "cotton/sections/navbar/test/nav-dropdown.html"
    dropdown_class = "dropdown dropend"
    show_toggle = True


class SubMenuItem(MenuItem):
    """A menu item that can be used within a submenu."""

    template = "cotton/sections/navbar/test/dropdown-item.html"


class DropdownHeader(Menu):
    """A header item for a dropdown menu."""

    template = "cotton/sections/navbar/test/dropdown-header.html"


class NavMenu(Menu):
    template = "cotton/sections/navbar/test/nav-dropdown.html"
    allowed_children = (SubMenu, SubMenuItem, DropdownHeader)
    dropdown_class = "nav-item dropdown-hover-all"
    dropdown_button_class = "nav-link"


class SiteMenu(Menu):
    allowed_children = (NavLink, NavMenu)


SiteNavigation = Menu(
    "SiteNavigation",
    label=_("Database"),
    template="cotton/sections/navbar/test/menu.html",
    # template="fairdm/menus/site_navigation.html",
    # template="fairdm/menus/database/menu.html",
    children=[
        # NavLink(_("Home"), view_name="home"),  # type: ignore
        NavMenu(
            _("Projects"),
            description=_("Discover planned, active, and historic research projects shared by our community members."),
            children=[
                SubMenuItem(
                    _("Browse Projects"),
                    view_name="project-list",
                    icon="project",
                ),
                SubMenuItem(_("Create New"), view_name="project-create", check=checks.user_is_authenticated),
            ],
        ),
        NavMenu(
            _("Data"),
            description=_(
                "Browse datasets that meet the data and metadata quality standards required by our community."
            ),
            children=[
                SubMenuItem(_("Create New"), view_name="dataset-create", check=checks.user_is_authenticated),
                DropdownHeader(_("Explore")),
                SubMenuItem(
                    _("Browse Datasets"),
                    view_name="dataset-list",
                    icon="dataset",
                ),
                SubMenu(_("Data Collections")),
            ],
        ),
        NavMenu(
            _("Community"),
            description=_(
                "Find a person or organization that has directly or indirectly contributed to this data portal."
            ),
            children=[
                DropdownHeader(_("People")),
                SubMenuItem(
                    _("Portal Team"),
                    view_name="portal-team",
                    description=_("Explore the contributors to this data portal."),
                ),
                SubMenuItem(
                    _("Active Members"),
                    view_name="active-member-list",
                    description=_("Explore the contributors to this data portal."),
                ),
                SubMenuItem(
                    _("All Contributors"),
                    view_name="contributor-list",
                    description=_("Explore the contributors to this data portal."),
                ),
                DropdownHeader(_("Organizations")),
                SubMenuItem(
                    _("Organizations"),
                    view_name="organization-list",
                    icon="organizations",
                    description=_("Explore the organizations that have contributed to this data portal."),
                ),
            ],
        ),
        NavMenu(
            _("More"),
            children=[
                SubMenuItem(
                    _("Literature"),
                    view_name="reference-list",
                    icon="literature",
                    description=_("Explore related published and unpublished literature relevant to this portal."),
                ),
            ],
        ),
    ],
)
