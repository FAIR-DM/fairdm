from dac.menus import AuthenticatedUserDropdown, DropdownMenuItem
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from fairdm.menus import user_is_staff


def get_contributor_url(request):
    if request.user.is_authenticated:
        # Use the user's UUID for authenticated users
        return reverse_lazy("contributor:overview", args=[request.user.uuid])
    return "/"


AuthenticatedUserDropdown.insert(
    [
        DropdownMenuItem(_("Profile"), url=get_contributor_url, icon="user"),
        DropdownMenuItem(
            _("Portal Administration"), check=user_is_staff, view_name="admin:index", icon="administration"
        ),
    ],
    position=0,
)
