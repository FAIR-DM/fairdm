# Contract: Dataset Admin

**Feature**: 004-core-datasets
**Purpose**: Define the public interface for DatasetAdmin with dynamic inlines and security-conscious bulk actions
**Input**: [data-model.md](../data-model.md), [plan.md](../plan.md)

## DatasetAdmin Interface

### Class Definition

```python
@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Dataset model.

    Features:
        - Search by name and UUID
        - Filters by project, license, visibility
        - Dynamic inline form limits based on vocabulary size
        - Bulk metadata export (JSON, DataCite format)
        - NO bulk visibility change actions (security)
        - License change warnings when DOI exists
        - Autocomplete on ForeignKey/ManyToMany fields

    Security:
        Bulk visibility changes are explicitly prohibited to prevent
        accidental exposure of private datasets by portal administrators.
    """
```

### Configuration Attributes

```python
# Search
search_fields = ['name', 'uuid']
search_help_text = _('Search by dataset name or UUID')

# List display
list_display = [
    'name',
    'project',
    'visibility',
    'has_data',
    'added',
    'modified',
]

# Filters
list_filter = [
    'project',
    'license',
    'visibility',
    'added',
    'modified',
]

# Read-only fields
readonly_fields = ['uuid', 'added', 'modified']

# Autocomplete
autocomplete_fields = ['project', 'related_literature']

# Inline editors
inlines = [
    DatasetDescriptionInline,
    DatasetDateInline,
    DatasetIdentifierInline,
]

# Field organization
fieldsets = [
    (_('Basic Information'), {
        'fields': ['name', 'uuid', 'image'],
    }),
    (_('Project & Access'), {
        'fields': ['project', 'visibility'],
        'description': _('Project association and access control settings'),
    }),
    (_('Licensing & References'), {
        'fields': ['license', 'reference', 'related_literature'],
        'description': _('License for data usage and related publications'),
    }),
    (_('Metadata'), {
        'fields': ['added', 'modified'],
        'classes': ['collapse'],
    }),
]
```

### Dynamic Inline Configuration

```python
class DatasetDescriptionInline(admin.TabularInline):
    """
    Inline editor for dataset descriptions with dynamic form limits.

    Form Limit:
        Automatically adjusts max_num based on number of available
        description types in vocabulary. Prevents hard-coded limits
        that break when vocabularies are extended.
    """
    model = DatasetDescription
    extra = 1
    # max_num dynamically set in get_formset()

class DatasetDateInline(admin.TabularInline):
    """
    Inline editor for dataset dates with dynamic form limits.

    Form Limit:
        Automatically adjusts max_num based on number of available
        date types in vocabulary.
    """
    model = DatasetDate
    extra = 1
    # max_num dynamically set in get_formset()
```

### Methods

#### get_formset() - Dynamic Inline Limits

```python
def get_formset(self, request, obj=None, **kwargs):
    """
    Dynamically set max_num for inline formsets based on vocabulary size.

    Args:
        request: HttpRequest object
        obj: Dataset instance (None for add view)
        **kwargs: Additional formset arguments

    Returns:
        Formset class with dynamic max_num

    Behavior:
        - For DescriptionInline: max_num = len(Dataset.DESCRIPTION_TYPES)
        - For DateInline: max_num = len(Dataset.DATE_TYPES)
        - Ensures forms adapt when vocabularies are extended

    Example:
        If DESCRIPTION_TYPES has 5 types, max_num = 5
        If vocabulary extended to 8 types, max_num automatically becomes 8
    """
    formset = super().get_formset(request, obj, **kwargs)

    # Determine inline type and set appropriate max_num
    if isinstance(self, DatasetDescriptionInline):
        formset.max_num = len(Dataset.DESCRIPTION_TYPES)
    elif isinstance(self, DatasetDateInline):
        formset.max_num = len(Dataset.DATE_TYPES)

    return formset
```

#### save_model() - License Change Warnings

```python
def save_model(self, request, obj, form, change):
    """
    Save dataset with license change warning if DOI exists.

    Args:
        request: HttpRequest object
        obj: Dataset instance being saved
        form: ModelForm instance
        change: Boolean indicating edit (True) vs create (False)

    Behavior:
        - If license changed AND dataset has DOI identifier:
          Display warning message about license change implications
        - Saves dataset regardless (allows corrections)
        - Warning appears in Django messages framework
    """
    # Check if license changed
    if change and 'license' in form.changed_data:
        # Check for DOI
        has_doi = obj.identifiers.filter(identifier_type='DOI').exists()
        if has_doi:
            messages.warning(
                request,
                _(
                    'This dataset has a DOI. Changing the license may have '
                    'legal implications. Ensure this change is authorized.'
                )
            )

    super().save_model(request, obj, form, change)
```

### Actions

#### Bulk Metadata Export (Allowed)

```python
@admin.action(description=_('Export selected datasets as JSON'))
def export_metadata_json(modeladmin, request, queryset):
    """
    Export dataset metadata as JSON.

    Args:
        modeladmin: ModelAdmin instance
        request: HttpRequest object
        queryset: QuerySet of selected datasets

    Returns:
        HttpResponse with JSON file download

    Format:
        [
            {
                "uuid": "d123abc",
                "name": "Dataset Name",
                "visibility": "PUBLIC",
                "license": "CC BY 4.0",
                ...
            },
            ...
        ]
    """
    data = []
    for dataset in queryset:
        data.append({
            'uuid': dataset.uuid,
            'name': dataset.name,
            'visibility': dataset.get_visibility_display(),
            'license': dataset.license.name if dataset.license else None,
            'project': dataset.project.name if dataset.project else None,
            'added': dataset.added.isoformat(),
            'modified': dataset.modified.isoformat(),
        })

    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="datasets.json"'
    return response

@admin.action(description=_('Export selected datasets as DataCite JSON'))
def export_metadata_datacite(modeladmin, request, queryset):
    """
    Export dataset metadata as DataCite JSON.

    Args:
        modeladmin: ModelAdmin instance
        request: HttpRequest object
        queryset: QuerySet of selected datasets

    Returns:
        HttpResponse with DataCite JSON file download

    Format:
        Follows DataCite Metadata Schema 4.x
        https://schema.datacite.org/meta/kernel-4/
    """
    # Implementation generates DataCite-compliant JSON
    ...

# Register actions
actions = [export_metadata_json, export_metadata_datacite]
```

#### Bulk Visibility Changes (PROHIBITED)

```python
# NO bulk visibility change actions
# Rationale documented in class docstring:
#
# Bulk visibility changes are too dangerous. Portal administrators
# could accidentally expose private datasets to the public. Data
# protection is a constitutional requirement in FairDM. Visibility
# changes must be made individually with explicit confirmation.
#
# Examples of PROHIBITED actions:
# - make_public()
# - make_private()
# - make_internal()
# - bulk_change_visibility()
```

---

## Testing Contracts

### Search Tests

```python
def test_admin_search_by_name(admin_client):
    """Admin search finds datasets by name."""
    DatasetFactory(name="Rock Collection")
    DatasetFactory(name="Water Samples")

    url = reverse('admin:dataset_dataset_changelist')
    response = admin_client.get(url, {'q': 'rock'})

    assert response.status_code == 200
    assert b'Rock Collection' in response.content
    assert b'Water Samples' not in response.content

def test_admin_search_by_uuid(admin_client):
    """Admin search finds datasets by UUID."""
    dataset = DatasetFactory(uuid="d123abc")
    DatasetFactory()  # Other dataset

    url = reverse('admin:dataset_dataset_changelist')
    response = admin_client.get(url, {'q': '123abc'})

    assert response.status_code == 200
    assert bytes(dataset.name, 'utf-8') in response.content
```

### List Display Tests

```python
def test_admin_list_display_shows_has_data(admin_client):
    """Admin list displays has_data indicator."""
    empty_dataset = DatasetFactory()
    dataset_with_data = DatasetFactory()
    SampleFactory(dataset=dataset_with_data)

    url = reverse('admin:dataset_dataset_changelist')
    response = admin_client.get(url)

    # Check for visual indicator (icon, boolean, etc.)
    assert response.status_code == 200
```

### Filter Tests

```python
def test_admin_filter_by_project(admin_client):
    """Admin filters datasets by project."""
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    DatasetFactory(project=project1, count=3)
    DatasetFactory(project=project2, count=2)

    url = reverse('admin:dataset_dataset_changelist')
    response = admin_client.get(url, {'project__id__exact': project1.id})

    assert response.status_code == 200
    # Assert only project1 datasets appear
```

### Inline Tests

```python
def test_dynamic_inline_limits_match_vocabulary(admin_client):
    """Inline form limits match vocabulary size."""
    dataset = DatasetFactory()
    url = reverse('admin:dataset_dataset_change', args=[dataset.pk])
    response = admin_client.get(url)

    # Check formset max_num matches vocabulary
    description_types_count = len(Dataset.DESCRIPTION_TYPES)
    date_types_count = len(Dataset.DATE_TYPES)

    # Assert formset configuration
    assert response.status_code == 200
```

### Bulk Action Tests

```python
def test_bulk_metadata_export_json(admin_client):
    """Bulk metadata export action generates JSON."""
    DatasetFactory.create_batch(5)

    url = reverse('admin:dataset_dataset_changelist')
    data = {
        'action': 'export_metadata_json',
        '_selected_action': Dataset.objects.values_list('pk', flat=True),
    }
    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    assert 'datasets.json' in response['Content-Disposition']

def test_no_bulk_visibility_change_actions_exist(admin_client):
    """Admin has NO bulk visibility change actions."""
    dataset_admin = admin.site._registry[Dataset]

    action_names = [action.__name__ for action in dataset_admin.actions]

    prohibited = [
        'make_public',
        'make_private',
        'make_internal',
        'bulk_change_visibility',
        'change_visibility',
    ]

    for prohibited_action in prohibited:
        assert prohibited_action not in action_names
```

### License Warning Tests

```python
def test_license_change_warning_when_doi_exists(admin_client):
    """Changing license with DOI shows warning."""
    dataset = DatasetFactory()
    DatasetIdentifierFactory(
        related=dataset,
        identifier_type='DOI',
        identifier='10.1234/test'
    )

    url = reverse('admin:dataset_dataset_change', args=[dataset.pk])
    new_license = LicenseFactory()
    response = admin_client.post(url, {
        'name': dataset.name,
        'license': new_license.pk,
        # ... other fields
    }, follow=True)

    messages = list(response.context['messages'])
    assert any('DOI' in str(m) for m in messages)
    assert any('license' in str(m).lower() for m in messages)
```

### Autocomplete Tests

```python
def test_autocomplete_on_project_field(admin_client):
    """Project field uses autocomplete."""
    dataset = DatasetFactory()
    url = reverse('admin:dataset_dataset_change', args=[dataset.pk])
    response = admin_client.get(url)

    # Check for autocomplete widget markup
    assert response.status_code == 200
    # Assert autocomplete widget present in HTML
```

---

## Usage Examples

### Customizing in Portal

```python
# Portal-specific admin customization
from fairdm.core.dataset.admin import DatasetAdmin as BaseDatasetAdmin

@admin.register(Dataset)
class CustomDatasetAdmin(BaseDatasetAdmin):
    """Portal-specific customizations."""

    # Add custom list display
    list_display = BaseDatasetAdmin.list_display + ['custom_field']

    # Add custom action
    actions = BaseDatasetAdmin.actions + [custom_export_action]
```

### Adding Custom Inline

```python
class CustomMetadataInline(admin.TabularInline):
    model = CustomMetadata
    extra = 1

class CustomDatasetAdmin(BaseDatasetAdmin):
    inlines = BaseDatasetAdmin.inlines + [CustomMetadataInline]
```

---

## Migration Path

### Phase 1: Basic Configuration (Non-Breaking)

```python
# Add search, filters, list_display
search_fields = ['name', 'uuid']
list_filter = ['project', 'license', 'visibility']
list_display = ['name', 'added', 'modified']
```

### Phase 2: Add Inlines (Feature Addition)

```python
# Add inline editors
inlines = [DatasetDescriptionInline, DatasetDateInline]
```

### Phase 3: Dynamic Limits & Actions (Feature Addition)

```python
# Implement get_formset() for dynamic limits
# Add bulk export actions
# Add license change warnings in save_model()
```

**Impact**: All changes are backwards compatible. Existing admin functionality preserved while adding new features.
