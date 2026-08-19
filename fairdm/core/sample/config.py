"""
Base registry configuration for Sample subclasses.

Provides a base configuration class that sample type subclasses can inherit from.
Do NOT register the base Sample model - only polymorphic subclasses should be registered.

Example usage in custom sample models:
    ```python
    from fairdm.core.sample.config import BaseSampleConfiguration
    from fairdm.registry import registry


    class RockSampleConfiguration(BaseSampleConfiguration):
        model = RockSample
        fields = ["name", "dataset", "rock_type", "mineral_content"]


    registry.register(RockSampleConfiguration)
    ```
"""

from fairdm.registry.config import ModelConfiguration


class BaseSampleConfiguration(ModelConfiguration):
    """Base registry configuration for Sample subclasses to inherit from.

    Declares only the shared `fields` list every component (form, table, filter
    set, serializer, resource, admin) falls back to when a subclass names no
    field list of its own, per `ModelConfiguration.resolve_fields`. It
    deliberately does **not** also declare `form_fields`, `table_fields`,
    `filterset_fields` or `serializer_fields`: each of those, if set here,
    would win over a subclass's own `fields` for that one component
    (`resolve_fields` prefers a component's own list first), silently
    replacing a specimen type's declared fields with this base's generic ones
    for every component it did not individually restate - the opposite of
    "sensible defaults without restating them" (D-013). A subclass that wants
    every component to share one field list therefore only has to set
    `fields`, exactly as it would with a bare `ModelConfiguration`; this base
    only saves that one declaration for a subclass that wants the framework's
    own defaults outright.

    WARNING: Do NOT register the base Sample model. Only register polymorphic subclasses.
    """

    # A subclass supplies `model`. The base class already defaults it to None, so
    # restating that here would only add a line to keep in step.

    # The framework's own default fields, used by every component whose own
    # field list (and `fields` itself) a subclass leaves unset.
    fields = [
        "name",
        "dataset",
        "local_id",
        "status",
        "location",
        "image",
    ]
