# How to add a record field to a form

This guide adds a searchable field that chooses a project or a dataset to a form of your own. The
person typing sees the records they may reach, and the form refuses any other. For every setting,
see [Record fields](record-fields.md).

## Before you start

- Your form is built in a view that has the request, or you pass it to the form yourself.
- The portal has `django_tomselect` in `INSTALLED_APPS` and its middleware, which FairDM's own
  settings already add.

## Steps

1. Import the field for the kind of record you want to choose.

   ```python
   from fairdm.contrib.autocomplete.fields import DatasetChoiceField
   ```

2. Declare it on the form and say what the person needs to be able to do with the record. A
   record that your form places something inside needs `scope="edit"`.

   ```python
   from django import forms

   from myapp.models import RockSample


   class RockSampleForm(forms.ModelForm):
       dataset = DatasetChoiceField(scope="edit")

       class Meta:
           model = RockSample
           fields = ["name", "dataset"]
   ```

3. Build the form inside a request.

   ```python
   form = RockSampleForm(request.POST or None)
   ```

   The field finds the person through the request the form is built in. A form that has a
   `request` attribute, as FairDM's own record forms do, uses that request instead.

4. Save the form. The sample belongs to the dataset that was chosen, and a dataset the person may
   not edit is refused with the field's `invalid_choice` error.

To choose several records, use the multiple field. It offers public records by default, which
suits a filter, so pass `scope="edit"` when the form changes the records it chooses.

```python
from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField


class ProjectPickerForm(forms.Form):
    projects = ProjectMultipleChoiceField(scope="view")
```

## Check that it works

Open the page signed in as someone who can edit one private dataset, type part of the dataset's
name, and the dataset is offered with its project beneath it.
