from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from django_filters import FilterSet

from fairdm import plugins
from fairdm.core.plugins import (
    ActivityPlugin,
    ContactPlugin,
    DatasetPlugin,
    ManageBaseObjectPlugin,
    OverviewPlugin,
    ProjectPlugin,
    SharePlugin,
)
from fairdm.views import FairDMListView

from .forms.person import UserProfileForm
from .models import Contribution


@plugins.contributor.register()
class Overview(OverviewPlugin):
    title = False
    description = _(
        "This overview provides a summary of the contributors involved in the project, dataset, or activity. It includes key information about each contributor, such as their roles, contributions, and affiliations."
    )
    menu_item = {
        "name": _("Overview"),
        "icon": "user-circle",
    }


plugins.contributor.register(
    ProjectPlugin,
    DatasetPlugin,
    ActivityPlugin,
    ContactPlugin,
    SharePlugin,
)


@plugins.contributor.register()
class Profile(ManageBaseObjectPlugin):
    title = _("Profile")
    form_class = UserProfileForm
    fields = ["image", "name", "lang", "profile"]


class ContributorsPlugin(plugins.Explore, FairDMListView):
    template_name = "contributors/contribution_list.html"
    model = Contribution
    filterset_fields = ["contributor__name"]
    menu_item = {
        "name": _("Contributors"),
        "icon": "contributors",
    }
    title = _("Contributors")
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
