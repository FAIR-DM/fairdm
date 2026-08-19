# Sample Form and Filter Mixins

This guide explains how to use and customize the form and filter mixins provided by FairDM for Sample models.

## Overview

FairDM provides two reusable mixins — `SampleFormMixin` and `SampleFilterMixin` — that configure
common Sample behaviour so that a portal's own form and filter set for a specimen type do not have
to restate it: widget configuration, dataset-queryset filtering by permission, and the filters a
reader expects. The registry's own auto-generated form and filter set for a specimen type that
supplies neither are built on these same two mixins, so what you get by inheriting them is exactly
what registration gives you for free.

```{note}
These are the extension point a portal developer touches. `SampleForm` and `SampleFilter` in
`fairdm.core.sample` are a reference implementation with no callers outside their own tests —
`fairdm_demo`'s `RockSampleForm` and `RockSampleFilter`, shown throughout this page, inherit the
mixins directly, and that is the pattern to copy.
```

## Sample Form Mixin

### SampleFormMixin

`SampleFormMixin` provides standard form configuration for Sample creation and editing. It is a
plain mixin, combined with `forms.ModelForm` in your own class — not a `ModelForm` itself.

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

**Dataset filtering by permission**: `SampleFormMixin.__init__` takes a `request` keyword
argument, not a `user`. When it is given a request carrying an authenticated user, the `dataset`
field's queryset narrows to the datasets that user holds `dataset.change_dataset` on. Given no
request, or a request with no authenticated user, the queryset is `Dataset.objects.none()` — a
form that has authorised nobody proposes no dataset, rather than guessing:

```python
# In a view
form = RockSampleForm(request=request, data=request.POST)
```

**Optimized widget settings**: the mixin sets a Select2 widget with an "add another" link for
`dataset`, a plain `Select` for `status`, and a Select2 widget for `location`, whenever those
field names are present on the form. Add your own widgets for your own fields the normal Django
way:

```python
# In your form
class Meta:
    model = RockSample
    fields = ['name', 'dataset', 'collection_date']
    widgets = {
        'collection_date': forms.DateInput(attrs={'type': 'date'}),
    }
```

**Status field default**: if `status` is one of the form's fields, its initial value is set to
`"unknown"` — matching `Sample.status`'s own model default. The mixin does not assert where a
specimen physically is on the strength of nobody having chosen.

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

`SampleFormMixin.__init__` already builds a crispy-forms `FormHelper` with `form_tag = False`.
Set your own `self.helper.layout` after calling `super().__init__()` to control field order:

```python
from crispy_forms.layout import Layout, Fieldset, Row, Column

class RockSampleForm(SampleFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
class WaterSampleForm(SampleFormMixin, forms.ModelForm):
    class Meta:
        model = WaterSample
        fields = ['name', 'dataset', 'water_source', 'ph_level']
        widgets = {
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
        """Pass the request so the mixin can filter dataset choices by permission."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
```

#### Update View

```python
class RockSampleUpdateView(LoginRequiredMixin, UpdateView):
    model = RockSample
    form_class = RockSampleForm
    template_name = 'samples/rock_sample_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
```

## Sample Filter Mixin

### SampleFilterMixin

`SampleFilterMixin` is a `django_filters.FilterSet` subclass, not a plain mixin — that matters,
because django-filter's metaclass only collects declared filters from a class body or from a base
that carries them, and a plain Python class never does. Its `Meta` deliberately has no `model`:
that is what lets it exist as an abstract base with no concrete model to generate implicit filters
from.

#### Basic Filter Usage

The mixin declares one filter (`image`, a `BooleanFilter`) and one `Meta.fields` list
(`["status", "dataset", "polymorphic_ctype"]`). A subclass with its own `model`-bearing `Meta`
**must extend `SampleFilterMixin.Meta`**, or it loses that inherited field list — the declared
`image` filter survives regardless, since declared filters are collected independently of `Meta`:

```python
from fairdm.core.sample.filters import SampleFilterMixin
import django_filters
from myapp.models import RockSample

class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    rock_type = django_filters.ChoiceFilter(
        choices=[
            ('igneous', 'Igneous'),
            ('sedimentary', 'Sedimentary'),
            ('metamorphic', 'Metamorphic'),
        ]
    )

    class Meta(SampleFilterMixin.Meta):
        model = RockSample
        fields = SampleFilterMixin.Meta.fields + ['rock_type']
```

Writing a fresh `class Meta:` here instead — without extending `SampleFilterMixin.Meta` — would
still register the `rock_type` filter and the `image` filter, but the mixin's `status`, `dataset`
and `polymorphic_ctype` fields would silently disappear from the filter set.

#### Filter Features Provided

**Common Sample filters**: inheriting the mixin gets you:

- `image` — a boolean filter for whether the sample has an image attached (declared filter)
- `status`, `dataset`, `polymorphic_ctype` — implicit filters generated from `Meta.fields`, once
  your own `Meta` extends `SampleFilterMixin.Meta`

**Dataset queryset widening**: `SampleFilterMixin.__init__` runs on every subclass through the
method resolution order and sets the `dataset` filter's queryset to `Dataset.all_objects.all()`
whenever `dataset` is one of the filter set's fields — `Dataset`'s own default manager is
privacy-first, so without this a filter set would offer no private dataset to filter by, which is
every dataset until one is published.

### Custom Filters

#### Range Filters

```python
class WaterSampleFilter(SampleFilterMixin, django_filters.FilterSet):
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

    class Meta(SampleFilterMixin.Meta):
        model = WaterSample
        fields = SampleFilterMixin.Meta.fields + ['ph_level']
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

    class Meta(SampleFilterMixin.Meta):
        model = RockSample
        fields = SampleFilterMixin.Meta.fields + ['rock_type', 'collection_date']
```

#### Vocabulary/Concept Filters

```python
from research_vocabs.models import Concept

class SoilSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    texture = django_filters.ModelMultipleChoiceFilter(
        queryset=Concept.objects.filter(vocabulary__name="soil-texture"),
        label='Texture Classes',
        widget=forms.CheckboxSelectMultiple
    )

    class Meta(SampleFilterMixin.Meta):
        model = SoilSample
        fields = SampleFilterMixin.Meta.fields + ['texture']
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

    class Meta(SampleFilterMixin.Meta):
        model = RockSample
        fields = SampleFilterMixin.Meta.fields + ['rock_type']
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

If you don't need custom forms or filters, the registry can auto-generate them — and what it
generates for a specimen type that supplies neither carries the mixins' behaviour, not the
framework's plain defaults:

```python
from fairdm.core.sample.config import BaseSampleConfiguration
from fairdm.registry import register

@register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ['name', 'local_id', 'rock_type', 'collection_date', 'weight_grams']
```

This automatically generates a `ModelForm` built on `SampleFormMixin` and a `FilterSet` built on
`SampleFilterMixin`, with the field list above, plus appropriate widgets.

## Testing Forms and Filters

### Testing Forms

```python
import pytest
from datetime import date

@pytest.mark.django_db
def test_rock_sample_form_valid_data(rf, user, dataset):
    """Test form with valid data. `rf` is pytest-django's RequestFactory fixture."""
    from guardian.shortcuts import assign_perm
    assign_perm("dataset.change_dataset", user, dataset)

    request = rf.post("/")
    request.user = user

    form = RockSampleForm(
        request=request,
        data={
            'name': 'RS-001',
            'dataset': dataset.pk,
            'rock_type': 'igneous',
            'collection_date': date.today(),
            'weight_grams': 125.5,
        },
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
    from myapp.factories import RockSampleFactory

    RockSampleFactory(name='Igneous', dataset=dataset, rock_type='igneous')
    RockSampleFactory(name='Sedimentary', dataset=dataset, rock_type='sedimentary')

    filterset = RockSampleFilter(
        data={'rock_type': 'igneous'},
        queryset=RockSample.objects.all()
    )

    assert filterset.qs.count() == 1
    assert filterset.qs.first().rock_type == 'igneous'
```

## Best Practices

### Form Design

1. **Always pass `request` to forms**: it is what `SampleFormMixin` uses for dataset queryset filtering — a form built with no request offers no dataset at all
2. **Use crispy-forms for layout**: Better than manual HTML
3. **Validate early**: Use field-level validators when possible
4. **Provide helpful error messages**: Clear, actionable feedback

### Filter Design

1. **Extend `SampleFilterMixin.Meta`, always**: `class Meta(SampleFilterMixin.Meta):` plus `fields = SampleFilterMixin.Meta.fields + [...]` — a fresh `Meta` silently drops the mixin's fields
2. **Start simple**: Add filters as needed, don't overload the UI
3. **Use appropriate filter types**: Range filters for numbers, choice filters for enums
4. **Consider performance**: Add database indexes for frequently filtered fields
5. **Test filter combinations**: Ensure filters work together correctly

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
        form = RockSampleForm(request=request, data=request.POST)
        formset = SampleDescriptionFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            sample = form.save()
            formset.instance = sample
            formset.save()
            return redirect(sample.get_absolute_url())
    else:
        form = RockSampleForm(request=request)
        formset = SampleDescriptionFormSet()

    return render(request, 'sample_form.html', {
        'form': form,
        'formset': formset,
    })
```

## See Also

- [Custom Samples](../models/custom-samples.md) - Sample model patterns
- [Model Configuration](../model_configuration.md) - Registry configuration
- [Filtering by Vocabulary](../filtering-by-vocabulary.md) - Concept filters
