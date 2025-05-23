from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.plugins import ContributorsPlugin
from fairdm.contrib.generic.plugins import KeyDatesPlugin, KeywordsPlugin
from fairdm.contrib.generic.views import UpdateCoreObjectBasicInfo
from fairdm.core.plugins import ActivityPlugin, DatasetPlugin, DiscussionPlugin, ManageBaseObjectPlugin, OverviewPlugin
from fairdm.plugins import ModelFormPlugin
from fairdm.utils.utils import user_guide

from .forms import ProjectForm
from .models import Project, ProjectDate


class Overview(OverviewPlugin):
    fieldsets = []
    slug = ""


plugins.project.explore(
    Overview,
    ContributorsPlugin,
    DatasetPlugin,
    DiscussionPlugin,
    ActivityPlugin,
)


# ======== Management Plugins ======== #
@plugins.project.actions()
class Configure(ManageBaseObjectPlugin):
    description = _(
        "Configure the dataset's metadata, including project, reference, license, and visibility. This is essential for ensuring that the dataset is properly categorized and accessible to the right audience."
    )
    learn_more = user_guide("project/configure")
    form_class = ProjectForm
    fields = ["image", "owner", "visibility"]


class BasicInformation(ModelFormPlugin, UpdateCoreObjectBasicInfo):
    title = name = _("Basic Information")
    description = _(
        "Descriptions provide additional context and information about the dataset, enhancing its discoverability and usability. By adding descriptions, you can help users understand the dataset's content, purpose, and any specific considerations they should be aware of when using it."
    )
    learn_more = user_guide("dataset/basic-information")
    icon = "gear"
    form_class = ProjectForm
    fields = ["name"]


class Keywords(KeywordsPlugin):
    description = _(
        "Providing keywords for your dataset enhances its discoverability, making it easier for others to find and understand the dataset through search engines and data catalogs. Keywords offer a quick summary of the dataset's content, helping users assess its relevance for their own research or application without needing to read through full documentation."
    )


class KeyDates(KeyDatesPlugin):
    description = _(
        "Providing key dates enhances transparency, usability, and trust. These temporal markers help users understand the timeframe the data covers, assess its relevance for time-sensitive analyses, and determine how current or historic the dataset is. Clear documentation of data availability and collection periods also supports reproducibility and proper citation, enabling users to contextualize findings and align datasets from different sources."
    )
    model = Project
    inline_model = ProjectDate


plugins.project.manage(
    Configure,
    BasicInformation,
    Keywords,
    KeyDates,
)
