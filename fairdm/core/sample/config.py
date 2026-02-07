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

    This configuration provides common field setup for all sample types.
    Subclasses should override the model attribute and customize fields as needed.

    WARNING: Do NOT register the base Sample model. Only register polymorphic subclasses.
    """

    # model should be set by subclass (e.g., RockSample, WaterSample)
    model = None

    # Fields for all auto-generated components
    fields = [
        "name",
        "dataset",
        "local_id",
        "status",
        "location",
        "image",
    ]

    # Table columns for list views
    table_fields = [
        "name",
        "dataset",
        "local_id",
        "status",
        "added",
        "modified",
    ]

    # Form fields for create/edit views
    form_fields = [
        "name",
        "dataset",
        "local_id",
        "status",
        "location",
        "image",
    ]

    # FilterSet fields for search/filter functionality
    filterset_fields = [
        "dataset",
        "status",
        "added",
    ]

    # Serializer fields for API (when implemented)
    serializer_fields = [
        "id",
        "uuid",
        "name",
        "dataset",
        "local_id",
        "status",
        "location",
        "added",
        "modified",
    ]

    # Display metadata
    display_name = "Sample"
    description = "Physical or digital specimen/artifact for research"
