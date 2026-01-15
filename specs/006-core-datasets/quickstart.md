# Developer Quickstart: Dataset App

**Feature**: 006-core-datasets
**Purpose**: Onboarding guide for developers working with the enhanced dataset app
**Audience**: Portal developers, contributors, plugin authors

---

## 1. Creating Datasets

### Basic Dataset Creation

```python
from fairdm.core.dataset.models import Dataset

# Create basic dataset
dataset = Dataset.objects.create(
    name="Geological Survey 2024",
    project=my_project,
    description="Regional geological survey data from 2024 field season"
)
```

### With Full Metadata

```python
from licensing.models import License

# Create dataset with complete metadata
dataset = Dataset.objects.create(
    name="XRF Analysis Results",
    project=project,
    description="X-ray fluorescence analysis of rock samples",
    image="datasets/xrf_setup.jpg",
    license=License.objects.get(name="CC BY 4.0"),
    visibility=Dataset.PUBLIC,
)

# Add descriptions
dataset.descriptions.create(
    description_type="Abstract",
    description="Detailed abstract text..."
)
dataset.descriptions.create(
    description_type="Methods",
    description="Methodology description..."
)

# Add important dates
from datetime import date
dataset.dates.create(
    date_type="Created",
    date=date(2024, 1, 15)
)
dataset.dates.create(
    date_type="Submitted",
    date=date(2024, 3, 20)
)

# Add identifiers
dataset.identifiers.create(
    identifier_type="DOI",
    identifier="10.1000/xyz123"
)
```

---

## 2. Using DatasetForm

### Basic Form Usage

```python
from fairdm.core.dataset.forms import DatasetForm

# In views.py
def create_dataset(request):
    if request.method == 'POST':
        # IMPORTANT: Pass request for user context
        form = DatasetForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            dataset = form.save()
            return redirect('dataset_detail', pk=dataset.pk)
    else:
        form = DatasetForm(request=request)

    return render(request, 'dataset/create.html', {'form': form})
```

### Understanding User Context

The form requires `request` parameter to:

1. Filter project queryset (user can only create datasets in projects they have access to)
2. Set default license (CC BY 4.0)
3. Track user creating the dataset (via `save(commit=False)`)

```python
# Example: Custom queryset filtering
form = DatasetForm(request=request)
# Form automatically filters projects based on user's permissions
# form.fields['project'].queryset includes only user's projects
```

### Handling DOI Field

```python
# DOI input creates DatasetIdentifier on save
form = DatasetForm(request.POST, request=request)
if form.is_valid():
    dataset = form.save()  # Automatically creates DOI identifier if provided

    # DOI is stored in identifiers
    doi = dataset.identifiers.filter(identifier_type='DOI').first()
    print(doi.identifier)  # "10.1000/xyz123"
```

---

## 3. Using DatasetFilter

### In Views

```python
from django_filters.views import FilterView
from fairdm.core.dataset.filters import DatasetFilter
from fairdm.core.dataset.tables import DatasetTable

class DatasetListView(FilterView):
    model = Dataset
    filterset_class = DatasetFilter
    table_class = DatasetTable
    template_name = 'dataset/list.html'

    def get_queryset(self):
        # Use privacy-first queryset
        return Dataset.objects.all()  # Excludes PRIVATE by default
```

### In Templates

```html
<!-- templates/dataset/list.html -->
<form method="get">
    {{ filter.form }}
    <button type="submit">Filter</button>
</form>

{% load render_table from django_tables2 %}
{% render_table table %}
```

### Filter Examples

```python
# Generic search (searches name, uuid, keywords, related descriptions)
?search=geological

# Filter by project
?project=5

# Filter by license
?license=CC+BY+4.0

# Filter by visibility
?visibility=PUBLIC

# Filter by description type content
?description=methodology

# Filter by date type
?date_type=Created

# Combine filters (AND logic)
?search=rock&project=5&license=CC+BY+4.0
```

---

## 4. Working with DatasetLiteratureRelation

### Creating Relationships

```python
from fairdm.core.dataset.models import DatasetLiteratureRelation
from literature.models import LiteratureItem

# Create relationship with DataCite type
DatasetLiteratureRelation.objects.create(
    dataset=my_dataset,
    literature_item=paper,
    relationship_type='IsCitedBy'
)
```

### Common Relationship Types

| Type | Meaning | Example Use Case |
|------|---------|------------------|
| `IsCitedBy` | Dataset is cited by this literature | Paper citing your dataset |
| `IsDocumentedBy` | Dataset is documented by this literature | Methods paper describing dataset |
| `IsDerivedFrom` | Dataset is derived from this literature | Dataset based on published data |
| `IsSupplementTo` | Dataset supplements this literature | Additional data for a paper |
| `Cites` | Dataset cites this literature | Dataset references a methodology |

**See [contracts/intermediate_models.py](contracts/intermediate_models.py) for full list of DataCite types.**

### Querying Relationships

```python
# Get all papers citing a dataset
citing_papers = dataset.related_literature.filter(
    dataset_relations__relationship_type='IsCitedBy'
)

# Get all datasets documented by a paper
documented = paper.related_datasets.filter(
    literature_relations__relationship_type='IsDocumentedBy'
)

# Get relationship details
for relation in dataset.literature_relations.all():
    print(f"{relation.literature_item.title}: {relation.relationship_type}")
```

### Admin Integration

Literature relationships appear as inline formsets in Dataset admin:

- Autocomplete search for literature items
- Dropdown for DataCite relationship types
- Can add multiple relationships with different types

---

## 5. Understanding Privacy-First QuerySets

### Default Behavior

```python
# Privacy-first: Excludes PRIVATE datasets by default
Dataset.objects.all()  # Returns PUBLIC, REGISTERED, EMBARGOED

# Explicitly include PRIVATE
Dataset.objects.with_private()  # Returns ALL visibility levels

# Get truly all datasets (manager method)
Dataset.objects.get_all()  # Returns all (bypasses privacy filter)
```

### When to Use Each Method

| Method | Use Case | Returns PRIVATE? |
|--------|----------|------------------|
| `.all()` | Public lists, search results | ❌ No |
| `.with_private()` | Admin views, owner access | ✅ Yes |
| `.get_all()` | System tasks, migrations | ✅ Yes |

### Permission Checks

```python
# Check if user can view dataset
if user.has_perm('dataset.view_dataset', dataset):
    # Show dataset
    pass

# Check if user can edit dataset
if user.has_perm('dataset.change_dataset', dataset):
    # Allow editing
    pass
```

### Optimization

```python
# Use with_related() to prefetch related data
datasets = Dataset.objects.all().with_related()
# Prefetches: project, license, image, contributors

# For specific relationships
datasets = Dataset.objects.select_related('project', 'license')
```

---

## 6. Adding DOIs to Datasets

### Via Form

The `DatasetForm` includes a `doi` field that automatically creates a `DatasetIdentifier`:

```python
form_data = {
    'name': 'My Dataset',
    'project': project.id,
    'doi': '10.1000/xyz123',  # Creates identifier on save
}
form = DatasetForm(form_data, request=request)
if form.is_valid():
    dataset = form.save()
    # DOI identifier created automatically
```

### Programmatically

```python
from fairdm.core.dataset.models import DatasetIdentifier

# Add DOI identifier
DatasetIdentifier.objects.create(
    dataset=dataset,
    identifier_type='DOI',
    identifier='10.1000/xyz123'
)

# Check if dataset has DOI
has_doi = dataset.identifiers.filter(identifier_type='DOI').exists()
```

### License Change Protection

Once a dataset has a DOI, changing the license triggers a warning in admin:

```python
# In admin save_model()
if dataset.pk and 'license' in form.changed_data:
    if dataset.identifiers.filter(identifier_type='DOI').exists():
        messages.warning(
            request,
            "This dataset has a DOI. Changing the license may affect "
            "published metadata. Update DOI registration if needed."
        )
```

---

## 7. Role-Based Permissions

### FairDM Roles

The dataset app integrates with FairDM role system:

| Role | Permissions |
|------|-------------|
| **Viewer** | View public datasets, view project datasets if member |
| **Contributor** | Create datasets in projects they belong to |
| **Editor** | Edit datasets in projects they belong to |
| **Manager** | Full control over project datasets |

### Checking Permissions

```python
from fairdm.core.utils.permissions import user_can_view, user_can_edit

# Check view permission
if user_can_view(user, dataset):
    # Show dataset
    pass

# Check edit permission
if user_can_edit(user, dataset):
    # Show edit form
    pass
```

### Dataset Visibility Rules

| Visibility | Who Can View? |
|------------|---------------|
| `PUBLIC` | Anyone (including anonymous) |
| `REGISTERED` | Logged-in users only |
| `EMBARGOED` | Project members + portal admins |
| `PRIVATE` | Dataset contributors + project managers + portal admins |

---

## 8. Admin Customization

### Dynamic Inline Limits

Description and Date inlines automatically limit max_num based on vocabulary size:

```python
# In admin.py
class DatasetDescriptionInline(admin.TabularInline):
    model = DatasetDescription

    def get_formset(self, request, obj=None, **kwargs):
        kwargs['max_num'] = len(Dataset.DESCRIPTION_TYPES)
        return super().get_formset(request, obj, **kwargs)
```

**Why?** If Dataset has 10 description types, no point showing 20 empty forms.

### Custom Actions

```python
from django.contrib import admin
from fairdm.core.dataset.admin import DatasetAdmin

# Extend with custom action
@admin.action(description="Mark as reviewed")
def mark_reviewed(modeladmin, request, queryset):
    queryset.update(reviewed=True)

class MyDatasetAdmin(DatasetAdmin):
    actions = DatasetAdmin.actions + [mark_reviewed]
```

### Search Configuration

```python
class DatasetAdmin(admin.ModelAdmin):
    search_fields = ['name', 'uuid', 'descriptions__description']
    # Searches: dataset name, UUID, and related description text
```

---

## 9. Common Patterns & Gotchas

### ✅ DO: Use Privacy-First Defaults

```python
# Good: Privacy-first
datasets = Dataset.objects.all()

# Good: Explicit when needed
all_datasets = Dataset.objects.with_private()
```

### ❌ DON'T: Bypass Privacy Unnecessarily

```python
# Bad: Exposes private datasets
datasets = Dataset.objects.get_all()  # Only for system tasks!
```

### ✅ DO: Pass Request to Forms

```python
# Good: Form can filter by user
form = DatasetForm(request.POST, request=request)
```

### ❌ DON'T: Omit Request Parameter

```python
# Bad: Breaks user context
form = DatasetForm(request.POST)  # TypeError!
```

### ✅ DO: Use PROTECT for Projects

```python
# Good: Deleting project checks for datasets first
project.delete()  # Raises ProtectedError if has datasets
```

### ❌ DON'T: Force Delete Projects

```python
# Bad: Orphans datasets
for dataset in project.datasets.all():
    dataset.project = None
    dataset.save()
project.delete()
```

### ✅ DO: Validate Relationship Types

```python
# Good: Use DataCite vocabulary
DatasetLiteratureRelation.objects.create(
    dataset=dataset,
    literature_item=paper,
    relationship_type='IsCitedBy'  # Valid DataCite type
)
```

### ❌ DON'T: Use Custom Relationship Types

```python
# Bad: Not DataCite standard
DatasetLiteratureRelation.objects.create(
    relationship_type='MyCustomType'  # ValidationError!
)
```

---

## 10. Testing Your Dataset Code

### Factory Usage

```python
from fairdm.core.dataset.factories import DatasetFactory

# Create test dataset
dataset = DatasetFactory()

# With specific values
dataset = DatasetFactory(
    name="Test Dataset",
    visibility=Dataset.PUBLIC
)

# Create batch
datasets = DatasetFactory.create_batch(10)
```

### Testing Forms

```python
import pytest
from fairdm.core.dataset.forms import DatasetForm

@pytest.mark.django_db
def test_dataset_form_requires_request():
    """DatasetForm must receive request parameter."""
    with pytest.raises(TypeError):
        form = DatasetForm({})  # Missing request

@pytest.mark.django_db
def test_dataset_form_filters_projects(rf):
    """Form filters projects by user permissions."""
    request = rf.get('/')
    request.user = user

    form = DatasetForm(request=request)
    # Only shows projects user has access to
    assert form.fields['project'].queryset.count() > 0
```

### Testing QuerySets

```python
@pytest.mark.django_db
def test_privacy_first_queryset():
    """Default queryset excludes PRIVATE datasets."""
    DatasetFactory(visibility=Dataset.PUBLIC)
    DatasetFactory(visibility=Dataset.PRIVATE)

    assert Dataset.objects.all().count() == 1  # Only PUBLIC

@pytest.mark.django_db
def test_with_private_includes_all():
    """with_private() includes PRIVATE datasets."""
    DatasetFactory(visibility=Dataset.PUBLIC)
    DatasetFactory(visibility=Dataset.PRIVATE)

    assert Dataset.objects.with_private().count() == 2
```

### Testing Admin

```python
from django.contrib.admin.sites import AdminSite
from fairdm.core.dataset.admin import DatasetAdmin

@pytest.mark.django_db
def test_dynamic_inline_max_num(rf):
    """Description inline limits to vocabulary size."""
    request = rf.get('/')
    admin = DatasetAdmin(Dataset, AdminSite())

    formset = admin.get_formset(request, obj=None)
    assert formset.max_num == len(Dataset.DESCRIPTION_TYPES)
```

---

## Next Steps

1. **Read contracts/**: Detailed interface specifications for all components
2. **Explore fairdm_demo/**: Reference implementation and examples
3. **Check tests/**: Comprehensive test suite demonstrating all features
4. **Review plan.md**: Architectural decisions and trade-offs

## Questions?

- **Architecture**: See [plan.md](plan.md) for technology decisions
- **Data Models**: See [data-model.md](data-model.md) for entity definitions
- **Implementation Details**: See [contracts/](contracts/) for interface specs
- **User Stories**: See [spec.md](spec.md) for functional requirements
