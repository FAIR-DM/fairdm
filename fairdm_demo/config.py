"""
FairDM Demo Portal Configuration

This module demonstrates various model registration patterns using the FairDM registry system.
It showcases different configuration approaches and serves as executable documentation
for developers building their own research portals.

The examples in this module illustrate:

1. **Basic Registration**: Simple field lists for quick setup
2. **Component-Specific Fields**: Different field sets for tables, forms, and filters
3. **Custom Component Classes**: Overriding auto-generated components
4. **Metadata Configuration**: Rich metadata with authorities, citations, and keywords
5. **Performance Patterns**: Efficient registration for production use

## Related Documentation

- **Getting Started Guide**: `docs/portal-development/getting_started.md`
  - Basic registration walkthrough and first model creation

- **Model Configuration Guide**: `docs/portal-development/model_configuration.md`
  - Complete API reference for ModelConfiguration options

- **Registry Usage**: `docs/portal-development/using_the_registry.md`
  - Advanced patterns and introspection capabilities
"""

from django.utils.translation import gettext_lazy as _

from fairdm.registry import ModelConfiguration, register
from fairdm.registry.config import Authority, Citation, ModelMetadata

# Import filters lazily to avoid app registry issues
# from .filters import CustomSampleFilter
from .models import (
    CustomParentSample,
    CustomSample,
    ExampleMeasurement,
    ICP_MS_Measurement,
    RockSample,
    SoilSample,
    WaterSample,
    XRFMeasurement,
)
from .tables import CustomSampleTable


@register
class CustomParentSampleConfig(ModelConfiguration):
    """
    Example configuration demonstrating rich metadata and authority information.

    This configuration showcases:
    - Complete metadata with authority, citation, and repository information
    - Grouped field layouts using tuples for visual organization
    - Custom resource class for specialized import/export handling
    - Internationalization support with gettext_lazy

    See: docs/portal-development/model_configuration.md#metadata-configuration
    """

    model = CustomParentSample
    metadata = ModelMetadata(
        description="A rock sample is a naturally occurring solid material that is composed of one or more minerals or mineraloids and represents a fragment of a larger geological formation or rock unit. The sample is typically obtained from a specific location in order to study its physical properties, mineral composition, texture, structure, and formation processes.",
        authority=Authority(
            name=str(_("FairDM Core Development")),
            short_name="FairDM",
            website="https://fairdm.org",
        ),
        citation=Citation(
            text="FairDM Core Development Team (2021). FairDM: A FAIR Data Management Tool. https://fairdm.org",
            doi="https://doi.org/10.5281/zenodo.123456",
        ),
        repository_url="https://github.com/FAIR-DM/fairdm",
        keywords=[],
    )
    fields = [
        ("name", "status"),
        "char_field",
    ]
    # resource_class = SampleResource  # Not implemented in demo
    # table_class = SampleTable


@register
class CustomSampleConfig(ModelConfiguration):
    """
    Advanced configuration with custom component classes and component-specific fields.

    This configuration demonstrates:
    - Component-specific field definitions (different fields for table vs form)
    - Custom Table and FilterSet class overrides
    - Mixed auto-generation and custom components
    - Performance optimization through targeted field selection

    Pattern: Use this approach when you need fine-grained control over
    different UI components while maintaining auto-generation benefits.

    See: docs/portal-development/model_configuration.md#component-specific-fields
    """

    model = CustomSample
    metadata = ModelMetadata(
        description="A thin section is a small, flat slice of rock, mineral, or other material that has been carefully ground and polished to a standard thickness, typically around 30 micrometers (0.03 millimeters). This thinness allows light to pass through the sample when viewed under a polarizing light microscope. Thin sections are used in petrography (the study of rocks) and mineralogy to examine the optical properties, texture, and microstructure of the sample, which helps in identifying the minerals present, understanding the rock's formation history, and determining its geological significance.",
        authority=Authority(
            name=str(_("FairDM Core Development")),
            short_name="FairDM",
            website="https://fairdm.org",
        ),
        citation=Citation(
            text="FairDM Core Development Team (2021). FairDM: A FAIR Data Management Tool. https://fairdm.org",
            doi="https://doi.org/10.5281/zenodo.123456",
        ),
        repository_url="https://github.com/FAIR-DM/fairdm",
        keywords=[],
    )

    # Use custom classes for specific components (using string references to avoid import issues)
    filterset_class = "fairdm_demo.filters.CustomSampleFilter"
    table_class = CustomSampleTable

    # Field configuration for different components
    table_fields = [
        "name",
        "char_field",
        "boolean_field",
        "date_field",
    ]

    form_fields = [
        "name",
        "char_field",
        "text_field",
        "integer_field",
        "boolean_field",
        "date_field",
        "date_time_field",
        "time_field",
        "decimal_field",
        "float_field",
    ]

    filterset_fields = [
        "char_field",
        "boolean_field",
        "date_field",
    ]

    resource_fields = [
        "name",
        "char_field",
        "text_field",
        "integer_field",
        "boolean_field",
        "date_field",
    ]


@register
class ExampleMeasurementConfig(ModelConfiguration):
    model = ExampleMeasurement
    metadata = ModelMetadata(
        description="An example measurement",
        authority=Authority(
            name=str(_("FairDM Core Development")),
            short_name="FairDM",
            website="https://fairdm.org",
        ),
        citation=Citation(
            text="FairDM Core Development Team (2021). FairDM: A FAIR Data Management Tool. https://fairdm.org",
            doi="https://doi.org/10.5281/zenodo.123456",
        ),
        repository_url="https://github.com/FAIR-DM/fairdm",
        keywords=[],
    )
    # resource_class = MeasurementResource  # Not implemented in demo
    # table_class = MeasurementTable  # Not implemented in demo
    fields = [
        "sample",
        "name",
        "char_field",
        "text_field",
        "integer_field",
        "big_integer_field",
        "positive_integer_field",
        "positive_small_integer_field",
        "small_integer_field",
        "boolean_field",
        "date_field",
        "date_time_field",
        "time_field",
        "decimal_field",
        "float_field",
    ]


# ========================================================================
# Pattern 1: Minimal Configuration (RockSample)
# ========================================================================
# Just specify the fields you want to display. FairDM auto-generates everything else.
# This is the recommended approach for most models.
#
# See: Developer Guide > Registry > Registration Patterns
#      quickstart.md for setup instructions


@register
class RockSampleConfig(ModelConfiguration):
    """Demonstrates minimal registry configuration with auto-generation.

    Only the model and fields are specified. FairDM automatically generates:
    - Form with appropriate widgets for each field type
    - Table with sortable columns
    - FilterSet for common search patterns
    - Serializer for API endpoints
    - Import/Export resource for CSV/Excel
    - ModelAdmin for Django admin

    See: Developer Guide > Registry > Minimal Configuration
    """

    model = RockSample
    metadata = ModelMetadata(
        description=_(
            "Geological rock samples demonstrating minimal FairDM registry "
            "configuration. All components (form, table, filters) are "
            "auto-generated from field definitions."
        ),
        authority=Authority(
            name=str(_("FairDM Demo Project")),
            short_name="Demo",
            website="https://fairdm.org/demo",
        ),
        keywords=["geology", "rocks", "minerals", "demo"],
    )
    fields = [
        "name",
        "rock_type",
        "collection_date",
        "weight_grams",
        "hardness_mohs",
        "mineral_content",
    ]


# ========================================================================
# Pattern 2: Component-Specific Fields (SoilSample)
# ========================================================================
# Specify different fields for different components when you need
# different information density in tables vs forms.
#
# - table_fields: Shows summary columns (less is more for scanning)
# - form_fields: Shows all editable fields (comprehensive data entry)
# - filterset_fields: Common search criteria
# - fields: Parent fallback when component-specific not provided
#
# See: Developer Guide > Registry > Component-Specific Configuration


@register
class SoilSampleConfig(ModelConfiguration):
    """Demonstrates component-specific field configuration.

    Different fields are shown in different contexts:
    - Table: Shows compact summary (soil_type, ph_level, depth_cm)
    - Form: Shows all editable fields for comprehensive data entry
    - Filters: Common search criteria (type, pH range, depth range)

    This pattern is useful when your model has many fields but tables
    need to remain scannable while forms need to be complete.

    See: Developer Guide > Registry > Component-Specific Fields
    """

    model = SoilSample
    metadata = ModelMetadata(
        description=_(
            "Soil samples demonstrating component-specific field configuration. "
            "Tables show summary data while forms provide comprehensive "
            "data entry interfaces."
        ),
        authority=Authority(
            name=str(_("FairDM Demo Project")),
            short_name="Demo",
            website="https://fairdm.org/demo",
        ),
        keywords=["soil", "agriculture", "environmental", "demo"],
    )

    # Parent fields - used as fallback when component-specific fields not provided
    fields = [
        "name",
        "soil_type",
        "ph_level",
        "depth_cm",
        "organic_matter_percent",
        "moisture_content",
    ]

    # Table shows summary info only (3-5 key fields)
    table_fields = [
        "name",
        "soil_type",
        "ph_level",
        "depth_cm",
    ]

    # Form shows all fields for data entry
    form_fields = [
        "name",
        "soil_type",
        "ph_level",
        "organic_matter_percent",
        "texture",
        "moisture_content",
        "depth_cm",
    ]

    # Filters for common search criteria
    filterset_fields = [
        "soil_type",
        "ph_level",
        "depth_cm",
    ]


# ========================================================================
# Pattern 3: Custom Component Classes (WaterSample)
# ========================================================================
# Provide your own Form/Table/FilterSet classes when you need:
# - Custom widgets or validation logic
# - Special column rendering or formatting (e.g., color-coded pH levels)
# - Complex filter behavior
#
# See: Developer Guide > Registry > Custom Components


@register
class WaterSampleConfig(ModelConfiguration):
    """Demonstrates custom component override (future enhancement).

    Currently using basic configuration. In production, you would provide:
    - form_class: Custom form with range validation, unit conversion widgets
    - table_class: Custom table with color-coded pH levels, trend indicators
    - filterset_class: Custom filters with range selectors, source filtering

    Example (when implemented):
        from .forms import WaterSampleForm
        from .tables import WaterSampleTable

        @register
        class WaterSampleConfig(ModelConfiguration):
            form_class = WaterSampleForm  # Custom widgets
            # table_class = WaterSampleTable  # Color-coded pH (not implemented in demo)
            ...

    See: Developer Guide > Registry > Custom Component Classes
    """

    model = WaterSample
    metadata = ModelMetadata(
        description=_(
            "Water quality samples demonstrating where custom component "
            "classes would be used (forms with special widgets, tables "
            "with color-coded values, advanced filters)."
        ),
        authority=Authority(
            name=str(_("FairDM Demo Project")),
            short_name="Demo",
            website="https://fairdm.org/demo",
        ),
        keywords=["water", "quality", "environmental", "demo"],
    )
    fields = [
        "name",
        "water_source",
        "temperature_celsius",
        "ph_level",
        "turbidity_ntu",
        "dissolved_oxygen_mg_l",
        "conductivity_us_cm",
    ]


# ========================================================================
# Accessing the Registry Programmatically
# ========================================================================
# You can query registered models and their configurations:
#
# # Get all registered Sample models
# samples = fairdm.registry.samples
# print(f"Registered samples: {[s.__name__ for s in samples]}")
#
# # Get configuration for a specific model
# config = fairdm.registry.get_for_model(RockSample)
# print(f"RockSample display name: {config.display_name}")
# print(f"RockSample fields: {config.fields}")
#
# # Access auto-generated components
# form_class = config.form  # Auto-generated ModelForm
# table_class = config.table  # Auto-generated Table
# filterset_class = config.filterset  # Auto-generated FilterSet
# admin_class = config.admin  # Auto-generated ModelAdmin


# List of all models registered in this demo app
# Used by tests to verify registration completeness
DEMO_REGISTERED_MODELS = [
    CustomParentSample,
    CustomSample,
    RockSample,
    SoilSample,
    WaterSample,
    ExampleMeasurement,
    XRFMeasurement,
    ICP_MS_Measurement,
]


# Additional measurement model registrations demonstrating different patterns


@register
class XRFMeasurementConfig(ModelConfiguration):
    """
    XRF measurement configuration demonstrating measurement-specific patterns.

    Shows field customization for analytical chemistry data and component overrides.
    """

    model = XRFMeasurement
    metadata = ModelMetadata(
        description="X-ray fluorescence (XRF) spectroscopy is an analytical technique used to determine the elemental composition of materials. This measurement records quantitative elemental analysis data including concentrations, detection limits, and analytical conditions.",
        authority=Authority(
            name=str(_("FairDM Demo Team")),
            short_name="FairDM-Demo",
            website="https://fairdm.org/demo",
        ),
        citation=Citation(
            text="FairDM Demo Team (2026). XRF Measurement Protocol. FairDM Demo Portal.",
            doi="https://doi.org/10.5281/zenodo.demo.xrf",
        ),
        keywords=["XRF", "elemental analysis", "spectroscopy", "geochemistry"],
    )
    fields = [
        "element",
        "concentration_ppm",
        "detection_limit_ppm",
        "instrument_model",
        "measurement_conditions",
    ]
    # resource_class = MeasurementResource  # Not implemented in demo
    # table_class = MeasurementTable  # Not implemented in demo


@register
class ICP_MS_MeasurementConfig(ModelConfiguration):
    """
    ICP-MS measurement configuration with advanced field patterns.

    Demonstrates complex measurement data with isotopic information and uncertainty.
    """

    model = ICP_MS_Measurement
    metadata = ModelMetadata(
        description="Inductively Coupled Plasma Mass Spectrometry (ICP-MS) is a highly sensitive analytical technique for trace element determination. This measurement captures isotope-specific data with quantitative concentrations, analytical uncertainties, and quality control parameters.",
        authority=Authority(
            name=str(_("FairDM Demo Team")),
            short_name="FairDM-Demo",
            website="https://fairdm.org/demo",
        ),
        citation=Citation(
            text="FairDM Demo Team (2026). ICP-MS Analytical Protocol. FairDM Demo Portal.",
            doi="https://doi.org/10.5281/zenodo.demo.icpms",
        ),
        keywords=["ICP-MS", "isotope analysis", "mass spectrometry", "trace elements", "geochronology"],
    )
    fields = [
        ("isotope", "counts_per_second"),
        "concentration_ppb",
        ("uncertainty_percent", "dilution_factor"),
        "internal_standard",
        "analysis_date",
    ]
    # resource_class = MeasurementResource  # Not implemented in demo
    # table_class = MeasurementTable  # Not implemented in demo
