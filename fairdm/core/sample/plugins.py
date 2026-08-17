from typing import Any

from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.core.plugins import OverviewPlugin, UpdatePlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.utils.utils import user_guide

from ..utils import documentation_link
from .models import Sample


def check_has_edit_permission(request, instance, **kwargs):
    return True


@plugins.register(Sample, label=_("Overview"), icon="view", order=0)
class Overview(OverviewPlugin):
    # Was declared at module scope, outside the class it belongs to, so it configured nothing.
    fieldsets: list[tuple[str | None, dict[str, Any]]] = []


class SampleManagementMixin:
    """
    SampleManagementMixin is a mixin class that provides management functionality for sample objects.
    It includes methods for managing sample metadata, configuration, and other related tasks.
    """

    check = check_has_edit_permission


# ======== Management Plugins ======== #
@plugins.register(Sample, label=_("Edit"), icon="pencil", order=10)
class Edit(SampleManagementMixin, UpdatePlugin):
    """Plugin for editing basic sample information."""

    title = _("Basic Information")
    model = Sample
    fields = ["image", "name"]
    about = _(
        "Edit basic information about your sample, including its name and image. "
        "These fields help others understand your sample and its key characteristics."
    )
    learn_more = user_guide("sample/edit")


@plugins.register(Sample, label=_("Descriptions"), icon="description", order=510)
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


@plugins.register(Sample, label=_("Keywords"), icon="keywords", order=520)
class Keywords(SampleManagementMixin, KeywordsPlugin):
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/keywords")],
    }


@plugins.register(Sample, label=_("Key Dates"), icon="date", order=530)
class KeyDates(SampleManagementMixin, KeyDatesPlugin):
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/key-dates")],
    }
    inline_model = SampleDate
