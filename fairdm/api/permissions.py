"""FairDM API permission classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.exceptions import NotFound
from rest_framework.permissions import DjangoObjectPermissions

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class FairDMObjectPermissions(DjangoObjectPermissions):
    """Object-level permission class for FairDM API endpoints.

    Extends ``DjangoObjectPermissions`` to:

    1. Add ``view`` permissions to ``perms_map`` (required for guardian integration).
    2. Return HTTP 404 (not 403) for objects the user cannot view — non-disclosure.
    3. Allow unauthenticated read access for public data.
    4. Require authentication for all write operations.

    Integration:
    - :class:`fairdm.api.filters.FairDMVisibilityFilter` handles queryset-level list
      filtering so private objects never appear in list results.
    - ``ObjectPermissionsAssignmentMixin`` in serializers assigns permissions on
      create/update.
    - Calls ``user.has_perm()`` which routes through ModelBackend, guardian
      ``ObjectPermissionBackend``, and any custom permission backends
      (e.g. ``SamplePermissionBackend``, ``MeasurementPermissionBackend``).
    """

    # Extend the default perms_map to include view permissions for safe methods
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    # Allow unauthenticated access for read operations
    authenticated_users_only = False

    def has_permission(self, request: "Request", view: "APIView") -> bool:
        # Allow read operations without authentication
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Write operations require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        return super().has_permission(request, view)

    def has_object_permission(self, request: "Request", view: "APIView", obj) -> bool:
        """Return 404 (not 403) when user lacks permission on an existing object."""
        # Allow read access to any object; list-level filtering (FairDMVisibilityFilter)
        # ensures private objects never appear in list results.
        if request.method in ("GET", "HEAD", "OPTIONS"):
            # For public objects, allow access without checking guardian
            from fairdm.utils.choices import Visibility

            visibility = getattr(obj, "visibility", None)
            # Direct visibility on Project/Dataset
            if visibility is not None and visibility == Visibility.PUBLIC:
                return True
            # Cascaded visibility via parent Dataset (Sample, Measurement)
            parent = getattr(obj, "dataset", None)
            if parent is not None and getattr(parent, "visibility", None) == Visibility.PUBLIC:
                return True
            # For private objects, check object-level permission
            if not request.user or not request.user.is_authenticated:
                raise NotFound()
            if not super().has_object_permission(request, view, obj):
                raise NotFound()
            return True

        # Write operations: require authentication (already checked in has_permission)
        if not request.user or not request.user.is_authenticated:
            return False

        # Check object-level write permission
        has_perm = super().has_object_permission(request, view, obj)
        if not has_perm:
            # Non-disclosure: raise 404 only if user can't VIEW the object
            # (they shouldn't know it exists). If they can view it, return 403.
            view_perms = self.get_required_object_permissions("GET", obj.__class__)
            can_view = all(
                request.user.has_perm(perm, obj) for perm in view_perms
            )
            if not can_view:
                raise NotFound()
        return has_perm
