from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.utils.utils import user_guide

from .models import Dataset, DatasetDate, DatasetDescription

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


# ======== Management Plugins ======== #


@plugins.register(Dataset)
class Descriptions(DescriptionsPlugin):
    menu = {"label": _("Descriptions"), "icon": "description", "order": 510}
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
    menu = {"label": _("Keywords"), "icon": "keywords", "order": 520}
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
    menu = {"label": _("Key Dates"), "icon": "date", "order": 530}
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
