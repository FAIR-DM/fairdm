from django.utils.translation import gettext as _

from fairdm.utils.utils import user_guide

# UUID_RE_PATTERN = r"^(?P<uuid>[[pdsme][a-zA-Z0-9_-]{22})/$"

UUID_RE_PATTERN = r"^(?P<uuid>[pdsmea-zA-Z0-9_-]{22})/$"
"""A regex the matches the uuid of a core data object (project, sample, measurement, etc.) and captures it in a named group 'uuid'."""

CORE_PERMISSIONS = [
    ("add_contributor", "Can add contributors"),
    ("modify_contributor", "Can modify contributors"),
    ("modify_metadata", "Can modify metadata"),
]


def documentation_link(path):
    """
    Returns a URL to the documentation for the given path.
    """
    return {
        "text": _("Learn more"),
        "href": user_guide(path),
        "icon": "documentation",
    }


def get_non_polymorphic_instance(obj):
    """Return ``obj`` re-fetched through its polymorphic base's non-polymorphic manager.

    Gated on ``type_of`` directly (F6), not on ``polymorphic_model_marker``: every
    polymorphic model carries the marker, but only ``Sample``, ``Measurement`` and
    ``Contributor`` declare ``type_of`` - a portal-defined polymorphic model that is none of
    those would otherwise raise ``AttributeError`` here rather than being left alone.
    """
    base_class = getattr(obj, "type_of", None)
    if base_class is None:
        return obj

    return base_class.objects.non_polymorphic().get(pk=obj.pk)


def get_permission_target(obj, perm):
    """Return the object a permission check or grant should actually target.

    A polymorphic subclass instance (e.g. ``RockSample``) carries its own app label and content
    type, so guardian either raises ``WrongAppError`` or silently misses a stored row when the
    permission is declared on the polymorphic base instead (``research.md`` R2). Normalising to
    the base fixes that - but only when the base is the one that actually owns the permission
    being checked. Doing it unconditionally would retarget every polymorphic record's content
    type, including one whose own subclass owns the permission - an ``Organization`` normalised
    to ``Contributor`` would orphan every permission ever assigned to it (D-018).

    Gated on the object, not on the permission string: guardian only compares app labels when the
    permission carries one (``"." in perm``), so a gate keyed on that would never fire for an
    unqualified permission and the failure would become a silent denial instead of an error.

    Gated on ``type_of`` directly (F6), not on ``polymorphic_model_marker``: every polymorphic
    model carries the marker, but only ``Sample``, ``Measurement`` and ``Contributor`` declare
    ``type_of`` - a portal-defined polymorphic model that is none of those would otherwise raise
    ``AttributeError`` inside an authentication backend rather than being left alone.
    """
    if obj is None:
        return obj

    base_class = getattr(obj, "type_of", None)
    if base_class is None or type(obj) is base_class:
        return obj

    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    codename = perm.rsplit(".", 1)[-1]
    base_content_type = ContentType.objects.get_for_model(base_class)
    if not Permission.objects.filter(
        content_type=base_content_type, codename=codename
    ).exists():
        return obj

    return get_non_polymorphic_instance(obj)


def assign_perm(perm, user_or_group, obj):
    """Assign ``perm`` to ``user_or_group`` on ``obj``, normalising a polymorphic instance first.

    A backend takes no part in granting a right - ``guardian.shortcuts.assign_perm`` resolves the
    object's own content type directly, so a permission declared on a polymorphic base (e.g.
    ``change_sample``) still cannot be stored against a subclass instance even once the check side
    is fixed (D-019). Uses the same gate as the check side, so the two never disagree about which
    records they cover.
    """
    from guardian.shortcuts import assign_perm as guardian_assign_perm

    return guardian_assign_perm(perm, user_or_group, get_permission_target(obj, perm))


def remove_perm(perm, user_or_group, obj):
    """Remove ``perm`` from ``user_or_group`` on ``obj``, with :func:`assign_perm`'s normalisation."""
    from guardian.shortcuts import remove_perm as guardian_remove_perm

    return guardian_remove_perm(perm, user_or_group, get_permission_target(obj, perm))


def get_perms(user_or_group, obj):
    """List every permission ``user_or_group`` holds on ``obj``.

    Merges rows stored against ``obj``'s own content type with rows stored against its
    polymorphic base, because :func:`assign_perm` may have written to either depending on which
    one owns the permission - and there is no single ``perm`` here to gate the choice on.

    Gated on ``type_of`` directly (F6), not on ``polymorphic_model_marker`` - see
    :func:`get_permission_target`.
    """
    from guardian.shortcuts import get_perms as guardian_get_perms

    perms = set(guardian_get_perms(user_or_group, obj))
    base_class = getattr(obj, "type_of", None) if obj is not None else None
    if base_class is not None and type(obj) is not base_class:
        perms |= set(
            guardian_get_perms(user_or_group, get_non_polymorphic_instance(obj))
        )
    return sorted(perms)


def get_objects_for_user(user, perm, klass, **kwargs):
    """List the objects in ``klass`` that ``user`` holds ``perm`` for, normalising a polymorphic
    subclass's content type the same way :func:`assign_perm`/:func:`has_perm` do (F4).

    ``guardian.shortcuts.get_objects_for_user`` derives its content-type filter from ``perm``'s
    own app label and model name, so a naive permission built from a specimen subclass (e.g.
    ``"fairdm_demo.view_rocksample"``) finds nothing when the grant is filed under the
    polymorphic base's content type (``sample.view_sample``) - and it raises
    ``MixedContentTypeError`` outright if handed that base-model permission alongside a subclass
    queryset, so the two cannot simply be passed through together. This recomputes ``perm``
    against the base model, resolves matching primary keys there, and narrows the caller's own
    queryset by them - safe because a polymorphic subclass shares its primary key with its base.
    """
    from guardian.shortcuts import get_objects_for_user as guardian_get_objects_for_user

    queryset = klass if hasattr(klass, "model") else klass._default_manager.all()
    model = queryset.model
    base_class = getattr(model, "type_of", None)

    if base_class is None or base_class is model:
        return guardian_get_objects_for_user(user, perm, queryset, **kwargs)

    _app_label, codename = perm.split(".", 1)
    action = codename.rsplit(f"_{model._meta.model_name}", 1)[0]
    base_perm = f"{base_class._meta.app_label}.{action}_{base_class._meta.model_name}"

    allowed_pks = guardian_get_objects_for_user(
        user, base_perm, base_class._default_manager.all(), **kwargs
    ).values_list("pk", flat=True)
    return queryset.filter(pk__in=allowed_pks)


def model_class_inheritance_to_fieldsets(obj_or_class):
    from .models import Sample

    klass = obj_or_class if isinstance(obj_or_class, type) else obj_or_class.__class__
    declared_fields = {
        "id",
        "local_id",
        "sample_ptr",
        "polymorphic_ctype",
        "created",
        "modified",
        "options",
        "path",
        "depth",
        "numchild",
        "image",
    }
    result = []

    # Loop through the real model's MRO
    for base in reversed(klass.__mro__):
        # Only process Django models that are subclasses of models.Model
        if hasattr(base, "_meta") and issubclass(base, Sample):
            declared_in_base = []
            for field in base._meta.local_fields:
                # Check if field is already declared by a parent class
                if field.name not in declared_fields:
                    # Mark this field as declared
                    declared_fields.add(field.name)
                    declared_in_base.append(field.name)

            if declared_in_base:
                name = base._meta.verbose_name if base != Sample else None
                result.append((name, {"fields": declared_in_base}))

    # if len(result) == 1:
    # return {None: result["sample"]}
    # sample = result.pop("sample")
    # last_key = list(result.keys())[-1]

    first_group = result[0][1]
    last_group = result[-1][1]

    first_group["fields"] += last_group["fields"]
    del result[-1]

    return result
