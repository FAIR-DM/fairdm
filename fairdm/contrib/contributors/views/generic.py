from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.templatetags.static import static
from django.utils.translation import gettext as _
from django.views.generic.detail import SingleObjectMixin
from django_contact_form.views import ContactFormView

from fairdm.utils.utils import user_guide
from fairdm.views import BaseCRUDView, FairDMListView

from ..filters import ContributorFilter
from ..forms.forms import ContributionForm
from ..models import Contributor, Organization, Person


class ContributorContactView(LoginRequiredMixin, SingleObjectMixin, ContactFormView):
    """Contact form for a contributor."""

    model = Contributor

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    @property
    def recipient_list(self):
        email = [self.get_object().preferred_email]
        return email


class ContributionCRUDView(BaseCRUDView):
    form_class = ContributionForm
    lookup_url_kwarg = "contribution_uuid"

    def get_form(self, data=None, files=None, **kwargs):
        form = super().get_form(data, files, **kwargs)
        form.fields["roles"].widget.choices = self.model.CONTRIBUTOR_ROLES().choices
        return form


class ContributorListView(FairDMListView):
    """List view for contributions."""

    model = Contributor
    title = _("Contributors")
    grid_config = {
        "cols": 1,
        "gap": 2,
        "responsive": {"md": 2},
        "card": "contributor.card.person",
    }
    # description = _(
    #     "Discover past, present and future research projects shared by our community to see what other are working on."
    # )
    # about = [
    #     _(
    #         "A research project serves as a container for multiple datasets that share common metadata, such as funding sources, project descriptions, contributors, and institutional affiliations. This page presents publicly listed research projects contributed by community members, allowing you to explore what others are working on."
    #     ),
    #     _(
    #         "Search and filter projects by topic, field, or format. Each project may contain multiple datasets, which can be accessed individually."
    #     ),
    # ]
    learn_more = user_guide("project")
    image = static("img/stock/contributors.jpg")
    filterset_class = ContributorFilter

    paginate_by = 20

    def get_queryset(self):
        return self.model.objects.instance_of(Person).prefetch_related("affiliations", "identifiers")


class PersonAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Person.contributors.prefetch_related("organization_memberships__organization")
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs

    # def get_result_label(self, result):
    #     name = result.name
    #     affiliation = result.organization_memberships.filter(is_primary=True).first().organization
    #     return f"{name}, {affiliation}"


class OrganizationAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organization.objects.all()

        person = self.forwarded.get("contributor", None)
        if person:
            # prefetch = Prefetch(
            #     "memberships", queryset=OrganizationMember.objects.filter(person=person), to_attr="person_membership"
            # )

            # qs = qs.filter(members__id=person).prefetch_related(prefetch)
            qs = qs.filter(members__id=person)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs

    # def get_result_label(self, result):
    #     name = result.name
    #     membership = result.person_membership[0]
    #     if membership.is_primary:
    #         name += "<span class='badge badge-primary'>Primary</span>"
    #     if membership.is_current:
    #         name += "<span class='badge badge-success'>Current</span>"
    #     return mark_safe(name)
