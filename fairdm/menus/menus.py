"""Site navigation menu for FairDM."""

from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem, checks

# Main site navigation menu
SiteNavigation = Menu(
    "SiteNavigation",
    children=[
        # Projects dropdown
        MenuItem(
            name=_("Projects"),
            description=_("Discover planned, active, and historic research projects shared by our community members."),
            children=[
                MenuItem(
                    name=_("Browse Projects"),
                    view_name="project-list",
                    extra_context={"icon": "project"},
                ),
                MenuItem(
                    name=_("Create New"),
                    view_name="project-create",
                    check=checks.user_is_authenticated,
                ),
            ],
        ),
        # Data dropdown
        MenuItem(
            name=_("Data"),
            description=_(
                "Browse datasets that meet the data and metadata quality standards required by our community."
            ),
            children=[
                MenuItem(
                    name=_("Create New"),
                    view_name="dataset-create",
                    check=checks.user_is_authenticated,
                ),
                MenuItem(
                    name=_("Explore"),
                    extra_context={"is_header": True, "label": _("Explore")},
                ),
                MenuItem(
                    name=_("Browse Datasets"),
                    view_name="dataset-list",
                    extra_context={"icon": "dataset"},
                ),
                MenuItem(
                    name=_("Data Collections"),
                    extra_context={"is_header": True, "label": _("Data Collections")},
                ),
            ],
        ),
        # Community dropdown
        MenuItem(
            name=_("Community"),
            description=_(
                "Find a person or organization that has directly or indirectly contributed to this data portal."
            ),
            children=[
                MenuItem(
                    name=_("People"),
                    extra_context={"is_header": True, "label": _("People")},
                ),
                MenuItem(
                    name=_("Portal Team"),
                    view_name="portal-team",
                    description=_("Explore the contributors to this data portal."),
                ),
                MenuItem(
                    name=_("Active Members"),
                    view_name="active-member-list",
                    description=_("Explore the contributors to this data portal."),
                ),
                MenuItem(
                    name=_("All Contributors"),
                    view_name="contributor-list",
                    description=_("Explore the contributors to this data portal."),
                ),
                MenuItem(
                    name=_("Organizations"),
                    extra_context={"is_header": True, "label": _("Organizations")},
                ),
                MenuItem(
                    name=_("Organizations"),
                    view_name="organization-list",
                    extra_context={"icon": "organizations"},
                    description=_("Explore the organizations that have contributed to this data portal."),
                ),
            ],
        ),
        # More dropdown
        MenuItem(
            name=_("More"),
            children=[
                MenuItem(
                    name=_("Literature"),
                    view_name="reference-list",
                    extra_context={"icon": "literature"},
                    description=_("Explore related published and unpublished literature relevant to this portal."),
                ),
            ],
        ),
    ],
)
