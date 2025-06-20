from django.urls import include, path
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

from .forms.contribution import QuickAddContributionForm
from .forms.person import UserProfileForm
from .models import Contribution
from .views.contribution import (
    AddContributorFromOrcidView,
    ContributionCreateView,
    ContributionRemoveView,
    ContributionUpdateView,
    ContributorQuickAddView,
)


@plugins.contributor.register
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


@plugins.contributor.register
class Profile(ManageBaseObjectPlugin):
    title = _("Profile")
    form_class = UserProfileForm
    fields = ["image", "name", "lang", "profile"]


class ContributorsPlugin(plugins.Explore, FairDMListView):
    model = Contribution
    name = "contributors"
    title = _("Contributors")
    title_config = {
        "text": _("Contributors"),
        "actions": [
            "contributor.quick-add",
            # "components.actions.list-filter",
        ],
    }
    filterset_fields = ["contributor__name"]
    menu_item = {
        "name": _("Contributors"),
        "icon": "contributors",
    }
    grid_config = {
        "cols": 1,
        "gap": 2,
        "responsive": {"sm": 2, "md": 4},
        "card": "contributor.card.contribution",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quick_add_form = QuickAddContributionForm()
        quick_add_form.helper.form_action = plugins.reverse(self.base_object, "contributors-quick-add")
        context["quick_add_form"] = quick_add_form
        context["modals"] = [
            "contributor.modals.edit-contribution",
        ]
        return context

    def get_filterset_class(self):
        return FilterSet

    def get_queryset(self, *args, **kwargs):
        return self.base_object.contributors.all()

    @classmethod
    def get_suburls(cls, **kwargs):
        base_model = kwargs.get("base_model")
        menu = kwargs.get("menu")
        return [
            path("quick-add/", ContributorQuickAddView.as_view(base_model=base_model), name="contributors-quick-add"),
            path("create/", ContributionCreateView.as_view(base_model=base_model), name="contributors-create"),
            path(
                "add-from-orcid/",
                AddContributorFromOrcidView.as_view(base_model=base_model),
                name="contributors-add-from-orcid",
            ),
            path(
                "<pk>/edit/",
                ContributionUpdateView.as_view(base_model=base_model, menu=menu),
                name="contributor-update",
            ),
            path(
                "<pk>/remove/",
                ContributionRemoveView.as_view(base_model=base_model),
                name="contributor-remove",
            ),
        ]

    @classmethod
    def get_urls(cls, **kwargs):
        urls, view_name = super().get_urls(**kwargs)
        urls.append(path(view_name + "/", include(cls.get_suburls(**kwargs))))
        return urls, view_name
