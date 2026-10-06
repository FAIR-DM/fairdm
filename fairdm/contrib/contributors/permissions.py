"""Permission backends that derive rights from affiliations and from contribution levels."""

from django.contrib.auth.backends import BaseBackend

from fairdm.core.permissions import PolymorphicObjectPermissionBackend

from .access import RecordAccess


class OrganizationPermissionBackend(PolymorphicObjectPermissionBackend):
    """Derive ``manage_organization`` from a current OWNER affiliation instead of stored grants.

    ``user.has_perm("contributors.manage_organization", org)`` is true for an active account
    with a current OWNER affiliation to the organisation (``AffiliationQuerySet.owners()``) and
    for superusers. A deactivated account is refused, and a stored guardian grant of this
    permission is never honoured.

    Attributes:
        supports_object_permissions: Object-level permissions are handled.
        supports_anonymous_user: Anonymous users are passed in, and refused for organisations.

    Example:
        Add it to ``AUTHENTICATION_BACKENDS``::

            AUTHENTICATION_BACKENDS = [
                "django.contrib.auth.backends.ModelBackend",
                "fairdm.contrib.contributors.permissions.OrganizationPermissionBackend",
            ]
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """Derive ``manage_organization`` on organisations, and defer everything else to the parent."""
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        if not user_obj.is_authenticated:
            return False

        # Django grants as soon as one backend allows, so this backend must refuse deactivated users itself.
        if not user_obj.is_active:
            return False

        from fairdm.contrib.contributors.models import Affiliation, Organization

        if not isinstance(obj, Organization):
            return super().has_perm(user_obj, perm, obj)

        if perm not in ("contributors.manage_organization", "manage_organization"):
            return super().has_perm(user_obj, perm, obj)

        # Not delegated to the parent, which would also honour a stale stored guardian grant of this permission.
        if user_obj.is_superuser:
            return True

        return (
            Affiliation.objects.owners()
            .filter(
                person=user_obj,
                organization=obj,
            )
            .exists()
        )


class RecordLevelBackend(BaseBackend):
    """Answer every object-level question about a project, dataset, sample or measurement.

    The answer is the level the user holds on the record, or on a record above it, set against the
    level the permission needs (``REQUIRED_LEVEL``). It answers only for core records of any
    registered type, and only for object-level questions. For anything else it returns False and
    the other backends answer. Rows that django-guardian stores for a core record grant nothing.

    Extends ``BaseBackend`` for its no-op ``authenticate`` and ``get_user``, because
    ``django.contrib.auth.authenticate()`` introspects every configured backend.

    Attributes:
        supports_object_permissions: Object-level permissions are handled.
        supports_anonymous_user: Anonymous users are passed in, and refused.

    Example:
        Add it to ``AUTHENTICATION_BACKENDS``::

            AUTHENTICATION_BACKENDS = [
                "django.contrib.auth.backends.ModelBackend",
                "fairdm.contrib.contributors.permissions.RecordLevelBackend",
            ]
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """Grant a permission on a core record when the user's level on it is high enough.

        Args:
            user_obj: The user, or an anonymous user for a visitor.
            perm: The permission, with or without its app label.
            obj: The record asked about.

        Returns:
            True when the user is active and holds the level the permission needs. False for an
            inactive user, a permission the table does not know, and any object that is not a
            core record.
        """
        if obj is None or not RecordAccess.is_core_record(obj):
            return False
        access = RecordAccess(obj)
        needed = access.required_level(perm)
        if needed is None:
            return False
        level = access.level_of(user_obj)
        return level is not None and level >= needed
