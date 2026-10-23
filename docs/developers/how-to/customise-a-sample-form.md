# How to customise a sample form

This guide writes a form of your own for a sample type, with extra validation, a field order, a grouped layout and a custom widget. You would do this when the form the registry generates for the type is not enough.

## Before you start

You need a registered sample type. This guide uses `CoreSample`, a sample type of your portal with two fields of its own. To add one, see [How to add a sample type](add-a-sample-type.md).

```python
from fairdm.core.sample.models import Sample
from fairdm.db import models


class CoreSample(Sample):
    depth_m = models.FloatField("Depth (m)", null=True, blank=True)
    lithology = models.CharField("Lithology", max_length=100, blank=True)
```

## Steps

1. Write a form that combines `SampleFormMixin` with `forms.ModelForm`. The mixin gives the form its dataset field, its location input and its crispy-forms helper. See [Form and filter mixins](../reference/form-and-filter-mixins.md).

   ```python
   from django import forms

   from fairdm.core.sample.forms import SampleFormMixin
   from myportal.models import CoreSample


   class CoreSampleForm(SampleFormMixin, forms.ModelForm):
       class Meta:
           model = CoreSample
           fields = ["name", "dataset", "local_id", "status", "location", "depth_m", "lithology"]
   ```

   The form lists `dataset`, `status` and `location` in `Meta.fields` because the mixin configures a field only when the form has it.

2. Set the order of the fields with `Meta.fields`. The form draws them in that order.

3. Add validation for one field with a `clean_<field>` method, and across fields with `clean()`.

   ```python
   from django.core.exceptions import ValidationError


   class CoreSampleForm(SampleFormMixin, forms.ModelForm):
       class Meta:
           model = CoreSample
           fields = ["name", "dataset", "local_id", "status", "location", "depth_m", "lithology"]

       def clean_depth_m(self):
           depth = self.cleaned_data.get("depth_m")
           if depth is not None and depth < 0:
               raise ValidationError("Depth cannot be negative.")
           return depth

       def clean(self):
           cleaned_data = super().clean()
           if cleaned_data.get("depth_m") and not cleaned_data.get("lithology"):
               self.add_error("lithology", "Say what the core is made of.")
           return cleaned_data
   ```

4. Change a widget in `Meta.widgets`.

   ```python
   class Meta:
       model = CoreSample
       fields = ["name", "dataset", "local_id", "status", "location", "depth_m", "lithology"]
       widgets = {
           "depth_m": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
       }
   ```

5. To group the fields, set the helper's layout after the mixin has built it. List every field you want drawn, because a crispy layout draws only the fields it names. Leave the first group without a legend and give legends to the groups after it.

   ```python
   from crispy_forms.layout import Fieldset, Layout


   class CoreSampleForm(SampleFormMixin, forms.ModelForm):
       class Meta:
           model = CoreSample
           fields = ["name", "dataset", "local_id", "status", "location", "depth_m", "lithology"]

       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           # The mixin leaves out `dataset` for someone who cannot manage a saved sample.
           first = [n for n in ("name", "dataset", "local_id") if n in self.fields]
           self.helper.layout = Layout(
               *first,
               Fieldset("Core details", "depth_m", "lithology"),
               Fieldset("Where and in what state", "location", "status"),
           )
   ```

   The mixin sets `form_tag = False` on the helper, so the page supplies the `<form>` tag.

6. Tell the registry to use the form, so the type's edit page uses it. Put the configuration in your app's `config.py`.

   ```python
   import fairdm
   from fairdm.core.sample.config import BaseSampleConfiguration
   from myportal.models import CoreSample


   @fairdm.register
   class CoreSampleConfig(BaseSampleConfiguration):
       model = CoreSample
       form_class = "myportal.forms.CoreSampleForm"
   ```

   A configuration declares either `form_fields` or `form_class`, never both. To use the form in a view of your own instead, see [How to use a sample form in a view](use-a-sample-form-in-a-view.md).

## The result

The type's form keeps everything the mixin provides: a dataset field that offers only the datasets the person may edit, the location input, and a status that starts at "unknown". It also carries your validation, order, widget and layout. Always pass `request` when you build the form yourself, because the dataset field needs it to know who is choosing. A form built with no request offers no dataset.
