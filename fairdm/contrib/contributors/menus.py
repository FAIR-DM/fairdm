from django.urls import reverse_lazy


def get_contributor_url(request):
    if request.user.is_authenticated:
        # Use the user's UUID for authenticated users
        return reverse_lazy("contributor:overview", args=[request.user.uuid])
    return "/"


# AuthenticatedUserDropdown.insert(
#     [
#         DropdownMenuLink(_("Profile"), url=get_contributor_url, icon="user"),
#         DropdownMenuLink(
#             _("Portal Administration"), check=checks.user_is_staff, view_name="admin:index", icon="administration"
#         ),
#     ],
#     position=0,
# )
