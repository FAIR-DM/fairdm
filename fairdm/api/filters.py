"""FairDM API filter backends."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from rest_framework.filters import BaseFilterBackend

from fairdm.core.utils import get_objects_for_user

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


def _get_public_filter(model) -> dict:
    """Return a queryset filter dict that selects publicly-visible records.

    Project and Dataset carry an integer ``visibility`` field. Sample and
    Measurement have none, so their visibility cascades from the parent Dataset.

    Args:
        model: The model class to build the filter for.

    Returns:
        A dict to pass to ``queryset.filter(**...)``, or an empty dict when the
        model has no known visibility field and filtering should be skipped.
    """
    from django.db.models import IntegerField

    with contextlib.suppress(Exception):
        field = model._meta.get_field("visibility")
        if isinstance(field, IntegerField):
            from fairdm.utils.choices import Visibility

            return {"visibility": Visibility.PUBLIC}

    with contextlib.suppress(Exception):
        model._meta.get_field("dataset")
        from fairdm.utils.choices import Visibility

        return {"dataset__visibility": Visibility.PUBLIC}

    return {}


class FairDMVisibilityFilter(BaseFilterBackend):
    """Queryset-level visibility filter for FairDM API list endpoints.

    Restricts list querysets to objects the requesting user can see:

    - Records that are publicly visible (via ``visibility=PUBLIC`` or cascaded
      through ``dataset__visibility=PUBLIC``) are always included.
    - Records where the user has an explicit guardian 'view' permission are also
      included.

    Both sets are combined via queryset union to avoid N+1 queries.

    For models with no known visibility mechanism (such as Contributor), the
    filter returns the full queryset, making all records publicly accessible.
    Override ``filter_queryset()`` in a viewset subclass for stricter filtering.

    This replaces ``ObjectPermissionsFilter`` from ``djangorestframework-guardian``,
    which requires explicit guardian entries for *all* objects and so hides
    publicly-visible records that have no guardian permission rows.
    """

    def filter_queryset(self, request: Request, queryset, view: APIView):
        """Limit the queryset to public records plus those the user may view."""
        public_filter = _get_public_filter(queryset.model)

        if not public_filter:
            return queryset

        if request.user and request.user.is_authenticated:
            public_qs = queryset.filter(**public_filter)
            view_perm = f"{queryset.model._meta.app_label}.view_{queryset.model._meta.model_name}"
            permitted_qs = get_objects_for_user(
                request.user,
                view_perm,
                queryset,
            )
            return (public_qs | permitted_qs).distinct()

        return queryset.filter(**public_filter)
