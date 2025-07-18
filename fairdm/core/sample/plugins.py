from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.plugins import ContributorsPlugin
from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import ActivityPlugin, ManageBaseObjectPlugin, OverviewPlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.utils.utils import user_guide

from ..utils import documentation_link


def check_has_edit_permission(request, instance, **kwargs):
    return True


class Overview(OverviewPlugin):
    fieldsets = []


plugins.sample.register(
    Overview,
    ContributorsPlugin,
    ActivityPlugin,
)


class SampleManagementMixin:
    """
    SampleManagementMixin is a mixin class that provides management functionality for sample objects.
    It includes methods for managing sample metadata, configuration, and other related tasks.
    """

    check = check_has_edit_permission


# ======== Management Plugins ======== #
@plugins.sample.register
class Configure(SampleManagementMixin, ManageBaseObjectPlugin):
    heading_config = {
        "description": _(
            "Provide descriptions of your sample to convey its purpose and scope. This information is essential for helping users quickly understand the sample's relevance and applicability to their research or applications."
        ),
        "links": [documentation_link("sample/basic-information")],
    }
    fields = ["image", "name"]


@plugins.sample.register
class Descriptions(SampleManagementMixin, DescriptionsPlugin):
    name = "basic-information"
    title = _("Basic Information")
    heading_config = {
        "description": _(
            "Provide descriptions of your sample to convey its purpose and scope. This information is essential for helping users quickly understand the sample's relevance and applicability to their research or applications."
        ),
        "links": [documentation_link("sample/key-dates")],
    }
    learn_more = user_guide("dataset/basic-information")
    inline_model = SampleDescription


@plugins.sample.register
class Keywords(SampleManagementMixin, KeywordsPlugin):
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/keywords")],
    }


@plugins.sample.register
class KeyDates(SampleManagementMixin, KeyDatesPlugin):
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/key-dates")],
    }
    inline_model = SampleDate
