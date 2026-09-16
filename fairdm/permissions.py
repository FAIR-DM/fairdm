"""The object-level permission backend that makes a portal role's rights real.

A role's permissions are declared at the model level (``fairdm/portal_roles.py``), but
``ModelBackend.has_perm`` answers ``False`` for every object-level question
(``django/contrib/auth/backends.py``): a Data Curator holding ``change_dataset`` cannot in
fact change a dataset until something derives the object-level answer from it. This backend
is that derivation, and it is deliberately narrow: only a permission held through membership
of one of the four shipped portal roles (``fairdm/portal_roles.py``) confers the object-level
answer. A permission granted straight to a person, or held through a group the portal made up
itself, answers exactly as it did before this feature existed - an earlier feature (D14 in a
different specification) already refused Update, Delete and Descriptions to a person holding
only a model-level grant on a private record, on purpose, because a page that relies on
inheriting a visibility rule is not guarded at all (D20). Widening this backend to every
model-level grant reopened that hole; narrowing it to the four roles closes it again.
"""

from django.contrib.auth.backends import BaseBackend

from fairdm.portal_roles import PortalRoles

#: Never answered by this backend, even for a person carrying the stale ``Permission`` row
#: (D14). That right comes from a current owner affiliation and from nothing else
#: (``fairdm/core/permissions.py:44-53``), and Django ORs every backend's answer together, so
#: no later backend can veto a wrongly granted yes here.
_EXCLUDED_PERMISSIONS = ("contributors.manage_organization", "manage_organization")


class PortalRolePermissionBackend(BaseBackend):
    """Derives an object-level answer from a person's membership in a shipped portal role.

    Registered in ``AUTHENTICATION_BACKENDS`` after the existing backends
    (``fairdm/conf/settings/auth.py``). Writes no per-record row.

    Extends ``BaseBackend`` for its no-op ``authenticate``/``get_user`` - a permission-only
    backend that supplies neither still has to answer to them, because
    ``django.contrib.auth.authenticate()`` introspects every configured backend's
    ``authenticate`` signature before calling any of them, not only the one that ends up
    handling a given credential.
    """

    def has_perm(self, user_obj, perm, obj=None):
        # `obj is None` is the model-level question, which this backend never answers -
        # asking `user_obj.has_perm(perm)` below would otherwise recurse back into this
        # backend through Django's own backend chain (research R2).
        if obj is None:
            return False
        if not user_obj.is_active:
            return False
        if perm in _EXCLUDED_PERMISSIONS:
            return False
        app_label, codename = perm.split(".", 1)
        return user_obj.groups.filter(
            name__in=PortalRoles.shipped_names(),
            permissions__content_type__app_label=app_label,
            permissions__codename=codename,
        ).exists()
