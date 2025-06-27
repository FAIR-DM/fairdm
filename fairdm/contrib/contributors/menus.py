from account_management.menus import AccountMenu, FloatingAccountMenu
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem

from fairdm.menus import user_is_staff


def get_contributor_url(request):
    if request.user.is_authenticated:
        # Use the user's UUID for authenticated users
        return reverse_lazy("contributor:overview", args=[request.user.uuid])
    return "/"


AccountMenu.insert(
    [
        Menu(
            "ProfileMenu",
            label=_("Profile"),
            children=[
                MenuItem(_("Edit Profile"), view_name="contributor-profile", icon="user"),
                # MenuItem(_("Preferences"), view_name="contributor-identifiers", icon="preferences"),
                # MenuItem(_("Identifiers"), view_name="contributor-identifiers", icon="identifier"),
                # MenuItem(_("Affiliations"), view_name="contributor-affiliations", icon="organization"),
            ],
        ),
    ],
    position=0,
)

# Remove the Activity menu if it exists
# NOTE: Add this back later when the views are properly implemented
AccountMenu.pop("Activity")

FloatingAccountMenu.insert(
    [
        MenuItem(_("Profile"), url=get_contributor_url, icon="user"),
        MenuItem(_("Portal Administration"), check=user_is_staff, view_name="admin:index", icon="administration"),
    ],
    position=0,
)
