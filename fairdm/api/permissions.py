"""FairDM API permission classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.exceptions import NotAuthenticated, NotFound
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

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Allow read operations without authentication (object-level visibility
        # filtering via FairDMVisibilityFilter + has_object_permission handles
        # private-object access control for GET requests).
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Write operations require authentication.  Raise NotAuthenticated (not
        # return False) so DRF maps the response to HTTP 401 regardless of which
        # authenticator is configured.
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        # Any authenticated user may attempt a write; object-level permissions
        # (has_object_permission) enforce guardian-based per-object access for
        # PUT/PATCH/DELETE.  We intentionally skip DjangoObjectPermissions'
        # model-level permission check here because FairDM uses guardian object
        # permissions, not Django's model-level permissions, for access control.
        return True

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
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

        from fairdm.utils.choices import Visibility

        # Determine visibility BEFORE the guardian permission check so that we can
        # correctly distinguish "public + no write perm → 403" from
        # "private + no perm at all → 404".
        visibility = getattr(obj, "visibility", None)
        parent_vis = getattr(getattr(obj, "dataset", None), "visibility", None)
        is_publicly_visible = (visibility is not None and visibility == Visibility.PUBLIC) or (
            parent_vis is not None and parent_vis == Visibility.PUBLIC
        )

        # Check object-level write permission directly via guardian.
        # We intentionally bypass super().has_object_permission() here because
        # DjangoObjectPermissions.has_object_permission() itself raises Http404
        # when the user lacks BOTH write AND read permissions — which would suppress
        # the correct 403 we want for publicly-visible objects.
        write_perms = self.get_required_object_permissions(request.method, obj.__class__)
        has_perm = all(request.user.has_perm(perm, obj) for perm in write_perms)

        if not has_perm and not is_publicly_visible:
            # Private object: check if user can at least VIEW it.
            # If not, do not reveal it exists — raise 404 (non-disclosure).
            view_perms = self.get_required_object_permissions("GET", obj.__class__)
            can_view = all(request.user.has_perm(perm, obj) for perm in view_perms)
            if not can_view:
                raise NotFound()
        # Object is visible (public or user has view perm) but user lacks
        # write permission → return False → DRF raises PermissionDenied (403).
        return has_perm
