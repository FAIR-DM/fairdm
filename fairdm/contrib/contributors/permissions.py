"""Permission backend that derives organisation management rights from affiliations."""

from fairdm.core.permissions import PolymorphicObjectPermissionBackend


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
