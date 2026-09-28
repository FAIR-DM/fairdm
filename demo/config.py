"""Model registrations for the demo portal.

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

import fairdm
from fairdm.core.measurement.config import BaseMeasurementConfiguration
from fairdm.core.sample.config import BaseSampleConfiguration
from fairdm.registry import ModelConfiguration
from fairdm.registry.config import Authority, Citation, ModelMetadata

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


@fairdm.register
class CustomParentSampleConfig(BaseSampleConfiguration):
    """Example configuration demonstrating rich metadata and authority information.

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


@fairdm.register
class CustomSampleConfig(ModelConfiguration):
    """Advanced configuration with custom component classes and component-specific fields.

    Stays on `ModelConfiguration` rather than `BaseSampleConfiguration` on purpose:
    it declares no shared `fields` list at all, relying on the framework's own
    per-component field auto-detection for every component it does not name
    explicitly (`table_class`, `filterset_class`, `form_fields`,
    `resource_fields`). Inheriting `BaseSampleConfiguration` would hand every
    other component `BaseSampleConfiguration.fields` instead of that
    auto-detection, silently narrowing them - the opposite of what this
    configuration demonstrates.

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

    # The table and the filter set are supplied outright, so neither declares a
    # field list: a component configured both ways is refused at registration,
    # because the field list could never take effect.
    filterset_class = "demo.filters.CustomSampleFilter"
    table_class = CustomSampleTable

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

    resource_fields = [
        "name",
        "char_field",
        "text_field",
        "integer_field",
        "boolean_field",
        "date_field",
    ]


@fairdm.register
class ExampleMeasurementConfig(BaseMeasurementConfiguration):
    """Demonstration measurement configuration showing all supported field types.

    This example measurement serves as executable documentation for portal developers,
    illustrating how different field types (text, numeric, boolean, date/time) are
    represented in the FairDM registry and exposed via API endpoints.

    See: Developer Guide > Models > Custom Measurement Types
    """

    model = ExampleMeasurement
    metadata = ModelMetadata(
        description=(
            "A general-purpose example measurement that demonstrates all supported field "
            "types in the FairDM registry. Used as executable documentation for portal "
            "developers learning how to define custom measurement types."
        ),
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
    # Narrower than the default: `name` is not searched.
    search_fields = ["char_field"]


@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
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
    # Narrower than the default: `name` is not searched.
    search_fields = ["rock_type"]


@fairdm.register
class SoilSampleConfig(BaseSampleConfiguration):
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

    # Fallback for every component without its own field list.
    fields = [
        "name",
        "soil_type",
        "ph_level",
        "depth_cm",
        "organic_matter_percent",
        "moisture_content",
    ]

    table_fields = [
        "name",
        "soil_type",
        "ph_level",
        "depth_cm",
    ]

    form_fields = [
        "name",
        "soil_type",
        "ph_level",
        "organic_matter_percent",
        "texture",
        "moisture_content",
        "depth_cm",
    ]

    filterset_fields = [
        "soil_type",
        "ph_level",
        "depth_cm",
    ]

    # Names the default (`name`) explicitly alongside `soil_type`.
    search_fields = ["name", "soil_type"]


@fairdm.register
class WaterSampleConfig(BaseSampleConfiguration):
    """Demonstrates the third tier of customisation: overriding an accessor.

    The first two tiers are declarations. A field list configures every component,
    and a class attribute such as ``table_class`` replaces one of them outright.
    Both are enough for almost every portal.

    The third tier exists for the case a declaration cannot express, because the
    answer has to be worked out in code. Override the component's accessor and
    return whatever you like. Every part of the framework that needs that component
    calls the accessor, so your class is what all of it receives.

    Below, the filter set is narrowed to the fields that make sense to filter on,
    chosen from the shared field list rather than restated, so adding a field to
    ``fields`` does not silently add a filter for it.

    See: Developer Guide > Registry > Overriding a component accessor
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

    #: Fields worth filtering on, as opposed to merely displaying.
    FILTERABLE = {"water_source", "ph_level", "temperature_celsius"}

    def get_filterset_class(self):
        """Build the filter set from the filterable subset of `fields`."""
        # Derived so that a new entry in `fields` does not silently gain a filter.
        from fairdm.registry.factories import FilterFactory

        filterable = [
            f for f in self.resolve_fields("filterset") if f in self.FILTERABLE
        ]
        return FilterFactory(model=self.model, fields=filterable).generate()


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


@fairdm.register
class XRFMeasurementConfig(BaseMeasurementConfiguration):
    """XRF measurement configuration demonstrating measurement-specific patterns.

    Shows field customization for analytical chemistry data and component overrides.
    The ``metadata.description`` value surfaces in Swagger UI as the operation
    description for all ``/api/v1/measurements/xrf-measurements/`` endpoints.

    See: Developer Guide > RESTful API > Model Descriptions in the API Docs
    (docs/portal-development/restful-api.md#model-descriptions-in-the-api-docs)
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


@fairdm.register
class ICP_MS_MeasurementConfig(BaseMeasurementConfiguration):
    """ICP-MS measurement configuration with advanced field patterns.

    Demonstrates complex measurement data with isotopic information and uncertainty.
    The ``metadata.description`` value surfaces in Swagger UI as the operation
    description for all ``/api/v1/measurements/icp-ms-measurements/`` endpoints.

    See: Developer Guide > RESTful API > Model Descriptions in the API Docs
    (docs/portal-development/restful-api.md#model-descriptions-in-the-api-docs)
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
        keywords=[
            "ICP-MS",
            "isotope analysis",
            "mass spectrometry",
            "trace elements",
            "geochronology",
        ],
    )
    fields = [
        ("isotope", "counts_per_second"),
        "concentration_ppb",
        ("uncertainty_percent", "dilution_factor"),
        "internal_standard",
        "analysis_date",
    ]
