# Contract: Dataset Literature Relation

**Feature**: 004-core-datasets
**Purpose**: Define the public interface for DatasetLiteratureRelation intermediate model with DataCite relationship types
**Input**: [data-model.md](../data-model.md), [plan.md](../plan.md)

## DatasetLiteratureRelation Interface

### Class Definition

```python
class DatasetLiteratureRelation(models.Model):
    """
    Intermediate model for Dataset-to-LiteratureItem relationships with DataCite types.

    This model enables rich metadata about how datasets relate to publications,
    following DataCite RelationType vocabulary standards.

    Usage:
        Datasets and literature items have many-to-many relationships with
        specific relationship type metadata (IsCitedBy, Cites, IsSupplementTo, etc.)

    DataCite Standard:
        Follows DataCite Metadata Schema 4.x RelationType vocabulary
        https://schema.datacite.org/meta/kernel-4/doc/DataCite-MetadataKernel_v4.4.pdf
    """
```

### Fields

```python
dataset = models.ForeignKey(
    'dataset.Dataset',
    on_delete=models.CASCADE,
    related_name='literature_relations',
    verbose_name=_('dataset'),
    help_text=_('Dataset in the relationship'),
)

literature_item = models.ForeignKey(
    'literature.LiteratureItem',
    on_delete=models.CASCADE,
    related_name='dataset_relations',
    verbose_name=_('literature item'),
    help_text=_('Literature item (publication, report, etc.) in the relationship'),
)

relationship_type = models.CharField(
    max_length=50,
    choices=DATACITE_RELATIONSHIP_TYPES,
    verbose_name=_('relationship type'),
    help_text=_('Type of relationship between dataset and literature (DataCite standard)'),
)
```

### DataCite Relationship Types

Based on DataCite Metadata Schema 4.x:

```python
DATACITE_RELATIONSHIP_TYPES = [
    # Forward relationships (dataset → literature)
    ('Cites', _('Cites')),
    ('References', _('References')),
    ('IsSupplementTo', _('Is Supplement To')),
    ('IsDocumentedBy', _('Is Documented By')),
    ('IsDescribedBy', _('Is Described By')),
    ('IsDerivedFrom', _('Is Derived From')),
    ('IsSourceOf', _('Is Source Of')),
    ('IsVersionOf', _('Is Version Of')),
    ('IsPartOf', _('Is Part Of')),
    ('HasVersion', _('Has Version')),
    ('IsReviewedBy', _('Is Reviewed By')),
    ('Reviews', _('Reviews')),
    ('IsRequiredBy', _('Is Required By')),
    ('Requires', _('Requires')),

    # Reverse relationships (literature → dataset)
    ('IsCitedBy', _('Is Cited By')),
    ('IsReferencedBy', _('Is Referenced By')),
    ('IsSupplementedBy', _('Is Supplemented By')),
    ('Documents', _('Documents')),
    ('Describes', _('Describes')),
    ('IsVariantFormOf', _('Is Variant Form Of')),
    ('IsOriginalFormOf', _('Is Original Form Of')),
    ('IsIdenticalTo', _('Is Identical To')),
    ('HasPart', _('Has Part')),
    ('IsPublishedIn', _('Is Published In')),
    ('IsCompiledBy', _('Is Compiled By')),
    ('Compiles', _('Compiles')),
    ('IsCollectedBy', _('Is Collected By')),
    ('Collects', _('Collects')),
]
```

### Meta Configuration

```python
class Meta:
    verbose_name = _('dataset literature relation')
    verbose_name_plural = _('dataset literature relations')
    unique_together = [['dataset', 'literature_item', 'relationship_type']]
    indexes = [
        models.Index(fields=['dataset', 'relationship_type']),
        models.Index(fields=['literature_item', 'relationship_type']),
    ]
```

### Validation

```python
def clean(self):
    """
    Validate relationship type against DataCite vocabulary.

    Raises:
        ValidationError: If relationship_type not in DATACITE_RELATIONSHIP_TYPES
    """
    valid_types = [choice[0] for choice in self.DATACITE_RELATIONSHIP_TYPES]
    if self.relationship_type not in valid_types:
        raise ValidationError({
            'relationship_type': _(
                'Relationship type must be one of: %(types)s'
            ) % {'types': ', '.join(valid_types)}
        })
```

### String Representation

```python
def __str__(self):
    """Human-readable representation."""
    return f"{self.dataset.name} {self.relationship_type} {self.literature_item.title}"
```

---

## Usage in Dataset Model

### ManyToMany Through Configuration

```python
class Dataset(BaseModel):
    related_literature = models.ManyToManyField(
        'literature.LiteratureItem',
        through='DatasetLiteratureRelation',
        related_name='related_datasets',
        related_query_name='related_dataset',
        blank=True,
    )
```

---

## Usage Examples

### Creating Relationships

```python
# Direct creation
DatasetLiteratureRelation.objects.create(
    dataset=my_dataset,
    literature_item=paper,
    relationship_type='IsCitedBy'
)

# Bulk creation
relations = [
    DatasetLiteratureRelation(
        dataset=dataset,
        literature_item=paper1,
        relationship_type='IsDocumentedBy'
    ),
    DatasetLiteratureRelation(
        dataset=dataset,
        literature_item=paper2,
        relationship_type='IsDerivedFrom'
    ),
]
DatasetLiteratureRelation.objects.bulk_create(relations)
```

### Querying Relationships

```python
# Get all literature citing a dataset
citing_papers = dataset.related_literature.filter(
    dataset_relations__relationship_type='IsCitedBy'
)

# Get all datasets documented by a paper
documented_datasets = paper.related_datasets.filter(
    literature_relations__relationship_type='IsDocumentedBy'
)

# Get relationship details
relations = DatasetLiteratureRelation.objects.filter(
    dataset=my_dataset
).select_related('literature_item')

for relation in relations:
    print(f"{relation.literature_item.title}: {relation.relationship_type}")
```

### Filtering by Relationship Type

```python
# Datasets that cite literature
datasets_citing = Dataset.objects.filter(
    literature_relations__relationship_type='Cites'
).distinct()

# Literature cited by datasets
papers_cited = LiteratureItem.objects.filter(
    dataset_relations__relationship_type='IsCitedBy'
).distinct()
```

---

## Testing Contracts

### Relationship Creation Tests

```python
def test_create_literature_relation():
    """Can create dataset-literature relationship."""
    dataset = DatasetFactory()
    paper = LiteratureItemFactory()

    relation = DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsCitedBy'
    )

    assert relation.dataset == dataset
    assert relation.literature_item == paper
    assert relation.relationship_type == 'IsCitedBy'

def test_unique_together_constraint():
    """Cannot create duplicate relationships of same type."""
    dataset = DatasetFactory()
    paper = LiteratureItemFactory()

    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsCitedBy'
    )

    # Duplicate should raise IntegrityError
    with pytest.raises(IntegrityError):
        DatasetLiteratureRelation.objects.create(
            dataset=dataset,
            literature_item=paper,
            relationship_type='IsCitedBy'
        )

def test_different_relationship_types_allowed():
    """Same dataset-paper can have multiple relationship types."""
    dataset = DatasetFactory()
    paper = LiteratureItemFactory()

    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsCitedBy'
    )
    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsDocumentedBy'
    )

    assert dataset.literature_relations.count() == 2
```

### Validation Tests

```python
def test_invalid_relationship_type_raises_error():
    """Invalid relationship type raises ValidationError."""
    relation = DatasetLiteratureRelation(
        dataset=DatasetFactory(),
        literature_item=LiteratureItemFactory(),
        relationship_type='InvalidType'
    )

    with pytest.raises(ValidationError):
        relation.full_clean()

def test_valid_datacite_types_accepted():
    """All DataCite relationship types are valid."""
    dataset = DatasetFactory()
    paper = LiteratureItemFactory()

    for type_value, type_label in DATACITE_RELATIONSHIP_TYPES:
        relation = DatasetLiteratureRelation(
            dataset=dataset,
            literature_item=paper,
            relationship_type=type_value
        )
        relation.full_clean()  # Should not raise
```

### Query Tests

```python
def test_query_by_relationship_type():
    """Can filter by relationship type."""
    dataset = DatasetFactory()
    paper1 = LiteratureItemFactory()
    paper2 = LiteratureItemFactory()

    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper1,
        relationship_type='IsCitedBy'
    )
    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper2,
        relationship_type='IsDocumentedBy'
    )

    citing = dataset.related_literature.filter(
        dataset_relations__relationship_type='IsCitedBy'
    )
    assert citing.count() == 1
    assert paper1 in citing
```

### CASCADE Behavior Tests

```python
def test_cascade_on_dataset_delete():
    """Deleting dataset deletes relationships."""
    dataset = DatasetFactory()
    paper = LiteratureItemFactory()

    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsCitedBy'
    )

    dataset.delete()
    assert DatasetLiteratureRelation.objects.count() == 0

def test_cascade_on_literature_delete():
    """Deleting literature deletes relationships."""
    dataset = DatasetFactory()
    paper = LiteratureItemFactory()

    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsCitedBy'
    )

    paper.delete()
    assert DatasetLiteratureRelation.objects.count() == 0
```

---

## Admin Integration

### Inline Admin

```python
class DatasetLiteratureRelationInline(admin.TabularInline):
    """
    Inline editor for dataset-literature relationships in admin.

    Displays relationship type dropdown with DataCite choices.
    """
    model = DatasetLiteratureRelation
    extra = 1
    autocomplete_fields = ['literature_item']

class DatasetAdmin(admin.ModelAdmin):
    inlines = [DatasetLiteratureRelationInline, ...]
```

---

## Migration Path

### Phase 1: Create Model (Breaking Change)

```python
# Create DatasetLiteratureRelation model
# This converts simple ManyToMany to through model

class Migration:
    operations = [
        migrations.CreateModel(
            name='DatasetLiteratureRelation',
            fields=[...],
        ),
        migrations.AlterField(
            model_name='dataset',
            name='related_literature',
            field=models.ManyToManyField(
                through='DatasetLiteratureRelation',
                ...
            ),
        ),
    ]
```

**Impact**: Existing dataset-literature relationships are preserved. Django automatically migrates data from old join table to new intermediate model.

### Rollback

To revert to simple ManyToMany:

```python
class Migration:
    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='related_literature',
            field=models.ManyToManyField(
                # Remove through parameter
            ),
        ),
        migrations.DeleteModel(name='DatasetLiteratureRelation'),
    ]
```

**Note**: Relationship type metadata will be lost on rollback.
