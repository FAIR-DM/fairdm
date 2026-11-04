"""Plugins for organisation pages: the list of an organisation's members."""

from django.db.models import Exists, F, OuterRef, Subquery
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, is_instance_of

from ..models import Affiliation, Contributor, Organization, Person
from ..views.person import PersonListView


@plugins.register(Contributor, label=_("Members"), icon="member", order=50)
class OrganizationMembers(Plugin, PersonListView):
    """List an organisation's current, verified members on the People page's cards.

    The members are those the overview's Members card counts: the owner first, then the
    administrators, then the other members, each group by name. Pending and former members are
    left out. The tab is offered on an organisation's page only, to everyone the overview opens
    for.
    """

    url_path = "members"
    page_title = _("Members")
    queryset = Person.objects.all()
    check = staticmethod(is_instance_of(Organization))
    empty_state_heading = _("Nobody has listed this organization as an affiliation yet.")

    def get_queryset(self):
        """Limit the people to the organisation's members, the people who run it first."""
        memberships = Affiliation.objects.filter(
            organization=self.base_object,
            person=OuterRef("pk"),
            type__gte=Affiliation.MembershipType.MEMBER,
        ).current()
        return (
            super()
            .get_queryset()
            .filter(Exists(memberships))
            .annotate(
                membership=Subquery(memberships.order_by("-type").values("type")[:1])
            )
            .order_by("-membership", F("name").asc(nulls_first=True), "pk")
        )
