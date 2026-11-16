# How to add a record field to a form

This guide adds a searchable field that chooses a dataset to a form of your own. The person typing sees the datasets they may reach, and the form refuses any other. You would do this on a form that puts something inside a dataset, or links to one.

## Before you start

- The form is built in a request, in a view, or you pass the request to it yourself.
- For every argument of the field, see [Record fields](../reference/record-fields.md).

## Steps

1. Import the field for the kind of record you want to choose. FairDM has one for projects, datasets, samples, measurements, people and organizations.

   ```python
   from fairdm.contrib.autocomplete.fields import DatasetChoiceField
   ```

2. Declare it on the form and say what the person needs to be able to do with the record. A record that your form places something inside needs `scope="edit"`. A record the form only links to needs the default, `"view"`.

   ```python
   from django import forms

   from fairdm.contrib.autocomplete.fields import DatasetChoiceField


   class AddToDatasetForm(forms.Form):
       name = forms.CharField()
       dataset = DatasetChoiceField(scope="edit")
   ```

3. Build the form inside a request.

   ```python
   form = AddToDatasetForm(request.POST or None)
   ```

   The field finds the person through the request the form is built in. A form that has a `request` attribute, as FairDM's own record forms do, uses that request instead.

4. Use the cleaned value. It is a `Dataset`.

   ```python
   if form.is_valid():
       dataset = form.cleaned_data["dataset"]
   ```

## The result

On the page, the person types part of the dataset's name and is offered the datasets they may edit, with each dataset's project beneath its name. A dataset they may not edit is refused with the field's `invalid_choice` error, whatever the browser sent.

## Choose several records

Use the multiple field. It takes the same arguments and offers the same records as the single field.

```python
from django import forms

from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField


class ProjectPickerForm(forms.Form):
    projects = ProjectMultipleChoiceField()
```

## Offer one person's records

On a page that lists one person's records, give the field that person as `owner`. It offers their private records to them and public records to everyone else. `owner` cannot be given with `scope`. It is a value of the page being shown, so create the field when the page is built, in the form's `__init__` or in the filter set's.

```python
from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField

projects = ProjectMultipleChoiceField(owner=person)
```

## Related guides

- [How to restrict a record field to one sample type](restrict-a-record-field-to-one-sample-type.md)
- [How to narrow a record field by another field](narrow-a-record-field-by-another-field.md)
- [How to filter a list by a record](filter-a-list-by-a-record.md)
