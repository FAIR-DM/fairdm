"""Site navigation menu for FairDM."""

from cotton_layouts.menus import SiteNavigation
from django.utils.translation import gettext_lazy as _
from flex_menu import MenuItem

# Main site navigation menu
SiteNavigation.extend(
    [
        # Projects dropdown
        MenuItem(
            name=_("Projects"),
            view_name="project-list",
            extra_context={
                "icon": "project",
                "tooltip": _(
                    "Discover planned, active, and historic research projects shared by our community members."
                ),
            },
        ),
        MenuItem(
            name=_("Datasets"),
            view_name="dataset-list",
            extra_context={
                "icon": "dataset",
                "tooltip": _(
                    "Browse datasets that meet the data and metadata quality standards required by our community."
                ),
            },
        ),
        MenuItem(
            name=_("Collections"),
            view_name="data-collections",
            extra_context={
                "icon": "table",
                "tooltip": _("Explore tabular data collections by sample or measurement type within this data portal."),
            },
        ),
        MenuItem(
            name=_("Community"),
            view_name="community-dashboard",
            extra_context={
                "icon": "people",
                "tooltip": _("Learn more about the people and organizations contributing to this data portal."),
            },
        ),
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
