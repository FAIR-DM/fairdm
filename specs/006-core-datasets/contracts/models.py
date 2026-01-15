# Contract: Dataset Models

**Feature**: 006-core-datasets
**Purpose**: Define the public interface for Dataset model and related metadata models
**Input**: [data-model.md](../data-model.md)

## Dataset Model Interface

### Class Definition

```python
class Dataset(BaseModel):
    """
    A dataset is a collection of samples, measurements and associated metadata.

    The Dataset model is the second level in the FairDM schema hierarchy. All geographic
    sites, samples, and sample measurements MUST relate back to a dataset.

    Privacy-First Design:
        The default QuerySet excludes PRIVATE datasets. Use get_all() or with_private()
        to explicitly access private datasets.

    PROTECT Behavior:
        Projects with attached datasets cannot be deleted (on_delete=PROTECT).
        Orphaned datasets (project=null) are permitted but not encouraged.
    """
```

### Class Attributes

```python
CONTRIBUTOR_ROLES: VocabularyConcepts  # FairDMRoles.from_collection("Dataset")
DATE_TYPES: VocabularyConcepts         # FairDMDates.from_collection("Dataset")
DESCRIPTION_TYPES: VocabularyConcepts  # FairDMDescriptions.from_collection("Dataset")
VISIBILITY_CHOICES: IntegerChoices     # Visibility enum (PUBLIC, INTERNAL, PRIVATE)
DEFAULT_ROLES: list[str]               # ["ProjectMember"]
objects: DatasetQuerySet               # Privacy-first QuerySet manager
```

### Model Fields

```python
# Identifier
uuid: ShortUUIDField              # Unique, prefix="d", editable=False

# Core Fields
name: CharField                   # max_length=200, required
visibility: IntegerField          # choices=VISIBILITY_CHOICES, default=PRIVATE
image: ImageField                 # optional, for cards and meta tags

# Relationships
project: ForeignKey               # to Project, on_delete=PROTECT, optional
reference: OneToOneField          # to LiteratureItem, on_delete=SET_NULL, optional
related_literature: ManyToManyField  # to LiteratureItem, through=DatasetLiteratureRelation
license: LicenseField             # optional, default CC BY 4.0
contributors: GenericRelation     # to Contribution

# Timestamps (audit trail)
added: DateTimeField              # auto_now_add
modified: DateTimeField           # auto_now
```

### Reverse Relations

```python
# Accessed via related_name
descriptions: QuerySet[DatasetDescription]  # One-to-many reverse
dates: QuerySet[DatasetDate]                # One-to-many reverse
identifiers: QuerySet[DatasetIdentifier]    # One-to-many reverse
samples: QuerySet[Sample]                   # One-to-many reverse
measurements: QuerySet[Measurement]         # One-to-many reverse
```

### Properties

```python
@cached_property
def has_data(self) -> bool:
    """
    Check if the dataset has any samples or measurements.

    Returns:
        True if dataset has samples or measurements, False otherwise.

    Note:
        Empty datasets are valid (planning phase) but should be flagged
        in admin interface for administrator awareness.
    """
    return self.samples.exists() or self.measurements.exists()

@cached_property
def bbox(self) -> dict:
    """
    Calculate geographic bounding box for dataset based on sample locations.

    Returns:
        Dictionary with bbox coordinates or empty dict if no locations.
    """
    ...
```

### Permissions

```python
class Meta:
    permissions = [
        ("view_dataset", "Can view dataset"),
        ("add_dataset", "Can add dataset"),
        ("change_dataset", "Can change dataset"),
        ("delete_dataset", "Can delete dataset"),
        ("import_data", "Can import data into dataset"),
    ]
```

### Validation Rules

1. **name**: Required, max_length=200, non-empty string
2. **visibility**: Must be one of VISIBILITY_CHOICES (PUBLIC, INTERNAL, PRIVATE)
3. **project**: Optional, but when set, uses PROTECT behavior (prevents project deletion)
4. **license**: Optional, defaults to CC BY 4.0 in forms
5. **uuid**: Auto-generated, unique, immutable

### Behavior Contracts

**PROTECT Behavior**:
- Projects with attached datasets CANNOT be deleted
- Attempting to delete raises `ProtectedError`
- Orphaned datasets (project=null) ARE permitted

**Privacy-First Default**:
- `Dataset.objects.all()` excludes PRIVATE datasets by default
- Use `Dataset.objects.get_all()` or `.with_private()` for private access
- Prevents accidental exposure of private data

**Empty Datasets**:
- Datasets without samples/measurements are valid
- Use `has_data` property to check for content
- Admin interface should flag empty datasets

---

## DatasetDescription Interface

### Class Definition

```python
class DatasetDescription(AbstractDescription):
    """
    Typed descriptions for datasets using controlled FAIR vocabulary.

    Validates description_type against FairDMDescriptions vocabulary.
    """
    VOCABULARY = FairDMDescriptions.from_collection("Dataset")
    related: ForeignKey  # to Dataset, on_delete=CASCADE
```

### Fields

```python
related: ForeignKey           # to Dataset, required, on_delete=CASCADE
description_type: CharField   # max_length=50, choices from VOCABULARY, required
description: TextField        # required
```

### Validation

- `description_type` MUST be valid choice from VOCABULARY
- Validation errors reference vocabulary concept URIs
- `description` MUST be non-empty

---

## DatasetDate Interface

### Class Definition

```python
class DatasetDate(AbstractDate):
    """
    Typed dates for datasets using controlled FAIR vocabulary.

    Validates date_type against FairDMDates vocabulary.
    """
    VOCABULARY = FairDMDates.from_collection("Dataset")
    related: ForeignKey  # to Dataset, on_delete=CASCADE
```

### Fields

```python
related: ForeignKey       # to Dataset, required, on_delete=CASCADE
date_type: CharField      # max_length=50, choices from VOCABULARY, required
date: DateField           # required
```

### Validation

- `date_type` MUST be valid choice from VOCABULARY
- Validation errors reference vocabulary concept URIs
- `date` MUST be valid date

---

## DatasetIdentifier Interface

### Class Definition

```python
class DatasetIdentifier(AbstractIdentifier):
    """
    Typed identifiers for datasets using controlled FAIR vocabulary.

    Validates identifier_type against FairDMIdentifiers vocabulary.

    DOI Support:
        Use identifier_type='DOI' for DOI identifiers.
        The Dataset.reference field is for literature items, not DOIs.
    """
    VOCABULARY = FairDMIdentifiers()
    related: ForeignKey  # to Dataset, on_delete=CASCADE
```

### Fields

```python
related: ForeignKey          # to Dataset, required, on_delete=CASCADE
identifier_type: CharField   # max_length=50, choices from VOCABULARY, required
identifier: CharField        # max_length=255, required
```

### Validation

- `identifier_type` MUST be valid choice from VOCABULARY
- Validation errors reference vocabulary concept URIs
- `identifier` MUST be non-empty, format depends on identifier_type

### DOI Usage

```python
# Creating a DOI identifier
DatasetIdentifier.objects.create(
    related=my_dataset,
    identifier_type='DOI',
    identifier='10.1234/example.doi'
)

# Querying DOI
dataset.identifiers.filter(identifier_type='DOI').first()
```

---

## DatasetLiteratureRelation Interface

### Class Definition

```python
class DatasetLiteratureRelation(models.Model):
    """
    Intermediate model for Dataset-to-LiteratureItem relationships.

    Specifies relationship type using DataCite RelationType vocabulary.
    Enables rich metadata about how datasets relate to publications.
    """
```

### Fields

```python
dataset: ForeignKey          # to Dataset, required, on_delete=CASCADE
literature_item: ForeignKey  # to LiteratureItem, required, on_delete=CASCADE
relationship_type: CharField # max_length=50, choices=DATACITE_TYPES, required
```

### DataCite Relationship Types

```python
DATACITE_TYPES = [
    ('IsCitedBy', 'Is Cited By'),
    ('Cites', 'Cites'),
    ('IsSupplementTo', 'Is Supplement To'),
    ('IsSupplementedBy', 'Is Supplemented By'),
    ('IsReferencedBy', 'Is Referenced By'),
    ('References', 'References'),
    ('IsDocumentedBy', 'Is Documented By'),
    ('Documents', 'Documents'),
    # Additional types from DataCite RelationType vocabulary (T011)
]
```

### Validation

- `relationship_type` MUST be valid DataCite RelationType
- `unique_together` = [["dataset", "literature_item", "relationship_type"]]
- Prevents duplicate relationships of same type

### Usage Patterns

```python
# Creating relationship
DatasetLiteratureRelation.objects.create(
    dataset=my_dataset,
    literature_item=paper,
    relationship_type='IsCitedBy'
)

# Querying by relationship type
my_dataset.related_literature.through.objects.filter(
    relationship_type='IsCitedBy'
).values_list('literature_item', flat=True)

# Accessing from dataset
my_dataset.related_literature.all()  # All related literature
my_dataset.related_literature.through.objects.filter(
    dataset=my_dataset,
    relationship_type='Cites'
)  # Specific relationship types
```

---

## Usage Examples

### Creating a Dataset with Metadata

```python
from licensing.models import License

# Create dataset
dataset = Dataset.objects.create(
    name="Rock Sample Collection 2024",
    visibility=Visibility.PUBLIC,
    project=my_project,
    license=License.objects.filter(name="CC BY 4.0").first()
)

# Add descriptions
DatasetDescription.objects.create(
    related=dataset,
    description_type='Abstract',
    description='Collection of igneous rock samples...'
)

# Add dates
DatasetDate.objects.create(
    related=dataset,
    date_type='Collected',
    date='2024-06-15'
)

# Add DOI
DatasetIdentifier.objects.create(
    related=dataset,
    identifier_type='DOI',
    identifier='10.1234/rocks.2024'
)

# Add literature relationship
DatasetLiteratureRelation.objects.create(
    dataset=dataset,
    literature_item=publication,
    relationship_type='IsDocumentedBy'
)
```

### Querying Datasets

```python
# Public datasets only (privacy-first default)
public_datasets = Dataset.objects.all()

# All datasets including private (explicit opt-in)
all_datasets = Dataset.objects.get_all()  # or .with_private()

# Optimized query with related data
datasets = Dataset.objects.with_related().filter(project=my_project)

# Query by metadata
datasets_with_doi = Dataset.objects.filter(
    identifiers__identifier_type='DOI'
).distinct()

datasets_collected_after = Dataset.objects.filter(
    dates__date_type='Collected',
    dates__date__gte='2024-01-01'
).distinct()
```

### Checking Dataset Status

```python
dataset = Dataset.objects.get(uuid='d12345')

# Check if empty
if not dataset.has_data:
    print("Dataset has no samples or measurements")

# Check visibility
if dataset.visibility == Visibility.PRIVATE:
    # Handle private dataset access
    ...

# Check for DOI
doi = dataset.identifiers.filter(identifier_type='DOI').first()
if doi:
    print(f"Dataset DOI: {doi.identifier}")
```

---

## Migration Path

### Phase 1: Add New Models

```python
# Add DatasetLiteratureRelation
# Add vocabulary validators to Description/Date/Identifier
```

### Phase 2: Update Relationships

```python
# Change Dataset.project on_delete to PROTECT
# Update Dataset.related_literature through= parameter
```

### Phase 3: Update QuerySet

```python
# Implement privacy-first default in DatasetQuerySet
# Add get_all() or with_private() method
```

### Rollback Considerations

- CASCADE → PROTECT: Reversible, behavior change only
- through= parameter: Reversible, preserves data
- Privacy-first default: Reversible, code changes needed
- Vocabulary validators: Reversible, validate existing data first
