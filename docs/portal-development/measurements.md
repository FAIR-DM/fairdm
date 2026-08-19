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
```

**What you get automatically:**

- `sample` - ForeignKey to the sample being measured
- `dataset` - ForeignKey to the dataset containing this measurement
- `name` - Descriptive name for the measurement
- `image` - Optional image/plot
- `added`, `modified` - Automatic timestamps
- All FAIR metadata fields (descriptions, dates, identifiers, contributors)

### The Value Convention

A measurement type does not implement its own reporting. It nominates a `value`
field and, where the analysis produces one, an `uncertainty` field. `Measurement`
itself supplies `get_value()` and `print_value()`, and both read those two fields:

- `get_value()` returns `self.value` on its own, or a pint `Measurement` combining
  `value` and `uncertainty` when both are set and `value` supports the arithmetic
  (a pint quantity does; a plain number does not, and is returned unchanged). A
  type that defines neither field falls back to `self.name`.
- `print_value()` renders whatever `get_value()` returns as a string, through the
  framework's shared quantity formatter - the same code path a template uses, so a
  value printed in a shell or a test looks the same as one rendered on a page.

Neither method is something a type overrides. `value` does not have to be a pint
quantity field - `get_value()` degrades gracefully for a plain number - but a type
that wants the formatted `"value ± uncertainty unit"` output needs both fields to
be quantity fields sharing compatible units.

`ICP_MS_Measurement` in `fairdm_demo/models.py` is the shipped example. It carries
its historical `concentration_ppb`/`uncertainty_percent` fields unchanged, and adds
the two the convention expects:

```python
class ICP_MS_Measurement(Measurement):
    """Inductively Coupled Plasma Mass Spectrometry (ICP-MS) measurement."""

    isotope = models.CharField(
        "Isotope",
        max_length=20,
        help_text="Isotope notation (e.g., 207Pb, 206Pb, 238U)",
    )
    counts_per_second = models.DecimalField(
        "Counts per Second",
        max_digits=15,
        decimal_places=2,
        help_text="Raw instrument counts per second",
    )
    # ... concentration_ppb, uncertainty_percent, dilution_factor and the rest of
    # the model's pre-existing fields are unchanged ...

    value = models.DecimalQuantityField(
        "microgram / liter",
        verbose_name="Value",
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="The measured concentration, reported as a quantity carrying its own units.",
    )
    uncertainty = models.DecimalQuantityField(
        "microgram / liter",
        verbose_name="Uncertainty",
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=(
            "The analytical uncertainty of the measured concentration, in the "
            "same units as the value."
        ),
    )
```

No `get_value()` or `print_value()` override anywhere on the class. Creating one
and reading its value back proves it (executed on this branch):

```python
>>> measurement = ICP_MS_Measurement.objects.create(
...     name="ICP-MS Pb Analysis",
...     sample=sample,
...     dataset=sample.dataset,
...     isotope="207Pb",
...     counts_per_second="15000.00",
...     value="5.000",
...     uncertainty="0.300",
... )
>>> measurement.get_value()
<Measurement(5.0, 0.3, microgram/liter)>
>>> measurement.print_value()
'5.00 ± 0.30 µg/l'
>>> str(measurement)
'5.00 ± 0.30 µg/l'
```

This appears in:

- Admin changelist columns
- String representations (`str(measurement)`)
- Anywhere a portal calls `print_value()` directly

## Step 2: Register Your Measurement

Registering a type is what turns a plain model into something a portal can add,
edit, filter and browse. Subclass `BaseMeasurementConfiguration` (a thin
`ModelConfiguration` that a measurement type builds on), name the model and the
fields that matter, and decorate it with `@register`:

```python
# myapp/config.py
from fairdm.registry import register
from fairdm.core.measurement.config import BaseMeasurementConfiguration
from .models import XRFMeasurement

@register
class XRFMeasurementConfig(BaseMeasurementConfiguration):
    model = XRFMeasurement

    # The field list shared by every component that doesn't declare its own
    fields = ["name", "sample", "dataset", "element", "concentration_ppm", "detection_limit_ppm"]

    display_name = "XRF Measurement"
    description = "X-ray fluorescence elemental analysis"
```

**What registering produces.** From that one declaration the registry generates,
on demand and without caching, six components: a `ModelForm`, a django-filter
`FilterSet`, a django-tables2 `Table`, a `ModelAdmin`, a DRF serializer and an
import-export resource. The four a portal developer meets day to day:

- **A form** - built on `MeasurementFormMixin` (see Step 4), so a type's form
  gets the shared widgets and dataset scoping without writing a form class.
- **A filter set** - built on `MeasurementFilterMixin` (see Step 4), so a type's
  filter set gets dataset, sample, type, search and date-range filtering for free.
- **A table** - column layout and Bootstrap 5 styling from the field list.
- **An administrative entry** - a `ModelAdmin` subclassing `MeasurementChildAdmin`
  (see Step 3), registered with `admin.site` automatically.

**Configuration attributes:**

| Attribute | Purpose | Example |
|--------|---------|---------|
| `fields` | Field list every component falls back to when it declares none of its own | `["name", "sample", "dataset", "element"]` |
| `form_fields` | Fields on the generated form only | `["name", "dataset", "sample", "element"]` |
| `table_fields` | Columns on the generated table only | `["name", "element", "concentration_ppm"]` |
| `filterset_fields` | Fields on the generated filter set only | `["element", "dataset"]` |
| `admin_list_display` | Columns on the admin changelist only | `["name", "element", "dataset"]` |
| `table_class` | Custom django-tables2 Table, replacing generation | `MyCustomMeasurementTable` |
| `form_class` | Custom ModelForm, replacing generation | `"myapp.forms.XRFMeasurementForm"` |
| `filterset_class` | Custom FilterSet, replacing generation | `"myapp.filters.XRFMeasurementFilter"` |
| `admin_class` | Custom ModelAdmin, replacing generation | `"myapp.admin.XRFMeasurementAdmin"` |
| `display_name` | Human-readable name, defaults to the model's verbose name | `"XRF Measurement"` |
| `description` | Description of this type, surfaced in the API docs | `"X-ray fluorescence elemental analysis"` |

Declaring a component's field list (e.g. `form_fields`) and a class for the same
component (e.g. `form_class`) at once is refused at registration - the field list
would never take effect, so the registry treats it as a configuration error rather
than silently preferring one.

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
        "detection_limit_ppm", "dataset", "added"
    ]

    # Add custom filters
    list_filter = ["element", "dataset", "added"]

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

**A type gets this behaviour whether or not it writes a form or filter set of its
own.** Step 2's registry generation builds the generated form on top of
`MeasurementFormMixin` and the generated filter set on top of
`MeasurementFilterMixin` - that wiring is what makes every registered measurement
type's form and filter set behave consistently without a portal writing a line of
form or filter code. Reach for the mixins directly, as this section shows, only
when the generated component isn't enough and a custom `form_class` or
`filterset_class` is supplied instead.

### Custom Forms with MeasurementFormMixin

The `MeasurementFormMixin` adds widget configuration and dataset scoping:

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
            # Below detection limit - a domain-specific case for this type to flag,
            # e.g. through a field error or a description added at save time.
            pass

        return cleaned_data
```

**What MeasurementFormMixin provides:**

- A Select2 autocomplete widget for `dataset`, with an "add another" link to the
  dataset admin
- The `dataset` queryset scoped to datasets the requesting user holds
  `change_dataset` on, when the form is built with `request=...`
- A Select2 autocomplete widget for `sample`
- A crispy-forms `FormHelper` (`form_tag = False`, so the surrounding page
  supplies the `<form>` tag)

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
            'added': ['gte', 'lte'],
        }
```

**What MeasurementFilterMixin provides:**

- `dataset` - a `ModelChoiceFilter`, scoped to the requesting user's datasets when
  the filter set is built with `request=...`, matching `MeasurementFormMixin`
- `sample` - a `ModelChoiceFilter` over every sample
- `polymorphic_ctype` - a `ModelChoiceFilter` over the registered measurement types,
  so a mixed list can be narrowed to one type
- `search` - a `CharFilter` matching `name` or `uuid`
- `description` - a `CharFilter` matching text in the measurement's descriptions
- `date_after` / `date_before` - range filters over the measurement's dates. These
  accept a year, a year-and-month, or a full date (matching
  `MeasurementDate.value`'s own partial-date format) and reject anything else as a
  form error rather than an unhandled exception at query time

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
| `with_related()` | sample, dataset, contributors | List views, API endpoints |
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

    # No get_value()/print_value() override: this type nominates neither a
    # `value` nor an `uncertainty` field, so Measurement.get_value() falls back
    # to the record's own `name` - the reporting a microscopy image doesn't
    # otherwise have.

# myapp/config.py
from fairdm.registry import register
from fairdm.core.measurement.config import BaseMeasurementConfiguration

@register
class MicroscopyMeasurementConfig(BaseMeasurementConfiguration):
    model = MicroscopyMeasurement
    fields = [
        "name", "sample", "dataset",
        "microscope_type", "magnification", "scale_bar_microns", "image",
    ]
    filterset_fields = ["microscope_type", "dataset", "sample"]

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
from myapp.factories import RockSampleFactory

@pytest.mark.django_db
class TestXRFMeasurement:
    def test_create_measurement(self):
        """Test basic measurement creation."""
        sample = RockSampleFactory()
        measurement = XRFMeasurement.objects.create(
            name="Iron Analysis",
            sample=sample,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=5000.0
        )

        assert measurement.element == "Fe"
        # XRFMeasurement nominates no `value` field, so get_value() falls back
        # to the record's name (the same behaviour proven for `fairdm_demo`'s
        # ExampleMeasurement in tests/test_core/test_measurement/test_value.py).
        assert measurement.get_value() == "Iron Analysis"
```

For a type that does nominate `value` (and optionally `uncertainty`), test the
value itself rather than a hand-built string - see
`tests/test_core/test_measurement/test_value.py`, which exercises exactly this on
`ICP_MS_Measurement`.

## Best Practices

1. **Nominate `value` (and `uncertainty`) where the type has one** - `get_value()`
   and `print_value()` do the reporting; do not override either
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
