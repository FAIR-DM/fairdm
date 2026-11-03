"""The object-level permission backend that makes a portal role's rights real.

A role's permissions are declared at the model level (``fairdm/portal_roles.py``), but
``ModelBackend.has_perm`` answers ``False`` for every object-level question
(``django/contrib/auth/backends.py``): a Data Curator holding ``change_dataset`` cannot in
fact change a dataset until something derives the object-level answer from it. This backend
is that derivation, and it is deliberately narrow: only a permission held through membership
of one of the four shipped portal roles confers the object-level answer. A permission granted
straight to a person, or held through a group the portal made up itself, answers as before.
A model-level grant outside those roles gives no right on any record, public or private, so
every check that has a record in hand asks the object-level question.
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
        if obj is None or perm in _EXCLUDED_PERMISSIONS:
            return False
        return PortalRoles.reaches_every_record(user_obj, perm)
