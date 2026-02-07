# Quickstart: Creating Custom Sample Types

**Feature**: 005-core-samples | **Audience**: Portal Developers

## Overview

This guide shows how to create custom sample types that integrate with the FairDM registry system. Custom sample types automatically get forms, filters, tables, and admin interfaces through registry registration.

## Prerequisites

- FairDM framework installed
- Feature 004 (registry system) functional
- Feature 006 (datasets) functional
- Basic understanding of Django models

## Step 1: Define Your Sample Model

Create a model inheriting from `Sample`:

```python
# myapp/models.py
from fairdm.core.models import Sample
from django.db import models

class RockSample(Sample):
    """
    Geological rock sample with mineral composition.

    This custom sample type extends the base Sample model with
    rock-specific fields for geological research portals.
    """
    mineral_type = models.CharField(
        max_length=100,
        help_text="Primary mineral composition (e.g., Quartz, Feldspar)"
    )

    hardness = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Mohs hardness scale (1.0-10.0)"
    )

    grain_size = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('fine', 'Fine (<0.1mm)'),
            ('medium', 'Medium (0.1-1mm)'),
            ('coarse', 'Coarse (>1mm)'),
        ],
        help_text="Average grain size classification"
    )

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"

    def __str__(self):
        return f"{self.name} ({self.mineral_type})"
```

**Key Points**:

- Inherit from `Sample` (polymorphic base)
- Add domain-specific fields
- Use descriptive help_text for each field
- Define Meta class with verbose names

## Step 2: Register with FairDM Registry

Create a configuration class and register:

```python
# myapp/config.py
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration
from .models import RockSample

@register
class RockSampleConfig(ModelConfiguration):
    """
    Registry configuration for RockSample model.

    Specifies which fields to include in auto-generated forms,
    filters, tables, and admin interfaces.
    """
    model = RockSample

    # Fields for all auto-generated components
    fields = [
        'name',
        'dataset',
        'status',
        'location',
        'mineral_type',
        'hardness',
        'grain_size',
    ]

    # Optional: Override specific component fields
    table_fields = ['name', 'dataset', 'mineral_type', 'hardness', 'added']
    filterset_fields = ['dataset', 'status', 'mineral_type', 'grain_size']

    # Optional: Display metadata
    display_name = "Rock Sample"
    description = "Geological rock samples with mineral composition data"
```

**That's it!** The registry now auto-generates:

- `RockSampleForm` (ModelForm)
- `RockSampleFilter` (FilterSet)
- `RockSampleTable` (django-tables2 Table)
- `RockSampleAdmin` (Django admin)

## Step 3: Run Migrations

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

## Step 4: Use Auto-Generated Components

### In Views

```python
from fairdm.registry import registry

# Get auto-generated components
config = registry.get_for_model(RockSample)

# Use auto-generated form
form_class = config.form
form = form_class(request.POST or None)

# Use auto-generated filter
filter_class = config.filterset
sample_filter = filter_class(request.GET, queryset=RockSample.objects.all())

# Use auto-generated table
table_class = config.table
table = table_class(sample_filter.qs)
```

### In Admin (Auto-Registered)

The registry automatically creates a `RockSampleAdmin` accessible at `/admin/myapp/rocksample/`.

## Advanced: Custom Forms with Mixins

If you need custom form behavior, inherit from `SampleFormMixin`:

```python
# myapp/forms.py
from fairdm.core.forms import SampleFormMixin
from django import forms
from .models import RockSample

class RockSampleForm(SampleFormMixin, forms.ModelForm):
    """
    Custom form for RockSample with specialized validation.

    Inherits common sample form behavior from SampleFormMixin
    (dataset autocomplete, status select) and adds rock-specific
    validation logic.
    """
    class Meta:
        model = RockSample
        fields = [
            'name',
            'dataset',
            'status',
            'location',
            'mineral_type',
            'hardness',
            'grain_size',
        ]

    def clean_hardness(self):
        """Validate hardness is within Mohs scale range."""
        hardness = self.cleaned_data.get('hardness')
        if hardness and (hardness < 1.0 or hardness > 10.0):
            raise forms.ValidationError(
                "Hardness must be between 1.0 and 10.0 on Mohs scale"
            )
        return hardness
```

Then reference the custom form in your registry config:

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    form_class = RockSampleForm  # Use custom form
    fields = ['name', 'dataset', 'status', 'mineral_type', 'hardness']
```

## Advanced: Custom Filters with Mixins

Similarly, create custom filters with `SampleFilterMixin`:

```python
# myapp/filters.py
from fairdm.core.filters import SampleFilterMixin
import django_filters
from .models import RockSample

class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    """
    Custom filter for RockSample with hardness range filtering.

    Inherits common sample filters from SampleFilterMixin
    (status, dataset, search) and adds rock-specific filters.
    """
    hardness_min = django_filters.NumberFilter(
        field_name='hardness',
        lookup_expr='gte',
        label='Minimum Hardness'
    )

    hardness_max = django_filters.NumberFilter(
        field_name='hardness',
        lookup_expr='lte',
        label='Maximum Hardness'
    )

    class Meta:
        model = RockSample
        fields = {
            'mineral_type': ['exact', 'icontains'],
            'grain_size': ['exact'],
        }
```

Reference in registry config:

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    filterset_class = RockSampleFilter  # Use custom filter
```

## Sample Relationships

Create relationships between samples:

```python
from fairdm.core.models import SampleRelation

# Create parent sample
parent = RockSample.objects.create(
    name="Rock Core A",
    dataset=my_dataset,
    mineral_type="Granite"
)

# Create child sample
child = RockSample.objects.create(
    name="Rock Core A - Section 1",
    dataset=my_dataset,
    mineral_type="Granite"
)

# Link with relationship
SampleRelation.objects.create(
    source=child,
    target=parent,
    relationship_type='section-of',
    notes='Top section, 10cm'
)

# Query relationships (bidirectional access)
outgoing = parent.related.all()  # Samples where parent is source
incoming = child.related_to.all()  # Samples where child is target
```

## Adding Metadata

Add descriptions, dates, identifiers:

```python
from fairdm.core.models import SampleDescription, SampleDate, SampleIdentifier

# Add description
SampleDescription.objects.create(
    content_object=rock_sample,
    description_type='methods',
    text='Sample collected from outcrop using rock hammer'
)

# Add collection date
SampleDate.objects.create(
    content_object=rock_sample,
    date_type='collected',
    date=datetime.date(2026, 1, 15)
)

# Add IGSN identifier
SampleIdentifier.objects.create(
    content_object=rock_sample,
    identifier_type='IGSN',
    identifier='IGSN:ABCD1234'
)
```

## Testing Your Sample Type

```python
# tests/unit/myapp/test_rock_sample.py
import pytest
from myapp.models import RockSample
from fairdm.core.factories import DatasetFactory

@pytest.mark.django_db
class TestRockSample:
    def test_create_rock_sample(self):
        """Test creating a rock sample with required fields."""
        dataset = DatasetFactory()
        sample = RockSample.objects.create(
            name="Test Rock",
            dataset=dataset,
            mineral_type="Quartz"
        )
        assert sample.name == "Test Rock"
        assert sample.mineral_type == "Quartz"

    def test_polymorphic_query(self):
        """Test that polymorphic queries return correct type."""
        dataset = DatasetFactory()
        rock = RockSample.objects.create(
            name="Rock",
            dataset=dataset,
            mineral_type="Granite"
        )

        # Query base Sample model
        from fairdm.core.models import Sample
        samples = Sample.objects.all()

        # Should return RockSample instance, not Sample
        assert isinstance(samples.first(), RockSample)
```

## Query Optimization

Use built-in QuerySet methods to optimize database queries:

### Prefetch Related Data

```python
# Bad: N+1 queries
samples = RockSample.objects.all()
for sample in samples:
    print(sample.dataset.name)  # Query per sample!
    print(sample.location.name)  # Another query per sample!

# Good: Prefetch in bulk
samples = RockSample.objects.with_related()
for sample in samples:
    print(sample.dataset.name)  # No additional query
    print(sample.location.name)  # No additional query
```

### Prefetch Metadata

```python
# Prefetch descriptions, dates, identifiers in bulk
samples = RockSample.objects.with_metadata()
for sample in samples:
    descriptions = list(sample.descriptions.all())  # No query
    dates = list(sample.dates.all())  # No query
    identifiers = list(sample.identifiers.all())  # No query
```

### Chain Optimizations

```python
# Combine optimization methods
samples = (
    RockSample.objects
    .with_related()  # Prefetch dataset, location, contributors
    .with_metadata()  # Prefetch descriptions, dates, identifiers
    .filter(dataset=my_dataset)
    .order_by('name')
)

# Now iterate with minimal queries
for sample in samples:
    print(f"{sample.name} from {sample.dataset.name}")
    for desc in sample.descriptions.all():
        print(f"  - {desc.value}")
```

### Performance Goals

For optimal performance, aim for:

- **<10 queries** for 1000 samples with `with_related()`
- **<200ms** query time for large result sets
- **80% query reduction** compared to unoptimized queries

Test query counts using Django's query debugging:

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as context:
    samples = list(RockSample.objects.with_related()[:100])
    for sample in samples:
        _ = sample.dataset.name
        _ = list(sample.contributors.all())

print(f"Total queries: {len(context.captured_queries)}")
# Should be ~3-5 queries for 100 samples
```

## Demo App Examples

See `fairdm_demo/` for complete working examples:

- `fairdm_demo/models.py` - RockSample, WaterSample examples
- `fairdm_demo/config.py` - Registry configurations
- `fairdm_demo/forms.py` - Custom forms with mixins
- `fairdm_demo/filters.py` - Custom filters with mixins
- `fairdm_demo/tests/` - Test examples

## Next Steps

- Read [Sample Model Documentation](../../docs/developer-guide/models/samples.md)
- Explore [Registry System](../../docs/developer-guide/registry.md)
- Learn about [Sample Relationships](../../docs/developer-guide/models/sample-relationships.md)

## Troubleshooting

### "Sample model has no attribute 'objects'"

Make sure your model inherits from `Sample`, not `models.Model`.

### "Registry error: Model already registered"

Each model can only be registered once. Check for duplicate `@register` decorators.

### "Polymorphic query returns base Sample, not custom type"

Use `.select_subclasses()` or ensure django-polymorphic is properly configured.

### "Form doesn't show my custom fields"

Specify custom fields in registry config `fields` list or define custom form with all fields.
