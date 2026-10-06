"""Serializer base classes and the factory that builds model serializers."""

from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.services.crediting import Crediting

# One class per input, or drf-spectacular warns about components with identical names.
_SERIALIZER_CACHE: dict[tuple, type] = {}


class CreatorCreditMixin:
    """Credit the person who creates a record through the API, and hold back what needs manage.

    Visibility and the record a record sits under decide who can get in, so changing either needs
    the manage level on the record, as on the update forms.

    Attributes:
        manager_only_fields: The names of the fields only someone who can manage the record may
            change.
    """

    manager_only_fields = ("visibility", "owner", "project", "dataset", "sample")

    def create(self, validated_data):
        """Create the record, then list the requesting user on it at the manage level.

        Args:
            validated_data: The validated fields of the new record.

        Returns:
            The new record.
        """
        record = super().create(validated_data)
        Crediting(record).make_creator(self.context["request"].user)
        return record

    def update(self, instance, validated_data):
        """Update the record, refusing a manager-only field changed by someone who cannot manage it.

        Args:
            instance: The record to update.
            validated_data: The validated fields to set.

        Returns:
            The updated record.

        Raises:
            PermissionDenied: When a manager-only field would change and the requesting user
                cannot manage the record.
        """
        changed = [
            name
            for name in self.manager_only_fields
            if name in validated_data
            and validated_data[name] != getattr(instance, name, None)
        ]
        if changed and not RecordAccess(instance).can_manage(
            self.context["request"].user
        ):
            raise PermissionDenied(
                _("Changing %(fields)s needs the manage level on this record.")
                % {"fields": ", ".join(changed)},
                code="manage_level_required",
            )
        return super().update(instance, validated_data)


class BaseSampleSerializer(CreatorCreditMixin, serializers.ModelSerializer):
    """Base DRF serializer for all Sample subtypes.

    All auto-generated serializers for registered :class:`~fairdm.core.sample.models.Sample`
    subclasses inherit from this class.  When a portal developer provides a custom
    ``serializer_class`` via the registry config it MUST subclass this class; otherwise
    :func:`generate_viewset` raises :exc:`~django.core.exceptions.ImproperlyConfigured`.

    Guaranteed fields:
    ``url``, ``uuid``, ``name``, ``local_id``, ``status``, ``dataset``,
    ``added``, ``modified``, ``polymorphic_ctype``
    """

    class Meta:
        from fairdm.core.sample.models import Sample

        model = Sample
        fields = [
            "url",
            "uuid",
            "name",
            "local_id",
            "status",
            "dataset",
            "added",
            "modified",
            "polymorphic_ctype",
        ]


class BaseMeasurementSerializer(CreatorCreditMixin, serializers.ModelSerializer):
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

    class Meta:
        from fairdm.core.measurement.models import Measurement

        model = Measurement
        fields = [
            "url",
            "uuid",
            "name",
            "sample",
            "dataset",
            "added",
            "modified",
            "polymorphic_ctype",
        ]


def _validate_sample_serializer(cls: type) -> None:
    """Require a custom Sample serializer to subclass :class:`BaseSampleSerializer`.

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
    """Require a custom Measurement serializer to subclass its base serializer.

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
        view_name="",  # Set per model by build_model_serializer()
        lookup_field="uuid",
        read_only=True,
    )


def _flatten_fields(fields: list) -> list[str]:
    """Flatten a grouped field list, as :func:`fairdm.registry.config.flatten_fields` does.

    Args:
        fields: Field names, possibly grouped in tuples or nested lists.

    Returns:
        The flat list of field names.
    """
    from fairdm.registry.config import flatten_fields

    return flatten_fields(fields)


def build_model_serializer(
    model,
    fields: list[str],
    view_name: str | None = None,
    extra_kwargs: dict[str, Any] | None = None,
    base_class: type[serializers.ModelSerializer] | None = None,
) -> type[serializers.ModelSerializer]:
    """Build a DRF ModelSerializer for *model* exposing *fields*.

    A read-only ``url`` hyperlinked field is included when *view_name* is provided.

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
            ``serializers.ModelSerializer`` wrapped with ``CreatorCreditMixin`` for a project,
            dataset, sample or measurement and with ``ObjectPermissionsAssignmentMixin`` for any
            other model).  Pass
            :class:`BaseSampleSerializer` or :class:`BaseMeasurementSerializer`
            so that auto-generated subtype serializers satisfy the inheritance
            constraint enforced by :func:`_validate_sample_serializer` /
            :func:`_validate_measurement_serializer`.

    Returns:
        A ``ModelSerializer`` subclass.
    """
    flat_fields = _flatten_fields(fields)
    cache_key = (
        model,
        tuple(flat_fields),
        view_name,
        tuple(sorted((extra_kwargs or {}).items())),
        base_class,
    )
    if cache_key in _SERIALIZER_CACHE:
        return _SERIALIZER_CACHE[cache_key]

    meta_fields: list[str] = []
    serializer_attrs: dict[str, Any] = {}

    if view_name:
        meta_fields.append("url")
        serializer_attrs["url"] = serializers.HyperlinkedIdentityField(
            view_name=view_name,
            lookup_field="uuid",
            read_only=True,
        )

    meta_fields.extend(flat_fields)

    meta_extra_kwargs: dict[str, Any] = extra_kwargs or {}
    Meta = type(
        "Meta",
        (),
        {"model": model, "fields": meta_fields, "extra_kwargs": meta_extra_kwargs},
    )
    serializer_attrs["Meta"] = Meta

    # A given base_class already carries the mixin that credits the creator.
    bases: tuple[type, ...]
    if base_class is not None:
        bases = (base_class,)
    elif RecordAccess.is_core_model(getattr(model, "type_of", None) or model):
        bases = (CreatorCreditMixin, serializers.ModelSerializer)
    else:
        model_name = model._meta.model_name
        perm_codenames = [
            f"view_{model_name}",
            f"change_{model_name}",
            f"delete_{model_name}",
        ]

        def get_permissions_map(self, created: bool) -> dict[str, list]:
            """Assign guardian object permissions to the requesting user."""
            current_user = self.context["request"].user
            return {perm: [current_user] for perm in perm_codenames}

        serializer_attrs["get_permissions_map"] = get_permissions_map
        bases = (ObjectPermissionsAssignmentMixin, serializers.ModelSerializer)

    serializer_cls = type(
        f"{model.__name__}Serializer",
        bases,
        serializer_attrs,
    )
    _SERIALIZER_CACHE[cache_key] = serializer_cls
    return serializer_cls
