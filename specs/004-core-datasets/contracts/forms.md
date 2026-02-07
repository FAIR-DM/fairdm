# Contract: Dataset Forms

**Feature**: 004-core-datasets
**Purpose**: Define the public interface for DatasetForm with user context and internationalization
**Input**: [data-model.md](../data-model.md), [plan.md](../plan.md)

## DatasetForm Interface

### Class Definition

```python
class DatasetForm(forms.ModelForm):
    """
    ModelForm for Dataset creation and editing with user context awareness.

    Features:
        - Permission-based queryset filtering via request parameter
        - CC BY 4.0 license default
        - Internationalized help text (gettext_lazy)
        - Autocomplete widgets on all ForeignKey/ManyToMany fields
        - DOI entry field that creates DatasetIdentifier

    Request Context:
        Pass optional `request` parameter to __init__() to enable:
        - Project queryset filtering based on user permissions
        - Anonymous user handling

    Usage:
        # Authenticated user
        form = DatasetForm(request=request)

        # Anonymous user
        form = DatasetForm(request=None)

        # Edit existing dataset
        form = DatasetForm(instance=dataset, request=request)
    """
```

### Constructor

```python
def __init__(self, *args, request=None, **kwargs):
    """
    Initialize form with optional request context for permission filtering.

    Args:
        request: Optional HttpRequest object for user context
        *args: Standard form positional arguments
        **kwargs: Standard form keyword arguments (instance, initial, etc.)

    Behavior:
        - If request provided and user authenticated:
          Filters project queryset to user.projects.all()
        - If request is None or user anonymous:
          Shows only public projects or empty queryset
        - Sets license field default to CC BY 4.0
    """
    super().__init__(*args, **kwargs)
    self.request = request

    # Filter project queryset based on user permissions
    if request and request.user.is_authenticated:
        self.fields['project'].queryset = request.user.projects.all()
    else:
        # Anonymous users: show only public projects or no projects
        self.fields['project'].queryset = Project.objects.filter(
            visibility=Visibility.PUBLIC
        )

    # Set license default to CC BY 4.0
    if not self.instance.pk:  # New dataset only
        self.fields['license'].initial = License.objects.filter(
            name="CC BY 4.0"
        ).first()
```

### Meta Configuration

```python
class Meta:
    model = Dataset
    fields = [
        'name',
        'image',
        'project',
        'license',
        'doi',  # Custom field for DOI entry
        'visibility',
    ]
    widgets = {
        'project': Select2Widget(),  # Autocomplete for project selection
        'license': Select2Widget(),  # Autocomplete for license selection
        # DOI field widget defined separately
    }
    help_texts = {
        'name': _('Human-readable name for the dataset. Required.'),
        'image': _('Optional image for dataset visualization in cards and meta tags. Recommended aspect ratio: 16:9.'),
        'project': _('Select the project this dataset belongs to. Only projects you have access to are shown.'),
        'license': _('License governing dataset usage. Defaults to CC BY 4.0 (Creative Commons Attribution 4.0 International).'),
        'doi': _('Digital Object Identifier for published datasets. Format: 10.xxxxx/xxxxx'),
        'visibility': _('Access control level. PRIVATE (default) restricts access, PUBLIC makes dataset findable by all users.'),
    }
```

### Custom Fields

```python
doi = forms.CharField(
    required=False,
    max_length=255,
    help_text=_('Digital Object Identifier for published datasets. Format: 10.xxxxx/xxxxx'),
    widget=forms.TextInput(attrs={'placeholder': '10.1234/example.doi'}),
)
```

### Field Validation

```python
def clean_name(self):
    """Validate name is non-empty."""
    name = self.cleaned_data.get('name')
    if not name or not name.strip():
        raise forms.ValidationError(_('Dataset name cannot be empty.'))
    return name.strip()

def clean_doi(self):
    """Validate DOI format if provided."""
    doi = self.cleaned_data.get('doi')
    if doi:
        # Basic DOI format validation (10.xxxxx/xxxxx)
        if not doi.startswith('10.') or '/' not in doi:
            raise forms.ValidationError(_(
                'Invalid DOI format. Expected format: 10.xxxxx/xxxxx'
            ))
    return doi
```

### Save Method

```python
def save(self, commit=True):
    """
    Save dataset and create DOI identifier if provided.

    Args:
        commit: Whether to save to database immediately

    Returns:
        Dataset instance

    Behavior:
        - Saves dataset with form data
        - If DOI provided, creates DatasetIdentifier with identifier_type='DOI'
        - DOI creation only happens if commit=True
    """
    dataset = super().save(commit=commit)

    if commit and self.cleaned_data.get('doi'):
        # Create DOI identifier
        DatasetIdentifier.objects.get_or_create(
            related=dataset,
            identifier_type='DOI',
            defaults={'identifier': self.cleaned_data['doi']}
        )

    return dataset
```

---

## Internationalization Requirements

All help_text strings MUST use `gettext_lazy()` for internationalization:

```python
from django.utils.translation import gettext_lazy as _

class Meta:
    help_texts = {
        'name': _('Human-readable name...'),  # ✅ Correct
        'project': 'Select the project...',    # ❌ Wrong
    }
```

**Form-Specific Help Text**:
- Help text SHOULD be form-specific, not copied from model
- Model help_text describes the field's purpose
- Form help_text guides the user through data entry

---

## Widget Configuration

### Autocomplete Widgets

Apply Select2Widget or autocomplete to ALL ForeignKey/ManyToMany fields:

```python
widgets = {
    'project': Select2Widget(),
    'license': Select2Widget(),
    'related_literature': Select2MultipleWidget(),  # If exposed in form
}
```

### Add Another Functionality

Project field supports "add another" for inline creation:

```python
from django_addanother.widgets import AddAnotherWidgetWrapper

widgets = {
    'project': AddAnotherWidgetWrapper(
        Select2Widget(),
        reverse_lazy('admin:project_project_add')
    ),
}
```

---

## Testing Contracts

### Queryset Filtering Tests

```python
def test_authenticated_user_sees_own_projects(self):
    """Form filters project queryset to user's projects."""
    user = UserFactory()
    my_project = ProjectFactory()
    user.projects.add(my_project)
    other_project = ProjectFactory()

    request = RequestFactory().get('/')
    request.user = user
    form = DatasetForm(request=request)

    assert my_project in form.fields['project'].queryset
    assert other_project not in form.fields['project'].queryset

def test_anonymous_user_sees_public_projects(self):
    """Form shows only public projects to anonymous users."""
    public_project = ProjectFactory(visibility=Visibility.PUBLIC)
    private_project = ProjectFactory(visibility=Visibility.PRIVATE)

    request = RequestFactory().get('/')
    request.user = AnonymousUser()
    form = DatasetForm(request=request)

    assert public_project in form.fields['project'].queryset
    assert private_project not in form.fields['project'].queryset
```

### License Default Tests

```python
def test_license_defaults_to_cc_by_4(self):
    """New datasets default to CC BY 4.0 license."""
    form = DatasetForm()
    assert form.fields['license'].initial.name == "CC BY 4.0"

def test_existing_dataset_preserves_license(self):
    """Editing existing dataset preserves current license."""
    dataset = DatasetFactory(license=custom_license)
    form = DatasetForm(instance=dataset)
    assert form.instance.license == custom_license
```

### Internationalization Tests

```python
def test_help_text_uses_gettext_lazy(self):
    """All help_text strings use gettext_lazy for i18n."""
    form = DatasetForm()
    for field_name, field in form.fields.items():
        if field.help_text:
            # Check that help_text is a lazy translation proxy
            assert isinstance(field.help_text, Promise)
```

### DOI Field Tests

```python
def test_doi_creates_dataset_identifier(self):
    """Providing DOI creates DatasetIdentifier with type='DOI'."""
    form = DatasetForm(data={
        'name': 'Test Dataset',
        'doi': '10.1234/test',
        'visibility': Visibility.PUBLIC,
    })
    assert form.is_valid()
    dataset = form.save()

    doi_identifier = dataset.identifiers.filter(identifier_type='DOI').first()
    assert doi_identifier is not None
    assert doi_identifier.identifier == '10.1234/test'

def test_invalid_doi_format_raises_error(self):
    """Invalid DOI format raises validation error."""
    form = DatasetForm(data={
        'name': 'Test Dataset',
        'doi': 'invalid-doi',
    })
    assert not form.is_valid()
    assert 'doi' in form.errors
```

### Widget Tests

```python
def test_autocomplete_widgets_on_all_foreign_keys(self):
    """All ForeignKey and ManyToMany fields use autocomplete widgets."""
    form = DatasetForm()

    # Check project field
    assert isinstance(form.fields['project'].widget, Select2Widget)

    # Check license field
    assert isinstance(form.fields['license'].widget, Select2Widget)
```

---

## Base Form Pattern Consideration

**Research Task (T101)**: Consider moving request parameter pattern to base form class.

### Potential Base Class

```python
class RequestAwareForm(forms.ModelForm):
    """
    Base form with request context support for permission filtering.

    Subclasses can override filter_queryset_by_user() to customize filtering.
    """
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

        if request and hasattr(self, 'filter_querysets_by_user'):
            self.filter_querysets_by_user(request.user)

    def filter_querysets_by_user(self, user):
        """Override in subclasses to filter querysets."""
        pass
```

### Usage in DatasetForm

```python
class DatasetForm(RequestAwareForm):
    def filter_querysets_by_user(self, user):
        if user.is_authenticated:
            self.fields['project'].queryset = user.projects.all()
        else:
            self.fields['project'].queryset = Project.objects.filter(
                visibility=Visibility.PUBLIC
            )
```

**Decision**: Research if this pattern is applicable to other FairDM forms. If yes, implement base class. If no, keep pattern in DatasetForm only.

---

## Migration Path

### Phase 1: Add request Parameter (Non-Breaking)

```python
def __init__(self, *args, request=None, **kwargs):
    # request is optional, form works without it
```

### Phase 2: Add Internationalization (Non-Breaking)

```python
# Wrap help_texts in gettext_lazy()
help_texts = {
    'name': _('...'),
}
```

### Phase 3: Add DOI Field (Feature Addition)

```python
# Add custom DOI field and save() logic
doi = forms.CharField(...)

def save(self, commit=True):
    # Create DatasetIdentifier if DOI provided
```

**Impact**: All changes are backwards compatible. Existing code continues to work.
