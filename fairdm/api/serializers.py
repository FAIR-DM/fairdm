"""FairDM API serializer helpers and base mixin."""

from typing import Any

from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

# Module-level cache so build_model_serializer always returns the same class
# object for identical inputs.  Without this drf-spectacular warns about
# "2 components with identical names and different identities" when schema
# generation traverses multiple viewset instances for the same model.
_SERIALIZER_CACHE: dict[tuple, type] = {}


# ---------------------------------------------------------------------------
# Concrete base serializers for polymorphic domain models
# ---------------------------------------------------------------------------


class BaseSampleSerializer(ObjectPermissionsAssignmentMixin, serializers.ModelSerializer):
    """Base DRF serializer for all Sample subtypes.

    All auto-generated serializers for registered :class:`~fairdm.core.sample.models.Sample`
    subclasses inherit from this class.  When a portal developer provides a custom
    ``serializer_class`` via the registry config it MUST subclass this class; otherwise
    :func:`generate_viewset` raises :exc:`~django.core.exceptions.ImproperlyConfigured`.

    Guaranteed fields:
    ``url``, ``uuid``, ``name``, ``local_id``, ``status``, ``dataset``,
    ``added``, ``modified``, ``polymorphic_ctype``
    """

    def get_permissions_map(self, created: bool) -> dict[str, list]:
        """Assign guardian object permissions to the requesting user on create/update."""
        current_user = self.context["request"].user
        model_name = self.Meta.model._meta.model_name  # type: ignore[attr-defined]
        return {
            f"view_{model_name}": [current_user],
            f"change_{model_name}": [current_user],
            f"delete_{model_name}": [current_user],
        }

    class Meta:
        from fairdm.core.sample.models import Sample

        model = Sample
        fields = ["url", "uuid", "name", "local_id", "status", "dataset", "added", "modified", "polymorphic_ctype"]


class BaseMeasurementSerializer(ObjectPermissionsAssignmentMixin, serializers.ModelSerializer):
    """Base DRF serializer for all Measurement subtypes.

    All auto-generated serializers for registered
    :class:`~fairdm.core.measurement.models.Measurement` subclasses inherit from this class.
    When a portal developer provides a custom ``serializer_class`` via the registry config
    it MUST subclass this class; otherwise :func:`generate_viewset` raises
    :exc:`~django.core.exceptions.ImproperlyConfigured`.

    Guaranteed fields:
    ``url``, ``uuid``, ``name``, ``sample``, ``dataset``,
    ``added``, ``modified``, ``polymorphic_ctype``
    """

    def get_permissions_map(self, created: bool) -> dict[str, list]:
        """Assign guardian object permissions to the requesting user on create/update."""
        current_user = self.context["request"].user
        model_name = self.Meta.model._meta.model_name  # type: ignore[attr-defined]
        return {
            f"view_{model_name}": [current_user],
            f"change_{model_name}": [current_user],
            f"delete_{model_name}": [current_user],
        }

    class Meta:
        from fairdm.core.measurement.models import Measurement

        model = Measurement
        fields = ["url", "uuid", "name", "sample", "dataset", "added", "modified", "polymorphic_ctype"]


# ---------------------------------------------------------------------------
# Validation helpers for custom serializer_class enforcement
# ---------------------------------------------------------------------------


def _validate_sample_serializer(cls: type) -> None:
    """Raise :exc:`~django.core.exceptions.ImproperlyConfigured` if *cls* does not
    subclass :class:`BaseSampleSerializer`.

    Args:
        cls: The custom serializer class to validate.

    Raises:
        ImproperlyConfigured: When *cls* is not a subclass of ``BaseSampleSerializer``.
    """
    if not (isinstance(cls, type) and issubclass(cls, BaseSampleSerializer)):
        raise ImproperlyConfigured(
            f"Custom serializer_class '{cls.__name__}' for a Sample type must subclass "
            f"'fairdm.api.serializers.BaseSampleSerializer'."
        )


def _validate_measurement_serializer(cls: type) -> None:
    """Raise :exc:`~django.core.exceptions.ImproperlyConfigured` if *cls* does not
    subclass :class:`BaseMeasurementSerializer`.

    Args:
        cls: The custom serializer class to validate.

    Raises:
        ImproperlyConfigured: When *cls* is not a subclass of ``BaseMeasurementSerializer``.
    """
    if not (isinstance(cls, type) and issubclass(cls, BaseMeasurementSerializer)):
        raise ImproperlyConfigured(
            f"Custom serializer_class '{cls.__name__}' for a Measurement type must subclass "
            f"'fairdm.api.serializers.BaseMeasurementSerializer'."
        )


class BaseSerializerMixin:
    """Mixin that adds a ``url`` hyperlinked field to auto-generated serializers.

    This mixin is applied by :func:`fairdm.api.viewsets.generate_viewset` when
    building serializer classes that do not have an explicit ``serializer_class``
    in the registry config.

    The ``url`` field uses ``lookup_field="uuid"`` to match the viewset's lookup.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="",  # Overridden per-model by generate_serializer()
        lookup_field="uuid",
        read_only=True,
    )


def _flatten_fields(fields: list) -> list[str]:
    """Flatten a fields list that may contain grouped tuples.

    Registry configurations may group fields in tuples for form layout purposes
    (e.g. ``[("name", "status"), "description"]``).  API serializers only
    understand flat string lists, so this helper expands all nested
    sequences to individual field names.
    """
    result: list[str] = []
    for item in fields:
        if isinstance(item, (tuple, list)):
            result.extend(str(f) for f in item)
        elif isinstance(item, str):
            result.append(item)
    return result


def build_model_serializer(
    model,
    fields: list[str],
    view_name: str | None = None,
    extra_kwargs: dict[str, Any] | None = None,
    base_class: type[serializers.ModelSerializer] | None = None,
) -> type[serializers.ModelSerializer]:
    """Build a DRF ModelSerializer for *model* exposing *fields*.

    The generated class is named ``{ModelName}APISerializer`` to distinguish it
    from the registry's plain serializer.  A read-only ``url`` hyperlinked field
    is included when *view_name* is provided.

    Results are cached by ``(model, fields, view_name)`` so the same Python
    class object is returned for identical inputs — preventing drf-spectacular
    "components with identical names" warnings.

    The generated class is named ``{ModelName}Serializer`` so that
    drf-spectacular derives clean OpenAPI schema component names (e.g. ``RockSample``
    rather than ``RockSampleAPI``).

    Args:
        model: Django model class.
        fields: List of field name strings (tuples/nested lists are flattened).
        view_name: DRF ``HyperlinkedIdentityField`` ``view_name``; includes the
            "url" field only when provided.
        extra_kwargs: Merged into the ``Meta.extra_kwargs`` dict.
        base_class: Base serializer class to inherit from (default:
            ``serializers.ModelSerializer`` wrapped with
            ``ObjectPermissionsAssignmentMixin``).  Pass
            :class:`BaseSampleSerializer` or :class:`BaseMeasurementSerializer`
            so that auto-generated subtype serializers satisfy the inheritance
            constraint enforced by :func:`_validate_sample_serializer` /
            :func:`_validate_measurement_serializer`.

    Returns:
        A ``ModelSerializer`` subclass.
    """
    flat_fields = _flatten_fields(fields)
    cache_key = (model, tuple(flat_fields), view_name, tuple(sorted((extra_kwargs or {}).items())), base_class)
    if cache_key in _SERIALIZER_CACHE:
        return _SERIALIZER_CACHE[cache_key]

    meta_fields: list[str] = []
    serializer_attrs: dict[str, Any] = {}

    if view_name:
        # Prepend url as the first field so it appears before all data fields
        meta_fields.append("url")
        serializer_attrs["url"] = serializers.HyperlinkedIdentityField(
            view_name=view_name,
            lookup_field="uuid",
            read_only=True,
        )

    meta_fields.extend(flat_fields)

    meta_extra_kwargs: dict[str, Any] = extra_kwargs or {}
    Meta = type("Meta", (), {"model": model, "fields": meta_fields, "extra_kwargs": meta_extra_kwargs})
    serializer_attrs["Meta"] = Meta

    # Build get_permissions_map so the mixin assigns guardian object permissions
    # (view, change, delete) to the submitting user when objects are created or
    # updated via the API.  The permission codenames follow Django's convention:
    # <action>_<model_name> (e.g. "view_project", "change_project").
    model_name = model._meta.model_name  # type: ignore[union-attr]
    perm_codenames = [f"view_{model_name}", f"change_{model_name}", f"delete_{model_name}"]

    def get_permissions_map(self, created: bool) -> dict[str, list]:
        """Assign guardian object permissions to the requesting user."""
        current_user = self.context["request"].user
        return {perm: [current_user] for perm in perm_codenames}

    serializer_attrs["get_permissions_map"] = get_permissions_map

    # Determine the base class for the generated serializer.  If a specific
    # base_class is given (e.g. BaseSampleSerializer) use it directly since it
    # already includes ObjectPermissionsAssignmentMixin in its MRO.  Otherwise
    # fall back to the generic mixin + ModelSerializer combination.
    effective_base = base_class if base_class is not None else None
    if effective_base is not None:
        bases = (effective_base,)
    else:
        bases = (ObjectPermissionsAssignmentMixin, serializers.ModelSerializer)

    serializer_cls = type(
        f"{model.__name__}Serializer",
        bases,
        serializer_attrs,
    )
    _SERIALIZER_CACHE[cache_key] = serializer_cls
    return serializer_cls
