from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import (
    DeleteObjectPlugin,
    ManageBaseObjectPlugin,
    OverviewPlugin,
)
from fairdm.plugins import EXPLORE, MANAGEMENT, register_plugin
from fairdm.utils.utils import user_guide

from .forms import DatasetForm
from .models import Dataset, DatasetDate, DatasetDescription
from .views import DatasetDetailView

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


@register_plugin(DatasetDetailView)
class Overview(OverviewPlugin):
    category = EXPLORE
    title = _("Overview")
    fieldsets = DATASET_SETTINGS.get("detail", {}).get("info_block_fields", None)


# ======== Management Plugins ======== #
@register_plugin(DatasetDetailView)
class ManageDatasetPlugin(ManageBaseObjectPlugin):
    category = MANAGEMENT
    heading_config = {
        "description": _(
            "Configure your dataset's metadata to ensure it's properly categorized and accessible to the right audience."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/configure"),
                "icon": "book",
            }
        ],
    }
    form_class = DatasetForm
    fields = ["image", "name", "project", "reference", "license", "visibility"]


@register_plugin(DatasetDetailView)
class DeleteDatasetPlugin(DeleteObjectPlugin):
    category = MANAGEMENT
    heading_config = {
        "title": _("Delete Dataset"),
        "description": _(
            "Deleting a dataset is a permanent action that removes it from the system. Please see the documentation by clicking the link below to understand what happens when a dataset is deleted."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/delete"),
                "icon": "book",
            }
        ],
    }


@register_plugin(DatasetDetailView)
class EditDescriptions(DescriptionsPlugin):
    category = MANAGEMENT
    heading_config = {
        "title": _("Descriptions"),
        "description": _(
            "Provide key details about your dataset, including its name and key descriptions. This information is essential for conveying the dataset's purpose and scope, helping users quickly understand its relevance."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/descriptions"),
                "icon": "book",
            }
        ],
    }
    model = Dataset
    inline_model = DatasetDescription


@register_plugin(DatasetDetailView)
class EditKeywords(KeywordsPlugin):
    category = MANAGEMENT
    heading_config = {
        "title": _("Keywords"),
        "description": _(
            "Keywords enhance your dataset's visibility in search engines and catalogs by summarizing its content. They help others quickly evaluate its relevance without reading the full documentation."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/keywords"),
                "icon": "book",
            }
        ],
    }


@register_plugin(DatasetDetailView)
class EditDates(KeyDatesPlugin):
    category = MANAGEMENT
    heading_config = {
        "title": _("Key Dates"),
        "description": _(
            "Entering key dates helps track important milestones and timelines, supporting effective dataset management and giving others insight into the dataset's history and progress."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/key-dates"),
                "icon": "book",
            }
        ],
    }
    model = Dataset
    inline_model = DatasetDate
