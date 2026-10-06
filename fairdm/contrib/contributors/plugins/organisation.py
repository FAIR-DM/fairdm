"""Plugins for organization pages: the Members list tab (prototype for specification 023)."""

from django.db.models import OuterRef, Subquery
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, is_instance_of

from ..models import Affiliation, Contributor, Organization, Person
from ..views.person import PersonListView


@plugins.register(Contributor, label=_("Members"), icon="member", order=50)
class Members(Plugin, PersonListView):
    """List an organization's current, verified members, the people who run it first."""

    page_title = _("Members")
    check = is_instance_of(Organization)
    list_item_template = "contributors/member_card.html"
    model = Person
    search_fields = ["name"]
    order_by = []
    paginate_by = 24
    grid = {"md": 2, "xl": 3}

    def show_create_action(self, user):
        """Offer no way to add a member: managing members is not part of this tab."""
        return False

    def get_queryset(self, *args, **kwargs):
        """Limit to current members, each once, with the kind of member and since when."""
        current = Affiliation.objects.filter(
            organization=self.base_object,
            person=OuterRef("pk"),
            end_date__isnull=True,
            type__gte=Affiliation.MembershipType.MEMBER,
        ).order_by("-type")
        self.queryset = (
            Person.objects.annotate(
                membership_type=Subquery(current.values("type")[:1]),
                membership_start=Subquery(current.values("start_date")[:1]),
            )
            .filter(membership_type__isnull=False)
            .order_by("-membership_type", "name")
        )
        return super().get_queryset()

    def handle_no_permission(self):
        """Answer "not found" on a person's page, which has no Members tab."""
        raise Http404("No organization matches the given query.")

    def get_lookup_kwargs(self) -> dict:
        """Return no lookup kwargs, as the queryset is already scoped to the organization."""
        return {}
