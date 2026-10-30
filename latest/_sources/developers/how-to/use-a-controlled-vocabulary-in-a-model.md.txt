# How to use a controlled vocabulary in a model

A controlled vocabulary limits a field to a published list of defined terms. You add one to a sample or measurement type when everyone should describe a property, such as texture, with the same words.

## Before you start

You need a registered sample or measurement type. This guide adds a field to `SedimentSample` from [How to add a sample type](add-a-sample-type.md).

You need the vocabulary as a SKOS file, in Turtle, RDF/XML or JSON-LD, and the address of its concept scheme. Use a vocabulary someone already publishes where one exists. If you write one yourself, give it an address you control.

## Steps

1. Keep a copy of the vocabulary with the portal, so a deploy never depends on another server, and declare it in the portal's settings by the slug the portal gives it.

   ```python
   # settings.py
   CONTROLLED_VOCABULARIES = {
       "sediment-texture": {"source": BASE_DIR / "vocabularies" / "sediment-texture.ttl"},
   }
   ```

2. Add a `ConceptField` to the model. Name the vocabulary by the address of its concept scheme.

   ```python
   # sediments/models.py
   from controlled_vocabularies.fields import ConceptField
   from django.utils.translation import gettext_lazy as _

   SEDIMENT_TEXTURE = "https://vocab.example.org/sediment-texture"


   class SedimentSample(Sample):
       # ... fields ...
       texture = ConceptField(
           vocabulary=SEDIMENT_TEXTURE,
           null=True,
           blank=True,
           related_name="+",
           verbose_name=_("texture"),
           help_text=_("The dominant texture class."),
       )
   ```

   Leave out `null=True` and `blank=True` to make the field required. To offer only some of the terms, pass the address of one of the vocabulary's collections as `collection`. The field is described on [Model fields](../reference/model-fields.md#conceptfield).

3. Create the migration, apply it and load the vocabulary.

   ```bash
   python manage.py makemigrations sediments
   python manage.py migrate
   python manage.py sync_vocabularies
   ```

   The migration records the vocabulary's address and nothing about where it is read from, so moving the file needs no migration.

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

5. Set and read a value by the term's address.

   ```python
   sample.texture_id = f"{SEDIMENT_TEXTURE}/clay"
   sample.save()

   sample.refresh_from_db()
   sample.get_texture_uri()      # "https://vocab.example.org/sediment-texture/clay"
   sample.get_texture_label()    # "Clay"
   ```

## The result

The field is a search box in the type's form and the administration page, offering the vocabulary's terms by name. `full_clean()` refuses a concept from any other vocabulary, and a concept a sample holds cannot be deleted. Filtering works on the stored address, as in `SedimentSample.objects.filter(texture=f"{SEDIMENT_TEXTURE}/clay")`.

A new term reaches the portal when you replace the file with the vocabulary's new release and run `sync_vocabularies` again, with no migration. FairDM's own vocabularies are loaded the same way. See [Controlled vocabularies](../../explanation/controlled-vocabularies.md).
