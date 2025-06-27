from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView
from meta.views import MetadataMixin

from fairdm.views import FairDMListView

from ..filters import OrganizationFilter
from ..forms.organization import RORForm
from ..models import Organization


class OrganizationListView(FairDMListView):
    """List of organizations that the user is a member of."""

    model = Organization
    filterset_class = OrganizationFilter  # No filter for organizations
    title = _("Organizations")
    title_config = {
        "text": _("All Organizations"),
    }
    grid_config = {
        "responsive": {"md": 3},
        "card": "contributor.card.organization",
    }


class OrgRORCreateView(MetadataMixin, LoginRequiredMixin, CreateView):
    """Create a new organization using the RORForm."""

    model = Organization
    template_name = "organizations/organization_form.html"
    success_url = "/"
    form_class = RORForm

    def get_success_url(self):
        return reverse("organization-detail", kwargs={"uuid": self.object.uuid})

    def form_valid(self, form):
        data = form.cleaned_data["data"]
        # if data["orcid-identifier"]:
        #     c = contributor_from_orcid(data)
        # elif data["id"].startswith("https://ror.org/"):
        #     c = contributor_from_ror(data)
        # # Organization.from_ror(form.cleaned_data["data"])
        # return HttpResponseRedirect(self.get_success_url())
        # return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class OrganizationCreateView(MetadataMixin, LoginRequiredMixin, CreateView):
    """Create a new organization."""

    template_name = "organizations/organization_form.html"
    success_url = "/"
    form_class = RORForm


class OrganizationUserListView(MetadataMixin, ListView):
    """List of users in an organization."""

    org_model = Organization

    def get(self, request, *args, **kwargs):
        self.organization = self.get_organization()
        self.object_list = self.organization.organization_users.all()
        context = self.get_context_data(
            object_list=self.object_list,
            organization_users=self.object_list,
            organization=self.organization,
        )
        return self.render_to_response(context)
