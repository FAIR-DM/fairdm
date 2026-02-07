# Custom Sample Types

This guide explains how to create and configure custom Sample types in your FairDM portal.

## Overview

Samples are physical or digital objects that form the core of your research data. FairDM provides a flexible `Sample` base class that you extend with your domain-specific fields and behaviors.

### Key Features

- **Polymorphic Inheritance**: All Sample subclasses are stored in a single table with automatic type detection
- **Rich Metadata**: Built-in support for descriptions, dates, identifiers, and contributors
- **Relationships**: Track provenance and relationships between samples
- **Location Support**: Optional spatial data integration
- **Registry Integration**: Automatic form, filter, and admin generation

## Basic Sample Creation

### Simple Example

```python
from fairdm.core.sample.models import Sample
from django.db import models

class RockSample(Sample):
    """Geological rock sample with basic metadata."""

    rock_type = models.CharField(
        max_length=100,
        help_text="Type of rock (e.g., igneous, sedimentary, metamorphic)"
    )
    collection_date = models.DateField(
        help_text="Date the sample was collected"
    )
    weight_grams = models.FloatField(
        null=True,
        blank=True,
        help_text="Sample weight in grams"
    )

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"
```

### Required Fields

The `Sample` base class provides these required fields:

- `name`: Short identifier/label for the sample
- `dataset`: Foreign key to the parent Dataset
- `uuid`: Automatically generated unique identifier

### Optional Fields

- `local_id`: Local identifier within your lab/project
- `status`: Sample status (available, used, archived, etc.)
- `location`: Spatial location (requires GeoDjango)

## Advanced Field Types

### Using QuantityField

For measurements with units:

```python
from fairdm.db.models import QuantityField

class WaterSample(Sample):
    temperature = QuantityField(
        base_units="celsius",
        help_text="Water temperature at collection"
    )
    ph_level = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(14)]
    )
```

### Using ConceptField

For controlled vocabulary fields:

```python
from fairdm.db.models import ConceptField

class SoilSample(Sample):
    soil_type = ConceptField(
        vocabulary="soil_taxonomy",
        help_text="USDA Soil Taxonomy classification"
    )
    texture = ConceptField(
        vocabulary="soil_texture",
        null=True,
        blank=True
    )
```

### Using PartialDateField

For dates with varying precision:

```python
from fairdm.db.models import PartialDateField

class ArchaeologicalSample(Sample):
    estimated_age = PartialDateField(
        help_text="Estimated date (can be year, year-month, or full date)"
    )
    # Can store: "2024", "2024-03", or "2024-03-15"
```

## Sample Metadata

Samples support rich metadata through related models:

### Descriptions

Multiple descriptions of different types:

```python
from fairdm.core.sample.models import SampleDescription

# In your view or factory
SampleDescription.objects.create(
    related=my_sample,
    type="abstract",
    value="Basalt sample from mid-ocean ridge"
)
SampleDescription.objects.create(
    related=my_sample,
    type="methods",
    value="Collected using rock hammer and chisel"
)
```

Available description types:

- `abstract`: Brief summary
- `methods`: Collection/preparation methods
- `other`: Any other description type

### Dates

Track important dates:

```python
from fairdm.core.sample.models import SampleDate

SampleDate.objects.create(
    related=my_sample,
    type="collected",
    value="2024-03-15"  # PartialDate format
)
```

Available date types:

- `collected`: Sample collection date
- `available`: Date made available
- `created`: Record creation date

### Identifiers

Assign persistent identifiers:

```python
from fairdm.core.sample.models import SampleIdentifier

# IGSN (International Geo Sample Number)
SampleIdentifier.objects.create(
    related=my_sample,
    type="IGSN",
    value="IEABC0123"
)

# Local barcode
SampleIdentifier.objects.create(
    related=my_sample,
    type="barcode",
    value="RS-2024-001"
)
```

### Contributors

Track who collected, analyzed, or owns samples:

```python
from fairdm.core.sample.models import SampleContribution

SampleContribution.objects.create(
    related=my_sample,
    contributor=researcher,  # User or Contact instance
    roles=["collector", "analyst"]
)
```

## Sample Relationships

Track provenance and relationships between samples:

```python
from fairdm.core.sample.models import SampleRelation

# Parent-child relationship
SampleRelation.objects.create(
    source=child_sample,
    target=parent_sample,
    type="child_of",
    description="Split from parent core sample"
)

# Derived sample
SampleRelation.objects.create(
    source=powder_sample,
    target=rock_sample,
    type="derived-from",
    description="Crushed to powder for XRD analysis"
)
```

### Common Relationship Types

- `child_of`: Sample is a child/subsample of another
- `derived-from`: Sample derived through processing
- `split-from`: Sample split from a larger sample
- `replicate-of`: Duplicate/replicate sample

### Querying Relationships

```python
# Get child samples
children = parent_sample.get_children()

# Get parent samples
parents = child_sample.get_parents()

# Get all descendants (recursive)
descendants = parent_sample.get_descendants(depth=5)

# Query by relationship type
related = Sample.objects.by_relationship(
    related_to=my_sample,
    relationship_type="child_of"
)
```

## Polymorphic Queries

Django-polymorphic automatically returns the correct subclass type:

```python
# Returns RockSample, WaterSample, etc. (not base Sample)
samples = Sample.objects.all()

for sample in samples:
    print(type(sample).__name__)  # RockSample, WaterSample, etc.
    # Can access subclass-specific fields directly
    if hasattr(sample, 'rock_type'):
        print(f"Rock type: {sample.rock_type}")
```

### Filtering by Type

```python
# Only get specific types
rocks = Sample.objects.instance_of(RockSample)
water_or_soil = Sample.objects.instance_of(WaterSample, SoilSample)

# Exclude types
non_rocks = Sample.objects.not_instance_of(RockSample)
```

## Query Optimization

Use provided QuerySet methods to optimize database queries:

```python
# Prefetch related data in bulk
samples = Sample.objects.with_related()  # Dataset, location, contributors

# Prefetch metadata
samples = Sample.objects.with_metadata()  # Descriptions, dates, identifiers

# Chain optimization methods
samples = (
    Sample.objects
    .with_related()
    .with_metadata()
    .filter(dataset=my_dataset)
    .order_by('name')
)

# Access prefetched data without additional queries
for sample in samples:
    print(sample.dataset.name)  # No query
    print(list(sample.descriptions.all()))  # No query
```

## Custom QuerySet Methods

Add domain-specific query methods:

```python
from fairdm.core.sample.managers import SampleQuerySet

class RockSampleQuerySet(SampleQuerySet):
    """Custom queryset for RockSample."""

    def igneous(self):
        """Filter for igneous rocks only."""
        return self.filter(rock_type__icontains="igneous")

    def by_weight_range(self, min_grams=None, max_grams=None):
        """Filter by weight range."""
        qs = self
        if min_grams is not None:
            qs = qs.filter(weight_grams__gte=min_grams)
        if max_grams is not None:
            qs = qs.filter(weight_grams__lte=max_grams)
        return qs

class RockSample(Sample):
    rock_type = models.CharField(max_length=100)
    weight_grams = models.FloatField(null=True, blank=True)

    objects = RockSampleQuerySet.as_manager()

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"

# Usage
igneous_rocks = RockSample.objects.igneous()
heavy_rocks = RockSample.objects.by_weight_range(min_grams=100)
```

## Validation

Add custom validation logic:

```python
from django.core.exceptions import ValidationError

class WaterSample(Sample):
    ph_level = models.FloatField()
    temperature_celsius = models.FloatField()

    def clean(self):
        """Validate pH is in valid range."""
        super().clean()

        if self.ph_level < 0 or self.ph_level > 14:
            raise ValidationError({
                'ph_level': 'pH must be between 0 and 14'
            })

        if self.temperature_celsius < -273.15:
            raise ValidationError({
                'temperature_celsius': 'Temperature cannot be below absolute zero'
            })
```

## Registry Configuration

Register your Sample type for automatic integration:

```python
# In your app's config.py or registry.py
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    # Fields to show in tables/lists
    fields = ["name", "local_id", "rock_type", "collection_date", "weight_grams"]

    # Display metadata
    display_name = "Rock Sample"
    description = "Geological rock samples with collection metadata"

# This automatically generates:
# - ModelForm for create/edit
# - FilterSet for filtering
# - Table for list views
# - ModelAdmin for admin site
```

See [Model Configuration](../model_configuration.md) for complete registry documentation.

## Testing Custom Samples

### Basic Tests

```python
import pytest
from datetime import date
from myapp.models import RockSample

@pytest.mark.django_db
def test_rock_sample_creation(dataset):
    """Test creating a rock sample with required fields."""
    sample = RockSample.objects.create(
        name="RS-001",
        dataset=dataset,
        rock_type="igneous",
        collection_date=date.today()
    )

    assert sample.pk is not None
    assert sample.rock_type == "igneous"
    assert sample.uuid.startswith("s_")

@pytest.mark.django_db
def test_rock_sample_validation():
    """Test sample validation logic."""
    sample = RockSample(
        name="Invalid",
        rock_type="",  # Empty rock_type
    )

    with pytest.raises(ValidationError):
        sample.full_clean()
```

### Testing Relationships

```python
@pytest.mark.django_db
def test_sample_relationships(dataset):
    """Test creating and querying sample relationships."""
    from fairdm.core.sample.models import SampleRelation

    parent = RockSample.objects.create(
        name="Parent Core",
        dataset=dataset,
        rock_type="igneous",
        collection_date=date.today()
    )

    child = RockSample.objects.create(
        name="Child Sample",
        dataset=dataset,
        rock_type="igneous",
        collection_date=date.today()
    )

    SampleRelation.objects.create(
        source=child,
        target=parent,
        type="child_of"
    )

    # Test convenience methods
    assert child in parent.get_children()
    assert parent in child.get_parents()
```

## Best Practices

### Model Organization

1. **Keep models focused**: One Sample type per physical object type
2. **Use descriptive names**: `WaterSample` not `Sample1`
3. **Add help_text**: Document every field's purpose and format
4. **Use appropriate field types**: `FloatField` for decimals, `IntegerField` for counts

### Field Design

1. **Avoid null=True on CharFields**: Use `blank=True` and empty string instead
2. **Provide choices where applicable**: Use `choices` parameter for fixed options
3. **Set max_length appropriately**: Don't use `max_length=9999` - be realistic
4. **Use validators**: Add range checks, format validators, etc.

### Documentation

1. **Write docstrings**: Document the purpose of each Sample type
2. **Document relationships**: Explain parent-child hierarchies in docstrings
3. **Provide examples**: Include usage examples in docstrings
4. **Keep Meta updated**: Set verbose_name and verbose_name_plural

### Performance

1. **Use with_related()**: Always prefetch related data when iterating
2. **Add select_related for FKs**: For your own custom foreign keys
3. **Index frequently queried fields**: Add `db_index=True` to filtered fields
4. **Avoid N+1 queries**: Test query counts in your integration tests

## Common Patterns

### Hierarchical Samples

For samples with parent-child hierarchies:

```python
# Creating a hierarchy
core = CoreSample.objects.create(name="Core-001", dataset=dataset)
section_a = CoreSection.objects.create(name="Section-A", dataset=dataset)
section_b = CoreSection.objects.create(name="Section-B", dataset=dataset)

# Link sections to core
SampleRelation.objects.create(source=section_a, target=core, type="child_of")
SampleRelation.objects.create(source=section_b, target=core, type="child_of")

# Query descendants
all_sections = core.get_descendants()
```

### Replicate Samples

For duplicate samples:

```python
original = WaterSample.objects.create(...)
replicate = WaterSample.objects.create(...)

SampleRelation.objects.create(
    source=replicate,
    target=original,
    type="replicate-of",
    description="Field replicate for quality control"
)
```

### Derived Samples

For processed samples:

```python
original = RockSample.objects.create(...)
powder = PowderSample.objects.create(...)

SampleRelation.objects.create(
    source=powder,
    target=original,
    type="derived-from",
    description="Ground to <63μm powder"
)
```

## Troubleshooting

### Polymorphic Queries Not Working

If you're getting base Sample objects instead of typed instances:

1. Ensure you're querying through `Sample.objects` not `RockSample.objects`
2. Check that `polymorphic_ctype` is being set correctly
3. Verify migrations are up to date

### Circular Relationship Errors

If you're getting validation errors on relationships:

```python
# This is prevented by validation
SampleRelation.objects.create(source=sample_a, target=sample_a, type="child_of")  # Error

# This is also prevented
SampleRelation.objects.create(source=sample_a, target=sample_b, type="child_of")
SampleRelation.objects.create(source=sample_b, target=sample_a, type="child_of")  # Error
```

### Query Performance Issues

If queries are slow:

1. Use `with_related()` and `with_metadata()` consistently
2. Add database indexes to frequently filtered fields
3. Use `only()` and `defer()` for large querysets where you don't need all fields
4. Consider using `select_related()` for your custom foreign keys

## See Also

- [Model Configuration](../model_configuration.md) - Registry configuration
- [Defining Models](../defining_models.md) - General model patterns
- [Special Fields](../special_fields.md) - Custom field types
- [Filtering](../filtering-by-vocabulary.md) - Filter configuration
