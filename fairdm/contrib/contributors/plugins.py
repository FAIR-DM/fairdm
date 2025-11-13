from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.urls import include, path
from django.utils.translation import gettext as _
from django_filters import FilterSet
from guardian.shortcuts import get_perms

from fairdm.core.plugins import (
    ManageBaseObjectPlugin,
    OverviewPlugin,
)
from fairdm.plugins import EXPLORE, MANAGEMENT, PluginMenuItem, register_plugin
from fairdm.views import FairDMListView

from .forms.contribution import QuickAddContributionForm
from .forms.organization import OrganizationProfileForm
from .forms.person import UserProfileForm
from .models import Contribution, Person
from .views.contribution import (
    ContributionCreateView,
    ContributionRemoveView,
    ContributionUpdateView,
    ContributorQuickAddView,
)


# Overview plugin for Person model
@register_plugin
class PersonOverview(OverviewPlugin):
    category = EXPLORE
    menu_item = PluginMenuItem(name=_("Overview"), icon="user-circle")
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
            model_class = content_type.model_class()
            if model_class:
                verbose_name = model_class._meta.verbose_name_plural
                if verbose_name:
                    model_verbose_name = str(verbose_name).title()
                    result[model_verbose_name] = entry["count"]
        return result


# Overview plugin for Organization model
@register_plugin
class OrganizationOverview(OverviewPlugin):
    category = EXPLORE
    menu_item = PluginMenuItem(name=_("Overview"), icon="user-circle")
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
            model_class = content_type.model_class()
            if model_class:
                verbose_name = model_class._meta.verbose_name_plural
                if verbose_name:
                    model_verbose_name = str(verbose_name).title()
                    result[model_verbose_name] = entry["count"]
        return result


# Profile management plugin for Person model
@register_plugin
class PersonProfile(ManageBaseObjectPlugin):
    category = MANAGEMENT
    menu_item = PluginMenuItem(name=_("Profile"), icon="user")
    title = _("Profile")
    form_class = UserProfileForm
    sections = {
        "sidebar_secondary": False,
    }


# Profile management plugin for Organization model
@register_plugin
class OrganizationProfile(ManageBaseObjectPlugin):
    category = MANAGEMENT
    menu_item = PluginMenuItem(name=_("Profile"), icon="building")
    title = _("Profile")
    form_class = OrganizationProfileForm
    sections = {
        "sidebar_secondary": False,
    }


@register_plugin
class ContributorsPlugin(FairDMListView):
    category = EXPLORE
    model = Contribution
    name = "contributors"
    title = _("Contributors")
    heading_config = {
        "icon": "contributors",
        "title": _("Contributors"),
        "description": _("The following individuals have made contributions towards this database entry. "),
        "title_actions": [
            "contributor.quick-add",
        ],
    }
    filterset_fields = ["contributor__name"]
    menu_item = PluginMenuItem(name=_("Contributors"), icon="contributors")
    grid_config = {
        "cols": 1,
        "gap": 2,
        "responsive": {"sm": 2, "md": 4},
        "card": "contributor.card.contribution",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quick_add_form = QuickAddContributionForm()
        # TODO: Fix URL generation for quick-add form
        # This needs to be updated to work with the new plugin system
        # if context.get("non_polymorphic_object"):
        #     quick_add_form.helper.form_action = plugins.reverse(
        #         context["non_polymorphic_object"], "contributors-quick-add"
        #     )
        # else:
        #     quick_add_form.helper.form_action = plugins.reverse(self.base_object, "contributors-quick-add")
        context["quick_add_form"] = quick_add_form
        context["modals"] = [
            "contributor.modals.edit-contribution",
        ]

        context["user_permissions"] = get_perms(self.request.user, self.base_object)
        if self.request.user.is_authenticated:
            context["can_modify_contributor"] = (
                "modify_contributor" in context["user_permissions"]
                # Note: removed is_data_admin check as it's not available in base User model
            )
        return context

    def get_filterset_class(self):
        return FilterSet

    def get_queryset(self, *args, **kwargs):
        # restrict to contributors of type Person
        person_type = ContentType.objects.get_for_model(Person)
        return self.base_object.contributors.filter(contributor__polymorphic_ctype=person_type)
        # show people and organizations
        # return self.base_object.contributors.all()

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
