# Custom Sample Types

This guide explains how to create and configure custom Sample types in your FairDM portal.

## Overview

Samples are physical or digital objects that form the core of your research data. FairDM provides a flexible `Sample` base class that you extend with your domain-specific fields and behaviors.

### Key Features

- **Polymorphic Inheritance**: All Sample subclasses are stored in a single table with automatic type detection
- **Rich Metadata**: Built-in support for descriptions, dates, identifiers, and contributors
- **Relationships**: Track provenance between samples
- **Location Support**: Optional spatial data integration
- **Registry Integration**: Automatic form, filter, and admin generation

```{note}
The base `Sample` model itself cannot be created — not through the ORM, a form, the admin, or a
factory. Every route to create one raises. This is deliberate: `Sample` is a polymorphic base a
portal is meant to extend, never a record in its own right. Everything below defines a concrete
subclass instead.
```

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
- `uuid`: Automatically generated unique identifier, prefixed `s_`, not editable afterwards

### Optional Fields

- `local_id`: Local identifier within your lab/project — need not be unique; two samples in
  different datasets may share one
- `status`: Custody status, drawn from a fixed vocabulary — `available`, `in_use`, `stored`,
  `destroyed`, `unknown`. Defaults to `unknown` when nothing is set, and can move to any other
  status from any status, including back out of `destroyed`
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

For controlled vocabulary fields, define a small vocabulary and pass the class itself as
`vocabulary` — not a vocabulary name string:

```python
from django.utils.translation import gettext_lazy as _
from research_vocabs.core import VocabularyBuilder
from research_vocabs.fields import ConceptField

class SoilTexture(VocabularyBuilder):
    sandy = {"skos:prefLabel": _("Sandy")}
    loamy = {"skos:prefLabel": _("Loamy")}
    clay = {"skos:prefLabel": _("Clay")}

    class Meta:
        name = "soil-texture"

class SoilSample(Sample):
    texture = ConceptField(
        vocabulary=SoilTexture,
        help_text="Dominant soil texture class",
    )
```

See [Controlled Vocabularies](../controlled_vocabularies.md) for the full guide to declaring one.

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

Samples support rich metadata through related models. Each of `SampleDescription`, `SampleDate`
and `SampleIdentifier` is scoped to its own vocabulary — a `type` outside it is refused by
`full_clean()`, though not by a plain `.objects.create()`, which does not call it.

### Descriptions

Several descriptions, each drawn from the sample description vocabulary
(`SampleCollection`, `SamplePreparation`, `SampleStorage`, `SampleDestruction`, `Other`):

```python
from fairdm.core.sample.models import SampleDescription

SampleDescription.objects.create(
    related=my_sample,
    type="SampleCollection",
    value="Basalt sample from mid-ocean ridge, collected by dredge.",
)
SampleDescription.objects.create(
    related=my_sample,
    type="SamplePreparation",
    value="Crushed and sieved to <2mm for analysis.",
)
```

A sample carries at most one description of each type — the database enforces `(related, type)`
as unique.

### Dates

The sample date vocabulary is `Created`, `Destroyed`, `Collected`, `Returned`, `Prepared`,
`Archival`, `Restored`:

```python
from fairdm.core.sample.models import SampleDate

SampleDate.objects.create(
    related=my_sample,
    type="Collected",
    value="2024-03-15",  # PartialDate format: "2024", "2024-03", or "2024-03-15"
)
```

### Identifiers

The sample identifier vocabulary contains only two types — `IGSN` and `DOI` — the same
vocabulary datasets, projects and people use has no member that names a sample at all, so this
is a separate, sample-scoped collection:

```python
from fairdm.core.sample.models import SampleIdentifier

SampleIdentifier.objects.create(
    related=my_sample,
    type="IGSN",
    value="10.58052/SSH000SUA",
)
```

Two rules apply whenever a `SampleIdentifier.full_clean()` runs (also true for project, dataset
and measurement identifiers, since they share the same abstract base):

- **Normalisation.** A common display prefix — `https://doi.org/`, `http://doi.org/`,
  `https://igsn.org/`, `hdl.handle.net/`, `doi:`, `igsn:` — is stripped from the value before it
  is compared or stored. IGSN allocation moved to DataCite in 2023, so an IGSN today is validated
  as any DataCite DOI (`10.NNNN/…`, case-insensitive, suffix unconstrained) or the legacy
  `10273/…` handle — there is no longer a single prefix or suffix shape to check.
- **Global uniqueness.** `value` must be unique across every record type that carries
  identifiers — a sample, a dataset, a project and a measurement cannot share one, not only
  samples among themselves.

### Contributors

Track who collected, analyzed, or owns a sample through the shared `Contribution` model, the same
one projects and datasets use, linked by a generic relation:

```python
from fairdm.contrib.contributors.models import Contribution
from research_vocabs.models import Concept

contribution = Contribution.objects.create(
    contributor=researcher,  # a Person or Organization instance
    content_object=my_sample,
)
collector_role = Concept.objects.get(vocabulary=my_sample.CONTRIBUTOR_ROLES, label="Collector")
contribution.roles.add(collector_role)
```

## Sample Relationships

Record that one sample came from another. There is one relationship type, `child_of`, and the
relationship record carries no field to explain *why* — if that matters, put it in a description
on the child instead.

```python
from fairdm.core.sample.models import SampleRelation

SampleRelation.objects.create(
    source=child_sample,
    target=parent_sample,
    type="child_of",
)
```

A sample cannot be related to itself, the reverse of an existing link cannot also be recorded
(A `child_of` B and B `child_of` A), and the same link cannot be saved twice. All three are
refused on `save()` directly, not only through form validation.

### Querying Relationships

```python
# Get child samples
children = parent_sample.get_children()

# Get parent samples
parents = child_sample.get_parents()

# Get all descendants (recursive, optional depth limit)
descendants = parent_sample.get_descendants(depth=5)

# Get all ancestors (recursive, optional depth limit)
ancestors = child_sample.get_ancestors(depth=3)

# Query by relationship type
related = Sample.objects.by_relationship(
    related_to=my_sample,
    relationship_type="child_of",
)
```

Each helper on `Sample` delegates to the matching method on `Sample.objects` — there is exactly
one implementation of the traversal, not two that could disagree.

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
# Prefetch dataset, location and contributors
samples = Sample.objects.with_related()

# Prefetch descriptions, dates and identifiers
samples = Sample.objects.with_metadata()

# Prefetch controlled keywords
samples = Sample.objects.with_keywords()

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

`super().clean()` matters here — it is what refuses a bare `Sample` from ever validating, and
skipping it silently drops that guard for your subclass too.

## Registry Configuration

Register your Sample type for automatic integration. `BaseSampleConfiguration` is the recommended
base — it declares the same `fields` list every generated component (form, table, filter set,
serializer, resource, admin) falls back to, so a type that wants one shared field list only states
`fields` once:

```python
# In your app's config.py
from fairdm.core.sample.config import BaseSampleConfiguration
from fairdm.registry import register
from .models import RockSample

@register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "local_id", "rock_type", "collection_date", "weight_grams"]

# This automatically generates:
# - ModelForm for create/edit
# - FilterSet for filtering
# - Table for list views
# - ModelAdmin for admin site
```

`BaseSampleConfiguration` deliberately declares only `fields`, not `form_fields`, `table_fields`,
`filterset_fields` or `serializer_fields`. If your type relies on the registry auto-detecting
per-component field lists rather than sharing one list across every component, subclass the
plain `ModelConfiguration` instead — setting any of those on `BaseSampleConfiguration` would win
over your own per-component lists for the one component you didn't restate.

See [Model Configuration](../model_configuration.md) for the complete registry documentation.

## Testing Custom Samples

FairDM's own `fairdm.factories.SampleFactory` is abstract — it declares the fields every sample
factory needs but cannot itself build a `Sample`, for the same reason the model can't. Write your
own concrete factory alongside your sample type, the way `fairdm_demo.factories.RockSampleFactory`
does for the reference implementation:

```python
import factory
from fairdm.factories import SampleFactory
from myapp.models import RockSample

class RockSampleFactory(SampleFactory):
    class Meta:
        model = RockSample

    rock_type = "igneous"
    collection_date = factory.Faker("date_this_decade")
```

### Basic Tests

```python
import pytest
from datetime import date
from myapp.factories import RockSampleFactory

@pytest.mark.django_db
def test_rock_sample_creation(dataset):
    """Test creating a rock sample with required fields."""
    sample = RockSampleFactory(
        dataset=dataset,
        rock_type="igneous",
        collection_date=date.today(),
    )

    assert sample.pk is not None
    assert sample.rock_type == "igneous"
    assert sample.uuid.startswith("s_")

@pytest.mark.django_db
def test_base_sample_cannot_be_created(dataset):
    """The polymorphic base itself is refused, by every route."""
    from django.core.exceptions import ValidationError
    from fairdm.core.sample.models import Sample

    with pytest.raises(ValidationError):
        Sample.objects.create(name="Bare sample", dataset=dataset)
```

### Testing Relationships

```python
@pytest.mark.django_db
def test_sample_relationships(dataset):
    """Test creating and querying sample relationships."""
    from fairdm.core.sample.models import SampleRelation

    parent = RockSampleFactory(name="Parent Core", dataset=dataset)
    child = RockSampleFactory(name="Child Sample", dataset=dataset)

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
2. **Document relationships**: Explain what `child_of` means for your specimen type in a docstring, since the relation record itself carries no explanation field
3. **Provide examples**: Include usage examples in docstrings
4. **Keep Meta updated**: Set verbose_name and verbose_name_plural

### Performance

1. **Use with_related() and with_metadata()**: Always prefetch related data when iterating
2. **Add select_related for FKs**: For your own custom foreign keys
3. **Index frequently queried fields**: Add `db_index=True` to filtered fields
4. **Avoid N+1 queries**: Test query counts in your integration tests

## Common Patterns

### Hierarchical Samples

For samples with parent-child hierarchies:

```python
# Creating a hierarchy
core = CoreSampleFactory(name="Core-001", dataset=dataset)
section_a = CoreSectionFactory(name="Section-A", dataset=dataset)
section_b = CoreSectionFactory(name="Section-B", dataset=dataset)

# Link sections to core
SampleRelation.objects.create(source=section_a, target=core, type="child_of")
SampleRelation.objects.create(source=section_b, target=core, type="child_of")

# Query descendants
all_sections = core.get_descendants()
```

## Troubleshooting

### Polymorphic Queries Not Working

If you're getting base Sample objects instead of typed instances:

1. Ensure you're querying through `Sample.objects` not `RockSample.objects`
2. Check that `polymorphic_ctype` is being set correctly
3. Verify migrations are up to date

### "Cannot create base Sample instances directly"

You, a fixture, or a library called `Sample.objects.create()` (or `.save()`) somewhere instead of
a concrete subclass. This is refused everywhere, including `bulk_create` and fixture loading —
retarget the call at your own sample type's factory or model.

### Circular Relationship Errors

If you're getting validation errors on relationships:

```python
# This is prevented by validation, and on save() directly
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
- [Sample Form and Filter Mixins](../forms-and-filters/sample-mixins.md) - The mixins your own forms and filters inherit
- [Filtering](../filtering-by-vocabulary.md) - Filter configuration
