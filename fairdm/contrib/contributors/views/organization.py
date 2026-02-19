from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from guardian.decorators import permission_required_or_403

from fairdm.views import FairDMCreateView, FairDMListView

from ..filters import OrganizationFilter
from ..forms.organization import OrganizationCreateForm
from ..models import Affiliation, Organization, Person


class OrganizationListView(FairDMListView):
    """List of organizations that the user is a member of."""

    model = Organization
    filterset_class = OrganizationFilter
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
    card_template = "contributors/contributor_card.html"


class OrganizationCreateView(FairDMCreateView):
    """Create a new organization."""

    heading_config = {
        "title": _("Create Organization"),
    }
    form_class = OrganizationCreateForm

    def form_valid(self, form):
        """Handle form submission."""
        response = super().form_valid(form)
        return response


# ── T067: Organization ownership transfer view ──────────────────────────────


@login_required
@require_POST
@permission_required_or_403("contributors.manage_organization", (Organization, "pk", "org_pk"))
def transfer_ownership(request, org_pk, new_owner_pk):
    """Transfer organization ownership to a new person.

    Requires manage_organization permission on the organization.
    Updates the Affiliation type to OWNER for the new owner and demotes
    the current owner to ADMIN.

    Args:
        request: HTTP request
        org_pk: Primary key of the Organization
        new_owner_pk: Primary key of the Person to become new owner

    Returns:
        HttpResponseRedirect to organization detail or changelist
    """
    organization = get_object_or_404(Organization, pk=org_pk)
    new_owner = get_object_or_404(Person, pk=new_owner_pk)

    # Verify new owner is a member of the organization
    new_owner_affiliation = organization.affiliations.filter(person=new_owner).first()
    if not new_owner_affiliation:
        messages.error(
            request,
            _("{person} is not a member of {organization}.").format(
                person=new_owner.name,
                organization=organization.name,
            ),
        )
        return redirect("admin:contributors_organization_change", org_pk)

    # Get current owner affiliation
    current_owner_affiliation = organization.affiliations.filter(type=Affiliation.MembershipType.OWNER).first()

    # Demote current owner to ADMIN if exists
    if current_owner_affiliation:
        current_owner_affiliation.type = Affiliation.MembershipType.ADMIN
        current_owner_affiliation.save()

        messages.info(
            request,
            _("{person} has been demoted from Owner to Admin.").format(
                person=current_owner_affiliation.person.name,
            ),
        )

    # Promote new owner
    new_owner_affiliation.type = Affiliation.MembershipType.OWNER
    new_owner_affiliation.save()

    messages.success(
        request,
        _("{person} is now the owner of {organization}.").format(
            person=new_owner.name,
            organization=organization.name,
        ),
    )

    # Redirect to organization admin page
    return redirect("admin:contributors_organization_change", org_pk)
