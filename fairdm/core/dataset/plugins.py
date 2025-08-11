from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.plugins import ContributorsPlugin
from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import (
    ActivityPlugin,
    DeleteObjectPlugin,
    ManageBaseObjectPlugin,
    OverviewPlugin,
)
from fairdm.utils.utils import user_guide

from ..plugins import DataTablePlugin
from .forms import DatasetForm
from .models import Dataset, DatasetDate, DatasetDescription

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


class Overview(OverviewPlugin):
    fieldsets = DATASET_SETTINGS.get("detail", {}).get("info_block_fields", None)


plugins.dataset.register(
    Overview,
    ContributorsPlugin,
    DataTablePlugin,
    ActivityPlugin,
)


# ======== Management Plugins ======== #
@plugins.dataset.register
class ManageDatasetPlugin(ManageBaseObjectPlugin):
    heading_config = {
        "description": _(
            "Configure your dataset's metadata to ensure it's properly categorized and accessible to the right audience."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/configure"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
    form_class = DatasetForm
    fields = ["image", "name", "project", "reference", "license", "visibility"]


class DeleteDatasetPlugin(DeleteObjectPlugin):
    heading_config = {
        "title": _("Delete Dataset"),
        "description": _(
            "Deleting a dataset is a permanent action that removes it from the system. Please see the documentation by clicking the link below to understand what happens when a dataset is deleted."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/delete"),
                "icon": "fa-solid fa-book",
            }
        ],
    }


class EditDescriptions(DescriptionsPlugin):
    heading_config = {
        "title": _("Descriptions"),
        "description": _(
            "Provide key details about your dataset, including its name and key descriptions. This information is essential for conveying the dataset's purpose and scope, helping users quickly understand its relevance."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/descriptions"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
    model = Dataset
    inline_model = DatasetDescription


class EditKeywords(KeywordsPlugin):
    heading_config = {
        "title": _("Keywords"),
        "description": _(
            "Keywords enhance your dataset's visibility in search engines and catalogs by summarizing its content. They help others quickly evaluate its relevance without reading the full documentation."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/keywords"),
                "icon": "fa-solid fa-book",
            }
        ],
    }


class EditDates(KeyDatesPlugin):
    heading_config = {
        "title": _("Key Dates"),
        "description": _(
            "Entering key dates helps track important milestones and timelines, supporting effective dataset management and giving others insight into the dataset's history and progress."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/key-dates"),
                "icon": "fa-solid fa-book",
            }
        ],
    }
    model = Dataset
    inline_model = DatasetDate


plugins.dataset.register(
    EditDescriptions,
    EditKeywords,
    EditDates,
    DeleteDatasetPlugin,
)
