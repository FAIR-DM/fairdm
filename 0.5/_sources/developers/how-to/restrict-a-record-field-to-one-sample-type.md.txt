# How to restrict a record field to one sample type

This guide keeps a sample field to the samples of one registered type. You would do this on a form that must refer to, say, a core sample and never to a water sample.

## Before you start

You need a registered sample type. This guide uses `CoreSample`, a sample type of your portal. To add one, see [How to add a sample type](add-a-sample-type.md).

## Steps

1. Import the sample field and your sample model.

   ```python
   from fairdm.contrib.autocomplete.fields import SampleChoiceField
   from myportal.models import CoreSample
   ```

2. Pass the model as `type`.

   ```python
   from django import forms


   class CompareCoresForm(forms.Form):
       core_sample = SampleChoiceField(type=CoreSample)
   ```

3. Build the form inside a request, as in [How to add a record field to a form](add-a-record-field-to-a-form.md).

   ```python
   form = CompareCoresForm(request.POST or None)
   ```

## The result

The field offers core samples only, found by name, local ID or identifier. A sample of any other type is refused with `invalid_choice` when the form is saved, even if the browser sent its key.

`type` must be a subclass of the kind's model. A project or dataset field, or a model of another kind, raises `ValueError` when the field is created. The multiple field takes `type` in the same way.
