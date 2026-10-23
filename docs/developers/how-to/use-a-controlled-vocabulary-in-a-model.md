# How to use a controlled vocabulary in a model

A controlled vocabulary limits a field to a fixed list of defined terms. You add one to a sample or measurement type when everyone should describe a property, such as texture, with the same words.

## Before you start

You need a registered sample or measurement type. This guide adds a field to `SedimentSample` from [How to add a sample type](add-a-sample-type.md).

## Steps

1. Declare the vocabulary in a module of the app, such as `vocabularies.py`. Each term is a class attribute holding a dictionary with a label and, where you can, a definition.

   ```python
   # sediments/vocabularies.py
   from django.utils.translation import gettext_lazy as _
   from research_vocabs.vocabularies import VocabularyBuilder


   class SedimentTexture(VocabularyBuilder):
       sand = {
           "skos:prefLabel": _("Sand"),
           "skos:definition": _("Particles between 0.0625 and 2 mm."),
       }
       silt = {
           "skos:prefLabel": _("Silt"),
           "skos:definition": _("Particles between 0.004 and 0.0625 mm."),
       }
       clay = {
           "skos:prefLabel": _("Clay"),
           "skos:definition": _("Particles finer than 0.004 mm."),
       }

       class Meta:
           name = "sediment-texture"
           prefix = "SEDIMENTS"
           namespace = "https://example.org/vocabularies/sediment-texture/"
           scheme_attrs = {
               "skos:prefLabel": _("Sediment texture"),
               "skos:definition": _("Texture classes for sediment."),
           }
   ```

   The attribute name is what the database stores, so use letters, digits, `-`, `_` and `.` only. Set `namespace` to an address you control.

2. Add a `ConceptField` to the model. Pass the vocabulary class itself, not its name.

   ```python
   # sediments/models.py
   from research_vocabs.fields import ConceptField

   from .vocabularies import SedimentTexture


   class SedimentSample(Sample):
       # ... fields ...
       texture = ConceptField(
           vocabulary=SedimentTexture,
           blank=True,
           help_text="The dominant texture class.",
       )
   ```

   Leave out `blank=True` to make the field required. To offer only some of the terms, add `include_only=["sand", "silt"]`. The field is described on [Model fields](../reference/model-fields.md#conceptfield).

3. Create the migration and apply it.

   ```bash
   python manage.py makemigrations sediments
   python manage.py migrate
   ```

   The migration records the vocabulary by its import path. Do not move or rename the class afterwards, or the migration can no longer be loaded.

4. Add the field to the type's configuration.

   ```python
   # sediments/config.py
   @register
   class SedimentSampleConfig(BaseSampleConfiguration):
       model = SedimentSample
       fields = [
           *BaseSampleConfiguration.fields,
           "core_number",
           "depth",
           "collected_on",
           "texture",
       ]
   ```

5. Set and read a value by the term's name.

   ```python
   sample.texture = "clay"
   sample.save()

   sample.refresh_from_db()
   str(sample.texture)           # "clay"
   sample.texture.label()        # "Clay"
   sample.texture.definition()   # "Particles finer than 0.004 mm."
   ```

## The result

The field is a choice list in the type's form and the administration page, offering the terms sorted by label. `full_clean()` raises a `ValueError` for a name that is not in the vocabulary. Filtering works on the stored name, as in `SedimentSample.objects.filter(texture="clay")`.

Adding a term whose name is longer than every existing one changes the field's `max_length`, so run `makemigrations` again after you add it.

A vocabulary can also come from a file in your code or from a published address, and FairDM's own vocabularies are built the same way. See [Controlled vocabularies](../../explanation/controlled-vocabularies.md).
