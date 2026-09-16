from django.contrib.auth.models import Group
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from fairdm.portal_roles import PortalRoles
from fairdm.views import FairDMTemplateView

from ..models import Person


class TeamView(FairDMTemplateView):
    """Who runs the portal, grouped by the portal role each person holds.

    Public (FR-031), lists active holders only (FR-030), a role nobody holds
    is left off (FR-034), and shows portal roles only - never a
    `Contribution`'s role (FR-035).
    """

    template_name = "contributors/team.html"
    page_title = _("Portal Team")
    page_subtitle = _(
        "The people who run this portal, grouped by the portal role each one holds."
    )
    page_info = _(
        "A portal role is granted by an administrator and governs what someone can "
        "do across the whole portal. It is distinct from a contribution role, which "
        "is set per dataset and only applies there."
    )
    page_info_actions = [
        {
            "text": _("About portal roles"),
            "href": "https://fairdm.org/portal-administration/roles/",
            "icon": "external-link",
            "target": "_blank",
        }
    ]
    list_item_template = "contributors/contributor_card.html"
    grid_config = {"cols": 1, "md": 2, "lg": 4, "gap": 4}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = self.get_roles()
        context["list_item_template"] = self.list_item_template
        context["grid_config"] = self.grid_config
        return context

    def get_roles(self):
        """Each shipped role paired with its active holders, in declaration order.

        One query for the role groups and one more, via `Prefetch`, for their
        members - the same two queries however many roles or holders exist, so
        the page's query count does not grow with the number of holders.
        """
        active_holders = Person.objects.filter(is_active=True).order_by("name")
        groups = {
            group.name: group
            for group in Group.objects.filter(
                name__in=PortalRoles.shipped_names()
            ).prefetch_related(Prefetch("user_set", queryset=active_holders))
        }

        roles = []
        for role in PortalRoles.ROLES:
            group = groups.get(role.name)
            holders = list(group.user_set.all()) if group is not None else []
            if holders:
                roles.append({"role": role, "holders": holders})
        return roles
