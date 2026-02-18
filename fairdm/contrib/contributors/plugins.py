from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import (
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_filters import FilterSet

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.views import DatasetListView
from fairdm.core.measurement.models import Measurement
from fairdm.core.plugins import (
    EditPlugin,
    InlineFormSetPlugin,
    OverviewPlugin,
)
from fairdm.core.project.models import Project
from fairdm.core.project.views import ProjectListView
from fairdm.core.sample.models import Sample
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMListView

from .forms.contribution import QuickAddContributionForm, UpdateContributionForm
from .forms.forms import AffiliationForm, UserIdentifierForm, UserIdentifierFormSet
from .forms.organization import OrganizationProfileForm
from .forms.person import UserProfileForm
from .models import (
    Affiliation,
    Contribution,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)


@plugins.register(Contributor)
class Overview(OverviewPlugin):
    """Overview plugin for Contributor detail pages (Person and Organization)."""

    def get_context_data(self, **kwargs):
        """Add contribution counts and ORCID identifier to the context."""
        context = super().get_context_data(**kwargs)
        context["contributions_by_type"] = self.get_contribution_counts()
        context["object"] = self.object

        # Add ORCID identifier if available (for Person objects)
        if isinstance(self.object, Person):
            orcid = self.object.identifiers.filter(type="ORCID").first()
            context["orcid_identifier"] = orcid

        return context

    def get_contribution_counts(self):
        """
        Calculate contribution counts by content type.

        Returns:
            dict: Mapping of model verbose names to contribution counts
                  (e.g., {"Projects": 5, "Datasets": 3})
        """
        contributions_by_type = self.object.contributions.values("content_type").annotate(count=Count("id"))
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


@plugins.register(Contributor)
class ContributorProjects(Plugin, ProjectListView):
    """Projects plugin for Contributor model - shows all projects a contributor is associated with."""

    menu = {"label": _("Projects"), "icon": "project", "order": 200}
    template_name = "plugins/list_view.html"

    def get_queryset(self, *args, **kwargs):
        """Filter projects to only those associated with this contributor."""
        return self.object.projects.all()


@plugins.register(Contributor)
class ContributorDatasets(Plugin, DatasetListView):
    """Datasets plugin for Contributor model - shows all datasets a contributor is associated with."""

    menu = {"label": _("Datasets"), "icon": "dataset", "order": 210}
    template_name = "plugins/list_view.html"

    def get_queryset(self, *args, **kwargs):
        """Filter datasets to only those associated with this contributor."""
        return self.object.datasets.all()


# ============ MANAGEMENT PLUGINS =================


@plugins.register(Contributor)
class Profile(EditPlugin):
    """Profile editing plugin for Contributor detail pages.

    Dynamically selects the appropriate form based on contributor type.
    """

    model = Contributor
    about = _(
        "Edit your public profile information, including your name, biography, and profile image. "
        "This information is visible to all visitors of the portal."
    )
    learn_more = user_guide("contributor/profile")

    def get_form_class(self):
        """Return appropriate form based on contributor type."""
        if isinstance(self.base_object, Person):
            return UserProfileForm
        elif isinstance(self.base_object, Organization):
            return OrganizationProfileForm
        return super().get_form_class()


@plugins.register(Contributor)
class Identifiers(InlineFormSetPlugin):
    """Plugin for managing persistent identifiers (ORCID, ROR, etc.)."""

    name = "identifiers"
    title = _("Identifiers")
    menu = {"label": _("Identifiers"), "icon": "identifier", "order": 510}

    # Page configuration
    about = _(
        "Manage your persistent identifiers such as ORCID, which help uniquely identify you "
        "in research outputs and allow automatic synchronization of your profile data."
    )
    learn_more = user_guide("contributor/identifiers")

    # InlineFormSetView configuration
    model = Contributor
    inline_model = ContributorIdentifier
    form_class = UserIdentifierForm
    formset_class = UserIdentifierFormSet
    display_as_table = True

    def get_factory_kwargs(self):
        """Override to set max_num based on contributor type (Person vs Organization)."""
        kwargs = super().get_factory_kwargs()
        # Limit to one identifier per type, but only show appropriate types
        vocabulary = self.inline_model.VOCABULARY
        if isinstance(self.object, Person):
            # Person: ORCID, ResearcherID
            kwargs["max_num"] = len(vocabulary.from_collection("Person").values)
        elif isinstance(self.object, Organization):
            # Organization: ROR, Wikidata, ISNI, Crossref Funder ID
            kwargs["max_num"] = len(vocabulary.from_collection("Organization").values)
        else:
            # Fallback to all identifiers
            kwargs["max_num"] = len(vocabulary.values)
        return kwargs

    def get_formset_kwargs(self):
        """Pass contributor instance to form for filtering identifier choices."""
        kwargs = super().get_formset_kwargs()
        kwargs["form_kwargs"] = {"contributor_instance": self.object}
        return kwargs


@plugins.register(Contributor)
class Affiliations(InlineFormSetPlugin):
    """Plugin for managing organizational affiliations (Person only)."""

    name = "affiliations"
    title = _("Affiliations")
    learn_more = user_guide("contributor/affiliations")
    check = lambda request, obj: obj is None or isinstance(obj, Person)
    model = Person
    inline_model = Affiliation
    form_class = AffiliationForm
    display_as_table = True


@plugins.register(Contributor)
class Keywords(EditPlugin):
    """Plugin for managing research interests/keywords."""

    name = "keywords"
    title = _("Research Interests")
    menu = {"label": _("Research Interests"), "icon": "keywords", "order": 530}
    about = _(
        "Manage your research interests and keywords. These help others discover your work "
        "and understand your areas of expertise."
    )
    learn_more = user_guide("contributor/keywords")
    model = Contributor
    fields = ["keywords"]


@plugins.register(Contributor)
class Links(EditPlugin):
    """Plugin for managing external links."""

    name = "links"
    title = _("External Links")
    menu = {"label": _("Links"), "icon": "link", "order": 540}
    about = _(
        "Add links to your personal website, social media profiles, institutional pages, "
        "or other relevant online presence."
    )
    learn_more = user_guide("contributor/links")
    model = Contributor
    fields = ["links"]


@plugins.register(Organization)
class SubOrganizations(Plugin, FairDMListView):
    """Plugin for displaying sub-organizations (Organization only)."""

    name = "sub-organizations"
    title = _("Sub-Organizations")
    menu = {"label": _("Sub-Organizations"), "icon": "relationships", "order": 100}
    model = Organization
    check = lambda request, obj: obj is None or isinstance(obj, Organization)

    def get_queryset(self):
        """Return sub-organizations of this organization."""
        return self.object.sub_organizations.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading_config"] = {
            "icon": "relationships",
            "title": _("Sub-Organizations"),
            "description": _("Departments, research groups, and other units within this organization."),
        }
        return context


@plugins.register(Organization)
class OrganizationMembers(Plugin, FairDMListView):
    """Plugin for displaying organization members (Organization only)."""

    name = "members"
    title = _("Members")
    menu = {"label": _("Members"), "icon": "users", "order": 110}
    model = Affiliation
    check = lambda request, obj: obj is None or isinstance(obj, Organization)
    filterset_fields = ["person__name", "type", "is_primary"]

    def get_queryset(self):
        """Return members of this organization."""
        return self.object.affiliations.select_related("person").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading_config"] = {
            "icon": "users",
            "title": _("Members"),
            "description": _("People affiliated with this organization."),
        }
        return context


@plugins.register(Contributor)
class Activity(Plugin, FairDMListView):
    """Plugin showing recent activity/contributions chronologically."""

    name = "activity"
    title = _("Recent Activity")
    menu = {"label": _("Activity"), "icon": "timeline", "order": 120}
    model = Contribution
    card_template = "cotton/contributor/card/contribution.html"

    def get_filterset_class(self):
        """Return a basic FilterSet for contributions."""

        return FilterSet

    def get_queryset(self):
        """Return all contributions ordered by most recent."""
        return self.object.contributions.select_related("content_type", "contributor").order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = {
            "title": _("Recent Activity"),
        }
        return context


@plugins.register(Contributor)
class Statistics(Plugin, TemplateView):
    """Plugin showing detailed contribution statistics."""

    name = "statistics"
    title = _("Statistics")
    menu = {"label": _("Statistics"), "icon": "statistics", "order": 130}
    template_name = "contributors/plugins/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get contribution counts by type
        contributions_by_type = {}
        for entry in self.object.contributions.values("content_type").annotate(count=Count("id")):
            content_type = ContentType.objects.get(pk=entry["content_type"])
            model_class = content_type.model_class()
            if model_class:
                contributions_by_type[model_class._meta.verbose_name_plural] = entry["count"]

        context.update(
            {
                "total_contributions": self.object.contributions.count(),
                "contributions_by_type": contributions_by_type,
            }
        )

        return context


@plugins.register(Contributor)
class Collaborators(Plugin, FairDMListView):
    """Plugin showing frequent collaborators."""

    name = "collaborators"
    title = _("Collaborators")
    menu = {"label": _("Collaborators"), "icon": "people", "order": 140}
    model = Contributor
    card_template = "cotton/contributor_card.html"

    def get_queryset(self):
        """
        Return contributors who have worked on the same projects/datasets.

        This finds all content objects this contributor has contributed to,
        then finds other contributors to those same objects.
        """
        # Get all content objects this contributor has contributed to
        content_types = self.object.contributions.values_list("content_type", "object_id")

        # Find other contributors to the same objects
        collaborator_ids = set()
        for ct_id, obj_id in content_types:
            related_contributions = (
                Contribution.objects.filter(content_type_id=ct_id, object_id=obj_id)
                .exclude(contributor=self.object)
                .values_list("contributor_id", flat=True)
            )
            collaborator_ids.update(related_contributions)

        # Return collaborators annotated with collaboration count
        return (
            Contributor.objects.filter(id__in=collaborator_ids)
            .annotate(collaboration_count=Count("contributions"))
            .order_by("-collaboration_count")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = {
            "title": _("Collaborators"),
        }
        return context


# =========== PLUGIN FOR CORE DATA MODELS =================


@plugins.register(Project, Dataset, Sample, Measurement)
class Contributors(Plugin, ListView):
    """
    Plugin for managing contributors on any model with a 'contributors' GenericRelation.
    """

    model = Contribution
    menu = {"label": _("Contributors"), "icon": "people", "order": 200}
    template_name = "contributors/plugins/list_view.html"

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


# =========== CONTRIBUTION CRUD PLUGINS =================


@plugins.register(Project, Dataset, Sample, Measurement)
class AddContribution(Plugin, FormView):
    """Quick add plugin for adding multiple contributors to an object."""

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


@plugins.register(Project, Dataset, Sample, Measurement)
class EditContribution(Plugin, UpdateView):
    """Edit plugin for updating contribution roles and affiliation."""

    template_name = "contributors/plugins/contribution_form.html"
    form_class = UpdateContributionForm
    model = Contribution

    def get_form_kwargs(self):
        """Pass the base object to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.object
        return kwargs

    def get_success_url(self):
        """Return to the contributors page after successful edit."""
        return self.object.get_plugin_url("contributors")

    def form_valid(self, form):
        """Save the contribution and trigger HTMX refresh."""
        response = super().form_valid(form)

        # For HTMX requests, return a success response with trigger
        if self.request.htmx:
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "contributionUpdated"
            return response

        return response


@plugins.register(Project, Dataset, Sample, Measurement)
class RemoveContribution(Plugin, DeleteView):
    """Delete plugin for removing a contribution."""

    template_name = "contributors/plugins/contribution_confirm_delete.html"
    model = Contribution

    def get_success_url(self):
        """Return to the contributors page after successful deletion."""
        return self.object.get_plugin_url("contributors")

    def delete(self, request, *args, **kwargs):
        """Delete the contribution and trigger HTMX refresh."""
        response = super().delete(request, *args, **kwargs)

        # For HTMX requests, return a success response with trigger
        if self.request.htmx:
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "contributionUpdated"
            return response

        return response
