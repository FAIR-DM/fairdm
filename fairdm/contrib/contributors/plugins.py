from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from django_filters import FilterSet

from fairdm import plugins
from fairdm.core.plugins import ActivityPlugin, DatasetPlugin, OverviewPlugin, ProjectPlugin
from fairdm.plugins import GenericPlugin
from fairdm.views import FairDMListView

from .models import Contribution

plugins.contributor.explore(
    OverviewPlugin,
    ProjectPlugin,
    DatasetPlugin,
    ActivityPlugin,
)


class ContributorsPlugin(GenericPlugin, FairDMListView):
    template_name = "contributors/contribution_list.html"
    model = Contribution
    filterset_fields = ["contributor__name"]
    icon = "contributors"
    title = name = _("Contributors")
    grid_config = {"cols": 1, "gap": 2, "responsive": {"sm": 2, "md": 4}}
    card = "contributor.card.contribution"

    def get_filterset_class(self):
        return FilterSet

    def get_queryset(self, *args, **kwargs):
        return self.base_object.contributors.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.base_object
        return context
