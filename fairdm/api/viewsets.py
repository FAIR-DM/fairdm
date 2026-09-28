"""API viewsets and discovery views.

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

import contextlib
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from fairdm.api.serializers import (
    BaseMeasurementSerializer,
    BaseSampleSerializer,
    _validate_measurement_serializer,
    _validate_sample_serializer,
    build_model_serializer,
)
from fairdm.contrib.contributors.models import Contributor
from fairdm.core.models import Dataset, Measurement, Project, Sample


class BaseViewSet(ModelViewSet):
    """Internal base class — see generated subclasses for API documentation.

    Portal developers: use :func:`generate_viewset` or subclass the per-model
    viewsets that appear in the browsable API at ``/api/v1/``.
    """

    lookup_field = "uuid"

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """Require an authenticated user before saving."""
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to create objects.")
        serializer.save()

    def perform_update(self, serializer: serializers.BaseSerializer) -> None:
        """Require an authenticated user before saving."""
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to update objects.")
        serializer.save()

    def perform_destroy(self, instance) -> None:
        """Require an authenticated user before deleting."""
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to delete objects.")
        instance.delete()


class ProjectViewSet(BaseViewSet):
    """Research projects registered in the portal.

    Projects are the top-level organizational unit containing datasets, samples,
    and measurements. Use this endpoint to browse, create, and manage projects
    you have permission to access.
    """

    @property
    def queryset(self):
        """Return all projects."""
        return Project.objects.all()

    def get_queryset(self):
        """Return all projects."""
        return Project.objects.all()

    def get_serializer_class(self):
        """Build the project serializer once and reuse it."""
        if hasattr(self, "_serializer_class"):
            return self._serializer_class
        self._serializer_class = build_model_serializer(
            Project,
            ["uuid", "name", "status", "visibility", "added", "modified"],
            view_name="api:project-detail",
        )
        return self._serializer_class

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """Save a new project, recording the request user as its creator."""
        # `created_by` is set in the same save, not a second
        # write that re-fires signals.
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to create objects.")
        serializer.save(created_by=self.request.user)


class DatasetViewSet(BaseViewSet):
    """Datasets within research projects.

    Each dataset contains samples and associated measurements. Use this endpoint
    to query, add, and manage datasets you have permission to access.
    """

    @property
    def queryset(self):
        """Return all datasets, including private ones the visibility filter admits."""
        # `all_objects`, not `objects`: the default manager would hide a private
        # dataset from a user who holds `view_dataset` before the filter can admit it.
        return Dataset.all_objects.all()

    def get_queryset(self):
        """Return all datasets, including private ones the visibility filter admits."""
        return Dataset.all_objects.all()

    def get_serializer_class(self):
        """Build the dataset serializer once and reuse it."""
        if hasattr(self, "_serializer_class"):
            return self._serializer_class
        self._serializer_class = build_model_serializer(
            Dataset,
            ["uuid", "name", "visibility", "added", "modified"],
            view_name="api:dataset-detail",
        )
        return self._serializer_class

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """Save a new dataset, recording the request user as its creator."""
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to create objects.")
        serializer.save(created_by=self.request.user)


class ContributorViewSet(ReadOnlyModelViewSet):
    """People and organizations that contribute to research projects.

    Contributor profiles are publicly accessible (read-only). Use this endpoint
    to look up individuals and institutions associated with portal data.
    """

    lookup_field = "uuid"

    @property
    def queryset(self):
        """Return all contributors."""
        return Contributor.objects.all()

    def get_queryset(self):
        """Return all contributors."""
        return Contributor.objects.all()

    def get_serializer_class(self):
        """Build the contributor serializer once and reuse it."""
        if hasattr(self, "_serializer_class"):
            return self._serializer_class
        self._serializer_class = build_model_serializer(
            Contributor,
            ["uuid", "name"],
            view_name="api:contributor-detail",
        )
        return self._serializer_class


def generate_viewset(config: Any, base_class: type = BaseViewSet) -> type:
    """Generate a :class:`ModelViewSet` subclass from a registry config.

    The serializer is resolved in this order:

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

    if config.serializer_class is not None:
        serializer_cls = config._get_class(config.serializer_class)
        if issubclass(model, Sample):
            _validate_sample_serializer(serializer_cls)
        elif issubclass(model, Measurement):
            _validate_measurement_serializer(serializer_cls)
    else:
        fields: list[str] = list(config.serializer_fields or config.fields or [])
        if not fields:
            # Same default-field rule every generated component uses.
            from fairdm.utils.inspection import FieldInspector

            fields = FieldInspector(model).get_default_fields()
        else:
            from fairdm.api.serializers import _flatten_fields

            fields = _flatten_fields(fields)

        slug = _model_to_slug(model)
        if hasattr(model, "sample_ptr"):
            view_name = f"api:samples-{slug}-detail"
        elif hasattr(model, "measurement_ptr"):
            view_name = f"api:measurements-{slug}-detail"
        else:
            view_name = f"api:{model._meta.model_name}-detail"

        if issubclass(model, Sample):
            ser_base_class = BaseSampleSerializer
        elif issubclass(model, Measurement):
            ser_base_class = BaseMeasurementSerializer
        else:
            ser_base_class = None

        serializer_cls = build_model_serializer(
            model, fields, view_name=view_name, base_class=ser_base_class
        )

    # Via the accessor so a configuration overriding get_filterset_class() is honoured.
    filterset_class = None
    with contextlib.suppress(Exception):
        filterset_class = config.get_filterset_class()

    _model = model

    class _GeneratedViewSet(base_class):
        pass

    _GeneratedViewSet.__name__ = f"{model_name}ViewSet"
    _GeneratedViewSet.__qualname__ = f"{model_name}ViewSet"
    _GeneratedViewSet.serializer_class = serializer_cls
    _GeneratedViewSet.queryset = _model.objects.all()

    if filterset_class is not None:
        _GeneratedViewSet.filterset_class = filterset_class

    # drf-spectacular reads this as the operation description, so it is not
    # BaseViewSet's docstring.
    description: str = ""
    if getattr(config, "description", None):
        description = config.description
    elif getattr(config, "metadata", None) and getattr(
        config.metadata, "description", None
    ):
        description = config.metadata.description
    elif model.__doc__:
        description = model.__doc__
    if not description:
        description = f"Endpoints for managing {model._meta.verbose_name_plural}."
    _GeneratedViewSet.__doc__ = description

    return _GeneratedViewSet


def _model_to_slug(model) -> str:
    """Derive a URL-safe kebab-case slug from ``verbose_name_plural``.

    Portal developers control the slug through the model's ``verbose_name_plural``.
    Renaming it changes the URL prefix and basename of that model's API endpoints,
    which is a breaking change for API consumers.

    Args:
        model: The model class to derive the slug from.

    Returns:
        The lowercased plural name with spaces replaced by hyphens, for example
        ``"rock-samples"`` for ``verbose_name_plural="rock samples"``.
    """
    return str(model._meta.verbose_name_plural).lower().replace(" ", "-")


class _BaseDiscoveryView(APIView):
    """Shared base for sample/measurement discovery catalog views."""

    permission_classes: list = []
    registry_attr: str = ""
    url_prefix: str = ""

    def get(self, request: Request) -> Response:
        """List every registered type with its endpoint, fields and record count."""
        from fairdm.registry import registry

        types = []
        for model in getattr(registry, self.registry_attr):
            config = registry.get_for_model(model)
            slug = _model_to_slug(model)
            endpoint = f"{request.scheme}://{request.get_host()}/api/v1/{self.url_prefix}/{slug}/"

            # Anonymous users are counted on public records only.
            try:
                if request.user and request.user.is_authenticated:
                    count = model.objects.count()
                else:
                    from fairdm.utils.choices import Visibility

                    # Samples and measurements inherit visibility from their dataset.
                    if hasattr(model, "visibility"):
                        count = model.objects.filter(
                            visibility=Visibility.PUBLIC
                        ).count()
                    else:
                        count = model.objects.filter(
                            dataset__visibility=Visibility.PUBLIC
                        ).count()
            except Exception:
                count = 0

            fields = list(config.fields or [])
            filterable = list(
                getattr(config, "filter_fields", None)
                or getattr(config, "filterset_fields", None)
                or []
            )

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
