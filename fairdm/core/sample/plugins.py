from typing import Any

from django.http import Http404
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.core.plugins import OverviewPlugin, UpdatePlugin
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.utils.utils import user_guide

from ..utils import documentation_link
from . import overview
from .models import Sample


@plugins.register(Sample, label=_("Overview"), icon="view", order=0)
class Overview(OverviewPlugin):
    """The sample's own page.

    Drawn from ``sample/sample_overview.html``, which reads only the base ``Sample`` model. A
    sample type adds its own content by providing ``<app_label>/<model_name>_overview.html``,
    extending that template and filling its blocks — see :meth:`get_template_names`.
    """

    # Was declared at module scope, outside the class it belongs to, so it configured nothing.
    fieldsets: list[tuple[str | None, dict[str, Any]]] = []
    check = staticmethod(overview.sample_is_visible)

    def handle_no_permission(self):
        # A sample the requester may not see answers 404, as a private dataset does, so its
        # address never confirms that it exists.
        raise Http404(_("No sample matches the given query."))

    def get_template_names(self):
        """The most specific overview template the sample's own type chain provides.

        Walks the sample's class hierarchy from its own type up to ``Sample``, so a type can
        provide ``<app_label>/<model_name>_overview.html`` and a subtype of it inherits that
        page until it provides its own. Each of those templates extends
        ``sample/sample_overview.html`` and uses ``{{ block.super }}`` to add to a block rather
        than replace it.
        """
        names = []
        for cls in type(self.base_object).__mro__:
            if cls is Sample:
                break
            if isinstance(cls, type) and issubclass(cls, Sample) and not cls._meta.abstract:
                names.append(f"{cls._meta.app_label}/{cls._meta.model_name}_overview.html")
        return [*names, "sample/sample_overview.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sample"] = self.base_object
        context.update(
            overview.build(
                self.request,
                self.base_object,
                can_manage=has_perm(self.request, "dataset.change_dataset", self.base_object.dataset),
            )
        )
        return context


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
    # SingleObjectMixin.get_queryset() needs this to resolve the record; Edit above declares it,
    # this and KeyDates below never did (issue #280).
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
