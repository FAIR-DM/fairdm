"""FairDM API serializer helpers and base mixin."""

from typing import Any

from rest_framework import serializers

# Module-level cache so build_model_serializer always returns the same class
# object for identical inputs.  Without this drf-spectacular warns about
# "2 components with identical names and different identities" when schema
# generation traverses multiple viewset instances for the same model.
_SERIALIZER_CACHE: dict[tuple, type] = {}


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
) -> type[serializers.ModelSerializer]:
    """Build a DRF ModelSerializer for *model* exposing *fields*.

    The generated class is named ``{ModelName}APISerializer`` to distinguish it
    from the registry's plain serializer.  A read-only ``url`` hyperlinked field
    is included when *view_name* is provided.

    Results are cached by ``(model, fields, view_name)`` so the same Python
    class object is returned for identical inputs — preventing drf-spectacular
    "components with identical names" warnings.

    Args:
        model: Django model class.
        fields: List of field name strings (tuples/nested lists are flattened).
        view_name: DRF ``HyperlinkedIdentityField`` ``view_name``; includes the
            "url" field only when provided.
        extra_kwargs: Merged into the ``Meta.extra_kwargs`` dict.

    Returns:
        A ``ModelSerializer`` subclass.
    """
    flat_fields = _flatten_fields(fields)
    cache_key = (model, tuple(flat_fields), view_name, tuple(sorted((extra_kwargs or {}).items())))
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

    serializer_cls = type(
        f"{model.__name__}APISerializer",
        (serializers.ModelSerializer,),
        serializer_attrs,
    )
    _SERIALIZER_CACHE[cache_key] = serializer_cls
    return serializer_cls
