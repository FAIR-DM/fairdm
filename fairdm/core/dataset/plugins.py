from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.plugins import ContributorsPlugin
from fairdm.contrib.generic.plugins import KeyDatesPlugin, KeywordsPlugin
from fairdm.contrib.generic.views import UpdateCoreObjectBasicInfo
from fairdm.core.plugins import ActivityPlugin, DiscussionPlugin, ManageBaseObjectPlugin, OverviewPlugin
from fairdm.utils.utils import user_guide

from ..plugins import DataTablePlugin
from .forms import DatasetForm
from .models import Dataset, DatasetDate

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


class Overview(OverviewPlugin):
    fieldsets = DATASET_SETTINGS.get("detail", {}).get("info_block_fields", None)


plugins.dataset.register(
    Overview,
    ContributorsPlugin,
    DataTablePlugin,
    DiscussionPlugin,
    ActivityPlugin,
)


# ======== Management Plugins ======== #
@plugins.dataset.register
class ManageDatasetPlugin(ManageBaseObjectPlugin):
    description = _(
        "Configure the dataset's metadata, including project, reference, license, and visibility. This is essential for ensuring that the dataset is properly categorized and accessible to the right audience."
    )
    learn_more = user_guide("dataset/configure")
    form_class = DatasetForm
    fields = ["image", "project", "reference", "license", "visibility"]


class UpdateBasicInformation(plugins.Management, UpdateCoreObjectBasicInfo):
    title = _("Basic Information")
    menu_item = {
        "name": _("Basic Information"),
        "icon": "info",
    }
    description = _(
        "Descriptions provide additional context and information about the dataset, enhancing its discoverability and usability. By adding descriptions, you can help users understand the dataset's content, purpose, and any specific considerations they should be aware of when using it."
    )
    sections = {
        "form": "components.form.form-with-inlines",
    }

    learn_more = user_guide("dataset/basic-information")
    form_class = DatasetForm
    fields = ["name"]


class DatasetKeywordsPlugin(KeywordsPlugin):
    description = _(
        "Providing keywords for your dataset enhances its discoverability, making it easier for others to find and understand the dataset through search engines and data catalogs. Keywords offer a quick summary of the dataset's content, helping users assess its relevance for their own research or application without needing to read through full documentation."
    )


class EditDates(KeyDatesPlugin):
    description = _(
        "Providing key dates enhances transparency, usability, and trust. These temporal markers help users understand the timeframe the data covers, assess its relevance for time-sensitive analyses, and determine how current or historic the dataset is. Clear documentation of data availability and collection periods also supports reproducibility and proper citation, enabling users to contextualize findings and align datasets from different sources."
    )
    model = Dataset
    inline_model = DatasetDate


plugins.dataset.register(
    UpdateBasicInformation,
    KeywordsPlugin,
    EditDates,
)
