# Form and filter mixins

FairDM ships a form mixin and a filter set for each of the two record kinds a portal adds types of: samples and measurements. A portal's own form or filter set for a type inherits from them, and the registry builds the form and filter set of a type that supplies neither on the same classes (see [ADR 0006](../../adr/0006-generated-components-carry-the-framework-mixins.md)). This page lists what each provides. For the tasks, see [How to customise a sample form](../how-to/customise-a-sample-form.md), [How to add a filter to a sample type](../how-to/add-a-filter-to-a-sample-type.md) and [How to use a sample form in a view](../how-to/use-a-sample-form-in-a-view.md).

## Form mixins

A form mixin is a plain class combined with `forms.ModelForm` in the form of a concrete type. It is not a `ModelForm` itself. In the examples on this page, `CoreSample` stands for a sample type of your portal.

```python
from django import forms

from fairdm.core.sample.forms import SampleFormMixin


class CoreSampleForm(SampleFormMixin, forms.ModelForm):
    class Meta:
        model = CoreSample
        fields = ["name", "dataset", "location", "depth_m"]
```

### `SampleFormMixin`

Module: `fairdm.core.sample.forms`. Bases: `LocationFormMixin` and `ManagerOnlyFieldsMixin`.

| Argument | Type | Default | What it does | What it accepts |
|---|---|---|---|---|
| `request` | `HttpRequest` or `None` | `None` | Names the person the form is built for, and is kept as `self.request`. | The current request. It is removed from the arguments before `ModelForm` sees them. |

| Provides | When |
|---|---|
| Replaces `dataset` with a `DatasetChoiceField` at `edit` scope, keeping the label, `required` and help text | `dataset` is among the form's fields |
| Limits the dataset choices to the datasets the request's user holds at least the edit level on | The request has an authenticated user |
| Offers and accepts no dataset, and logs a warning | No request, or no authenticated user on it |
| Leaves `dataset` out for someone who cannot manage the sample | The form edits a saved sample |
| Sets the `status` widget to a `Select` and its initial value to `"unknown"` | `status` is among the form's fields |
| Replaces `location` with a `LocationField` and removes `location_elevation` and `location_uncertainty` | `location` is among the form's fields |
| Sets `helper` to a crispy-forms `FormHelper` with `form_tag = False` | Always |

`manager_only_fields` is `("dataset",)`.

### `MeasurementFormMixin`

Module: `fairdm.core.measurement.forms`. Bases: `LocationFormMixin` and `ManagerOnlyFieldsMixin`. It takes `request` as `SampleFormMixin` does.

| Provides | When |
|---|---|
| Replaces `dataset` with a `DatasetChoiceField` at `edit` scope, limited to the datasets the request's user holds at least the edit level on | `dataset` is among the form's fields |
| Leaves `dataset` out for someone who cannot manage the measurement | The form edits a saved measurement |
| Replaces `sample` with a `SampleChoiceField(prefer="dataset")`, which lists the chosen dataset's samples first and accepts any sample the person may view | `sample` is among the form's fields |
| Replaces `location` with a `LocationField`, and sets its help text to say that it is for a measurement made somewhere other than where its sample was taken | `location` is among the form's fields |
| Sets `helper` to a crispy-forms `FormHelper` with `form_tag = False` | Always |

`manager_only_fields` is `("dataset",)`.

### `ManagerOnlyFieldsMixin`

Module: `fairdm.core.forms`. It leaves the fields that decide who gets into a record out of the form of anyone who cannot manage it.

| Name | Type | Default | What it does |
|---|---|---|---|
| `manager_only_fields` | `tuple[str, ...]` | `()` | The names of the fields to leave out |
| `withhold_manager_only_fields(request)` | method | — | Removes those fields unless the form is for a new record or the request's user can manage the record |

### `LocationFormMixin`

Module: `fairdm.utils.location.forms`. It gives a form the location input. See [Location fields](location-fields.md).

## Filter sets

A filter set mixin is a `django_filters.FilterSet` subclass, because django-filter collects declared filters only from a class body or from a base that carries them. Its `Meta` names no `model`, so it can stand as a base for any concrete type. A subclass names its own `model` and must extend the mixin's `Meta`, or it loses the mixin's `fields` list.

```python
import django_filters

from fairdm.core.sample.filters import SampleFilterMixin


class CoreSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    class Meta(SampleFilterMixin.Meta):
        model = CoreSample
        fields = [*SampleFilterMixin.Meta.fields, "lithology"]
```

### `SampleFilterMixin`

Module: `fairdm.core.sample.filters`.

| Filter | Type | What it does |
|---|---|---|
| `image` | `BooleanFilter`, labelled "Has image" | Keeps the samples that do, or do not, carry an image |
| `status`, `dataset`, `polymorphic_ctype` | Generated by django-filter from `Meta.fields` | Filter by custody status, dataset and sample type, once the subclass's `Meta` names a model |

`Meta.fields` is `["status", "dataset", "polymorphic_ctype"]`.

### `SampleFilter`

Module: `fairdm.core.sample.filters`. The filter set for `Sample` itself, built on `SampleFilterMixin`.

| Filter | Type | What it does |
|---|---|---|
| `status` | `ChoiceFilter` over the sample status vocabulary | Filters by custody status |
| `dataset` | `RecordMultipleFilter` at `public` scope | Keeps the samples of any chosen dataset |
| `polymorphic_ctype` | `ModelChoiceFilter` | Filters by sample type |
| `q` | `SearchFilter` over `name`, `local_id` and `uuid` | Searches by any word of the text |
| `description` | `CharFilter` on the description text, contains | Searches the descriptions |
| `date_after`, `date_before` | `PartialDateFilter` on the dates' values | Keeps the samples with a date on or after, or on or before, a year, a year and month, or a day |

### `MeasurementFilterMixin`

Module: `fairdm.core.measurement.filters`. It declares every filter below, and its `Meta.fields` is `["dataset", "sample", "polymorphic_ctype"]`.

| Filter | Type | What it does |
|---|---|---|
| `dataset` | `RecordMultipleFilter` at `public` scope | Keeps the measurements of any chosen dataset |
| `sample` | `RecordMultipleFilter` at `public` scope | Keeps the measurements of any chosen sample |
| `polymorphic_ctype` | `ModelChoiceFilter`, labelled "Measurement Type" | Offers the registered measurement types |
| `q` | `SearchFilter` over `name` and `uuid` | Searches by any word of the text |
| `description` | `CharFilter` on the description text, contains | Searches the descriptions |
| `date_after`, `date_before` | `PartialDateFilter` on the dates' values | Keeps the measurements with a date on or after, or on or before, a year, a year and month, or a day |

### `MeasurementFilter`

Module: `fairdm.core.measurement.filters`. The filter set for `Measurement` itself. Every filter comes from `MeasurementFilterMixin`, and `Meta.fields` adds `date_after` and `date_before`.

### `PartialDateFilter`

Module: `fairdm.core.measurement.filters`. A `CharFilter` whose form field, `PartialDateFilterField`, accepts `YYYY`, `YYYY-MM` or `YYYY-MM-DD` and refuses anything else as a form error.

### Dataset filters

A `RecordMultipleFilter` at `public` scope offers the same public datasets to a visitor and to a signed-in researcher. A filter set that uses one must be built with the request, as `CoreSampleFilter(request.GET, queryset=..., request=request)`. A filter set built without a request offers and accepts nothing. See [Record fields](record-fields.md).

## Generated components

The registry builds a form for a sample or measurement type on a class made from the matching form mixin and `ModelForm`, and a filter set on the matching filter set mixin. For a type that supplies neither, these are the forms and filter sets the portal gets. See [Model configuration](model-configuration.md) and [The registry](registry.md).
