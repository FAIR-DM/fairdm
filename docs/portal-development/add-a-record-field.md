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

   from demo.models import RockSample
   from fairdm.contrib.autocomplete.fields import DatasetChoiceField


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

To choose several records, use the multiple field. It takes the same arguments and offers the same
records as the single field: the ones the person may view, unless you pass `scope`.

```python
from django import forms

from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField


class ProjectPickerForm(forms.Form):
    projects = ProjectMultipleChoiceField()
```

## Keep a sample field to one type

To offer only the samples of one registered type, pass the model as `type`. A sample of any other
type is refused when the form is saved.

```python
from django import forms

from demo.models import RockSample
from fairdm.contrib.autocomplete.fields import SampleChoiceField


class CompareRocksForm(forms.Form):
    rock_sample = SampleChoiceField(type=RockSample)
```

The demo portal has this form as `SampleReferenceFormExample` in `demo/forms.py`.

## Narrow a field by another field

To offer only the samples of the dataset chosen in another field of the form, pass that field's
name as `depends_on`. To list those samples first and still offer the rest, pass it as `prefer`.

```python
from django import forms

from fairdm.contrib.autocomplete.fields import DatasetChoiceField, SampleChoiceField


class MeasurementPlacementForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit")
    sample = SampleChoiceField(depends_on="dataset")
```

## Offer one person's records

On a page that lists one person's records, give the field that person as `owner`. It offers their
private records to them and public records to everyone else.

```python
from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField

projects = ProjectMultipleChoiceField(owner=person)
```

## Filter a list by a record

To let a visitor narrow a list to the records that point at any of several chosen records, declare
a `RecordMultipleFilter` on the filter set. It draws the multiple field of the kind you name, at
public scope, so a visitor and a signed-in researcher are offered the same public records.

```python
import django_filters

from demo.models import RockSample
from fairdm.contrib.autocomplete.fields import DatasetMultipleChoiceField
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter


class RockSampleFilter(django_filters.FilterSet):
    dataset = RecordMultipleFilter(DatasetMultipleChoiceField, field_name="dataset")

    class Meta:
        model = RockSample
        fields = ["dataset"]
```

Build the filter set with the request, as `RockSampleFilter(request.GET, queryset=..., request=request)`
does in a list view. The values come back from the list's address as repeated parameters, such as
`?dataset=3&dataset=5`, and a record the field would not offer is refused. A filter set built with
no request offers and accepts nothing.

## Check that it works

Open the page signed in as someone who can edit one private dataset, type part of the dataset's
name, and the dataset is offered with its project beneath it. For a filter, open the list signed out
and tick two datasets: the list narrows to their records.
