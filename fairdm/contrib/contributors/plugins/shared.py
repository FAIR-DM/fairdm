from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.project.models import Project
from fairdm.views import FairDMCreateView, FairDMDeleteView, FairDMListView, FairDMUpdateView

from ..forms.contribution import QuickAddContributionForm, UpdateContributionForm
from ..models import Contribution


class ContributionCreate(Plugin, FairDMCreateView):
    """Quick add plugin for adding multiple contributors to an object."""

    url_path = "add"
    template_name = "contributors/plugins/contribution_quick_add.html"
    form_class = QuickAddContributionForm

    def get_form_kwargs(self):
        """Pass base_object to form for autocomplete filtering."""
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        """Add base object verbose name to context."""
        context = super().get_context_data(**kwargs)
        context["base_object_verbose_name"] = self.object._meta.verbose_name
        return context

    def get_success_url(self):
        """Return to the contributors page after successful add."""
        return self.object.get_plugin_url("contributors")

    def form_valid(self, form):
        """Add selected contributors to the base object."""
        contributors = form.cleaned_data["contributors"]
        for contributor in contributors:
            # Use the Contribution.add_to classmethod for consistency
            Contribution.add_to(
                contributor=contributor,
                obj=self.object,
                roles=None,  # Default roles can be set later via edit
                affiliation=None,
            )

        # For HTMX requests, return a success response
        if self.request.htmx:
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "contributionUpdated"
            return response

        return super().form_valid(form)


class ContributionUpdate(Plugin, FairDMUpdateView):
    """Edit plugin for updating contribution roles and affiliation."""

    url_path = "edit"
    form_class = UpdateContributionForm
    model = Contribution

    def get_form_kwargs(self):
        """Pass the base object to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.object
        return kwargs


class ContributionRemove(Plugin, FairDMDeleteView):
    """Delete plugin for removing a contribution."""

    url_path = "remove"
    template_name = "contributors/plugins/contribution_confirm_delete.html"
    model = Contribution


@plugins.register(Project, label=_("Contributors"), icon="users", order=150)
class ContributionList(Plugin, FairDMListView):
    """
    Plugin for managing contributors on any model with a 'contributors' GenericRelation.
    """

    url_path = "contributors"
    model = Contribution
    list_item_template = "contributors/contributor_card.html"
    subviews = [
        ContributionCreate,
        ContributionUpdate,
        ContributionRemove,
    ]
    search_fields = ["contributor__name"]

    class Media:
        css = {"all": ("contributors/css/contributor-filter.css",)}
        js = ("contributors/js/contributor-filter.js",)

    def get_queryset(self, *args, **kwargs):
        """Return contributors of type Person for the base object."""
        return self.object.contributors.all()

    def get_context_data(self, **kwargs):
        """Add available roles to the context for filtering."""
        context = super().get_context_data(**kwargs)
        # Get all unique roles from the contributions grouped by contributor type
        person_roles = set()
        org_roles = set()

        for contribution in context["object_list"]:
            is_person = contribution.contributor.polymorphic_ctype.model == "person"
            for role in contribution.roles.all():
                if is_person:
                    person_roles.add((role.name, role.label, "person"))
                else:
                    org_roles.add((role.name, role.label, "organization"))

        # Combine and sort all roles
        all_roles = list(person_roles) + list(org_roles)
        context["available_roles"] = sorted(all_roles, key=lambda x: (x[2], x[1]))

        return context
