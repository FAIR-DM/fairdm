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


@plugins.register(Sample, label=_("Overview"), icon="view", order=0)
class Overview(OverviewPlugin):
    # Was declared at module scope, outside the class it belongs to, so it configured nothing.
    fieldsets: list[tuple[str | None, dict[str, Any]]] = []


# ======== Management Plugins ======== #
# Each of these is an editing surface. A plugin with no declared `permission` admits every
# request, anonymous included (FR-033a) - so, matching the dataset plugins one app over
# (`fairdm/core/dataset/plugins.py`), each names the right it needs.
@plugins.register(Sample, label=_("Edit"), icon="pencil", order=10)
class Edit(UpdatePlugin):
    """Plugin for editing basic sample information."""

    permission = "sample.change_sample"
    title = _("Basic Information")
    model = Sample
    fields = ["image", "name"]
    about = _(
        "Edit basic information about your sample, including its name and image. "
        "These fields help others understand your sample and its key characteristics."
    )
    learn_more = user_guide("sample/edit")


@plugins.register(Sample, label=_("Descriptions"), icon="description", order=510)
class Descriptions(DescriptionsPlugin):
    permission = "sample.change_sample"
    name = "basic-information"
    title = _("Basic Information")
    learn_more = user_guide("dataset/basic-information")
    # SingleObjectMixin.get_queryset() needs this to resolve the record; Edit (above) declares
    # it, this and KeyDates below never did (issue #280).
    model = Sample
    inline_model = SampleDescription


@plugins.register(Sample, label=_("Keywords"), icon="keywords", order=520)
class Keywords(KeywordsPlugin):
    permission = "sample.change_sample"
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/keywords")],
    }


@plugins.register(Sample, label=_("Key Dates"), icon="date", order=530)
class KeyDates(KeyDatesPlugin):
    permission = "sample.change_sample"
    model = Sample
    inline_model = SampleDate
