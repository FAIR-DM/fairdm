"""Views for listing and creating organisations."""

from django.utils.translation import gettext_lazy as _

from fairdm.views import FairDMCreateView, FairDMListView

from ..filters import OrganizationFilter
from ..forms.organization import OrganizationCreateForm
from ..models import Organization


class OrganizationListView(FairDMListView):
    """List organisations."""

    model = Organization
    filterset_class = OrganizationFilter
    title = _("Organizations")
    list_item_template = "contributors/contributor_card.html"
    grid = {"md": 2, "xl": 3}
    toolbar_filters = ["search", "country"]


class OrganizationCreateView(FairDMCreateView):
    """Create a new organization."""

    heading_config = {
        "title": _("Create Organization"),
    }
    form_class = OrganizationCreateForm

    def form_valid(self, form):
        """Save the organisation."""
        response = super().form_valid(form)
        return response
