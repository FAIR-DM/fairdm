from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.core.plugins import EditPlugin, OverviewPlugin
from fairdm.utils.utils import user_guide

from .models import Measurement, MeasurementDate, MeasurementDescription


def check_has_edit_permission(request, instance, **kwargs):
    return True


@plugins.register(Measurement)
class Overview(OverviewPlugin):
    menu = {"label": _("Overview"), "icon": "view", "order": 0}
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
    menu = {"label": _("Descriptions"), "icon": "description", "order": 510}
    name = "basic-information"
    title = _("Basic Information")
    description = _(
        "Descriptions provide additional context and information about the measurement, enhancing its discoverability and usability. By adding descriptions, you can help users understand the measurement's content, purpose, and any specific considerations they should be aware of when using it."
    )
    learn_more = user_guide("measurement/basic-information")
    inline_model = MeasurementDescription


@plugins.register(Measurement)
class Keywords(MeasurementManagementMixin, KeywordsPlugin):
    menu = {"label": _("Keywords"), "icon": "keywords", "order": 520}
    description = _(
        "Providing keywords for your measurement enhances its discoverability, making it easier for others to find and understand the measurement through search engines and data catalogs. Keywords offer a quick summary of the measurement's content, helping users assess its relevance for their own research or application without needing to read through full documentation."
    )


@plugins.register(Measurement)
class KeyDates(MeasurementManagementMixin, KeyDatesPlugin):
    menu = {"label": _("Key Dates"), "icon": "date", "order": 530}
    description = _(
        "Providing key dates enhances transparency, usability, and trust. These temporal markers help users understand the timeframe the measurement covers, assess its relevance for time-sensitive analyses, and determine how current or historic the measurement data is. Clear documentation of data availability and collection periods also supports reproducibility and proper citation, enabling users to contextualize findings and align measurements from different sources."
    )
    inline_model = MeasurementDate
