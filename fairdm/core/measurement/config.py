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

from fairdm.registry.config import ModelConfiguration


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

    # model should be set by subclass (e.g., XRFMeasurement, ICP_MS_Measurement)
    model = None

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
