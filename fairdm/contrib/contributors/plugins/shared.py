"""Plugins for managing the contributors of an object."""

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.core.project.models import Project
from fairdm.views import (
    FairDMCreateView,
    FairDMDeleteView,
    FairDMListView,
    FairDMUpdateView,
)

from ..forms.contribution import QuickAddContributionForm, UpdateContributionForm
from ..models import Contribution


class ContributionCreate(Plugin, FairDMCreateView):
    """Add several contributors to an object at once."""

    url_path = "add"
    template_name = "contributors/plugins/contribution_quick_add.html"
    form_class = QuickAddContributionForm

    def get_form_kwargs(self):
        """Pass the base object to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.base_object
        return kwargs

    def get_context_data(self, **kwargs):
        """Add the base object's verbose name."""
        context = super().get_context_data(**kwargs)
        context["base_object_verbose_name"] = self.base_object._meta.verbose_name
        return context

    def get_success_url(self):
        """Return to the contributors page."""
        return reverse(self.base_object, "contribution-list")

    def form_valid(self, form):
        """Add the selected contributors to the base object, without roles."""
        contributors = form.cleaned_data["contributors"]
        for contributor in contributors:
            Contribution.add_to(
                contributor=contributor,
                obj=self.base_object,
                roles=None,
                affiliation=None,
            )

        if self.request.htmx:
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "contributionUpdated"
            return response

        return super().form_valid(form)


class ContributionUpdate(Plugin, FairDMUpdateView):
    """Edit a contribution's roles and affiliation."""

    url_path = "<int:pk>/edit"
    form_class = UpdateContributionForm
    model = Contribution

    def get_form_kwargs(self):
        """Pass the base object to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.base_object
        return kwargs


class ContributionRemove(Plugin, FairDMDeleteView):
    """Remove a contribution."""

    url_path = "<int:pk>/remove"
    template_name = "contributors/plugins/contribution_confirm_delete.html"
    model = Contribution


@plugins.register(Project, label=_("Contributors"), icon="users", order=150)
class ContributionList(Plugin, FairDMListView):
    """List and manage the contributors of an object that has a ``contributors`` relation."""

    url_path = "contributors"
    model = Contribution
    list_item_template = "contributors/contributor_card.html"
    extra_views = [
        ContributionCreate,
        ContributionUpdate,
        ContributionRemove,
    ]
    search_fields = ["contributor__name"]

    class Media:
        css = {"all": ("contributors/css/contributor-filter.css",)}
        js = ("contributors/js/contributor-filter.js",)

    def get_queryset(self, *args, **kwargs):
        """Limit to the base object's contributions."""
        return self.base_object.contributors.all()

    def get_context_data(self, **kwargs):
        """Add the roles held on the listed contributions, for filtering."""
        context = super().get_context_data(**kwargs)
        person_roles = set()
        org_roles = set()

        for contribution in context["object_list"]:
            is_person = contribution.contributor.polymorphic_ctype.model == "person"
            for role in contribution.roles.all():
                if is_person:
                    person_roles.add((role.name, role.label, "person"))
                else:
                    org_roles.add((role.name, role.label, "organization"))

        all_roles = list(person_roles) + list(org_roles)
        context["available_roles"] = sorted(all_roles, key=lambda x: (x[2], x[1]))

        return context
