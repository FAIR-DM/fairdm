from fairdm.core.models import Measurement, Sample
from fairdm.db import models

# T033: Demo models showcasing different field types and patterns

\"\"\"FairDM Demo App Models

This module demonstrates recommended patterns for defining custom Sample and
Measurement models in FairDM portals. It showcases various field types, metadata
configurations, and relationship patterns.

**Dataset Metadata Best Practices:**

Datasets support rich FAIR metadata through related models. These examples show
how to programmatically create metadata:

1. **Literature Relationships (DatasetLiteratureRelation)**:

   Use DataCite relationship types to link datasets with publications:

   ```python
   from fairdm.core.dataset.models import DatasetLiteratureRelation
   from literature.models import LiteratureItem

   # Create a literature reference
   paper = LiteratureItem.objects.create(
       title=\"XRF Analysis Methods\",
       authors=\"Smith, J.; Doe, A.\",
       year=2024
   )

   # Link to dataset with relationship type
   DatasetLiteratureRelation.objects.create(
       dataset=my_dataset,
       literature_item=paper,
       relationship_type=\"IsDocumentedBy\"  # DataCite vocabulary
   )

   # Available relationship types (DataCite Metadata Schema 4.4):
   # IsCitedBy, Cites, IsSupplementTo, IsSupplementedBy, IsContinuedBy,
   # Continues, IsDescribedBy, Describes, HasMetadata, IsMetadataFor,
   # HasVersion, IsVersionOf, IsNewVersionOf, IsPreviousVersionOf, IsPartOf,
   # HasPart, IsPublishedIn, IsReferencedBy, References, IsDocumentedBy,
   # Documents, IsCompiledBy, Compiles, IsVariantFormOf, IsOriginalFormOf,
   # IsIdenticalTo, IsReviewedBy, Reviews, IsDerivedFrom, IsSourceOf,
   # IsRequiredBy, Requires, Obsoletes, IsObsoletedBy
   ```

2. **DOI Assignment (DatasetIdentifier)**:

   Assign DOIs using the DatasetIdentifier model (NOT the reference field):

   ```python
   from fairdm.core.dataset.models import DatasetIdentifier

   # Assign a DOI to a dataset
   doi = DatasetIdentifier.objects.create(
       related=my_dataset,
       type=\"DOI\",
       value=\"10.5061/dryad.12345\"
   )

   # Access DOI through convenience property
   if my_dataset.doi:
       print(f\"Dataset DOI: {my_dataset.doi}\")

   # Query datasets by DOI
   dataset = Dataset.objects.filter(
       identifiers__type=\"DOI\",
       identifiers__value=\"10.5061/dryad.12345\"
   ).first()
   ```

3. **Other Metadata Types**:

   ```python
   from fairdm.core.dataset.models import (
       DatasetDescription, DatasetDate, DatasetIdentifier
   )

   # Rich descriptions (one per type)
   DatasetDescription.objects.create(
       related=my_dataset,
       type=\"Abstract\",
       value=\"This dataset contains XRF measurements...\"
   )
   DatasetDescription.objects.create(
       related=my_dataset,
       type=\"Methods\",
       value=\"Samples were analyzed using...\"
   )

   # Temporal metadata (one per type)
   DatasetDate.objects.create(
       related=my_dataset,
       type=\"Created\",
       value=\"2024-01-15\"  # PartialDate format: YYYY, YYYY-MM, or YYYY-MM-DD
   )
   DatasetDate.objects.create(
       related=my_dataset,
       type=\"Available\",
       value=\"2024-06-01\"
   )

   # Additional identifiers (must be globally unique)
   DatasetIdentifier.objects.create(
       related=my_dataset,
       type=\"ARK\",
       value=\"ark:/12345/xyz123\"
   )
   ```
**QuerySet Optimization Patterns (T145-T146):**

FairDM provides optimized QuerySet methods to reduce N+1 query problems and
improve performance. Use these patterns in your views and APIs:

1. **Privacy-First Default**:

   By default, Dataset.objects.all() EXCLUDES PRIVATE datasets:

   ```python
   # Default behavior - excludes PRIVATE datasets
   public_datasets = Dataset.objects.all()  # Only PUBLIC and INTERNAL

   # Explicit access to private datasets (opt-in)
   all_datasets = Dataset.objects.with_private()  # Includes PRIVATE

   # Use in views with permission checks
   class DatasetListView(ListView):
       def get_queryset(self):
           qs = Dataset.objects.all()  # Privacy-first default

           # Grant private access based on permissions
           if self.request.user.has_perm('dataset.view_private'):
               qs = qs.with_private()

           return qs.with_related()  # Optimize queries
   ```

2. **Query Optimization with with_related()**:

   Reduces N+1 queries by 80%+ when accessing related objects:

   ```python
   # WITHOUT optimization (naive) - 21 queries for 10 datasets
   for ds in Dataset.objects.all():
       print(ds.project.name)  # N+1 query!
       print(ds.contributors.count())  # N+1 query!

   # WITH optimization - only 3 queries for 10 datasets
   for ds in Dataset.objects.with_related():
       print(ds.project.name)  # No additional query
       print(ds.contributors.count())  # No additional query

   # Expected query counts:
   # - 1 query: Main dataset query
   # - 1 query: Prefetch projects
   # - 1 query: Prefetch contributors
   # Total: 3 queries (86% reduction)
   ```

3. **Lighter Optimization with with_contributors()**:

   When you only need contributors (not projects), use the lighter method:

   ```python
   # Prefetch only contributors (2 queries instead of 3)
   datasets = Dataset.objects.with_contributors()
   for ds in datasets:
       # Access contributors without additional queries
       for contributor in ds.contributors.all():
           print(f"Contributor: {contributor.person.name}")
   ```

4. **Method Chaining**:

   All QuerySet methods can be chained in any order:

   ```python
   # Chain methods for complex queries
   datasets = (
       Dataset.objects
       .with_private()  # Include private datasets
       .filter(project=my_project)  # Filter by project
       .exclude(visibility=Dataset.Visibility.INTERNAL)  # Exclude internal
       .with_related()  # Optimize queries
       .order_by('-modified')  # Order by most recent
   )

   # Chain with search and filtering
   from fairdm.core.dataset.filters import DatasetFilter

   filterset = DatasetFilter(
       data=request.GET,
       queryset=Dataset.objects.with_private().with_related()
   )
   filtered_datasets = filterset.qs  # Filtered and optimized
   ```

5. **Performance Monitoring**:

   Verify query optimization with Django Debug Toolbar:

   ```python
   # In development, enable query logging
   from django.conf import settings
   settings.DEBUG = True

   # Check query count with django-debug-toolbar
   # Or use django.db.connection.queries
   from django.db import connection
   from django.test.utils import override_settings

   @override_settings(DEBUG=True)
   def view_datasets(request):
       connection.queries_log.clear()

       # Your query
       datasets = list(Dataset.objects.with_related()[:10])

       # Check query count
       print(f"Queries executed: {len(connection.queries)}")
       # Should be ≤3 queries regardless of result count
   ```

6. **Custom QuerySet for Your Models**:

   Apply the same patterns to your custom Sample/Measurement models:

   ```python
   from django.db.models import QuerySet

   class RockSampleQuerySet(QuerySet):
       \"\"\"Custom QuerySet with optimization methods.\"\"\"

       def with_location_data(self):
           \"\"\"Prefetch location and related geographic data.\"\"\"
           return self.select_related('location').prefetch_related(
               'location__coordinates',
               'location__region'
           )

       def with_measurements(self):
           \"\"\"Prefetch all related measurements.\"\"\"
           return self.prefetch_related('measurements')

   class RockSample(Sample):
       objects = RockSampleQuerySet.as_manager()
       # ... fields ...

   # Use in views
   samples = RockSample.objects.with_location_data().with_measurements()
   ```
**Portal Developer Notes:**

- All metadata models use the `related` field (not `dataset`) due to abstract
  base classes
- Metadata types are validated against controlled vocabularies (see Dataset model
  class attributes: DATE_TYPES, DESCRIPTION_TYPES, IDENTIFIER_TYPES)
- unique_together constraints ensure only one metadata entry per type per dataset
- DOIs should be assigned via DatasetIdentifier, not the reference field
- The reference field is for the primary data publication (LiteratureItem)

See Also:
    - Developer Guide > Models > Dataset Metadata
    - Developer Guide > Registry > Metadata Configuration
    - specs/006-core-datasets/quickstart.md
\"\"\"


class RockSample(Sample):
    \"\"\"Geological rock sample demonstrating basic Sample registration.

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
