# How to write a custom form or filter for a measurement type

The registry generates a form and a filter set for each measurement type. You write your own when the form needs validation across fields, or the filter set needs a filter the generator cannot make.

## Before you start

You need a registered measurement type. This guide uses `GrainSizeMeasurement` from [How to add a measurement type](add-a-measurement-type.md).

## Steps

1. Write the form on `MeasurementFormMixin`. Put the mixin before `forms.ModelForm`.

   ```python
   # sediments/forms.py
   from django import forms

   from fairdm.core.measurement.forms import MeasurementFormMixin

   from .models import GrainSizeMeasurement


   class GrainSizeMeasurementForm(MeasurementFormMixin, forms.ModelForm):
       class Meta:
           model = GrainSizeMeasurement
           fields = ["name", "sample", "dataset", "method", "value", "uncertainty"]

       def clean(self):
           cleaned_data = super().clean()
           value = cleaned_data.get("value")
           uncertainty = cleaned_data.get("uncertainty")
           if value is not None and uncertainty is not None and uncertainty > value:
               self.add_error(
                   "uncertainty",
                   "The uncertainty cannot be larger than the value.",
               )
           return cleaned_data
   ```

   The mixin turns `dataset` into a search box that offers the datasets the person may edit, and `sample` into a search box that lists the samples of the chosen dataset first. See [Record fields](../reference/record-fields.md). It also leaves out the form tag, so the page supplies it. Views pass the request as the `request` argument. The full list is on [Form and filter mixins](../reference/form-and-filter-mixins.md).

2. Write the filter set on `MeasurementFilterMixin`. Extend its `Meta`, so the filters it provides stay.

   ```python
   # sediments/filters.py
   import django_filters

   from fairdm.core.measurement.filters import MeasurementFilterMixin

   from .models import GrainSizeMeasurement


   class GrainSizeMeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
       method = django_filters.CharFilter(
           lookup_expr="iexact",
           label="Method",
       )

       class Meta(MeasurementFilterMixin.Meta):
           model = GrainSizeMeasurement
           fields = [*MeasurementFilterMixin.Meta.fields, "method"]
   ```

   The mixin provides filters for dataset, sample, measurement type, a search box over name and portal ID, description text and a date range. A date filter accepts a year, a year and month, or a full date, and reports anything else as a form error.

3. Name the classes in the type's configuration. Set the matching field list to `None`, because `BaseMeasurementConfiguration` declares one and the registry refuses a field list and a class for the same component.

   ```python
   # sediments/config.py
   from .filters import GrainSizeMeasurementFilter
   from .forms import GrainSizeMeasurementForm


   @register
   class GrainSizeMeasurementConfig(BaseMeasurementConfiguration):
       model = GrainSizeMeasurement
       fields = ["name", "sample", "dataset", "method", "value", "uncertainty"]
       form_fields = None
       form_class = GrainSizeMeasurementForm
       filterset_fields = None
       filterset_class = GrainSizeMeasurementFilter
   ```

   Each class also takes its dotted path as a string. A class must subclass `ModelForm` or `FilterSet`.

## The result

The type's form and filter set are your classes. The generated table, serializer and administration page are unchanged. If you leave `form_fields = None` out, the portal refuses to start and the error names the form component.

To write only one of the two, leave the other pair out of the configuration. For other changes to the generated classes, see [How to customise a generated component](customise-a-generated-component.md).
