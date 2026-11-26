"""A record's Contributors tab: people in the main column, organizations beside them."""

from django.utils.translation import gettext_lazy

from fairdm import plugins
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

from .tab_base import ContributorsBase
from .tab_credits import (
    CreditOrganization,
    EditCredit,
    RemoveCredit,
    Reorder,
    UndoRemove,
)
from .tab_organizations import AddOrganization
from .tab_people import AddPerson, AddPersonStep

__all__ = ["ContributionList"]


@plugins.register(
    Project,
    Dataset,
    Sample,
    Measurement,
    label=gettext_lazy("Contributors"),
    icon="users",
    order=150,
)
class ContributionList(ContributorsBase):
    """The Contributors tab: people in the main column, organizations beside them."""

    manager_only = False
    url_path = "contributors"
    template_name = "contributors/tab/page.html"
    page_title = gettext_lazy("Contributors")

    class Media:
        css = {"all": ["contributors/tab.css"]}
        js = ["contributors/tab.js"]

    extra_views = [
        AddPerson,
        AddPersonStep,
        AddOrganization,
        EditCredit,
        CreditOrganization,
        RemoveCredit,
        UndoRemove,
        Reorder,
    ]

    def get_context_data(self, **kwargs):
        """Add the region's context."""
        context = super().get_context_data(**kwargs)
        context.update(self.region_context())
        return context
