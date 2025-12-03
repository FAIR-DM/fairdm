from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import DescriptionsPlugin, KeyDatesPlugin, KeywordsPlugin
from fairdm.core.plugins import EditPlugin, OverviewPlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.utils.utils import user_guide

from .models import Measurement


def check_has_edit_permission(request, instance, **kwargs):
    return True


@plugins.register(Measurement)
class Overview(OverviewPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Overview"), category=plugins.EXPLORE, icon="view")
    fieldsets = []


class MeasurementManagementMixin:
    """
    MeasurementManagementMixin is a mixin class that provides management functionality for sample objects.
    It includes methods for managing sample metadata, configuration, and other related tasks.
    """

    check = check_has_edit_permission


# ======== Management Plugins ======== #
@plugins.register(Measurement)
class Edit(MeasurementManagementMixin, EditPlugin):
    """Plugin for editing basic measurement information."""

    title = _("Basic Information")
    model = Measurement
    fields = ["image", "name"]
    about = _(
        "Edit basic information about your measurement, including its name and image. "
        "These fields help others understand your measurement and its key characteristics."
    )
    learn_more = user_guide("measurement/edit")


@plugins.register(Measurement)
class Descriptions(MeasurementManagementMixin, DescriptionsPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Descriptions"), category=plugins.MANAGEMENT, icon="description")
    name = "basic-information"
    title = _("Basic Information")
    description = _(
        "Descriptions provide additional context and information about the dataset, enhancing its discoverability and usability. By adding descriptions, you can help users understand the dataset's content, purpose, and any specific considerations they should be aware of when using it."
    )
    learn_more = user_guide("dataset/basic-information")
    inline_model = SampleDescription


@plugins.register(Measurement)
class Keywords(MeasurementManagementMixin, KeywordsPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Keywords"), category=plugins.MANAGEMENT, icon="keywords")
    description = _(
        "Providing keywords for your dataset enhances its discoverability, making it easier for others to find and understand the dataset through search engines and data catalogs. Keywords offer a quick summary of the dataset's content, helping users assess its relevance for their own research or application without needing to read through full documentation."
    )


@plugins.register(Measurement)
class KeyDates(MeasurementManagementMixin, KeyDatesPlugin):
    menu_item = plugins.PluginMenuItem(name=_("Key Dates"), category=plugins.MANAGEMENT, icon="date")
    description = _(
        "Providing key dates enhances transparency, usability, and trust. These temporal markers help users understand the timeframe the data covers, assess its relevance for time-sensitive analyses, and determine how current or historic the dataset is. Clear documentation of data availability and collection periods also supports reproducibility and proper citation, enabling users to contextualize findings and align datasets from different sources."
    )
    inline_model = SampleDate
