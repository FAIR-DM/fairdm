# Sample Form and Filter Mixins

This guide explains how to use and customize the form and filter mixins provided by FairDM for Sample models.

## Overview

FairDM provides reusable mixins that configure forms and filters for Sample models with sensible defaults. These mixins handle common patterns like:

- Dataset queryset filtering based on user permissions
- Standard field ordering and widgets
- Common filter configurations
- Polymorphic type handling

## Sample Form Mixin

### SampleFormMixin

The `SampleFormMixin` provides standard form configuration for Sample creation and editing.

#### Basic Usage

```python
from fairdm.core.sample.forms import SampleFormMixin
from django import forms
from myapp.models import RockSample

class RockSampleForm(SampleFormMixin, forms.ModelForm):
    class Meta:
        model = RockSample
        fields = [
            'name',
            'local_id',
            'dataset',
            'location',
            'status',
            'rock_type',
            'collection_date',
            'weight_grams'
        ]
```

#### Features Provided

**Dataset Filtering**: Automatically filters the dataset queryset to only show datasets the user has permission to contribute to:

```python
def __init__(self, *args, user=None, **kwargs):
    super().__init__(*args, **kwargs)
    # Filters dataset queryset based on user permissions
    self.fields['dataset'].queryset = self.get_dataset_queryset(user)
```

**Optimized Widget Settings**: Provides sensible widget configurations:

```python
# In your form
class Meta:
    model = RockSample
    fields = ['name', 'dataset', 'collection_date']
    widgets = {
        'collection_date': forms.DateInput(attrs={'type': 'date'}),
        'dataset': autocomplete.ModelSelect2(url='dataset-autocomplete'),
    }
```

**Status Field Default**: Automatically sets status to 'available' if not provided.

### Customizing Forms

#### Adding Custom Validation

```python
from django.core.exceptions import ValidationError

class RockSampleForm(SampleFormMixin, forms.ModelForm):
    class Meta:
        model = RockSample
        fields = ['name', 'dataset', 'rock_type', 'weight_grams']

    def clean_weight_grams(self):
        """Validate weight is positive."""
        weight = self.cleaned_data.get('weight_grams')
        if weight is not None and weight <= 0:
            raise ValidationError("Weight must be positive")
        return weight

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        rock_type = cleaned_data.get('rock_type')
        weight = cleaned_data.get('weight_grams')

        if rock_type == 'pumice' and weight and weight > 50:
            raise ValidationError(
                "Pumice samples over 50g are unusual - please verify"
            )

        return cleaned_data
```

#### Custom Field Ordering

Use crispy-forms for layout control:

```python
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column

class RockSampleForm(SampleFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('name', css_class='col-md-6'),
                    Column('local_id', css_class='col-md-6'),
                ),
                'dataset',
            ),
            Fieldset(
                'Sample Details',
                Row(
                    Column('rock_type', css_class='col-md-6'),
                    Column('collection_date', css_class='col-md-6'),
                ),
                'weight_grams',
            ),
            Fieldset(
                'Location & Status',
                'location',
                'status',
            ),
        )

    class Meta:
        model = RockSample
        fields = [
            'name', 'local_id', 'dataset', 'rock_type',
            'collection_date', 'weight_grams', 'location', 'status'
        ]
```

#### Custom Widgets

```python
from dal import autocomplete

class WaterSampleForm(SampleFormMixin, forms.ModelForm):
    class Meta:
        model = WaterSample
        fields = ['name', 'dataset', 'water_source', 'ph_level']
        widgets = {
            'water_source': autocomplete.ListSelect2(
                url='water-source-autocomplete',
                attrs={
                    'data-placeholder': 'Select or type water source...',
                    'data-minimum-input-length': 1,
                }
            ),
            'ph_level': forms.NumberInput(attrs={
                'step': '0.1',
                'min': '0',
                'max': '14',
                'placeholder': 'pH (0-14)'
            }),
        }
```

### Using Forms in Views

#### Create View

```python
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

class RockSampleCreateView(LoginRequiredMixin, CreateView):
    model = RockSample
    form_class = RockSampleForm
    template_name = 'samples/rock_sample_form.html'

    def get_form_kwargs(self):
        """Pass user to form for dataset filtering."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Set creator before saving."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)
```

#### Update View

```python
class RockSampleUpdateView(LoginRequiredMixin, UpdateView):
    model = RockSample
    form_class = RockSampleForm
    template_name = 'samples/rock_sample_form.html'

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
```

## Sample Filter Mixin

### SampleFilterMixin

The `SampleFilterMixin` provides standard filter configuration for Sample list views.

#### Basic Usage

```python
from fairdm.core.sample.filters import SampleFilterMixin
import django_filters

class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    # Add custom filters
    rock_type = django_filters.ChoiceFilter(
        choices=[
            ('igneous', 'Igneous'),
            ('sedimentary', 'Sedimentary'),
            ('metamorphic', 'Metamorphic'),
        ]
    )

    weight_min = django_filters.NumberFilter(
        field_name='weight_grams',
        lookup_expr='gte',
        label='Min Weight (g)'
    )

    class Meta:
        model = RockSample
        fields = {
            'name': ['icontains'],
            'local_id': ['exact', 'icontains'],
            'dataset': ['exact'],
            'status': ['exact'],
            'rock_type': ['exact'],
        }
```

#### Features Provided

**Common Sample Filters**: The mixin provides filters for:

- Name (text search)
- Local ID (exact match and text search)
- Dataset (dropdown)
- Status (dropdown)
- Polymorphic type (for mixed querysets)

**Search Functionality**: Text search across name, local_id, and UUID:

```python
# Users can search by any of these
search = django_filters.CharFilter(method='search_samples')
```

**Date Range Filters**: Filter by creation/modification dates:

```python
created_after = django_filters.DateFilter(
    field_name='created',
    lookup_expr='gte'
)
```

### Custom Filters

#### Range Filters

```python
class WaterSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    # pH range
    ph_min = django_filters.NumberFilter(
        field_name='ph_level',
        lookup_expr='gte',
        label='Min pH'
    )
    ph_max = django_filters.NumberFilter(
        field_name='ph_level',
        lookup_expr='lte',
        label='Max pH'
    )

    # Temperature range
    temp_range = django_filters.NumericRangeFilter(
        field_name='temperature_celsius',
        label='Temperature Range (°C)'
    )

    class Meta:
        model = WaterSample
        fields = ['dataset', 'water_source', 'ph_level']
```

#### Date Range Filters

```python
class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    collection_date = django_filters.DateFromToRangeFilter(
        label='Collection Date Range',
        widget=django_filters.widgets.RangeWidget(
            attrs={'type': 'date'}
        )
    )

    class Meta:
        model = RockSample
        fields = ['dataset', 'rock_type', 'collection_date']
```

#### Vocabulary/Concept Filters

```python
class SoilSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    soil_type = django_filters.ModelChoiceFilter(
        queryset=Concept.objects.filter(vocabulary='soil_taxonomy'),
        label='Soil Type',
        empty_label='All Types'
    )

    texture = django_filters.ModelMultipleChoiceFilter(
        queryset=Concept.objects.filter(vocabulary='soil_texture'),
        label='Texture Classes',
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = SoilSample
        fields = ['dataset', 'soil_type', 'texture']
```

#### Custom Filter Methods

```python
class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    has_children = django_filters.BooleanFilter(
        method='filter_has_children',
        label='Has Child Samples'
    )

    def filter_has_children(self, queryset, name, value):
        """Filter for samples that have children."""
        from fairdm.core.sample.models import SampleRelation

        if value:
            # Get samples that are targets in child_of relationships
            parent_ids = SampleRelation.objects.filter(
                type='child_of'
            ).values_list('target_id', flat=True)
            return queryset.filter(id__in=parent_ids)
        return queryset

    class Meta:
        model = RockSample
        fields = ['dataset', 'rock_type']
```

### Using Filters in Views

#### ListView with Filters

```python
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin

class RockSampleListView(LoginRequiredMixin, FilterView):
    model = RockSample
    filterset_class = RockSampleFilter
    template_name = 'samples/rock_sample_list.html'
    context_object_name = 'samples'
    paginate_by = 50

    def get_queryset(self):
        """Optimize queryset with prefetching."""
        return RockSample.objects.with_related().with_metadata()
```

#### Template Usage

```django
{# templates/samples/rock_sample_list.html #}
{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block content %}
<h1>Rock Samples</h1>

{# Filter form #}
<div class="card mb-4">
  <div class="card-body">
    <form method="get">
      {{ filter.form|crispy }}
      <button type="submit" class="btn btn-primary">Filter</button>
      <a href="{{ request.path }}" class="btn btn-secondary">Clear</a>
    </form>
  </div>
</div>

{# Results #}
<div class="card">
  <div class="card-body">
    <p>Found {{ filter.qs.count }} samples</p>

    <table class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Rock Type</th>
          <th>Collection Date</th>
          <th>Weight</th>
          <th>Dataset</th>
        </tr>
      </thead>
      <tbody>
        {% for sample in samples %}
        <tr>
          <td><a href="{{ sample.get_absolute_url }}">{{ sample.name }}</a></td>
          <td>{{ sample.rock_type }}</td>
          <td>{{ sample.collection_date }}</td>
          <td>{{ sample.weight_grams }} g</td>
          <td>{{ sample.dataset.name }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    {# Pagination #}
    {% include "partials/pagination.html" %}
  </div>
</div>
{% endblock %}
```

## Registry Auto-Generation

If you don't need custom forms or filters, the registry can auto-generate them:

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    # Fields for auto-generated components
    fields = ['name', 'local_id', 'rock_type', 'collection_date', 'weight_grams']

    # Or specify different fields for each component
    form_fields = ['name', 'dataset', 'rock_type', 'collection_date', 'weight_grams']
    filterset_fields = ['dataset', 'rock_type', 'status']
```

This automatically generates:

- A ModelForm with the specified fields
- A FilterSet with the specified fields
- Appropriate widgets and validators

## Testing Forms and Filters

### Testing Forms

```python
import pytest
from datetime import date

@pytest.mark.django_db
def test_rock_sample_form_valid_data(user, dataset):
    """Test form with valid data."""
    form = RockSampleForm(
        data={
            'name': 'RS-001',
            'dataset': dataset.pk,
            'rock_type': 'igneous',
            'collection_date': date.today(),
            'weight_grams': 125.5,
        },
        user=user
    )

    assert form.is_valid()
    sample = form.save()
    assert sample.rock_type == 'igneous'

@pytest.mark.django_db
def test_rock_sample_form_validation():
    """Test form validation."""
    form = RockSampleForm(
        data={
            'name': '',  # Required field
            'rock_type': 'igneous',
        }
    )

    assert not form.is_valid()
    assert 'name' in form.errors
```

### Testing Filters

```python
@pytest.mark.django_db
def test_rock_sample_filter_by_type(dataset):
    """Test filtering by rock type."""
    # Create samples
    RockSample.objects.create(
        name='Igneous',
        dataset=dataset,
        rock_type='igneous',
        collection_date=date.today()
    )
    RockSample.objects.create(
        name='Sedimentary',
        dataset=dataset,
        rock_type='sedimentary',
        collection_date=date.today()
    )

    # Filter
    filterset = RockSampleFilter(
        data={'rock_type': 'igneous'},
        queryset=RockSample.objects.all()
    )

    assert filterset.qs.count() == 1
    assert filterset.qs.first().rock_type == 'igneous'

@pytest.mark.django_db
def test_rock_sample_filter_date_range(dataset):
    """Test filtering by date range."""
    from datetime import timedelta

    today = date.today()
    yesterday = today - timedelta(days=1)

    RockSample.objects.create(
        name='Recent',
        dataset=dataset,
        rock_type='igneous',
        collection_date=today
    )
    RockSample.objects.create(
        name='Older',
        dataset=dataset,
        rock_type='igneous',
        collection_date=yesterday
    )

    # Filter for today only
    filterset = RockSampleFilter(
        data={
            'collection_date_after': today,
            'collection_date_before': today,
        },
        queryset=RockSample.objects.all()
    )

    assert filterset.qs.count() == 1
    assert filterset.qs.first().name == 'Recent'
```

## Best Practices

### Form Design

1. **Always pass user to forms**: Required for dataset queryset filtering
2. **Use crispy-forms for layout**: Better than manual HTML
3. **Validate early**: Use field-level validators when possible
4. **Provide helpful error messages**: Clear, actionable feedback
5. **Use appropriate widgets**: Date pickers for dates, autocomplete for FKs

### Filter Design

1. **Start simple**: Add filters as needed, don't overload the UI
2. **Use appropriate filter types**: Range filters for numbers, choice filters for enums
3. **Consider performance**: Add database indexes for frequently filtered fields
4. **Test filter combinations**: Ensure filters work together correctly
5. **Provide clear labels**: Users should understand what each filter does

### Template Organization

1. **Reuse filter templates**: Create a shared filter sidebar component
2. **Make filtering obvious**: Clear "Filter" and "Clear" buttons
3. **Show active filters**: Display which filters are currently applied
4. **Provide feedback**: Show result counts, "no results" messages

## Common Patterns

### Inline Forms

For creating samples with related metadata in one form:

```python
from django.forms import inlineformset_factory
from fairdm.core.sample.models import SampleDescription

SampleDescriptionFormSet = inlineformset_factory(
    RockSample,
    SampleDescription,
    fields=['type', 'value'],
    extra=2,
    can_delete=True
)

# In your view
def sample_create_view(request):
    if request.method == 'POST':
        form = RockSampleForm(request.POST, user=request.user)
        formset = SampleDescriptionFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            sample = form.save()
            formset.instance = sample
            formset.save()
            return redirect(sample.get_absolute_url())
    else:
        form = RockSampleForm(user=request.user)
        formset = SampleDescriptionFormSet()

    return render(request, 'sample_form.html', {
        'form': form,
        'formset': formset,
    })
```

### Conditional Filters

Show/hide filters based on other selections:

```python
class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    rock_type = django_filters.ChoiceFilter(
        choices=[('igneous', 'Igneous'), ('sedimentary', 'Sedimentary')]
    )

    # Only relevant for igneous rocks
    igneous_subtype = django_filters.ChoiceFilter(
        choices=[('basalt', 'Basalt'), ('granite', 'Granite')],
        label='Igneous Subtype'
    )

    class Meta:
        model = RockSample
        fields = ['rock_type', 'igneous_subtype']

# Use JavaScript to show/hide igneous_subtype based on rock_type selection
```

## See Also

- [Custom Samples](../models/custom-samples.md) - Sample model patterns
- [Model Configuration](../model_configuration.md) - Registry configuration
- [Filtering by Vocabulary](../filtering-by-vocabulary.md) - Concept filters
