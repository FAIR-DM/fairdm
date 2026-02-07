# Data Model: Core Sample Model Enhancement

**Feature**: 005-core-samples | **Date**: 2026-01-16 | **Phase**: 1 - Design

## Entity Overview

```
┌─────────────────┐
│    Dataset      │
│   (Feature 006) │
└────────┬────────┘
         │ 1:N
         │
    ┌────▼─────────────────┐
    │      Sample          │◄──────────┐
    │   (Polymorphic)      │           │
    │  - uuid: ShortUUID   │           │
    │  - name: CharField   │           │
    │  - local_id: str     │           │
    │  - status: CharField │           │ N:N
    │  - location: FK      │           │ (typed)
    │  - image: ImageField │           │
    └──────┬───────────────┘           │
           │                    ┌──────┴────────┐
           │ 1:N                │SampleRelation │
           │                    │ - source      │
    ┌──────▼────────┐          │ - target      │
    │ RockSample    │          │ - type        │
    │ WaterSample   │          └───────────────┘
    │ (Custom types)│
    └───────────────┘                 │ 1:N
           │                          │
           │ Concrete FK              │
           ▼                          ▼
    ┌─────────────────┐      ┌──────────────────┐
    │Sample Metadata  │      │  Location,       │
    │ - Description   │      │  Contributors    │
    │ - Date          │      │  (GenericRelation│
    │ - Identifier    │      │   for contrib)   │
    └─────────────────┘      └──────────────────┘
```

## Core Models

### Sample (Enhanced)

**Purpose**: Polymorphic base model for all sample types in FairDM portals. Aligns with IGSN metadata schema.

**Fields**:

```python
class Sample(BasePolymorphicModel):
    """
    Base polymorphic model for research samples.

    Inherits from BasePolymorphicModel to support domain-specific sample types
    (e.g., RockSample, WaterSample) that automatically integrate with the
    FairDM registry system.

    Aligns with IGSN (International Generic Sample Number) v1.0 metadata schema
    for interoperability with global sample repositories.
    """
    # Identification
    uuid = ShortUUIDField(
        default=shortuuid.uuid,
        length=22,
        prefix="s",
        unique=True,
        editable=False,
        help_text="Unique stable identifier for this sample"
    )

    name = models.CharField(
        max_length=200,
        help_text="Primary name/title for this sample"
    )

    local_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Dataset creator's local identifier (e.g., field ID, lab code)"
    )

    # Relationships
    dataset = models.ForeignKey(
        'core.Dataset',
        on_delete=models.CASCADE,
        related_name='samples',
        help_text="Dataset this sample belongs to"
    )

    # IGSN Core Fields
    status = models.CharField(
        max_length=50,
        choices=[], # Populated from research_vocabs.FairDMSampleStatus
        default='available',
        help_text="Current status of the physical sample"
    )

    sample_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of sample (from controlled vocabulary)"
    )

    material = models.CharField(
        max_length=200,
        blank=True,
        help_text="Primary material or substance of the sample"
    )

    location = models.ForeignKey(
        'fairdm_location.Point',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='samples',
        help_text="Geographic location where sample was collected"
    )

    # Media
    image = models.ImageField(
        upload_to='samples/images/',
        null=True,
        blank=True,
        help_text="Representative image of the sample"
    )

    # Audit
    added = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # Generic Relations (contributions only)
    contributors = GenericRelation('contributors.Contribution')

    # Tagging
    keywords = TaggableManager(blank=True)
    tags = TaggableManager(blank=True, related_name='sample_tags')

    # Note: descriptions, dates, identifiers use concrete ForeignKey
    # relationships (SampleDescription.related, SampleDate.related, etc.)
    # and are accessible via reverse relations: sample.descriptions.all()

    # Relationships (typed via SampleRelation through-model)
    related = models.ManyToManyField(
        'self',
        through='SampleRelation',
        through_fields=('source', 'target'),
        symmetrical=False,
        related_name='related_to',
        help_text="Related samples with typed relationships (parent-child, derived-from, etc.)"
    )

    objects = SampleQuerySet.as_manager()

    class Meta:
        ordering = ['-added']
        permissions = [
            ('view_sample', 'Can view sample'),
            ('import_data', 'Can import sample data'),
        ]

    def __str__(self):
        return self.name

    def get_all_relationships(self):
        """
        Get all SampleRelation instances where this sample is either source or target.

        Returns:
            QuerySet of SampleRelation instances involving this sample
        """
        from django.db.models import Q
        return SampleRelation.objects.filter(
            Q(source=self) | Q(target=self)
        )

    def get_related_samples(self, relationship_type=None):
        """
        Get all samples related to this sample in either direction.

        Args:
            relationship_type: Optional filter by relationship type

        Returns:
            QuerySet of Sample instances (deduplicated)
        """
        from django.db.models import Q

        # Get IDs of all related samples (both directions)
        relationships = self.get_all_relationships()

        if relationship_type:
            relationships = relationships.filter(relationship_type=relationship_type)

        # Collect sample IDs from both source and target
        related_ids = set()
        for rel in relationships:
            related_ids.add(rel.source_id if rel.source_id != self.pk else rel.target_id)

        return Sample.objects.filter(pk__in=related_ids)
```

**Model Manager**:

```python
class SampleQuerySet(PolymorphicQuerySet):
    """Optimized queryset for polymorphic sample queries."""

    def with_related(self):
        """Prefetch dataset, location, and contributors."""
        return self.select_related(
            'dataset',
            'location'
        ).prefetch_related(
            'contributors'
        )

    def with_metadata(self):
        """Prefetch descriptions, dates, identifiers."""
        return self.prefetch_related(
            'descriptions',
            'dates',
            'identifiers'
        )

    def by_relationship(self, relationship_type):
        """Filter samples by relationship type."""
        return self.filter(
            children__samplerelation__relationship_type=relationship_type
        ).distinct()

    def get_descendants(self, sample, max_depth=None):
        """
        Retrieve all descendant samples recursively.

        Args:
            sample: Root Sample instance
            max_depth: Maximum relationship depth (None = unlimited)

        Returns:
            QuerySet of descendant Sample instances
        """
        # Implementation: iterative BFS or recursive CTE
        # Handles circular prevention via visited set
        pass
```

### SampleRelation (New)

**Purpose**: Typed relationships between samples for provenance tracking.

**Fields**:

```python
class SampleRelation(models.Model):
    """
    Typed relationship between samples for provenance tracking.

    Supports various relationship types (parent-child, derived-from,
    split-from, aliquot-of, section-of) to maintain scientific
    reproducibility and sample lineage. Relationship type determines
    the semantic meaning of the source→target connection.
    """
    source = models.ForeignKey(
        'core.Sample',
        on_delete=models.CASCADE,
        related_name='relationships_as_source',
        help_text="Source sample in the relationship"
    )

    target = models.ForeignKey(
        'core.Sample',
        on_delete=models.CASCADE,
        related_name='relationships_as_target',
        help_text="Target sample in the relationship"
    )

    relationship_type = models.CharField(
        max_length=50,
        choices=[], # Populated from research_vocabs.FairDMSampleRelationshipTypes
        help_text="Type of relationship between samples"
    )

    created = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [
            ('source', 'target', 'relationship_type')
        ]
        ordering = ['-created']

    def clean(self):
        """Prevent circular relationships and self-references."""
        # 1. Prevent self-reference
        if self.source == self.target:
            raise ValidationError("Sample cannot relate to itself")

        # 2. Prevent direct circular (A→B and B→A with same type)
        if SampleRelation.objects.filter(
            source=self.target,
            target=self.source,
            relationship_type=self.relationship_type
        ).exists():
            raise ValidationError(
                f"Circular relationship detected: {self.target} already "
                f"has {self.relationship_type} relationship to {self.source}"
            )

        # 3. Check for deep circular chains (configurable depth limit)
        # Implementation: graph traversal to detect cycles

    def __str__(self):
        return f"{self.source} {self.relationship_type} {self.target}"
```

**Bidirectional Querying**:

The ManyToManyField configuration with `symmetrical=False` provides bidirectional relationship access:

```python
# Example: thin_section derived-from rock_sample
rock_sample = Sample.objects.get(name="Parent Rock")
thin_section = Sample.objects.get(name="Thin Section")

SampleRelation.objects.create(
    source=thin_section,
    target=rock_sample,
    relationship_type='derived-from'
)

# === Convenience Methods (Recommended) ===

# Get all relationship objects (both directions)
rock_sample.get_all_relationships()
# Returns: QuerySet of SampleRelation where rock_sample is source OR target

# Get all related samples (both directions, deduplicated)
rock_sample.get_related_samples()
# Returns: QuerySet of Sample instances related in either direction

# Filter by relationship type
rock_sample.get_related_samples(relationship_type='derived-from')
# Returns: Only samples with 'derived-from' relationship

# === Direct Queries (Fine-grained control) ===

# Query samples THIS sample relates TO (outgoing - where this is source)
thin_section.related.all()
# Returns: [rock_sample]

# Query samples that relate to THIS sample (incoming - where this is target)
rock_sample.related_to.all()
# Returns: [thin_section]

# Access full relationship objects for advanced queries
thin_section.relationships_as_source.all()  # SampleRelation queryset
rock_sample.relationships_as_target.all()   # SampleRelation queryset

# Filter by relationship type
thin_section.relationships_as_source.filter(relationship_type='derived-from')
rock_sample.related_to.filter(
    samplerelation__relationship_type='derived-from'
)
```

### Sample Metadata Models (Concrete ForeignKey Pattern)

These follow concrete ForeignKey patterns from Feature 005/006 for optimal query performance:

```python
class SampleDescription(AbstractDescription):
    """Typed descriptions for samples using controlled vocabulary.

    Uses concrete ForeignKey for 2-4x better query performance vs GenericForeignKey.
    Enables natural Django ORM queries and standard admin inlines.

    See: specs/005-core-samples/research/generic-vs-concrete-relations.md
    """
    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey(
        'Sample',
        on_delete=models.CASCADE,
        related_name='descriptions'
    )
    type = models.CharField(max_length=50)  # From VOCABULARY
    value = models.TextField()

    class Meta:
        unique_together = [('related', 'type')]

class SampleDate(AbstractDate):
    """Typed dates for samples (collected, processed, analyzed).

    Uses concrete ForeignKey pattern - see SampleDescription docstring.
    """
    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey(
        'Sample',
        on_delete=models.CASCADE,
        related_name='dates'
    )
    type = models.CharField(max_length=50)  # From VOCABULARY
    value = models.DateField()

    class Meta:
        unique_together = [('related', 'type')]
        ordering = ['value']

class SampleIdentifier(AbstractIdentifier):
    """External identifiers for samples (IGSN, DOI, Handle).

    Uses concrete ForeignKey pattern - see SampleDescription docstring.
    Includes IGSN type with regex validation.
    """
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey(
        'Sample',
        on_delete=models.CASCADE,
        related_name='identifiers'
    )
    type = models.CharField(max_length=50)  # From VOCABULARY
    value = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        unique_together = [('related', 'type')]
```

**Design Decision**: Concrete ForeignKey relationships provide:

- ✅ 2-4x faster queries (direct JOINs vs ContentType lookups)
- ✅ Full type safety and IDE autocomplete
- ✅ Standard Django admin inlines (no generic formset complexity)
- ✅ Natural ORM queries: `sample.descriptions.filter(type='Abstract')`
- ✅ Automatic FK indexes

**Trade-off**: 12 additional tables (ProjectDescription, DatasetDescription, SampleDescription, MeasurementDescription, etc.) vs 4 shared tables. Acceptable for framework-scale project.

See detailed analysis: `specs/005-core-samples/research/generic-vs-concrete-relations.md`

## Custom Sample Types (Demo Examples)

```python
# fairdm_demo/models.py
class RockSample(Sample):
    """
    Geological rock sample with mineral composition data.

    Demonstrates polymorphic sample type extending Sample base model.
    Automatically integrates with FairDM registry when registered.

    See: docs/developer-guide/models/custom-samples.md
    """
    mineral_type = models.CharField(
        max_length=100,
        help_text="Primary mineral composition"
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
        ]
    )

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"


class WaterSample(Sample):
    """
    Water sample with hydrochemical properties.

    See: docs/developer-guide/models/custom-samples.md
    """
    ph_level = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="pH level (0-14)"
    )

    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Temperature in Celsius"
    )

    salinity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Salinity in parts per thousand"
    )
```

## Validation Rules

### Sample Model

- `name`: Required, max 200 characters
- `local_id`: Optional, duplicates allowed (dataset-specific identifiers)
- `dataset`: Required, CASCADE delete (samples removed when dataset deleted)
- `status`: Required, must be from FairDMSampleStatus vocabulary
- `location`: Optional, SET_NULL if location deleted
- `uuid`: Auto-generated, unique, immutable

### SampleRelation Model

- `source` and `target`: Required, CASCADE delete
- `relationship_type`: Required, must be from vocabulary
- Unique constraint: (source, target, relationship_type)
- Cannot create self-references (clean() validation)
- Cannot create direct circular relationships (clean() validation)
- Deep circular chains prevented (clean() validation with graph traversal)

### Metadata Models

- `description_type`: Must be from DESCRIPTION_TYPES vocabulary
- `date_type`: Must be from DATE_TYPES vocabulary
- `identifier_type`: Must be from IDENTIFIER_TYPES vocabulary
- IGSN identifiers: Regex validation against IGSN format

## Migrations Strategy

### Additive Changes

- New fields added with `null=True` or defaults to avoid data migration
- Existing Sample model already exists; enhancements are additive
- SampleRelation model is new (no existing data)

### Migration Order

1. Add new Sample fields (sample_type, material if not present)
2. Create SampleRelation model
3. Add SampleDescription, SampleDate, SampleIdentifier if not present
4. Update controlled vocabulary choices (data migration)

### Backward Compatibility

- Existing samples continue to work with new fields optional
- No breaking changes to Sample model API
- New QuerySet methods are additions, existing queries unaffected

## Performance Considerations

### Polymorphic Queries

- Overhead: ~10-20ms per query (one additional JOIN)
- Mitigation: Use `select_subclasses()` only when type-specific fields needed
- Prefetch strategies reduce N+1 queries

### Sample Relationships

- Shallow hierarchies (<5 levels): Standard ORM performs well
- Deep hierarchies: Use `get_descendants()` with iterative fetching
- Circular detection: O(V+E) graph traversal, cached results

### Indexes

```python
class Sample(BasePolymorphicModel):
    class Meta:
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['local_id', 'dataset']),
            models.Index(fields=['status']),
            models.Index(fields=['added']),
        ]

class SampleRelation(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['source', 'relationship_type']),
            models.Index(fields=['target', 'relationship_type']),
        ]
```

## Open Questions Resolved

From research.md:

1. **Multiple relationships of same type?** → No, unique constraint prevents duplicates
2. **Permission model for relationships?** → Inherit from sample permissions (view sample = view relationships)
3. **Soft-delete relationships?** → Hard delete (CASCADE), relationships removed when samples deleted
4. **Admin relationship display?** → Inline formset on Sample admin, separate admin for bulk management

## Next Steps (Phase 2)

- Generate tasks.md breaking down implementation
- Define test coverage for each model/method
- Plan demo app updates with examples
- Document mixin usage patterns
