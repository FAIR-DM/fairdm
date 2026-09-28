"""Base registry configuration for sample types.

Do not register the base ``Sample`` model, only its polymorphic subclasses.
"""

from fairdm.registry.config import ModelConfiguration


class BaseSampleConfiguration(ModelConfiguration):
    """Base registry configuration for sample types, declaring only the shared ``fields`` list.

    ``fields`` is what every component (form, table, filter set, serializer, resource, admin)
    falls back to when a subclass names no list of its own. The per-component lists
    (``form_fields`` and the rest) are deliberately not declared, because each would win over a
    subclass's own ``fields`` for that component. A subclass sets ``model`` and, to change every
    component at once, ``fields``. Do not register the base ``Sample`` model.

    Attributes:
        fields: The default fields for every component that names no list of its own.

    Example:
        ```python
        from fairdm.core.sample.config import BaseSampleConfiguration
        from fairdm.registry import registry


        class RockSampleConfiguration(BaseSampleConfiguration):
            model = RockSample
            fields = ["name", "dataset", "rock_type", "mineral_content"]


        registry.register(RockSampleConfiguration)
        ```
    """

    fields = [
        "name",
        "dataset",
        "local_id",
        "status",
        "location",
        "image",
    ]
