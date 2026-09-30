"""Public team page listing the people who hold portal roles."""

from django.contrib.auth.models import Group
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from fairdm.portal_roles import PortalRoles
from fairdm.views import FairDMTemplateView

from ..models import Person


class TeamView(FairDMTemplateView):
    """Public page listing the active holders of each portal role, leaving out roles nobody holds.

    Only portal roles are shown, never a contribution's role.
    """

    template_name = "contributors/team.html"
    page_title = _("Portal Team")
    page_subtitle = _(
        "Meet the individuals that maintain this portal and keep the community "
        "thriving."
    )
    page_info = _(
        "Data portals don't run themselves! Behind every portal is a dedicated team "
        "of contributors who help maintain and improve the space for the benefit of "
        "the wider community. Thanks to everyone who helps make this possible."
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
        """Add the roles with their holders and the grid settings."""
        context = super().get_context_data(**kwargs)
        context["roles"] = self.get_roles()
        context["list_item_template"] = self.list_item_template
        context["grid_config"] = self.grid_config
        return context

    def get_roles(self):
        """Pair each shipped role with its active holders, in declaration order.

        Uses two queries however many roles or holders there are.

        Returns:
            One ``{"role": role, "holders": [people]}`` dict per role that has holders.
        """
        active_holders = Person.objects.filter(is_active=True).for_cards().order_by("name")
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
