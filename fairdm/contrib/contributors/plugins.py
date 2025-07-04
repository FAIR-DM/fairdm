from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.urls import include, path
from django.utils.translation import gettext as _
from django_filters import FilterSet
from guardian.shortcuts import get_perms

from fairdm import plugins
from fairdm.core.plugins import (
    ActivityPlugin,
    DatasetPlugin,
    ManageBaseObjectPlugin,
    OverviewPlugin,
    ProjectPlugin,
)
from fairdm.views import FairDMListView

from .forms.contribution import QuickAddContributionForm
from .forms.organization import OrganizationProfileForm
from .forms.person import UserProfileForm
from .models import Contribution, Organization, Person
from .views.contribution import (
    ContributionCreateView,
    ContributionRemoveView,
    ContributionUpdateView,
    ContributorQuickAddView,
)


@plugins.contributor.register
class Overview(OverviewPlugin):
    description = _(
        "This overview provides a summary of the contributors involved in the project, dataset, or activity. It includes key information about each contributor, such as their roles, contributions, and affiliations."
    )
    menu_item = {
        "name": _("Overview"),
        "icon": "user-circle",
    }

    sections = {
        "title": False,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contributions_by_type"] = self.get_contribution_counts()
        return context

    def get_contribution_counts(self):
        """
        Returns a dictionary of contribution counts by type for the base object.
        """
        contributions_by_type = self.base_object.contributions.values("content_type").annotate(count=Count("id"))
        result = {}
        for entry in contributions_by_type:
            content_type = ContentType.objects.get(pk=entry["content_type"])
            model_verbose_name = content_type.model_class()._meta.verbose_name_plural.title()
            result[model_verbose_name] = entry["count"]
        return result


plugins.contributor.register(
    ProjectPlugin,
    DatasetPlugin,
    ActivityPlugin,
)


# @plugins.contributor.register
# class ContributorDatasets(DatasetPlugin):
#     pass


@plugins.contributor.register
class Profile(ManageBaseObjectPlugin):
    title = _("Profile")
    form_class = UserProfileForm
    sections = {
        "sidebar_secondary": False,
    }

    def get_form_class(self):
        if self.base_object.__class__ == Person:
            # If the base object is a Person, use the UserProfileForm
            return UserProfileForm
        elif self.base_object.__class__ == Organization:
            # If the base object is an Organization, use the OrganizationProfileForm
            return OrganizationProfileForm


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
        if context.get("non_polymorphic_object"):
            quick_add_form.helper.form_action = plugins.reverse(
                context["non_polymorphic_object"], "contributors-quick-add"
            )
        else:
            quick_add_form.helper.form_action = plugins.reverse(self.base_object, "contributors-quick-add")
        context["quick_add_form"] = quick_add_form
        context["modals"] = [
            "contributor.modals.edit-contribution",
        ]

        context["user_permissions"] = get_perms(self.request.user, self.base_object)
        context["can_modify_contributor"] = (
            "modify_contributor" in context["user_permissions"] or self.request.user.is_data_admin
        )
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
