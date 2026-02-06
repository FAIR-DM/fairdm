"""Site navigation menu for FairDM."""

from django.utils.translation import gettext_lazy as _
from flex_menu import MenuItem
from flex_menu.checks import user_is_staff
from mvp.menus import AppMenu, MenuCollapse, MenuGroup

AppMenu.extend(
    [
        MenuItem(
            name=_("Home"),
            view_name="home",
            extra_context={
                "icon": "home",
            },
        ),
        MenuItem(
            name=_("Projects"),
            view_name="project-list",
            extra_context={
                "icon": "project",
            },
        ),
        MenuItem(
            name=_("Datasets"),
            view_name="dataset-list",
            extra_context={
                "icon": "dataset",
            },
        ),
        MenuCollapse(
            name=_("Samples"),
            extra_context={
                "icon": "sample",
            },
        ),
        MenuCollapse(
            name=_("Measurements"),
            extra_context={
                "icon": "measurement",
            },
        ),
        MenuItem(
            name=_("Literature"),
            url="#",
            extra_context={"icon": "literature"},
        ),
        MenuGroup(
            _("Community"),
            children=[
                MenuItem(
                    name=_("Statistics"),
                    view_name="community-dashboard",
                    extra_context={"icon": "line-chart"},
                ),
                MenuItem(
                    name=_("People"),
                    view_name="people-list",
                    extra_context={"icon": "people"},
                ),
                MenuItem(
                    name=_("Organizations"),
                    view_name="organization-list",
                    extra_context={"icon": "organization"},
                ),
                MenuItem(
                    name=_("Portal Team"),
                    view_name="portal-team",
                    extra_context={"icon": "people"},
                ),
            ],
        ),
        MenuGroup(
            name=_("Documentation"),
            children=[
                MenuItem(
                    name=_("User Guides"),
                    url="https://faridm.org/user-guide/",
                    extra_context={"icon": "literature"},
                ),
                MenuItem(
                    name=_("Administrator Guides"),
                    url="https://faridm.org/admin-guide/",
                    check=user_is_staff,
                    extra_context={"icon": "literature"},
                ),
            ],
        ),
    ],
)
