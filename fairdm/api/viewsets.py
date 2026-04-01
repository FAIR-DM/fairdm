"""FairDM API ViewSets and discovery views.

This module provides:

- :class:`BaseViewSet` — the base class for all FairDM API viewsets.
- :class:`ProjectViewSet`, :class:`DatasetViewSet` — full CRUD viewsets for
  core models.
- :class:`ContributorViewSet` — read-only viewset for contributor profiles.
- :func:`generate_viewset` — factory that creates a ``ModelViewSet`` subclass
  from a registry :class:`~fairdm.registry.ModelConfiguration`.
- :class:`SampleDiscoveryView`, :class:`MeasurementDiscoveryView` — catalog
  views that list all registered Sample/Measurement types.
"""

from __future__ import annotations

import re
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from fairdm.api.serializers import build_model_serializer


# ---------------------------------------------------------------------------
# Base viewset
# ---------------------------------------------------------------------------


class BaseViewSet(ModelViewSet):
    """Base viewset for all FairDM API resource endpoints.

    Features:
    - ``lookup_field = "uuid"`` — all core models use a ``uuid`` field.
    - ``get_queryset()`` returns the model's default queryset; the
      :class:`~fairdm.api.filters.FairDMVisibilityFilter` backend then restricts
      results to objects the requesting user can see.
    - ``get_serializer_class()`` resolves the serializer from the viewset's own
      ``serializer_class`` attribute (set by :func:`generate_viewset`).
    - ``perform_create/update/destroy()`` enforce authentication as a last line
      of defence (the permission class already handles this, but explicit checks
      make the intent clear).
    """

    lookup_field = "uuid"

    def perform_create(self, serializer: serializers.Serializer) -> None:
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to create objects.")
        serializer.save()

    def perform_update(self, serializer: serializers.Serializer) -> None:
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to update objects.")
        serializer.save()

    def perform_destroy(self, instance) -> None:
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to delete objects.")
        instance.delete()


# ---------------------------------------------------------------------------
# Core model viewsets
# ---------------------------------------------------------------------------


class ProjectViewSet(BaseViewSet):
    """Full CRUD viewset for :class:`~fairdm.core.project.models.Project`.

    Endpoints::

        GET  /api/v1/projects/          — list (public & permitted)
        POST /api/v1/projects/          — create (authenticated)
        GET  /api/v1/projects/{uuid}/   — detail
        PUT  /api/v1/projects/{uuid}/   — full update (authorized)
        PATCH /api/v1/projects/{uuid}/  — partial update (authorized)
        DELETE /api/v1/projects/{uuid}/ — delete (authorized)
    """

    @property
    def queryset(self):
        from fairdm.core.project.models import Project

        return Project.objects.all()

    def get_queryset(self):
        from fairdm.core.project.models import Project

        return Project.objects.all()

    def get_serializer_class(self):
        from fairdm.core.project.models import Project

        if hasattr(self, "_serializer_class"):
            return self._serializer_class
        self._serializer_class = build_model_serializer(
            Project,
            ["uuid", "name", "status", "visibility", "added", "modified"],
            view_name="project-detail",
        )
        return self._serializer_class


class DatasetViewSet(BaseViewSet):
    """Full CRUD viewset for :class:`~fairdm.core.dataset.models.Dataset`.

    Endpoints::

        GET  /api/v1/datasets/           — list (public & permitted)
        POST /api/v1/datasets/           — create (authenticated)
        GET  /api/v1/datasets/{uuid}/    — detail
        PATCH /api/v1/datasets/{uuid}/   — partial update (authorized)
        DELETE /api/v1/datasets/{uuid}/  — delete (authorized)
    """

    @property
    def queryset(self):
        from fairdm.core.dataset.models import Dataset

        return Dataset.objects.all()

    def get_queryset(self):
        from fairdm.core.dataset.models import Dataset

        return Dataset.objects.all()

    def get_serializer_class(self):
        from fairdm.core.dataset.models import Dataset

        if hasattr(self, "_serializer_class"):
            return self._serializer_class
        self._serializer_class = build_model_serializer(
            Dataset,
            ["uuid", "name", "visibility", "added", "modified"],
            view_name="dataset-detail",
        )
        return self._serializer_class


class ContributorViewSet(ReadOnlyModelViewSet):
    """Read-only viewset for :class:`~fairdm.contrib.contributors.models.Contributor`.

    All contributor profiles are publicly accessible (GET only).

    Endpoints::

        GET /api/v1/contributors/          — list
        GET /api/v1/contributors/{uuid}/   — detail
    """

    lookup_field = "uuid"

    @property
    def queryset(self):
        from fairdm.contrib.contributors.models import Contributor

        return Contributor.objects.all()

    def get_queryset(self):
        from fairdm.contrib.contributors.models import Contributor

        return Contributor.objects.all()

    def get_serializer_class(self):
        from fairdm.contrib.contributors.models import Contributor

        if hasattr(self, "_serializer_class"):
            return self._serializer_class
        self._serializer_class = build_model_serializer(
            Contributor,
            ["uuid", "name"],
            view_name="contributor-detail",
        )
        return self._serializer_class


# ---------------------------------------------------------------------------
# Viewset factory
# ---------------------------------------------------------------------------


def generate_viewset(config: Any, base_class: type = BaseViewSet) -> type:
    """Generate a :class:`ModelViewSet` subclass from a registry config.

    Three-tier serializer resolution (per spec FR-016/US6):

    1. ``config.serializer_class`` set → use it directly (custom serializer).
    2. ``config.serializer_fields`` set → auto-generate serializer with those fields.
    3. Only ``config.fields`` set → auto-generate serializer with those fields.
    4. Nothing set → auto-generate from model field inspection.

    Args:
        config: A :class:`~fairdm.registry.ModelConfiguration` instance from the
            FairDM registry.
        base_class: Base viewset class (default: :class:`BaseViewSet`).

    Returns:
        A ``ModelViewSet`` subclass configured for ``config.model``.
    """
    model = config.model
    model_name = model.__name__

    # Determine serializer using three-tier resolution
    if config.serializer_class is not None:
        # Tier 3: explicit custom serializer_class
        serializer_cls = config._get_class(config.serializer_class)
    else:
        # Tier 1/2: serializer_fields overrides fields, both auto-generate
        fields: list[str] = list(config.serializer_fields or config.fields or [])
        if not fields:
            # Fallback: derive safe fields from model inspection
            from fairdm.registry.factories import FieldInspector

            inspector = FieldInspector(model)
            fields = inspector.get_safe_fields()
        else:
            # Flatten any grouped tuples used for form layout
            from fairdm.api.serializers import _flatten_fields

            fields = _flatten_fields(fields)

        # Try to determine the DRF view_name for the URL field
        slug = _model_to_slug(model)
        if hasattr(model, "sample_ptr"):
            view_name = f"samples-{slug}-detail"
        elif hasattr(model, "measurement_ptr"):
            view_name = f"measurements-{slug}-detail"
        else:
            view_name = f"{model._meta.model_name}-detail"

        serializer_cls = build_model_serializer(model, fields, view_name=view_name)

    # Determine filterset
    filterset_class = None
    if config.filterset is not None and not isinstance(config.filterset, type) or (
        isinstance(config.filterset, type) and config.filterset is not type
    ):
        try:
            filterset_class = config.filterset
        except Exception:
            pass

    # Build queryset attribute (evaluated lazily via lambda to avoid import order issues)
    _model = model

    class _GeneratedViewSet(base_class):
        pass

    _GeneratedViewSet.__name__ = f"{model_name}ViewSet"
    _GeneratedViewSet.__qualname__ = f"{model_name}ViewSet"
    _GeneratedViewSet.serializer_class = serializer_cls
    _GeneratedViewSet.queryset = _model.objects.all()

    if filterset_class is not None:
        _GeneratedViewSet.filterset_class = filterset_class

    return _GeneratedViewSet


def _model_to_slug(model) -> str:
    """Convert model class name to a URL-safe kebab-case slug.

    Uses the Python class name rather than ``verbose_name_plural`` to
    guarantee stable URLs — renaming a verbose name will never silently
    break existing API clients.

    Example: ``RockSample`` → ``"rock-sample"``,
             ``CustomParentSample`` → ``"custom-parent-sample"``
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "-", model.__name__).lower()


# ---------------------------------------------------------------------------
# Discovery views
# ---------------------------------------------------------------------------


class _BaseDiscoveryView(APIView):
    """Shared base for sample/measurement discovery catalog views."""

    permission_classes: list = []  # Public, no auth required
    registry_attr: str = ""  # "samples" or "measurements"
    url_prefix: str = ""  # "/api/v1/samples/" or "/api/v1/measurements/"

    def get(self, request: Request) -> Response:
        from fairdm.registry import registry

        types = []
        for model in getattr(registry, self.registry_attr):
            config = registry.get_for_model(model)
            slug = _model_to_slug(model)
            endpoint = f"{request.scheme}://{request.get_host()}/api/v1/{self.url_prefix}/{slug}/"

            # Count: public records only for anonymous, all accessible for authenticated
            try:
                if request.user and request.user.is_authenticated:
                    count = model.objects.count()
                else:
                    from fairdm.utils.choices import Visibility

                    # Samples/Measurements cascade visibility via dataset;
                    # fall back to total count if the field is absent
                    if hasattr(model, "visibility"):
                        count = model.objects.filter(visibility=Visibility.PUBLIC).count()
                    else:
                        count = model.objects.filter(dataset__visibility=Visibility.PUBLIC).count()
            except Exception:
                count = 0

            # Gather field metadata
            fields = list(config.fields or [])
            filterable = list(getattr(config, "filter_fields", None) or getattr(config, "filterset_fields", None) or [])

            types.append(
                {
                    "name": model.__name__,
                    "verbose_name": model._meta.verbose_name,
                    "verbose_name_plural": model._meta.verbose_name_plural,
                    "app_label": model._meta.app_label,
                    "endpoint": endpoint,
                    "fields": fields,
                    "filterable_fields": filterable,
                    "count": count,
                }
            )

        return Response({"types": types})


class SampleDiscoveryView(_BaseDiscoveryView):
    """Catalog of all registered Sample types.

    ``GET /api/v1/samples/`` returns a JSON object with a ``types`` list,
    each entry describing a registered Sample subtype.
    """

    registry_attr = "samples"
    url_prefix = "samples"


class MeasurementDiscoveryView(_BaseDiscoveryView):
    """Catalog of all registered Measurement types.

    ``GET /api/v1/measurements/`` returns a JSON object with a ``types`` list,
    each entry describing a registered Measurement subtype.
    """

    registry_attr = "measurements"
    url_prefix = "measurements"
