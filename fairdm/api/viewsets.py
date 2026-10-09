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
from typing import Any, cast

from django.core.exceptions import FieldDoesNotExist
from django.db.models import (
    Model,
    ProtectedError,
    Q,
    RestrictedError,
    prefetch_related_objects,
)
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from fairdm.api.filters import (
    DatasetFilterSet,
    FairDMFilterBackend,
    FairDMVisibilityFilter,
    SampleFilterSet,
)
from fairdm.api.serializers import (
    CatalogueSerializer,
    ContributorSerializer,
    DatasetSerializer,
    ProjectSerializer,
    _validate_measurement_serializer,
    _validate_sample_serializer,
)
from fairdm.contrib.contributors.models import Contributor, Organization, Person
from fairdm.core.models import Dataset, Measurement, Project, Sample
from fairdm.core.project.models import PublicDatasetsProtect


class DeleteRefused(APIException):
    """A delete the portal refuses for the state the record is in, answered 409 with a reason."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _("This record cannot be deleted in its present state.")
    default_code = "delete_refused"


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
        """Require an authenticated user before deleting, and refuse what the portal refuses.

        Raises:
            PermissionDenied: When the caller is not signed in.
            DeleteRefused: When the record has public datasets or other records depend on it.
                The reason is written here and names no other record, which the caller may not
                be allowed to see.
        """
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required to delete objects.")
        try:
            instance.delete()
        except PublicDatasetsProtect as error:
            raise DeleteRefused(
                _(
                    "This project has public datasets. Make them private or delete them first."
                )
            ) from error
        except (ProtectedError, RestrictedError) as error:
            raise DeleteRefused(
                _("Other records depend on this one. Delete or move them first.")
            ) from error


class ProjectViewSet(BaseViewSet):
    """Research projects registered in the portal.

    Projects are the top-level organizational unit containing datasets, samples,
    and measurements. Use this endpoint to browse, create, and manage projects
    you have permission to access.
    """

    serializer_class = ProjectSerializer
    ordering_fields = ("name", "added", "modified", "status", "uuid")

    def get_queryset(self):
        """Return all projects, with what the serializer reads loaded."""
        return ProjectSerializer.load_related(Project.objects.all())

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

    serializer_class = DatasetSerializer
    ordering_fields = ("name", "added", "modified", "uuid")

    def get_queryset(self):
        """Return all datasets, including private ones the visibility filter admits."""
        # `all_objects`, not `objects`: the default manager would hide a private
        # dataset from a user who holds `view_dataset` before the filter can admit it.
        return DatasetSerializer.load_related(Dataset.all_objects.all())

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
    permission_classes = (AllowAny,)
    serializer_class = ContributorSerializer
    ordering_fields = ("name", "added", "modified", "uuid")

    def get_queryset(self):
        """Return the people and organisations the portal's own lists show.

        Leaves out superusers and the anonymous account, as ``Person.objects.real()`` does.
        """
        hidden = Person.objects.filter(
            Q(is_superuser=True) | Q(email="AnonymousUser")
        ).values("pk")
        return Contributor.objects.exclude(pk__in=hidden).prefetch_related(
            "identifiers"
        )

    def get_serializer(self, instance=None, *args, **kwargs):
        """Load the affiliations and parents of the contributors about to be described.

        A queryset over the base type cannot prefetch what only a person or only an
        organisation has, so this loads them once the real types are known.

        Args:
            instance: The contributor, or the contributors of a list, to describe.
            *args: Passed on to the serializer.
            **kwargs: Passed on to the serializer, including ``many``.

        Returns:
            The serializer, holding contributors that read no further queries.
        """
        if instance is not None:
            records = list(instance) if kwargs.get("many") else [instance]
            prefetch_related_objects(
                [record for record in records if isinstance(record, Person)],
                "affiliations__organization",
            )
            prefetch_related_objects(
                [record for record in records if isinstance(record, Organization)],
                "parent",
            )
            instance = records if kwargs.get("many") else instance
        return super().get_serializer(instance, *args, **kwargs)


def sortable_fields(model, serializer_cls) -> list[str]:
    """List the fields a list may be sorted on: the model's own columns the serializer returns.

    Args:
        model: The model the list serves.
        serializer_cls: The serializer the list uses.

    Returns:
        The names of the stored, non-relational fields among the serializer's fields.
    """
    declared = serializer_cls.Meta.fields
    if declared == "__all__":
        declared = [field.name for field in model._meta.concrete_fields]
    names = []
    for name in declared:
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if field.concrete and not field.is_relation:
            names.append(name)
    return names


def generate_viewset(config: Any, base_class: type = BaseViewSet) -> type:
    """Generate a :class:`ModelViewSet` subclass from a registry config.

    The serializer is whatever ``config.get_serializer_class()`` returns: the class named in the
    registration, or one the registry builds from the configured fields. A sample or measurement
    serializer must build on the base serializer of its kind.

    Args:
        config: A :class:`~fairdm.registry.ModelConfiguration` instance from the
            FairDM registry.
        base_class: Base viewset class (default: :class:`BaseViewSet`).

    Returns:
        A ``ModelViewSet`` subclass configured for ``config.model``.

    Raises:
        ImproperlyConfigured: When the serializer of a sample or measurement type does not
            build on the base serializer of its kind.
    """
    model = config.model
    model_name = model.__name__

    serializer_cls = config.get_serializer_class()
    if issubclass(model, Sample):
        _validate_sample_serializer(serializer_cls)
    elif issubclass(model, Measurement):
        _validate_measurement_serializer(serializer_cls)

    # Via the accessor so a configuration overriding get_filterset_class() is honoured.
    filterset_class = None
    with contextlib.suppress(Exception):
        filterset_class = config.get_filterset_class()

    queryset = model.objects.all()
    if hasattr(queryset, "non_polymorphic"):
        queryset = queryset.non_polymorphic()
    if hasattr(serializer_cls, "load_related"):
        queryset = serializer_cls.load_related(queryset)

    class _GeneratedViewSet(base_class):
        pass

    _GeneratedViewSet.__name__ = f"{model_name}ViewSet"
    _GeneratedViewSet.__qualname__ = f"{model_name}ViewSet"
    _GeneratedViewSet.serializer_class = serializer_cls
    _GeneratedViewSet.queryset = queryset
    _GeneratedViewSet.ordering_fields = sortable_fields(model, serializer_cls)

    if issubclass(model, Sample):
        _GeneratedViewSet.parent_filterset = DatasetFilterSet
    elif issubclass(model, Measurement):
        _GeneratedViewSet.parent_filterset = SampleFilterSet
    _GeneratedViewSet.filter_backends = [
        FairDMVisibilityFilter,
        FairDMFilterBackend,
        OrderingFilter,
    ]

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

    # No docstring: drf-spectacular would show it instead of each subclass's own.
    @extend_schema(responses=CatalogueSerializer)
    def get(self, request: Request) -> Response:
        from fairdm.registry import registry

        types = [
            self.describe(request, model)
            for model in getattr(registry, self.registry_attr)
        ]
        return Response({"types": types})

    def describe(self, request: Request, model: type[Model]) -> dict[str, Any]:
        """Describe one registered type for the caller.

        Args:
            request: The request being answered.
            model: A registered sample or measurement type.

        Returns:
            The type's names, the address of its list, the fields its serializer carries,
            the filters its list accepts and how many of its records the caller may see.
        """
        route = reverse(f"api:{self.url_prefix}-{_model_to_slug(model)}-list")
        viewset = cast("Any", resolve(route).func).cls
        queryset = viewset.queryset.all()
        visible = FairDMVisibilityFilter().filter_queryset(request, queryset, self)
        return {
            "name": model.__name__,
            "verbose_name": model._meta.verbose_name,
            "verbose_name_plural": model._meta.verbose_name_plural,
            "app_label": model._meta.app_label,
            "endpoint": request.build_absolute_uri(route),
            "fields": list(viewset.serializer_class().fields),
            "filters": self.filter_names(request, viewset, queryset),
            "count": visible.count(),
        }

    def filter_names(self, request: Request, viewset: type, queryset) -> list[str]:
        """List the filters a type's list accepts, as the API builds them for a request.

        Args:
            request: The request being answered.
            viewset: The viewset serving the type's list.
            queryset: The type's records.

        Returns:
            The names of the filters, none for a list that takes no filter set.
        """
        view = viewset(request=request, format_kwarg=None, action="list")
        filterset_class = FairDMFilterBackend().get_filterset_class(view, queryset)
        if filterset_class is None:
            return []
        filterset = filterset_class(data={}, queryset=queryset, request=request)
        return list(filterset.filters)


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
