"""FairDM API serializer helpers and base mixin."""

from typing import Any

from rest_framework import serializers


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


def build_model_serializer(
    model,
    fields: list[str],
    view_name: str | None = None,
    extra_kwargs: dict[str, Any] | None = None,
) -> type[serializers.ModelSerializer]:
    """Build a DRF ModelSerializer for *model* exposing *fields*.

    The generated class is named ``{ModelName}APISerializer`` to distinguish it
    from the registry's plain serializer.  A read-only ``url`` hyperlinked field
    is included when *view_name* is provided.

    Args:
        model: Django model class.
        fields: List of field names to expose.
        view_name: DRF ``HyperlinkedIdentityField`` ``view_name``; includes the
            "url" field only when provided.
        extra_kwargs: Merged into the ``Meta.extra_kwargs`` dict.

    Returns:
        A ``ModelSerializer`` subclass.
    """
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

    meta_fields.extend(fields)

    meta_extra_kwargs: dict[str, Any] = extra_kwargs or {}
    Meta = type("Meta", (), {"model": model, "fields": meta_fields, "extra_kwargs": meta_extra_kwargs})
    serializer_attrs["Meta"] = Meta

    return type(
        f"{model.__name__}APISerializer",
        (serializers.ModelSerializer,),
        serializer_attrs,
    )
