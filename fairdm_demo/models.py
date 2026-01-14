from fairdm.core.models import Measurement, Sample
from fairdm.db import models

# T033: Demo models showcasing different field types and patterns


class RockSample(Sample):
    """Geological rock sample demonstrating basic Sample registration.

    This model shows the minimal configuration approach - just define
    your fields and let FairDM auto-generate forms, tables, filters.

    See: Developer Guide > Models > Sample Models
    """

    rock_type = models.CharField(
        "Rock Type",
        max_length=100,
        help_text="Type of rock (e.g., igneous, sedimentary, metamorphic)",
    )
    mineral_content = models.TextField(
        "Mineral Content",
        help_text="Description of minerals present in the sample",
        blank=True,
    )
    weight_grams = models.FloatField(
        "Weight (grams)",
        help_text="Sample weight in grams",
        null=True,
        blank=True,
    )
    collection_date = models.DateField(
        "Collection Date",
        help_text="Date when sample was collected",
    )
    hardness_mohs = models.DecimalField(
        "Mohs Hardness",
        max_digits=3,
        decimal_places=1,
        help_text="Hardness on Mohs scale (1-10)",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"


class SoilSample(Sample):
    """Soil sample demonstrating component-specific field configuration.

    This model showcases how to use different field lists for different
    components (table, form, filterset) in the registry configuration.

    See: Developer Guide > Registry > Field Resolution
    """

    soil_type = models.CharField(
        "Soil Type",
        max_length=50,
        help_text="Classification of soil type",
    )
    ph_level = models.DecimalField(
        "pH Level",
        max_digits=4,
        decimal_places=2,
        help_text="Soil pH (0-14 scale)",
    )
    organic_matter_percent = models.FloatField(
        "Organic Matter (%)",
        help_text="Percentage of organic matter",
        null=True,
        blank=True,
    )
    texture = models.CharField(
        "Soil Texture",
        max_length=100,
        help_text="Soil texture classification",
        blank=True,
    )
    moisture_content = models.FloatField(
        "Moisture Content (%)",
        help_text="Percentage of moisture",
        null=True,
        blank=True,
    )
    depth_cm = models.IntegerField(
        "Depth (cm)",
        help_text="Sampling depth in centimeters",
    )

    class Meta:
        verbose_name = "Soil Sample"
        verbose_name_plural = "Soil Samples"


class WaterSample(Sample):
    """Water sample demonstrating custom form/table override.

    This model shows how to provide custom form/table classes
    when you need special widgets or custom column behavior.

    See: Developer Guide > Registry > Custom Components
    """

    water_source = models.CharField(
        "Water Source",
        max_length=100,
        help_text="Source of water (river, lake, groundwater, etc.)",
    )
    temperature_celsius = models.FloatField(
        "Temperature (°C)",
        help_text="Water temperature in Celsius",
    )
    ph_level = models.DecimalField(
        "pH Level",
        max_digits=4,
        decimal_places=2,
        help_text="Water pH (0-14 scale)",
    )
    turbidity_ntu = models.FloatField(
        "Turbidity (NTU)",
        help_text="Turbidity in Nephelometric Turbidity Units",
        null=True,
        blank=True,
    )
    dissolved_oxygen_mg_l = models.FloatField(
        "Dissolved Oxygen (mg/L)",
        help_text="Dissolved oxygen concentration",
        null=True,
        blank=True,
    )
    conductivity_us_cm = models.FloatField(
        "Conductivity (μS/cm)",
        help_text="Electrical conductivity",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Water Sample"
        verbose_name_plural = "Water Samples"


# Original demo models (kept for backward compatibility)


class CustomParentSample(Sample):
    char_field = models.CharField(
        "Character Field", max_length=200, help_text="Enter a string of up to 200 characters."
    )

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"


class CustomSample(Sample):
    char_field = models.CharField(
        "Character Field", max_length=200, help_text="Enter a string of up to 200 characters.", blank=True, null=True
    )
    text_field = models.TextField("Text Field", help_text="Enter a large amount of text.", blank=True, null=True)
    integer_field = models.IntegerField("Integer Field", help_text="Enter an integer.", blank=True, null=True)
    big_integer_field = models.BigIntegerField(
        "Big Integer Field", help_text="Enter a large integer.", blank=True, null=True
    )
    positive_integer_field = models.PositiveIntegerField(
        "Positive Integer Field", help_text="Enter a positive integer.", blank=True, null=True
    )
    positive_small_integer_field = models.PositiveSmallIntegerField(
        "Positive Small Integer Field", help_text="Enter a small positive integer.", blank=True, null=True
    )
    small_integer_field = models.SmallIntegerField(
        "Small Integer Field", help_text="Enter a small integer.", blank=True, null=True
    )
    boolean_field = models.BooleanField(
        "Boolean Field", default=False, help_text="Select True or False.", blank=True, null=True
    )
    date_field = models.DateField("Date Field", help_text="Select a date.", blank=True, null=True)
    date_time_field = models.DateTimeField(
        "Date Time Field", help_text="Select a date and time.", blank=True, null=True
    )
    time_field = models.TimeField("Time Field", help_text="Select a time.", blank=True, null=True)
    decimal_field = models.DecimalField(
        "Decimal Field", max_digits=5, decimal_places=2, help_text="Enter a decimal number.", blank=True, null=True
    )
    float_field = models.FloatField("Float Field", help_text="Enter a floating point number.", blank=True, null=True)

    class Meta:
        verbose_name = "Thin Section"
        verbose_name_plural = "Thin Sections"


class ExampleMeasurement(Measurement):
    """Example measurement demonstrating basic Measurement registration.

    This model shows various field types supported in measurements
    and serves as a reference for standard measurement patterns.

    See: Developer Guide > Models > Measurement Models
    """

    # standard django fields
    char_field = models.CharField(
        "Character Field", max_length=200, help_text="Enter a string of up to 200 characters.", blank=True, null=True
    )
    text_field = models.TextField("Text Field", help_text="Enter a large amount of text.", blank=True, null=True)
    integer_field = models.IntegerField("Integer Field", help_text="Enter an integer.", blank=True, null=True)
    big_integer_field = models.BigIntegerField(
        "Big Integer Field", help_text="Enter a large integer.", blank=True, null=True
    )
    positive_integer_field = models.PositiveIntegerField(
        "Positive Integer Field", help_text="Enter a positive integer.", blank=True, null=True
    )
    positive_small_integer_field = models.PositiveSmallIntegerField(
        "Positive Small Integer Field", help_text="Enter a small positive integer.", blank=True, null=True
    )
    small_integer_field = models.SmallIntegerField(
        "Small Integer Field", help_text="Enter a small integer.", blank=True, null=True
    )
    boolean_field = models.BooleanField(
        "Boolean Field", default=False, help_text="Select True or False.", blank=True, null=True
    )
    date_field = models.DateField("Date Field", help_text="Select a date.", blank=True, null=True)
    date_time_field = models.DateTimeField(
        "Date Time Field", help_text="Select a date and time.", blank=True, null=True
    )
    time_field = models.TimeField("Time Field", help_text="Select a time.", blank=True, null=True)
    decimal_field = models.DecimalField(
        "Decimal Field", max_digits=5, decimal_places=2, help_text="Enter a decimal number.", blank=True, null=True
    )
    float_field = models.FloatField("Float Field", help_text="Enter a floating point number.", blank=True, null=True)


class XRFMeasurement(Measurement):
    """
    X-ray fluorescence (XRF) spectroscopy measurement.

    Demonstrates a measurement model with specific analytical parameters
    and custom configuration patterns in the registry.
    """

    element = models.CharField("Element", max_length=10, help_text="Chemical element symbol (e.g., Si, Al, Fe)")
    concentration_ppm = models.DecimalField(
        "Concentration (ppm)", max_digits=10, decimal_places=2, help_text="Element concentration in parts per million"
    )
    detection_limit_ppm = models.DecimalField(
        "Detection Limit (ppm)",
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Analytical detection limit in parts per million",
    )
    instrument_model = models.CharField(
        "Instrument Model", max_length=100, blank=True, help_text="XRF instrument model used for analysis"
    )
    measurement_conditions = models.TextField(
        "Measurement Conditions", blank=True, help_text="Analytical conditions (voltage, current, atmosphere, etc.)"
    )

    class Meta:
        verbose_name = "XRF Measurement"
        verbose_name_plural = "XRF Measurements"


class ICP_MS_Measurement(Measurement):
    """
    Inductively Coupled Plasma Mass Spectrometry (ICP-MS) measurement.

    Demonstrates a measurement model with isotope-specific data
    and advanced field validation patterns.
    """

    isotope = models.CharField("Isotope", max_length=20, help_text="Isotope notation (e.g., 207Pb, 206Pb, 238U)")
    counts_per_second = models.DecimalField(
        "Counts per Second", max_digits=15, decimal_places=2, help_text="Raw instrument counts per second"
    )
    concentration_ppb = models.DecimalField(
        "Concentration (ppb)",
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Calculated concentration in parts per billion",
    )
    uncertainty_percent = models.DecimalField(
        "Uncertainty (%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Analytical uncertainty as percentage",
    )
    dilution_factor = models.DecimalField(
        "Dilution Factor", max_digits=8, decimal_places=2, default=1.0, help_text="Sample dilution factor applied"
    )
    internal_standard = models.CharField(
        "Internal Standard", max_length=20, blank=True, help_text="Internal standard isotope used for drift correction"
    )
    analysis_date = models.DateTimeField(
        "Analysis Date", null=True, blank=True, help_text="Date and time of ICP-MS analysis"
    )

    class Meta:
        verbose_name = "ICP-MS Measurement"
        verbose_name_plural = "ICP-MS Measurements"
