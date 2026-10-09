"""Base registry configuration for measurement types.

Do not register the base ``Measurement`` model, only its polymorphic subclasses.
"""

from fairdm.registry.config import ModelConfiguration, flatten_fields

#: Components whose generated class carries a registered type's own fields as well as the common
#: ones. Excludes ``admin``, whose ``list_display`` already draws from ``fields``.
COMPONENTS_ADDING_OWN_FIELDS = ("form", "table", "filterset")


class BaseMeasurementConfiguration(ModelConfiguration):
    """Base registry configuration for measurement types, with the common field lists.

    A subclass sets ``model`` and lists its own ``fields``. Do not register the base
    ``Measurement`` model. See docs/portal-development/measurements.md.

    Attributes:
        fields: Fields for all generated components.
        table_fields: Table columns for list views.
        form_fields: Form fields for create and edit views.
        filterset_fields: Filterset fields for search and filtering.
        display_name: The name shown for the measurement type.
        description: A one-line description of the measurement type.

    Example:
        ```python
        from fairdm.core.measurement.config import BaseMeasurementConfiguration
        from fairdm.registry import register


        @register
        class XRFMeasurementConfig(BaseMeasurementConfiguration):
            model = XRFMeasurement
            fields = ["name", "sample", "dataset", "element", "concentration_ppm"]
            display_name = "XRF Measurement"
            description = "X-ray fluorescence elemental analysis"
        ```
    """

    fields = [
        "name",
        "sample",
        "dataset",
        "image",
    ]

    table_fields = [
        "name",
        "sample",
        "dataset",
        "added",
        "modified",
    ]

    form_fields = [
        "name",
        "sample",
        "dataset",
        "image",
    ]

    filterset_fields = [
        "sample",
        "dataset",
        "added",
    ]

    display_name = "Measurement"
    description = "Observation or calculation recorded from a sample"

    def resolve_fields(self, component: str) -> list[str]:
        """Return the fields every measurement has, followed by this type's own.

        ``ModelConfiguration.resolve_fields`` only falls back to ``self.fields`` when a component's
        own list is undeclared, and here it always is declared. Appending the type's own fields
        lets its form, table and filterset carry them without repeating the common list.

        Args:
            component: The component being generated, such as ``form`` or ``table``.

        Returns:
            The field names for the component.
        """
        common = super().resolve_fields(component)
        if component not in COMPONENTS_ADDING_OWN_FIELDS:
            return common

        own = flatten_fields(self.fields)
        excluded = set(self.exclude)
        return common + [
            name for name in own if name not in common and name not in excluded
        ]
