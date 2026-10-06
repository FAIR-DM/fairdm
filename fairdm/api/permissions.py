"""FairDM API permission classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

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
    - The serializers of projects, datasets, samples and measurements list the creator at the
      manage level on create.
    - Calls ``user.has_perm()`` which routes through ModelBackend, guardian
      ``ObjectPermissionBackend``, and any custom permission backends. For a project, dataset,
      sample or measurement the answer is the user's contribution level
      (``RecordLevelBackend``).
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    authenticated_users_only = False

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Allow reads to anyone and writes to any signed-in user."""
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Raised, not returned False, so DRF answers 401 whatever the authenticator.
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        # Model-level permissions are skipped on purpose: access is decided per
        # object by guardian, in has_object_permission.
        return True

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        """Return 404 (not 403) when user lacks permission on an existing object."""
        if request.method in ("GET", "HEAD", "OPTIONS"):
            from fairdm.utils.choices import Visibility

            visibility = getattr(obj, "visibility", None)
            if visibility is not None and visibility == Visibility.PUBLIC:
                return True
            # Sample and Measurement inherit visibility from their dataset.
            parent = getattr(obj, "dataset", None)
            if (
                parent is not None
                and getattr(parent, "visibility", None) == Visibility.PUBLIC
            ):
                return True
            if not request.user or not request.user.is_authenticated:
                raise NotFound()
            if not super().has_object_permission(request, view, obj):
                raise NotFound()
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        from fairdm.utils.choices import Visibility

        # Visibility decides between "public + no write perm" (403) and "private +
        # no perm at all" (404).
        visibility = getattr(obj, "visibility", None)
        parent_vis = getattr(getattr(obj, "dataset", None), "visibility", None)
        is_publicly_visible = (
            visibility is not None and visibility == Visibility.PUBLIC
        ) or (parent_vis is not None and parent_vis == Visibility.PUBLIC)

        # super().has_object_permission() raises Http404 when the user lacks both
        # write and read permission, which would hide the 403 a public object needs.
        # `method` is only None before the handler runs, so the cast is safe.
        write_perms = self.get_required_object_permissions(
            cast(str, request.method), obj.__class__
        )
        has_perm = all(request.user.has_perm(perm, obj) for perm in write_perms)

        if not has_perm and not is_publicly_visible:
            # A private object the user cannot even view must not be disclosed.
            view_perms = self.get_required_object_permissions("GET", obj.__class__)
            can_view = all(request.user.has_perm(perm, obj) for perm in view_perms)
            if not can_view:
                raise NotFound()
        return has_perm
