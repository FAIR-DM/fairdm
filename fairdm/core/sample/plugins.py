from django.utils.translation import gettext_lazy as _

from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import ManageBaseObjectPlugin, OverviewPlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.plugins import EXPLORE, MANAGEMENT, register_plugin
from fairdm.utils.utils import user_guide

from ..utils import documentation_link
from .views import SampleDetailView


def check_has_edit_permission(request, instance, **kwargs):
    return True


@register_plugin(SampleDetailView)
class Overview(OverviewPlugin):
    category = EXPLORE
    fieldsets = []


class SampleManagementMixin:
    """
    SampleManagementMixin is a mixin class that provides management functionality for sample objects.
    It includes methods for managing sample metadata, configuration, and other related tasks.
    """

    check = check_has_edit_permission


# ======== Management Plugins ======== #
@register_plugin(SampleDetailView)
class Configure(SampleManagementMixin, ManageBaseObjectPlugin):
    category = MANAGEMENT
    heading_config = {
        "description": _(
            "Provide descriptions of your sample to convey its purpose and scope. This information is essential for helping users quickly understand the sample's relevance and applicability to their research or applications."
        ),
        "links": [documentation_link("sample/basic-information")],
    }
    fields = ["image", "name"]


@register_plugin(SampleDetailView)
class Descriptions(SampleManagementMixin, DescriptionsPlugin):
    category = MANAGEMENT
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


@register_plugin(SampleDetailView)
class Keywords(SampleManagementMixin, KeywordsPlugin):
    category = MANAGEMENT
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/keywords")],
    }


@register_plugin(SampleDetailView)
class KeyDates(SampleManagementMixin, KeyDatesPlugin):
    category = MANAGEMENT
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/key-dates")],
    }
    inline_model = SampleDate
