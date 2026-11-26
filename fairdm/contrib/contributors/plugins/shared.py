"""What every page of a record's Contributors tab shares: the record, its kind and who may manage it.

Every page opens only when the record's overview would, and a page that changes anything asks
whether the viewer can manage the record on every request.
"""

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.access import can_open
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView

from ..access import RecordAccess
from ..choices import ContributionLevel


def level_choices(record, floor=None):
    """Return the three levels as the edit page draws them, marking those below ``floor``."""
    kind = RecordAccess(record).kind
    hints = {
        ContributionLevel.VIEW: _("Open this %(kind)s while it is private.")
        % {"kind": kind},
        ContributionLevel.EDIT: _("Also change this %(kind)s and the data in it.")
        % {"kind": kind},
        ContributionLevel.MANAGE: _(
            "Also change its contributors and their access, change its visibility and delete it."
        ),
    }
    return [
        {
            "value": level.value,
            "label": level.label,
            "hint": hints[level],
            "disabled": floor is not None and level < floor,
        }
        for level in ContributionLevel
    ]


class ContributionPage(Plugin, FairDMTemplateView):
    """What every page of the tab shares: the record, its kind and who may manage it."""

    manager_only = False

    @cached_property
    def access(self):
        """What people may do on this record."""
        return RecordAccess(self.base_object)

    @property
    def overview(self):
        """The overview plugin of the record's kind, whose check decides who may open the record."""
        from fairdm.core.dataset.plugins import Overview as DatasetOverview
        from fairdm.core.measurement.plugins import Overview as MeasurementOverview
        from fairdm.core.project.plugins import Overview as ProjectOverview
        from fairdm.core.sample.plugins import Overview as SampleOverview

        return {
            Project: ProjectOverview,
            Dataset: DatasetOverview,
            Sample: SampleOverview,
            Measurement: MeasurementOverview,
        }[self.access.model]

    def dispatch(self, request, *args, **kwargs):
        """Answer as the overview does when the record is closed to the viewer, then refuse a page for changing contributors to anyone who may not manage the record."""
        if not can_open(self.overview, request, self.base_object):
            raise Http404(
                _("No %(kind)s matches the given query.") % {"kind": self.access.kind}
            )
        if self.manager_only and not self.access.can_manage(request.user):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    @property
    def list_url(self):
        """The address of the record's Contributors tab."""
        return reverse(self.base_object, "contribution-list")

    def get_contribution(self):
        """Return the contribution named in the address, on this record only."""
        return get_object_or_404(
            self.base_object.contributors.select_related("contributor"),
            pk=self.kwargs["pk"],
        )

    @cached_property
    def can_see_levels(self):
        """Whether the viewer may be told what people may do: only someone who can manage."""
        return self.access.can_manage(self.request.user)

    def get_context_data(self, **kwargs):
        """Add the record's kind, the tab's address and whether the viewer may manage."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        context.update(
            record=record,
            kind=RecordAccess(record).kind,
            list_url=self.list_url,
            can_manage=self.access.can_manage(self.request.user),
        )
        return context
