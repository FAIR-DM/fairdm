# Measurement Development Guide

This guide walks you through creating custom measurement types in FairDM, from defining models to configuring admin interfaces and optimizing queries.

## Overview

Measurements in FairDM are polymorphic models that represent observations or analyses performed on samples. Each measurement type can have its own specific fields while sharing common metadata infrastructure.

**Key Concepts:**

- **Polymorphic inheritance**: Multiple measurement types in one table structure
- **Cross-dataset linking**: Measurements can reference samples from different datasets
- **Automatic admin generation**: Registry creates admin interfaces automatically
- **QuerySet optimization**: Built-in methods for efficient data loading
- **FAIR metadata**: Descriptions, dates, identifiers, contributors all included

## Step 1: Define Your Measurement Model

### Basic Structure

Create a new measurement type by subclassing `Measurement`:

```python
# myapp/models.py
from django.db import models
from fairdm.core import Measurement

class XRFMeasurement(Measurement):
    """X-ray fluorescence measurement for elemental analysis."""

    # Domain-specific fields
    element = models.CharField(
        max_length=10,
        help_text="Chemical symbol (e.g., Fe, Si, Ca)"
    )
    concentration_ppm = models.FloatField(
        help_text="Concentration in parts per million"
    )
    detection_limit_ppm = models.FloatField(
        null=True,
        blank=True,
        help_text="Instrument detection limit"
    )

    class Meta:
        verbose_name = "XRF Measurement"
        verbose_name_plural = "XRF Measurements"

    def get_value(self):
        """Return human-readable measurement value."""
        return f"{self.element}: {self.concentration_ppm} ppm"
```

**What you get automatically:**

- `sample` - ForeignKey to the sample being measured
- `dataset` - ForeignKey to the dataset containing this measurement
- `name` - Descriptive name for the measurement
- `image` - Optional image/plot
- `created`, `modified` - Automatic timestamps
- All FAIR metadata fields (descriptions, dates, identifiers, contributors)

### The `get_value()` Method

Override `get_value()` to provide a human-readable representation:

```python
def get_value(self):
    """Used in admin lists, detail views, and string representations."""
    if self.detection_limit_ppm and self.concentration_ppm < self.detection_limit_ppm:
        return f"{self.element}: <{self.detection_limit_ppm} ppm (below detection limit)"
    return f"{self.element}: {self.concentration_ppm} ppm"
```

This appears in:

- Admin changelist columns
- Measurement detail pages
- Search results
- String representations (`str(measurement)`)

### Advanced Example: ICP-MS Measurement

```python
class ICP_MS_Measurement(Measurement):
    """ICP-MS measurement with isotope-specific detection."""

    isotope = models.CharField(
        max_length=10,
        help_text="Isotope notation (e.g., 207Pb, 238U)"
    )
    counts_per_second = models.FloatField(
        help_text="Raw instrument counts per second"
    )
    concentration_ppb = models.FloatField(
        help_text="Calculated concentration in parts per billion"
    )
    standard_used = models.CharField(
        max_length=100,
        blank=True,
        help_text="Calibration standard reference"
    )

    class Meta:
        verbose_name = "ICP-MS Measurement"
        verbose_name_plural = "ICP-MS Measurements"

    def get_value(self):
        return f"{self.isotope}: {self.concentration_ppb} ppb ({self.counts_per_second:.0f} cps)"
```

## Step 2: Register Your Measurement

Use the FairDM registry to automatically generate admin, forms, filters, and tables:

```python
# myapp/config.py
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration
from .models import XRFMeasurement

@register
class XRFMeasurementConfig(ModelConfiguration):
    model = XRFMeasurement

    # Fields shown in admin list view
    list_fields = ["name", "sample", "element", "concentration_ppm", "dataset"]

    # Fields shown in detail view and forms
    detail_fields = [
        "name", "sample", "dataset",
        "element", "concentration_ppm", "detection_limit_ppm"
    ]

    # Fields available for filtering
    filterset_fields = ["element", "dataset", "sample"]

    # Searchable fields in admin
    search_fields = ["name", "element", "sample__name"]
```

**Configuration Options:**

| Option | Purpose | Example |
|--------|---------|---------|
| `list_fields` | Columns in admin changelist | `["name", "element", "concentration_ppm"]` |
| `detail_fields` | Fields in add/change forms | `["name", "sample", "dataset", "element"]` |
| `filterset_fields` | Filter sidebar options | `["element", "dataset"]` |
| `search_fields` | Full-text search fields | `["name", "element", "sample__name"]` |
| `table_class` | Custom django-tables2 Table | `MyCustomMeasurementTable` |
| `form_class` | Custom ModelForm | `XRFMeasurementForm` |
| `filterset_class` | Custom FilterSet | `XRFMeasurementFilter` |

## Step 3: Create Custom Admin (Optional)

If you need custom admin behavior beyond what the registry provides:

```python
# myapp/admin.py
from fairdm.core.measurement.admin import MeasurementChildAdmin
from .models import XRFMeasurement

class XRFMeasurementAdmin(MeasurementChildAdmin):
    """Custom admin for XRF measurements."""

    # Override default list display
    list_display = [
        "name", "sample", "element", "concentration_ppm",
        "detection_limit_ppm", "dataset", "created"
    ]

    # Add custom filters
    list_filter = ["element", "dataset", "created"]

    # Enhanced search
    search_fields = ["name", "element", "sample__name", "dataset__name"]

    # Fieldsets for organized form layout
    fieldsets = [
        ("Basic Information", {
            "fields": ["name", "sample", "dataset"]
        }),
        ("XRF Analysis", {
            "fields": ["element", "concentration_ppm", "detection_limit_ppm"],
            "description": "X-ray fluorescence elemental analysis results"
        }),
        ("Metadata", {
            "fields": ["image", "tags"],
            "classes": ["collapse"]
        }),
    ]

    # Custom queryset optimization
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sample', 'dataset', 'sample__dataset'
        ).prefetch_related('tags')

# Register with Django admin
from django.contrib import admin
admin.site.register(XRFMeasurement, XRFMeasurementAdmin)
```

**Key Base Classes:**

- `MeasurementChildAdmin` - For specific measurement types (XRF, ICP-MS, etc.)
  - Includes polymorphic handling
  - Adds metadata inlines automatically
  - Optimized querysets with select_related/prefetch_related

- `MeasurementParentAdmin` - For the base Measurement model (rarely customized)
  - Type selection interface
  - Redirects to appropriate child admin

## Step 4: Custom Forms and Filters

### Custom Forms with MeasurementFormMixin

The `MeasurementFormMixin` adds validation and widget configuration:

```python
# myapp/forms.py
from django import forms
from fairdm.core.measurement.forms import MeasurementFormMixin
from .models import XRFMeasurement

class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
    """Custom form with validation and enhanced widgets."""

    class Meta:
        model = XRFMeasurement
        fields = ["name", "sample", "dataset", "element", "concentration_ppm", "detection_limit_ppm"]
        widgets = {
            'element': forms.TextInput(attrs={
                'placeholder': 'e.g., Fe, Si, Ca',
                'pattern': '[A-Z][a-z]?',  # Chemical symbol format
            }),
            'concentration_ppm': forms.NumberInput(attrs={
                'min': '0',
                'step': '0.01',
            }),
        }

    def clean(self):
        """Custom validation."""
        cleaned_data = super().clean()
        concentration = cleaned_data.get('concentration_ppm')
        detection_limit = cleaned_data.get('detection_limit_ppm')

        if detection_limit and concentration and detection_limit > concentration:
            # This is okay, just mark it in get_value()
            pass

        return cleaned_data
```

**What MeasurementFormMixin provides:**

- Dataset/sample consistency validation
- Polymorphic type handling
- Standard widget configuration
- FAIR metadata field groups

### Custom Filters with MeasurementFilterMixin

```python
# myapp/filters.py
import django_filters
from fairdm.core.measurement.filters import MeasurementFilterMixin
from .models import XRFMeasurement

class XRFMeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
    """Custom filterset for XRF measurements."""

    # Range filter for concentration
    concentration_min = django_filters.NumberFilter(
        field_name='concentration_ppm',
        lookup_expr='gte',
        label='Minimum Concentration (ppm)'
    )
    concentration_max = django_filters.NumberFilter(
        field_name='concentration_ppm',
        lookup_expr='lte',
        label='Maximum Concentration (ppm)'
    )

    # Multiple choice for elements
    element = django_filters.MultipleChoiceFilter(
        choices=[
            ('Fe', 'Iron'),
            ('Si', 'Silicon'),
            ('Ca', 'Calcium'),
            ('Al', 'Aluminum'),
            ('Mg', 'Magnesium'),
        ]
    )

    class Meta:
        model = XRFMeasurement
        fields = {
            'dataset': ['exact'],
            'sample': ['exact'],
            'created': ['gte', 'lte'],
        }
```

**What MeasurementFilterMixin provides:**

- Common measurement filters (dataset, sample, date ranges)
- Cross-dataset filtering support
- Vocabulary-based filters for metadata

## Step 5: QuerySet Optimization

Use built-in QuerySet methods for efficient data loading:

```python
# In views or management commands
from myapp.models import XRFMeasurement

# Load measurements with related data (prevents N+1 queries)
measurements = XRFMeasurement.objects.with_related()

# Load measurements with FAIR metadata
measurements = XRFMeasurement.objects.with_metadata()

# Combine both
measurements = XRFMeasurement.objects.with_related().with_metadata()

# Filter and optimize
fe_measurements = XRFMeasurement.objects.filter(
    element='Fe'
).with_related().with_metadata()
```

**Available QuerySet Methods:**

| Method | What it loads | When to use |
|--------|---------------|-------------|
| `with_related()` | sample, dataset, sample.dataset | List views, API endpoints |
| `with_metadata()` | descriptions, dates, identifiers | Detail views, exports |
| `with_related().with_metadata()` | All of the above | Complete data exports |

### Custom QuerySet for Domain Logic

```python
# myapp/managers.py
from fairdm.core.measurement.managers import MeasurementQuerySet

class XRFMeasurementQuerySet(MeasurementQuerySet):
    """Custom queryset for XRF measurements."""

    def for_element(self, element):
        """Filter by chemical element."""
        return self.filter(element__iexact=element)

    def above_detection_limit(self):
        """Filter measurements above detection limit."""
        return self.filter(
            models.Q(detection_limit_ppm__isnull=True) |
            models.Q(concentration_ppm__gte=models.F('detection_limit_ppm'))
        )

    def major_elements(self):
        """Common major rock-forming elements."""
        return self.filter(element__in=['Si', 'Al', 'Fe', 'Ca', 'Mg', 'Na', 'K'])

# In models.py
class XRFMeasurement(Measurement):
    # ... fields ...

    objects = XRFMeasurementQuerySet.as_manager()
```

**Usage:**

```python
# All iron measurements above detection limit
fe_measurements = XRFMeasurement.objects.for_element('Fe').above_detection_limit()

# Major elements with related data
major = XRFMeasurement.objects.major_elements().with_related()
```

## Step 6: Permission Configuration

Measurements inherit permissions from their parent dataset. Permission configuration is deferred to Feature 007, but here's the planned structure:

```python
# Future: Custom permission backend (Feature 007)
from fairdm.core.measurement.permissions import MeasurementPermissionBackend

# Measurements inherit from dataset:
# - view_dataset → view_measurement
# - change_dataset → change_measurement
# - delete_dataset → delete_measurement
```

**Current behavior:**

- Django model-level permissions work (`user.has_perm('myapp.view_xrfmeasurement')`)
- Object-level permissions deferred to Feature 007

## Complete Example: Putting It All Together

Here's a complete example for a microscopy measurement type:

```python
# myapp/models.py
from django.db import models
from fairdm.core import Measurement
from fairdm.core.measurement.managers import MeasurementQuerySet

class MicroscopyQuerySet(MeasurementQuerySet):
    """Custom queryset for microscopy measurements."""

    def by_magnification(self, min_mag=None, max_mag=None):
        qs = self
        if min_mag:
            qs = qs.filter(magnification__gte=min_mag)
        if max_mag:
            qs = qs.filter(magnification__lte=max_mag)
        return qs

    def with_images(self):
        """Only measurements that have images."""
        return self.exclude(image='')

class MicroscopyMeasurement(Measurement):
    """Optical or electron microscopy image of a sample."""

    microscope_type = models.CharField(
        max_length=50,
        choices=[
            ('optical', 'Optical Microscope'),
            ('sem', 'Scanning Electron Microscope'),
            ('tem', 'Transmission Electron Microscope'),
        ]
    )
    magnification = models.IntegerField(
        help_text="Magnification factor (e.g., 100, 1000, 10000)"
    )
    scale_bar_microns = models.FloatField(
        null=True,
        blank=True,
        help_text="Length of scale bar in micrometers"
    )

    objects = MicroscopyQuerySet.as_manager()

    class Meta:
        verbose_name = "Microscopy Measurement"
        verbose_name_plural = "Microscopy Measurements"

    def get_value(self):
        return f"{self.get_microscope_type_display()} at {self.magnification}x"

# myapp/config.py
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class MicroscopyMeasurementConfig(ModelConfiguration):
    model = MicroscopyMeasurement
    list_fields = ["name", "sample", "microscope_type", "magnification", "dataset"]
    detail_fields = [
        "name", "sample", "dataset",
        "microscope_type", "magnification", "scale_bar_microns", "image"
    ]
    filterset_fields = ["microscope_type", "dataset", "sample"]
    search_fields = ["name", "sample__name"]

# myapp/admin.py
from django.contrib import admin
from fairdm.core.measurement.admin import MeasurementChildAdmin

class MicroscopyMeasurementAdmin(MeasurementChildAdmin):
    list_display = ["name", "sample", "microscope_type", "magnification", "dataset"]
    list_filter = ["microscope_type", "dataset"]

    fieldsets = [
        ("Basic Information", {
            "fields": ["name", "sample", "dataset"]
        }),
        ("Microscopy Settings", {
            "fields": ["microscope_type", "magnification", "scale_bar_microns"]
        }),
        ("Image", {
            "fields": ["image"]
        }),
    ]

admin.site.register(MicroscopyMeasurement, MicroscopyMeasurementAdmin)
```

## Testing Your Measurement Type

Create tests to verify your measurement implementation:

```python
# myapp/tests/test_xrf_measurement.py
import pytest
from myapp.models import XRFMeasurement
from fairdm.factories import SampleFactory, DatasetFactory

@pytest.mark.django_db
class TestXRFMeasurement:
    def test_create_measurement(self):
        """Test basic measurement creation."""
        sample = SampleFactory()
        measurement = XRFMeasurement.objects.create(
            name="Iron Analysis",
            sample=sample,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=5000.0
        )

        assert measurement.element == "Fe"
        assert measurement.get_value() == "Fe: 5000.0 ppm"

    def test_below_detection_limit(self):
        """Test handling of values below detection limit."""
        sample = SampleFactory()
        measurement = XRFMeasurement.objects.create(
            name="Trace Element",
            sample=sample,
            dataset=sample.dataset,
            element="Au",
            concentration_ppm=0.5,
            detection_limit_ppm=1.0
        )

        assert "<1.0 ppm" in measurement.get_value()
```

## Best Practices

1. **Always override `get_value()`** - Provides consistent string representation
2. **Use QuerySet methods** - Prevent N+1 queries with `with_related()`
3. **Validate data** - Add `clean()` methods for domain-specific validation
4. **Test cross-dataset scenarios** - Ensure measurements work with samples from different datasets
5. **Document your fields** - Use `help_text` for all custom fields
6. **Follow naming conventions** - End class names with "Measurement"
7. **Use vocabulary types** - For standardized metadata (see Controlled Vocabularies guide)

## Troubleshooting

### Issue: Measurement not appearing in admin type dropdown

**Cause**: Model not registered or migrations not run

**Solution**:

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

### Issue: N+1 query problems in list views

**Cause**: Not using QuerySet optimization methods

**Solution**:

```python
# Bad
measurements = XRFMeasurement.objects.all()

# Good
measurements = XRFMeasurement.objects.with_related()
```

### Issue: Admin form shows wrong fields for measurement type

**Cause**: Polymorphic type mismatch or incorrect admin class

**Solution**: Ensure you're using `MeasurementChildAdmin` as base class and registering the correct model

## Next Steps

- [Registry Documentation](registry.md) - Advanced registry configuration
- [Admin Guide](../portal-administration/measurements-admin.md) - Portal administrator guide
- [Controlled Vocabularies](controlled_vocabularies.md) - Standardized metadata terms
- [Forms and Filters Guide](forms-and-filters/) - Advanced form techniques

## See Also

- [Core Data Model Overview](../overview/data_model.md#understanding-the-measurement-model)
- [Testing Guide](testing-portal-projects.md)
- Demo app: `fairdm_demo/models.py` for working examples
