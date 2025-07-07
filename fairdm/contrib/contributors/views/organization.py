from django.utils.translation import gettext as _

from fairdm.views import FairDMCreateView, FairDMListView

from ..filters import OrganizationFilter
from ..forms.organization import OrganizationCreateForm
from ..models import Organization


class OrganizationListView(FairDMListView):
    """List of organizations that the user is a member of."""

    model = Organization
    filterset_class = OrganizationFilter  # No filter for organizations
    title = _("Organizations")
    heading_config = {
        "icon": "organization",
        "title": _("Organizations"),
        "description": _(
            "Organizations are entities that contribute to the Global Heat Flow Database. "
            "This section lists all organizations that have contributed data or resources."
        ),
    }
    grid_config = {
        "responsive": {"md": 3},
        "card": "contributor.card.organization",
    }


class OrganizationCreateView(FairDMCreateView):
    """Create a new organization."""

    heading_config = {
        "title": _("Create Organization"),
        "description": _(
            "This data import workflow allows you to upload an existing dataset formatted according to the latest specifications of the Global Heat Flow Database. "
        ),
    }
    form_class = OrganizationCreateForm

    def form_valid(self, form):
        """Handle form submission."""
        response = super().form_valid(form)
        return response
