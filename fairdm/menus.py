"""For information on how menus work, see django-flex-menu documentation: https://django-flex-menu.readthedocs.io/en/latest/"""

from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem
from literature.models import LiteratureItem

from fairdm.contrib.contributors.models import Contributor
from fairdm.core.models import Project
from fairdm.registry import registry


def get_sample_menu_items():
    """Get sample menu items based on the sample type."""

    sample_menu_items = [
        MenuItem(
            name=sample_type["verbose_name_plural"],
            view_name="data-table",
            label=sample_type["verbose_name_plural"],
            params={
                "type": sample_type["full_name"],
            },
        )
        for sample_type in registry.samples
    ]
    return sample_menu_items


def get_measurement_menu_items():
    """Get measurement menu items based on the measurement type."""

    measurement_menu_items = [
        MenuItem(
            name=measurement_type["verbose_name_plural"],
            view_name="data-table",
            label=measurement_type["verbose_name_plural"],
            params={
                "type": measurement_type["full_name"],
            },
        )
        for measurement_type in registry.measurements
    ]
    return measurement_menu_items


SiteNavigation = Menu(
    "SiteNavigation",
    label=_("Database"),
    root_template="fairdm/menus/site_navigation.html",
    template="fairdm/menus/database/menu.html",
    children=[
        MenuItem(
            _("Home"),
            view_name="home",
            icon="home",
        ),
        MenuItem(
            _("Projects"),
            view_name="project-list",
            icon="project",
            count=Project.objects.count,
            description=_("Discover planned, active, and historic research projects shared by our community members."),
        ),
        MenuItem(
            _("Data"),
            view_name="data",
            icon="dataset",
            description=_(
                "Browse datasets that meet the data and metadata quality standards required by our community."
            ),
        ),
        # MenuItem(
        #     _("Data Collections"),
        #     view_name="data-table",
        #     icon="sample",
        #     description=_("View database entries in tabular format by sample or measurement type."),
        # ),
        MenuItem(
            _("Contributors"),
            view_name="contributor-list",
            icon="contributors",
            count=Contributor.objects.count,
            description=_(
                "Find a person or organization that has directly or indirectly contributed to this data portal."
            ),
        ),
        MenuItem(
            _("Literature"),
            view_name="reference-list",
            icon="literature",
            count=LiteratureItem.objects.count,
            description=_("Explore related published and unpublished literature relevant to this portal."),
        ),
        MenuItem(
            _("API Documentation"),
            view_name="api:swagger-ui",
            icon="api",
            description=_("View the API documentation and learn how to interact programatically with this portal."),
        ),
    ],
)
