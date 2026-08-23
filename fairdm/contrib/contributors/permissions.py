"""
Custom permission backends for Organization model.

Provides derived permissions based on Affiliation relationships.
"""

from fairdm.core.permissions import PolymorphicObjectPermissionBackend


class OrganizationPermissionBackend(PolymorphicObjectPermissionBackend):
    """
    Custom permission backend that derives manage_organization from Affiliation.type.

    This backend extends django-guardian's ObjectPermissionBackend to support:
    1. Derived manage_organization permission based on OWNER affiliation (no guardian rows)
    2. Natural support for multiple owners (multiple OWNER affiliations)

    Permission Logic:
    - user.has_perm("contributors.manage_organization", org) returns True if:
      - The account is active, and has a *current* Affiliation with organization
        where type=OWNER (AffiliationQuerySet.owners() - end_date IS NULL)
      - OR user is a superuser
    - A deactivated account is refused whatever its affiliation says.
    - A stored guardian object-level grant of manage_organization is never
      honoured, even if a stale Permission row for it exists in the database
      (see the comment in has_perm below).

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
        1. Whether the user is a superuser (checked explicitly, not via the parent
           backend - see the comment at that check for why)
        2. Derived permission from a *current* OWNER Affiliation

        A stored guardian object-level grant is deliberately never consulted for
        this permission (Defect B): manage_organization was declared in one
        migration, its guardian rows removed in another, and the declaration
        dropped from Organization.Meta.permissions in a third, but Django does
        not delete the underlying Permission row when a permission leaves a
        model's options. A database migrated forward from before that removal
        can still carry the row, which means a guardian UserObjectPermission or
        GroupObjectPermission row can still be written against it - and calling
        the parent backend here would honour one if it found it. The derived
        affiliation rule and superuser status are the only two sources of this
        right, by design, so this method never delegates to the parent for a
        manage_organization decision.

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

        # A deactivated account holds nothing. Django grants a permission as soon as any
        # one backend allows it, and every other backend in the chain already refuses a
        # deactivated user, so refusing here is what makes deactivation mean anything
        # for an organization.
        if not user_obj.is_active:
            return False

        # Import here to avoid circular imports
        from fairdm.contrib.contributors.models import Affiliation, Organization

        # Only handle Organization objects
        if not isinstance(obj, Organization):
            return super().has_perm(user_obj, perm, obj)

        # Only derive manage_organization permission (handle both formats: with and without app label)
        if perm not in ("contributors.manage_organization", "manage_organization"):
            return super().has_perm(user_obj, perm, obj)

        # Checked explicitly rather than via super().has_perm(...): the parent chain
        # ends in guardian's ObjectPermissionChecker, which grants superusers True but
        # would *also* honour a stored guardian object-level grant if one exists for
        # this permission - and for manage_organization specifically, a stored grant
        # must never confer the right (Defect B, see the docstring above). Staff who
        # are not superusers get no shortcut here (D10).
        if user_obj.is_superuser:
            return True

        # Derive permission from a current OWNER Affiliation only - one whose
        # end_date has not been set. AffiliationQuerySet.owners() is the single
        # place that rule is expressed (Defect A).
        return (
            Affiliation.objects.owners()
            .filter(
                person=user_obj,
                organization=obj,
            )
            .exists()
        )
