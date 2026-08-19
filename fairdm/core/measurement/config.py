"""
Base registry configuration for Measurement subclasses.

Provides a base configuration class that measurement type subclasses can inherit from.
Do NOT register the base Measurement model - only polymorphic subclasses should be registered.

Example usage in custom measurement models:
    ```python
    from fairdm.core.measurement.config import BaseMeasurementConfiguration
    from fairdm.registry import registry


    class XRFMeasurementConfiguration(BaseMeasurementConfiguration):
        model = XRFMeasurement
        fields = ["name", "sample", "dataset", "element", "concentration_ppm"]


    registry.register(XRFMeasurementConfiguration)
    ```
"""

from fairdm.registry.config import ModelConfiguration, flatten_fields

#: Components whose generated class must carry a registered type's own fields
#: (``self.fields``) alongside the fields every measurement has. Excludes
#: ``admin``, whose generated ``list_display`` already draws from ``fields``
#: directly because ``BaseMeasurementConfiguration`` declares no
#: ``admin_list_display`` of its own.
COMPONENTS_ADDING_OWN_FIELDS = ("form", "table", "filterset")


class BaseMeasurementConfiguration(ModelConfiguration):
    """Base registry configuration for Measurement subclasses to inherit from.

    This configuration provides common field setup for all measurement types.
    Subclasses should override the model attribute and customize fields as needed.

    See Also:
        - Developer Guide: docs/portal-development/measurements.md#step-2-register-your-measurement
        - Registry Guide: docs/portal-development/using_the_registry.md#base-measurement-configuration-fields
        - Data Model: docs/overview/data_model.md#measurement-model

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

    WARNING: Do NOT register the base Measurement model. Only register polymorphic subclasses.
    """

    # A subclass supplies `model`. The base class already defaults it to None, so
    # restating that here would only add a line to keep in step.

    # Fields for all auto-generated components
    fields = [
        "name",
        "sample",
        "dataset",
        "image",
    ]

    # Table columns for list views
    table_fields = [
        "name",
        "sample",
        "dataset",
        "added",
        "modified",
    ]

    # Form fields for create/edit views
    form_fields = [
        "name",
        "sample",
        "dataset",
        "image",
    ]

    # FilterSet fields for search/filter functionality
    filterset_fields = [
        "sample",
        "dataset",
        "added",
    ]

    # Serializer fields for API (when implemented)
    serializer_fields = [
        "id",
        "uuid",
        "name",
        "sample",
        "dataset",
        "added",
        "modified",
    ]

    # Display metadata
    display_name = "Measurement"
    description = "Observation or calculation recorded from a sample"

    def resolve_fields(self, component: str) -> list[str]:
        """The fields every measurement has, followed by this type's own.

        The base class above declares a fixed field list per component, so a
        subclass's own ``fields`` (e.g. ``XRFMeasurementConfig.fields``) never
        reaches ``ModelConfiguration.resolve_fields`` for form, table or
        filterset - that method only falls back to ``self.fields`` when the
        component's own list is undeclared, and here it always is declared.
        Appending the type's own fields here is what lets a registered type's
        form, table and filterset carry its own fields as well as the common
        ones, without every type author repeating the common list.
        """
        common = super().resolve_fields(component)
        if component not in COMPONENTS_ADDING_OWN_FIELDS:
            return common

        own = flatten_fields(self.fields)
        excluded = set(self.exclude)
        return common + [
            name for name in own if name not in common and name not in excluded
        ]
