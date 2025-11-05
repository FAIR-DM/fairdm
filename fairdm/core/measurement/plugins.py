from django.utils.translation import gettext_lazy as _

from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import ManageBaseObjectPlugin, OverviewPlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.plugins import EXPLORE, MANAGEMENT, register_plugin
from fairdm.utils.utils import user_guide

from .views import MeasurementDetailView


def check_has_edit_permission(request, instance, **kwargs):
    return True


@register_plugin(MeasurementDetailView)
class Overview(OverviewPlugin):
    category = EXPLORE
    fieldsets = []


class MeasurementManagementMixin:
    """
    MeasurementManagementMixin is a mixin class that provides management functionality for sample objects.
    It includes methods for managing sample metadata, configuration, and other related tasks.
    """

    check = check_has_edit_permission


# ======== Management Plugins ======== #
@register_plugin(MeasurementDetailView)
class Configure(MeasurementManagementMixin, ManageBaseObjectPlugin):
    category = MANAGEMENT
    description = _(
        "Configure the dataset's metadata, including project, reference, license, and visibility. This is essential for ensuring that the dataset is properly categorized and accessible to the right audience."
    )
    learn_more = user_guide("sample/configure")
    fields = ["image", "name"]


@register_plugin(MeasurementDetailView)
class Descriptions(MeasurementManagementMixin, DescriptionsPlugin):
    category = MANAGEMENT
    name = "basic-information"
    title = _("Basic Information")
    description = _(
        "Descriptions provide additional context and information about the dataset, enhancing its discoverability and usability. By adding descriptions, you can help users understand the dataset's content, purpose, and any specific considerations they should be aware of when using it."
    )
    learn_more = user_guide("dataset/basic-information")
    inline_model = SampleDescription


@register_plugin(MeasurementDetailView)
class Keywords(MeasurementManagementMixin, KeywordsPlugin):
    category = MANAGEMENT
    description = _(
        "Providing keywords for your dataset enhances its discoverability, making it easier for others to find and understand the dataset through search engines and data catalogs. Keywords offer a quick summary of the dataset's content, helping users assess its relevance for their own research or application without needing to read through full documentation."
    )


@register_plugin(MeasurementDetailView)
class KeyDates(MeasurementManagementMixin, KeyDatesPlugin):
    category = MANAGEMENT
    description = _(
        "Providing key dates enhances transparency, usability, and trust. These temporal markers help users understand the timeframe the data covers, assess its relevance for time-sensitive analyses, and determine how current or historic the dataset is. Clear documentation of data availability and collection periods also supports reproducibility and proper citation, enabling users to contextualize findings and align datasets from different sources."
    )
    inline_model = SampleDate
