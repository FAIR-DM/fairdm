from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import EditPlugin, OverviewPlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.utils.utils import user_guide

from ..utils import documentation_link
from .models import Sample


def check_has_edit_permission(request, instance, **kwargs):
    return True


@plugins.register(Sample)
class Overview(OverviewPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Overview"), category=plugins.EXPLORE, icon="view")
    fieldsets = []


class SampleManagementMixin:
    """
    SampleManagementMixin is a mixin class that provides management functionality for sample objects.
    It includes methods for managing sample metadata, configuration, and other related tasks.
    """

    check = check_has_edit_permission


# ======== Management Plugins ======== #
@plugins.register(Sample)
class Edit(SampleManagementMixin, EditPlugin):
    """Plugin for editing basic sample information."""

    title = _("Basic Information")
    model = Sample
    fields = ["image", "name"]
    about = _(
        "Edit basic information about your sample, including its name and image. "
        "These fields help others understand your sample and its key characteristics."
    )
    learn_more = user_guide("sample/edit")


@plugins.register(Sample)
class Descriptions(SampleManagementMixin, DescriptionsPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Descriptions"), category=plugins.MANAGEMENT, icon="description")
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


@plugins.register(Sample)
class Keywords(SampleManagementMixin, KeywordsPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Keywords"), category=plugins.MANAGEMENT, icon="keywords")
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/keywords")],
    }


@plugins.register(Sample)
class KeyDates(SampleManagementMixin, KeyDatesPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Key Dates"), category=plugins.MANAGEMENT, icon="date")
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/key-dates")],
    }
    inline_model = SampleDate
