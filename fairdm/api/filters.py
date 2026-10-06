"""FairDM API filter backends."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from rest_framework.filters import BaseFilterBackend

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
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
    - Records the user holds at least the view level on, directly or from the dataset or
      project above, are also included. Rows that django-guardian stores for a project, dataset,
      sample or measurement grant nothing.
    - For any other model, records where the user holds a stored guardian 'view' permission.

    Both sets are combined in one query to avoid N+1 queries.

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
            model = queryset.model
            core = getattr(model, "type_of", None) or model
            if RecordAccess.is_core_model(core):
                manager = getattr(core, "all_objects", core.objects)
                held = manager.accessible_to(request.user, ContributionLevel.VIEW)
                permitted_qs = queryset.filter(pk__in=held.values("pk"))
            else:
                view_perm = f"{model._meta.app_label}.view_{model._meta.model_name}"
                permitted_qs = get_objects_for_user(request.user, view_perm, queryset)
            return (public_qs | permitted_qs).distinct()

        return queryset.filter(**public_filter)
