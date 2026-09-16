"""The object-level permission backend that makes a portal role's rights real.

A role's permissions are declared at the model level (``fairdm/portal_roles.py``), but
``ModelBackend.has_perm`` answers ``False`` for every object-level question
(``django/contrib/auth/backends.py``): a Data Curator holding ``change_dataset`` cannot in
fact change a dataset until something derives the object-level answer from it. This backend
is that derivation, and it is not specific to portal roles - a permission granted directly to
a person behaves the same way, which is the rule Django's own admin already follows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.db.models import Model

#: Never answered by this backend, even for a person carrying the stale ``Permission`` row
#: (D14). That right comes from a current owner affiliation and from nothing else
#: (``fairdm/core/permissions.py:44-53``), and Django ORs every backend's answer together, so
#: no later backend can veto a wrongly granted yes here.
_EXCLUDED_PERMISSIONS = ("contributors.manage_organization", "manage_organization")


class PortalRolePermissionBackend:
    """Derives an object-level answer from the model-level permissions a person holds.

    Registered in ``AUTHENTICATION_BACKENDS`` after the existing backends
    (``fairdm/conf/settings/auth.py``). Writes no per-record row.
    """

    def has_perm(self, user_obj: AbstractBaseUser, perm: str, obj: Model | None = None) -> bool:
        # `obj is None` is the model-level question, which this backend never answers -
        # asking `user_obj.has_perm(perm)` below would otherwise recurse back into this
        # backend through Django's own backend chain (research R2).
        if obj is None:
            return False
        if not user_obj.is_active:
            return False
        if perm in _EXCLUDED_PERMISSIONS:
            return False
        return user_obj.has_perm(perm)
