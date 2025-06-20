from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.plugins import ContributorsPlugin
from fairdm.contrib.generic.plugins import KeyDatesPlugin, KeywordsPlugin
from fairdm.contrib.generic.views import UpdateCoreObjectBasicInfo
from fairdm.core.plugins import ActivityPlugin, ManageBaseObjectPlugin, OverviewPlugin
from fairdm.core.sample.models import SampleDate
from fairdm.utils.utils import user_guide

from ..plugins import OverviewPlugin


class Overview(OverviewPlugin):
    fieldsets = []


plugins.sample.register(
    Overview,
    ContributorsPlugin,
    ActivityPlugin,
)


# ======== Management Plugins ======== #
@plugins.sample.register()
class Configure(ManageBaseObjectPlugin):
    description = _(
        "Configure the dataset's metadata, including project, reference, license, and visibility. This is essential for ensuring that the dataset is properly categorized and accessible to the right audience."
    )
    learn_more = user_guide("sample/configure")
    fields = ["image", "name"]


@plugins.sample.register()
class BasicInformation(plugins.Management, UpdateCoreObjectBasicInfo):
    name = "basic-information"
    title = _("Basic Information")
    menu_item = {
        "name": _("Basic Information"),
        "icon": "info",
    }
    description = _(
        "Descriptions provide additional context and information about the dataset, enhancing its discoverability and usability. By adding descriptions, you can help users understand the dataset's content, purpose, and any specific considerations they should be aware of when using it."
    )
    learn_more = user_guide("dataset/basic-information")
    fields = ["name"]


@plugins.sample.register()
class Keywords(KeywordsPlugin):
    description = _(
        "Providing keywords for your dataset enhances its discoverability, making it easier for others to find and understand the dataset through search engines and data catalogs. Keywords offer a quick summary of the dataset's content, helping users assess its relevance for their own research or application without needing to read through full documentation."
    )


@plugins.sample.register()
class KeyDates(KeyDatesPlugin):
    description = _(
        "Providing key dates enhances transparency, usability, and trust. These temporal markers help users understand the timeframe the data covers, assess its relevance for time-sensitive analyses, and determine how current or historic the dataset is. Clear documentation of data availability and collection periods also supports reproducibility and proper citation, enabling users to contextualize findings and align datasets from different sources."
    )
    inline_model = SampleDate
