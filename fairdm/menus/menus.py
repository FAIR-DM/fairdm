"""Declares the site navigation menu."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuCollapse, MenuGroup


def _has_registered(kind):
    """Return a visibility check for a heading that holds one entry per registered type.

    Declared here rather than left to whichever app fills the heading, because this module is
    imported by `fairdm.apps` and so the heading exists even when that app is not installed.
    flex_menu only auto-hides a container whose children all resolved invisible, so a heading
    with no children would otherwise render empty.

    Args:
        kind: The registry attribute to test, such as ``"samples"``.

    Returns:
        A check callable that is true when anything of that kind is registered.
    """

    def check(request, **kwargs):
        # Imported here because this module loads while the app registry is populating.
        from fairdm.registry import registry

        return bool(getattr(registry, kind))

    return check


def _can_reach_administration(request, **kwargs):
    """Return whether the request's user may open the administration interface.

    Whoever can open it should see the link to its documentation, not only somebody carrying
    `is_staff`, since `CustomAdminSite.has_permission` (`fairdm/contrib/admin/sites.py`) also
    admits a rights-carrying role holder. Calls the site's own method rather than re-deriving
    the rule.

    Args:
        request: The current request.
        **kwargs: Unused menu check keyword arguments.

    Returns:
        ``True`` when the user may open the administration interface.
    """
    if not (hasattr(request, "user") and request.user):
        return False
    return admin.site.has_permission(request)


AppMenu.extend(
    [
        MenuItem(
            name=_("Home"),
            view_name="home",
            extra_context={
                "icon": "home",
            },
        ),
        MenuItem(
            name=_("Projects"),
            view_name="project-list",
            extra_context={
                "icon": "project",
            },
        ),
        MenuItem(
            name=_("Datasets"),
            view_name="dataset-list",
            extra_context={
                "icon": "dataset",
            },
        ),
        MenuCollapse(
            name=_("Samples"),
            check=_has_registered("samples"),
            extra_context={
                "icon": "sample",
            },
        ),
        MenuCollapse(
            name=_("Measurements"),
            check=_has_registered("measurements"),
            extra_context={
                "icon": "measurement",
            },
        ),
        MenuItem(
            name=_("Literature"),
            url="#",
            extra_context={"icon": "literature"},
        ),
        MenuGroup(
            _("Community"),
            children=[
                MenuItem(
                    name=_("People"),
                    view_name="people-list",
                    extra_context={"icon": "people"},
                ),
                MenuItem(
                    name=_("Organizations"),
                    view_name="organization-list",
                    extra_context={"icon": "organization"},
                ),
                MenuItem(
                    name=_("Team"),
                    view_name="team",
                    extra_context={"icon": "member"},
                ),
            ],
        ),
        MenuGroup(
            name=_("Documentation"),
            children=[
                MenuItem(
                    name=_("API"),
                    view_name="api:api-docs",
                    extra_context={"icon": "api"},
                ),
                MenuItem(
                    name=_("User Guide"),
                    url="https://fairdm.org/user-guide/",
                    extra_context={"icon": "literature"},
                ),
                MenuItem(
                    name=_("Admin Guide"),
                    url="https://fairdm.org/admin-guide/",
                    check=_can_reach_administration,
                    extra_context={"icon": "literature"},
                ),
            ],
        ),
    ],
)
