from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.plugins import ContributorsPlugin
from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import (
    ActivityPlugin,
    DatasetPlugin,
    DeleteObjectPlugin,
    ManageBaseObjectPlugin,
    OverviewPlugin,
)
from fairdm.utils.utils import user_guide

from .forms import ProjectForm
from .models import Project, ProjectDate, ProjectDescription


class Overview(OverviewPlugin):
    fieldsets = []


plugins.project.register(
    Overview,
    ContributorsPlugin,
    DatasetPlugin,
    ActivityPlugin,
)


# ======== Management Plugins ======== #
@plugins.project.register
class Configure(ManageBaseObjectPlugin):
    heading_config = {
        "title": _("Configure Project"),
        "description": _(
            "Set up your project's metadata, including its name, a cover image, funding, and visibility settings. This helps ensure your project is accurately categorized and reaches the appropriate audience."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("project/configure"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
    form_class = ProjectForm
    fields = ["image", "name", "owner", "visibility"]


@plugins.project.register
class BasicInformation(DescriptionsPlugin):
    heading_config = {
        "title": _("Descriptions"),
        "description": _(
            "Provide key details about your project, including its name and key descriptions. This information is essential for conveying the project's purpose and scope, helping users quickly understand its relevance."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("project/basic-information"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
    model = Project
    inline_model = ProjectDescription


@plugins.project.register
class Keywords(KeywordsPlugin):
    heading_config = {
        "title": _("Keywords"),
        "description": _(
            "Adding keywords improves your project's visibility in search engines and data catalogs. They offer a quick summary of the content, helping others assess its relevance without reading the full documentation."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("project/keywords"),
                "icon": "fa-solid fa-book",
            }
        ],
    }


@plugins.project.register
class KeyDates(KeyDatesPlugin):
    name = "key-dates"
    heading_config = {
        "title": _("Key Dates"),
        "description": _(
            "Entering key dates helps track important milestones and timelines, supporting effective project management and giving others insight into the project's history and progress."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("project/key-dates"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
    model = Project
    inline_model = ProjectDate


@plugins.project.register
class DeleteProjectPlugin(DeleteObjectPlugin):
    heading_config = {
        "title": _("Delete Project"),
        "description": _(
            "Deleting a project is a permanent action that removes it from the system. Please see the documentation by clicking the link below to understand what happens when a project is deleted."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("project/delete"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
