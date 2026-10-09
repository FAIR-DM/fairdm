"""System checks on how registered types appear in the API."""

from django.core.checks import CheckMessage, Error

from fairdm.registry import registry


def required_fields_left_out(config) -> list[str]:
    """Return the required model fields the type's API serializer cannot accept.

    A field is required when it is editable, is not filled in by the database and may be
    neither blank nor null. The serializer accepts it when it has a writable field reading
    that model field.

    Args:
        config: The registered type's :class:`~fairdm.registry.ModelConfiguration`.

    Returns:
        The names of the required model fields no writable serializer field covers.
    """
    model = config.model
    serializer = config.get_serializer_class()()
    writable = {
        field.source or name
        for name, field in serializer.fields.items()
        if not field.read_only
    }
    return [
        field.name
        for field in (*model._meta.concrete_fields, *model._meta.many_to_many)
        if field.editable
        and not field.auto_created
        and not field.has_default()
        and not field.blank
        and not field.null
        and field.name not in writable
    ]


def check_registered_types(app_configs, **kwargs) -> list[CheckMessage]:
    """Report fairdm.E600 for each required field a registered type's API cannot accept.

    Without such a field no record of the type can be created through the API, and the
    caller would learn it only from the first failed request.

    Args:
        app_configs: Unused; the registry is not tied to one app.
        **kwargs: Unused.

    Returns:
        One error for each required field a sample or measurement type leaves out.
    """
    errors = []
    for model in (*registry.samples, *registry.measurements):
        config = registry.get_for_model(model)
        errors.extend(
            Error(
                f"The API serializer for {model._meta.label} does not accept the "
                f"required field '{name}', so no record of this type can be created "
                f"through the API.",
                hint=(
                    f"Add '{name}' to serializer_fields (or fields) in the type's "
                    f"registration, or to the serializer it names."
                ),
                obj=model,
                id="fairdm.E600",
            )
            for name in required_fields_left_out(config)
        )
    return errors
