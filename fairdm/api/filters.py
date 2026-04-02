"""FairDM API filter backends."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from guardian.shortcuts import get_objects_for_user
from rest_framework.filters import BaseFilterBackend

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


def _get_public_filter(model) -> dict:
    """Return a queryset filter dict that selects publicly-visible records.

    FairDM's core models (Project, Dataset) use an integer ``visibility`` field
    with ``Visibility.PUBLIC = 1``.  Sample/Measurement do not have a direct
    visibility field — their visibility cascades from the parent Dataset.

    Returns a dict suitable for passing to ``queryset.filter(**...)``, or an
    empty dict if no known visibility field is found (caller should skip filtering).
    """
    from django.db.models import IntegerField

    # Direct visibility field (Project, Dataset)
    with contextlib.suppress(Exception):
        field = model._meta.get_field("visibility")
        if isinstance(field, IntegerField):
            from fairdm.utils.choices import Visibility

            return {"visibility": Visibility.PUBLIC}

    # Dataset-cascaded visibility (Sample, Measurement)
    with contextlib.suppress(Exception):
        model._meta.get_field("dataset")
        from fairdm.utils.choices import Visibility

        return {"dataset__visibility": Visibility.PUBLIC}

    return {}  # No known visibility field


class FairDMVisibilityFilter(BaseFilterBackend):
    """Queryset-level visibility filter for FairDM API list endpoints.

    Restricts list querysets to objects the requesting user can see:
      - Records that are publicly visible (via ``visibility=PUBLIC`` or cascaded
        through ``dataset__visibility=PUBLIC``) are always included.
      - Records where the user has an explicit guardian 'view' permission are also
        included.

    Both sets are combined via queryset union to avoid N+1 queries.

    For models with no known visibility mechanism (e.g. Contributor), the filter
    short-circuits and returns the full unfiltered queryset, making all records
    publicly accessible. Override ``filter_queryset()`` in a viewset subclass if
    stricter filtering is needed for such models.

    This replaces ``ObjectPermissionsFilter`` from ``djangorestframework-guardian``,
    which requires explicit guardian entries for *all* objects — unsuitable for
    publicly-visible records that have no guardian permission rows at all.
    """

    def filter_queryset(self, request: Request, queryset, view: APIView):
        public_filter = _get_public_filter(queryset.model)

        # No known visibility mechanism: return everything (e.g. Contributor)
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

        # Anonymous users: public records only
        return queryset.filter(**public_filter)
