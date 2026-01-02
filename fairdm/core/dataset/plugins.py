from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import (
    DeleteObjectPlugin,
    EditPlugin,
    OverviewPlugin,
)
from fairdm.utils.utils import user_guide

from .forms import DatasetForm
from .models import Dataset, DatasetDate, DatasetDescription

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


@plugins.register(Dataset)
class Overview(OverviewPlugin):
    title = _("Overview")
    menu_item = plugins.PluginMenuItem(name=_("Overview"), category=plugins.EXPLORE, icon="view")
    fieldsets = DATASET_SETTINGS.get("detail", {}).get("info_block_fields", None)


# ======== Management Plugins ======== #
@plugins.register(Dataset)
class Edit(EditPlugin):
    """Plugin for editing basic dataset information."""

    title = _("Basic Information")
    model = Dataset
    form_class = DatasetForm
    fields = ["image", "name", "project", "reference", "license", "visibility"]
    about = _(
        "Edit basic information about your dataset, including its name, project association, and visibility. "
        "These fields help others understand your dataset and control who can access it."
    )
    learn_more = user_guide("dataset/edit")


@plugins.register(Dataset)
class Delete(DeleteObjectPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Delete"), category=plugins.MANAGEMENT, icon="delete")
    heading_config = {
        "title": _("Delete Dataset"),
        "description": _(
            "Deleting a dataset is a permanent action that removes it from the system. Please see the documentation by clicking the link below to understand what happens when a dataset is deleted."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/delete"),
                "icon": "documentation",
            }
        ],
    }


@plugins.register(Dataset)
class Descriptions(DescriptionsPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Descriptions"), category=plugins.MANAGEMENT, icon="description")
    heading_config = {
        "title": _("Descriptions"),
        "description": _(
            "Provide key details about your dataset, including its name and key descriptions. This information is essential for conveying the dataset's purpose and scope, helping users quickly understand its relevance."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/descriptions"),
                "icon": "documentation",
            }
        ],
    }
    model = Dataset
    inline_model = DatasetDescription


@plugins.register(Dataset)
class Keywords(KeywordsPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Keywords"), category=plugins.MANAGEMENT, icon="keywords")
    heading_config = {
        "title": _("Keywords"),
        "description": _(
            "Keywords enhance your dataset's visibility in search engines and catalogs by summarizing its content. They help others quickly evaluate its relevance without reading the full documentation."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/keywords"),
                "icon": "documentation",
            }
        ],
    }


@plugins.register(Dataset)
class KeyDates(KeyDatesPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Key Dates"), category=plugins.MANAGEMENT, icon="date")
    heading_config = {
        "title": _("Key Dates"),
        "description": _(
            "Entering key dates helps track important milestones and timelines, supporting effective dataset management and giving others insight into the dataset's history and progress."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/key-dates"),
                "icon": "documentation",
            }
        ],
    }
    model = Dataset
    inline_model = DatasetDate
