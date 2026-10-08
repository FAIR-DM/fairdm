"""Helpers for core records: polymorphic-aware permissions and fieldsets."""

UUID_RE_PATTERN = r"^(?P<uuid>[pdsmea-zA-Z0-9_-]{22})/$"
"""A regex the matches the uuid of a core data object (project, sample, measurement, etc.) and captures it in a named group 'uuid'."""

CORE_PERMISSIONS = [
    ("add_contributor", "Can add contributors"),
    ("modify_contributor", "Can modify contributors"),
    ("modify_metadata", "Can modify metadata"),
]


def get_non_polymorphic_instance(obj):
    """Return an object re-fetched through its polymorphic base's non-polymorphic manager.

    Gated on ``type_of`` directly, not on ``polymorphic_model_marker``: every
    polymorphic model carries the marker, but only ``Sample``, ``Measurement`` and
    ``Contributor`` declare ``type_of``. A portal-defined polymorphic model that is none of
    those would otherwise raise ``AttributeError`` here rather than being left alone.

    Args:
        obj: The record to re-fetch.

    Returns:
        The non-polymorphic instance, or ``obj`` itself when it declares no ``type_of``.
    """
    base_class = getattr(obj, "type_of", None)
    if base_class is None:
        return obj

    return base_class.objects.non_polymorphic().get(pk=obj.pk)


def get_permission_target(obj, perm):
    """Return the object a permission check or grant should actually target.

    A polymorphic subclass instance (e.g. ``RockSample``) carries its own app label and content
    type, so guardian either raises ``WrongAppError`` or silently misses a stored row when the
    permission is declared on the polymorphic base instead. Normalising to the base fixes that,
    but only when the base is the one that actually owns the permission being checked. Doing it
    unconditionally would retarget every polymorphic record's content type, including one whose
    own subclass owns the permission: an ``Organization`` normalised to ``Contributor`` would
    orphan every permission ever assigned to it.

    Gated on the object, not on the permission string: guardian only compares app labels when the
    permission carries one (``"." in perm``), so a gate keyed on that would never fire for an
    unqualified permission and the failure would become a silent denial instead of an error.

    Gated on ``type_of`` directly, not on ``polymorphic_model_marker``: a portal-defined
    polymorphic model that declares no ``type_of`` would otherwise raise ``AttributeError``
    inside an authentication backend rather than being left alone.

    Args:
        obj: The record the permission is checked or granted on, or ``None``.
        perm: The permission codename, with or without an app label.

    Returns:
        The object to pass to guardian: ``obj`` itself or its non-polymorphic base instance.
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
    """Assign a permission, normalising a polymorphic instance first.

    A backend takes no part in granting a right. ``guardian.shortcuts.assign_perm`` resolves the
    object's own content type directly, so a permission declared on a polymorphic base (e.g.
    ``change_sample``) could not be stored against a subclass instance. Uses the same gate as
    the check side, so the two never disagree about which records they cover.

    Args:
        perm: The permission to assign.
        user_or_group: The user or group receiving the permission.
        obj: The record the permission applies to.

    Returns:
        Whatever ``guardian.shortcuts.assign_perm`` returns.
    """
    from guardian.shortcuts import assign_perm as guardian_assign_perm

    return guardian_assign_perm(perm, user_or_group, get_permission_target(obj, perm))


def remove_perm(perm, user_or_group, obj):
    """Remove a permission, with the same normalisation as :func:`assign_perm`.

    Args:
        perm: The permission to remove.
        user_or_group: The user or group losing the permission.
        obj: The record the permission applies to.

    Returns:
        Whatever ``guardian.shortcuts.remove_perm`` returns.
    """
    from guardian.shortcuts import remove_perm as guardian_remove_perm

    return guardian_remove_perm(perm, user_or_group, get_permission_target(obj, perm))


def get_perms(user_or_group, obj):
    """List every permission a user or group holds on an object.

    Merges rows stored against the object's own content type with rows stored against its
    polymorphic base, because :func:`assign_perm` may have written to either depending on which
    one owns the permission, and there is no single permission here to gate the choice on.

    Args:
        user_or_group: The user or group to look up.
        obj: The record to look up permissions on.

    Returns:
        The sorted permission codenames.
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
    """List the objects a user holds a permission for, allowing for polymorphic subclasses.

    ``guardian.shortcuts.get_objects_for_user`` derives its content-type filter from the
    permission's own app label and model name, so a permission built from a subclass (e.g.
    ``"demo.view_rocksample"``) finds nothing when the grant is filed under the polymorphic
    base's content type (``sample.view_sample``). Handing it the base-model permission alongside
    a subclass queryset raises ``MixedContentTypeError``. This recomputes the permission against
    the base model, resolves matching primary keys there, and narrows the caller's own queryset
    by them. That is safe because a polymorphic subclass shares its primary key with its base.

    Args:
        user: The user to look up.
        perm: The permission, in ``app_label.codename`` form.
        klass: The model or queryset to filter.
        **kwargs: Keyword arguments passed to ``guardian.shortcuts.get_objects_for_user``.

    Returns:
        The queryset of objects the user holds the permission for.
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
    """Group a sample model's own fields into fieldsets, one per class in its inheritance chain.

    Each field appears once, under the first class in the chain that declares it, and the
    bookkeeping fields every sample carries (``id``, ``local_id``, ``image`` and the like) are
    left out. The most derived class's fields are then folded into the first group, and that
    last group is dropped.

    Args:
        obj_or_class: A sample instance or sample model class.

    Returns:
        A list of ``(name, {"fields": [...]})`` pairs. ``name`` is the class's verbose name,
        or ``None`` for ``Sample`` itself.
    """
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

    for base in reversed(klass.__mro__):
        if hasattr(base, "_meta") and issubclass(base, Sample):
            declared_in_base = []
            for field in base._meta.local_fields:
                if field.name not in declared_fields:
                    declared_fields.add(field.name)
                    declared_in_base.append(field.name)

            if declared_in_base:
                name = base._meta.verbose_name if base != Sample else None
                result.append((name, {"fields": declared_in_base}))

    first_group = result[0][1]
    last_group = result[-1][1]

    first_group["fields"] += last_group["fields"]
    del result[-1]

    return result
