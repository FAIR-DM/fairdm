# Research: DataCite RelationType Vocabulary

**Feature**: 004-core-datasets
**Task**: T011
**Purpose**: Document DataCite RelationType vocabulary for DatasetLiteratureRelation model

---

## DataCite Metadata Schema 4.x

**Source**: [DataCite Metadata Schema 4.4](https://schema.datacite.org/meta/kernel-4.4/doc/DataCite-MetadataKernel_v4.4.pdf)

**Property**: relatedIdentifier (with relationType attribute)

---

## Recommended Relationship Types for Datasets

Based on common dataset-publication relationships in research:

### Primary Types (Most Common)

| RelationType | Definition | Use Case | Example |
|-------------|------------|----------|---------|
| **IsCitedBy** | Indicates B includes A in a citation | Paper cites your dataset | "Smith 2024" cites "Dataset XYZ" |
| **Cites** | Indicates A includes B in a citation | Dataset cites methodology paper | Dataset cites "Methods Manual 2020" |
| **IsDocumentedBy** | Indicates B is documentation about A | Paper describes dataset methods | "Data Collection Protocol" documents dataset |
| **Documents** | Indicates A is documentation about B | Metadata document about paper | Technical report documents dataset |
| **IsSupplementTo** | Indicates A is a supplement to B | Dataset supplements paper | Additional data for published study |
| **IsSupplementedBy** | Indicates B is a supplement to A | Paper includes supplemental data | Paper supplements dataset with analysis |
| **IsDerivedFrom** | Indicates A is a derivative of B | Dataset derived from published data | Processed dataset from raw data paper |
| **IsSourceOf** | Indicates A is the source of B | Dataset is source for publication | Raw data used to create figures |

### Secondary Types (Less Common)

| RelationType | Definition | Use Case | Example |
|-------------|------------|----------|---------|
| **IsDescribedBy** | Indicates B describes A | Metadata record describes dataset | README describes dataset contents |
| **Describes** | Indicates A describes B | Dataset describes paper data | Metadata describes publication data |
| **IsVersionOf** | Indicates A is a version of B | Dataset v2 relates to v1 | Updated dataset from original |
| **HasVersion** | Indicates B is a version of A | Original has updated version | v1 has v2 as version |
| **IsPartOf** | Indicates A is a portion of B | Dataset subset of larger collection | Regional data is part of global dataset |
| **HasPart** | Indicates A includes B as a portion | Collection includes dataset | Multi-dataset project includes subset |
| **IsReferencedBy** | Indicates B references A | Paper references dataset without citing | Mentioned in literature review |
| **References** | Indicates A references B | Dataset metadata references paper | Dataset description mentions source |

### Specialized Types

| RelationType | Definition | Use Case | Example |
|-------------|------------|----------|---------|
| **IsReviewedBy** | Indicates B is a review of A | Peer review of dataset | Review article evaluates dataset |
| **Reviews** | Indicates A is a review of B | Dataset review article | Quality assessment of published data |
| **IsRequiredBy** | Indicates B requires A | Software requires dataset | Analysis code requires input data |
| **Requires** | Indicates A requires B | Dataset requires methodology paper | Dataset needs processing script |
| **IsCompiledBy** | Indicates B compiled/created A | Paper compiled dataset | Systematic review created dataset |
| **Compiles** | Indicates B is compiled/created by A | Dataset compiles paper data | Meta-analysis compiles studies |
| **IsCollectedBy** | Indicates B collected A | Organization collected dataset | Field campaign collected samples |
| **Collects** | Indicates B is collected by A | Collector created dataset | Researcher collected measurements |

---

## Recommended Implementation

### Django Model Choices

```python
DATACITE_RELATIONSHIP_TYPES = [
    # Most common - show first in dropdown
    ('IsCitedBy', _('Is Cited By')),
    ('Cites', _('Cites')),
    ('IsDocumentedBy', _('Is Documented By')),
    ('Documents', _('Documents')),
    ('IsSupplementTo', _('Is Supplement To')),
    ('IsSupplementedBy', _('Is Supplemented By')),
    ('IsDerivedFrom', _('Is Derived From')),
    ('IsSourceOf', _('Is Source Of')),

    # Secondary types
    ('IsDescribedBy', _('Is Described By')),
    ('Describes', _('Describes')),
    ('IsVersionOf', _('Is Version Of')),
    ('HasVersion', _('Has Version')),
    ('IsPartOf', _('Is Part Of')),
    ('HasPart', _('Has Part')),
    ('IsReferencedBy', _('Is Referenced By')),
    ('References', _('References')),

    # Specialized types
    ('IsReviewedBy', _('Is Reviewed By')),
    ('Reviews', _('Reviews')),
    ('IsRequiredBy', _('Is Required By')),
    ('Requires', _('Requires')),
    ('IsCompiledBy', _('Is Compiled By')),
    ('Compiles', _('Compiles')),
    ('IsCollectedBy', _('Is Collected By')),
    ('Collects', _('Collects')),

    # Bidirectional equivalence
    ('IsVariantFormOf', _('Is Variant Form Of')),
    ('IsOriginalFormOf', _('Is Original Form Of')),
    ('IsIdenticalTo', _('Is Identical To')),
    ('IsPublishedIn', _('Is Published In')),
]
```

### Usage Guidance Documentation

```python
class DatasetLiteratureRelation(models.Model):
    """
    Relationship between Dataset and LiteratureItem using DataCite types.

    Common Patterns:

    1. Paper cites your dataset:
       relationship_type='IsCitedBy'

    2. Paper describes dataset methodology:
       relationship_type='IsDocumentedBy'

    3. Dataset provides additional data for paper:
       relationship_type='IsSupplementTo'

    4. Dataset derived from published data:
       relationship_type='IsDerivedFrom'

    5. Paper is based on your dataset:
       relationship_type='IsSourceOf'

    See DataCite Metadata Schema 4.x for full definitions:
    https://schema.datacite.org/meta/kernel-4/
    """
```

---

## Validation Rules

### Field Validation

```python
def clean(self):
    """Validate relationship type against DataCite vocabulary."""
    valid_types = [choice[0] for choice in self.DATACITE_RELATIONSHIP_TYPES]
    if self.relationship_type not in valid_types:
        raise ValidationError({
            'relationship_type': _(
                'Relationship type must be one of: %(types)s'
            ) % {'types': ', '.join(valid_types)}
        })
```

### Uniqueness Constraint

```python
class Meta:
    unique_together = [['dataset', 'literature_item', 'relationship_type']]
```

**Rationale**: Same dataset-paper pair can have multiple relationship types (e.g., dataset both "Cites" and "IsDerivedFrom" the same paper).

---

## Admin Interface

### Inline Editor

```python
class DatasetLiteratureRelationInline(admin.TabularInline):
    model = DatasetLiteratureRelation
    extra = 1
    autocomplete_fields = ['literature_item']

    # Help text for relationship_type field
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['relationship_type'].help_text = _(
            'Select how this literature relates to the dataset. '
            'Common: IsCitedBy (paper cites dataset), IsDocumentedBy (paper describes methods), '
            'IsSupplementTo (dataset supplements paper).'
        )
        return formset
```

### Display in List

```python
@admin.display(description='Related Literature')
def literature_summary(self, obj):
    """Display summary of literature relationships."""
    relations = obj.literature_relations.all()[:5]
    if not relations:
        return "-"

    items = []
    for rel in relations:
        items.append(f"{rel.literature_item.title} ({rel.relationship_type})")

    result = ", ".join(items)
    if obj.literature_relations.count() > 5:
        result += f" ... +{obj.literature_relations.count() - 5} more"

    return result
```

---

## API Serialization

### Nested Representation

```python
class DatasetLiteratureRelationSerializer(serializers.ModelSerializer):
    """Serializer for dataset-literature relationships."""
    literature_item = LiteratureItemSerializer(read_only=True)
    relationship_type_display = serializers.CharField(
        source='get_relationship_type_display',
        read_only=True
    )

    class Meta:
        model = DatasetLiteratureRelation
        fields = [
            'id',
            'literature_item',
            'relationship_type',
            'relationship_type_display',
        ]


class DatasetSerializer(serializers.ModelSerializer):
    """Dataset serializer with literature relationships."""
    literature_relations = DatasetLiteratureRelationSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Dataset
        fields = [..., 'literature_relations']
```

---

## Testing Strategy

### Test Coverage Required

```python
# Test valid DataCite types
def test_all_datacite_types_valid():
    """All DataCite relationship types should validate."""
    for type_code, type_label in DATACITE_RELATIONSHIP_TYPES:
        relation = DatasetLiteratureRelation(
            dataset=dataset,
            literature_item=paper,
            relationship_type=type_code
        )
        relation.full_clean()  # Should not raise

# Test invalid types
def test_invalid_type_raises_error():
    """Non-DataCite types should raise ValidationError."""
    relation = DatasetLiteratureRelation(
        dataset=dataset,
        literature_item=paper,
        relationship_type='CustomType'
    )
    with pytest.raises(ValidationError):
        relation.full_clean()

# Test unique_together
def test_duplicate_relationships_prevented():
    """Cannot create duplicate dataset-paper-type combinations."""
    DatasetLiteratureRelation.objects.create(
        dataset=dataset,
        literature_item=paper,
        relationship_type='IsCitedBy'
    )

    with pytest.raises(IntegrityError):
        DatasetLiteratureRelation.objects.create(
            dataset=dataset,
            literature_item=paper,
            relationship_type='IsCitedBy'
        )

# Test multiple types allowed
def test_multiple_relationship_types_allowed():
    """Same dataset-paper can have multiple relationship types."""
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

---

## Documentation

### User-Facing Help

**In forms/admin**:
> **Relationship Type**: How this literature relates to the dataset. Common examples:
>
> - **Is Cited By**: The paper cites this dataset
> - **Is Documented By**: The paper describes the dataset methodology
> - **Is Supplement To**: This dataset provides additional data for the paper
> - **Is Derived From**: This dataset was created from data in the paper

**In developer docs**:
> DataCite RelationType vocabulary provides standardized relationship descriptors for scholarly resources. Use these types to describe how datasets and literature are connected, enabling better discovery and citation tracking.

---

## References

1. **DataCite Metadata Schema 4.4**: <https://schema.datacite.org/meta/kernel-4.4/>
2. **DataCite RelationType Vocabulary**: <https://support.datacite.org/docs/datacite-metadata-schema-44-properties-overview#12b-relationtype>
3. **FAIR Data Principles**: <https://www.go-fair.org/fair-principles/>

---

## Decision Summary

✅ **Use full DataCite 4.x RelationType vocabulary** (28 types)
✅ **Order by frequency of use** (common types first in dropdown)
✅ **Allow multiple relationships** per dataset-paper pair
✅ **Validate against vocabulary** at model level
✅ **Provide contextual help** in admin and forms
✅ **Include in API serialization** for external integrations
