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


@plugins.register(Dataset, label=_("Descriptions"), icon="description", order=510)
class Descriptions(DescriptionsPlugin):
    # These three plugins are editing surfaces, not reading ones. Without a
    # declared permission `can_open()` admits every request, anonymous
    # included, and a private dataset's metadata would stay readable and
    # writable by anyone holding its UUID.
    permission = "dataset.change_dataset"
    model = Dataset
    inline_model = DatasetDescription


@plugins.register(Dataset, label=_("Keywords"), icon="keywords", order=520)
class Keywords(KeywordsPlugin):
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
    permission = "dataset.change_dataset"


@plugins.register(Dataset, label=_("Key Dates"), icon="date", order=530)
class KeyDates(KeyDatesPlugin):
    permission = "dataset.change_dataset"
    model = Dataset
    inline_model = DatasetDate
