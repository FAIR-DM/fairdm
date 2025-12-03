from django.urls import reverse_lazy


def get_contributor_url(request):
    if request.user.is_authenticated:
        # Use the user's UUID for authenticated users
        # Users are Person instances, so use the 'person' namespace
        return reverse_lazy("person:overview", args=[request.user.uuid])
    return "/"


# AuthenticatedUserDropdown.insert(
#     [
#         DropdownMenuLink(_("Profile"), url=get_contributor_url, icon="person"),
#         DropdownMenuLink(
#             _("Portal Administration"), check=checks.user_is_staff, view_name="admin:index", icon="administration"
#         ),
#     ],
#     position=0,
# )
