"""Views that handle adding and editing contribution objects."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import UpdateView

from fairdm.utils.view_mixins import RelatedObjectMixin
from fairdm.views import FairDMCreateView

from .. import utils
from ..forms.forms import RemoteContributionForm
from ..models import Contribution, Contributor


class ContributionCreateView(RelatedObjectMixin, FairDMCreateView):
    """Adds a new Contribution to a Project, Dataset, Sample or Measurement. Used with htmx requests predominantly from
    the Contribution Plugin on detail pages.

    Returns:
        HttpResponse: A rendered partial HTML template.

    """

    form_class = RemoteContributionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_object"] = self.base_object
        return context

    def form_valid(self, form):
        data = form.cleaned_data["data"]
        if data.get("orcid-identifier"):
            contributor = utils.contributor_from_orcid_data(data)
        elif data["id"].startswith("https://ror.org/"):
            contributor = utils.contributor_from_ror_data(data)
        else:
            contributor = Contributor.objects.get(uuid=data["id"]).get_real_instance()

        contribution = self.base_object.add_contributor(contributor, with_roles=["ProjectMember"])
        return render(self.request, "contributors/contribution.html", {"contributor": contribution})


class EditContributionView(LoginRequiredMixin, UpdateView):
    model = Contribution
