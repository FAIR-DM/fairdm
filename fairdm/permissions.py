"""The object-level permission backend that makes a portal role's rights real.

A role's permissions are declared at the model level (``fairdm/portal_roles.py``), but
``ModelBackend.has_perm`` answers ``False`` for every object-level question
(``django/contrib/auth/backends.py``): a Data Curator holding ``change_dataset`` cannot in
fact change a dataset until something derives the object-level answer from it. This backend
is that derivation, and it is deliberately narrow: only a permission held through membership
of one of the four shipped portal roles confers the object-level answer. A permission granted
straight to a person, or held through a group the portal made up itself, answers as before.
Update, Delete and Descriptions stay refused to a person holding only a model-level grant on
a private record, because a page that relies on inheriting a visibility rule is not guarded.
"""

from django.contrib.auth.backends import BaseBackend

from fairdm.portal_roles import PortalRoles

#: Never answered by this backend, even for a person carrying the stale ``Permission`` row.
#: That right comes from a current owner affiliation and nothing else
#: (``fairdm/core/permissions.py``), and Django ORs every backend's answer together, so
#: no later backend can veto a wrongly granted yes here.
_EXCLUDED_PERMISSIONS = ("contributors.manage_organization", "manage_organization")


class PortalRolePermissionBackend(BaseBackend):
    """Derives an object-level answer from a person's membership in a shipped portal role.

    Registered in ``AUTHENTICATION_BACKENDS`` after the existing backends
    (``fairdm/conf/settings/auth.py``). Writes no per-record row.

    Extends ``BaseBackend`` for its no-op ``authenticate``/``get_user``, because
    ``django.contrib.auth.authenticate()`` introspects every configured backend's
    ``authenticate`` signature, not only the one that handles a given credential.
    """

    def has_perm(self, user_obj, perm, obj=None):
        """Answer object-level questions for permissions held through a shipped portal role."""
        # The model-level question (`obj is None`) is never answered here; asking it of
        # `user_obj` would recurse back into this backend.
        if obj is None:
            return False
        if not user_obj.is_active:
            return False
        if perm in _EXCLUDED_PERMISSIONS:
            return False
        # Roles declare `app_label.codename`; a bare codename (guardian's convention) can
        # never match one, so answer False rather than fail on the split below.
        if "." not in perm:
            return False
        app_label, codename = perm.split(".", 1)
        return user_obj.groups.filter(
            name__in=PortalRoles.shipped_names(),
            permissions__content_type__app_label=app_label,
            permissions__codename=codename,
        ).exists()
