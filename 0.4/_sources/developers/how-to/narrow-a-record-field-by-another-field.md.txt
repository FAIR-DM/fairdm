# How to narrow a record field by another field

This guide makes a sample field follow a dataset field on the same form. You would do this when a person should pick a sample from the dataset they have just chosen, or see that dataset's samples first.

## Steps

1. Declare the field the other one follows, with the scope the form needs.

   ```python
   from django import forms

   from fairdm.contrib.autocomplete.fields import DatasetChoiceField, SampleChoiceField


   class PlaceSampleForm(forms.Form):
       dataset = DatasetChoiceField(scope="edit")
   ```

2. Add the sample field to the form, with the name of the first field as `depends_on`.

   ```python
   class PlaceSampleForm(forms.Form):
       dataset = DatasetChoiceField(scope="edit")
       sample = SampleChoiceField(depends_on="dataset")
   ```

   The field then offers only the samples of the chosen dataset.

3. To list those samples first and still offer the rest, pass the name as `prefer` instead.

   ```python
   class PlaceSampleForm(forms.Form):
       dataset = DatasetChoiceField(scope="edit")
       sample = SampleChoiceField(prefer="dataset")
   ```

   The samples of the chosen dataset come first, under a heading of their own. The field still accepts every sample the person may view. Use this when a record may refer to a sample in another dataset, as a measurement may.

4. Build the form inside a request.

   ```python
   form = PlaceSampleForm(request.POST or None)
   ```

## The result

With `depends_on`, the browser searches only the samples of the chosen dataset and clears the sample choice when the dataset changes. On submit, the field reads the dataset from the form's own data and refuses a sample of any other dataset with `invalid_choice`. When no dataset is chosen, the field is not narrowed.

`depends_on` and `prefer` accept `"dataset"` or `"polymorphic_ctype"`, for samples and measurements. Any other name raises `ValueError` when the field is created. See [Record fields](../reference/record-fields.md).
