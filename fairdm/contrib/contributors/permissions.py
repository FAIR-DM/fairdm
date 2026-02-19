"""
Custom permission backends for Organization model.

Provides derived permissions based on Affiliation relationships.
"""

from guardian.backends import ObjectPermissionBackend


class OrganizationPermissionBackend(ObjectPermissionBackend):
    """
    Custom permission backend that derives manage_organization from Affiliation.type.

    This backend extends django-guardian's ObjectPermissionBackend to support:
    1. Derived manage_organization permission based on OWNER affiliation (no guardian rows)
    2. Natural support for multiple owners (multiple OWNER affiliations)

    Permission Logic:
    - user.has_perm("contributors.manage_organization", org) returns True if:
      - User has an Affiliation with organization where type=OWNER
      - OR user is staff/superuser (handled by ModelBackend)

    Usage:
        Add to settings.AUTHENTICATION_BACKENDS:
        ```python
        AUTHENTICATION_BACKENDS = [
            "django.contrib.auth.backends.ModelBackend",
            "fairdm.contrib.contributors.permissions.OrganizationPermissionBackend",
        ]
        ```

    Examples:
        ```python
        # Create OWNER affiliation
        affiliation = Affiliation.objects.create(
            person=user,
            organization=org,
            type=Affiliation.MembershipType.OWNER,
        )

        # Permission is derived automatically
        user.has_perm("contributors.manage_organization", org)  # True

        # Demote to MEMBER
        affiliation.type = Affiliation.MembershipType.MEMBER
        affiliation.save()

        user.has_perm("contributors.manage_organization", org)  # False
        ```

    Benefits:
    - No guardian permission rows to synchronize
    - No cache staleness issues
    - Permission reflects current database state
    - Transaction-safe by design
    - Follows same pattern as SamplePermissionBackend and MeasurementPermissionBackend
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has permission on object.

        For Organization objects with manage_organization permission, checks:
        1. Direct check via parent backend (handles staff/superuser)
        2. Derived permission from OWNER Affiliation

        Args:
            user_obj: User instance
            perm: Permission string (e.g., 'contributors.manage_organization')
            obj: Optional Organization instance

        Returns:
            bool: True if user has permission
        """
        # Let parent backend handle non-Organization objects and global permissions
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        # Check if user is anonymous
        if not user_obj.is_authenticated:
            return False

        # Import here to avoid circular imports
        from fairdm.contrib.contributors.models import Affiliation, Organization

        # Only handle Organization objects
        if not isinstance(obj, Organization):
            return super().has_perm(user_obj, perm, obj)

        # Only derive manage_organization permission (handle both formats: with and without app label)
        if perm not in ("contributors.manage_organization", "manage_organization"):
            return super().has_perm(user_obj, perm, obj)

        # Check if user is staff/superuser (handled by parent ModelBackend)
        if super().has_perm(user_obj, perm, obj):
            return True

        # Derive permission from OWNER Affiliation
        return Affiliation.objects.filter(
            person=user_obj,
            organization=obj,
            type=Affiliation.MembershipType.OWNER,
        ).exists()
