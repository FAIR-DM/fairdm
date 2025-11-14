from django.utils.translation import gettext_lazy as _

from fairdm.contrib.import_export.resources import MeasurementResource, SampleResource
from fairdm.core.tables import MeasurementTable, SampleTable
from fairdm.registry import register
from fairdm.registry.config import Authority, Citation, ModelConfiguration, ModelMetadata

from .filters import CustomSampleFilter
from .models import CustomParentSample, CustomSample, ExampleMeasurement
from .tables import CustomSampleTable


@register
class CustomParentSampleConfig(ModelConfiguration):
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
        ("added", "modified"),
    ]
    resource_class = SampleResource
    table_class = SampleTable


@register
class CustomSampleConfig(ModelConfiguration):
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

    # Use custom classes for specific components
    filterset_class = CustomSampleFilter
    table_class = CustomSampleTable

    # Field configuration for different components
    table_fields = [
        "name",
        "char_field",
        "boolean_field",
        "date_field",
        "added",
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
        "added",
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
    resource_class = MeasurementResource
    table_class = MeasurementTable
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
