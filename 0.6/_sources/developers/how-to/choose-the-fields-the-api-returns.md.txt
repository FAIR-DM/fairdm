# How to choose the fields the API returns

A sample or measurement type always returns the fields common to its kind and its metadata. You choose which of the type's own fields come with them. Do this when the API returns too much, too little, or something different from what the type's forms and tables show.

## Before you start

- Register the type. See [How to register a sample or measurement type](register-a-sample-or-measurement-type.md).
- The examples use a sample type `PlantSample` with the fields `species`, `collected_on`, `dry_weight_g`, `lab_code` and `parent_plant`, a foreign key to another sample. Use your own type's names.

## Steps

1. Open the module where the type is registered. It holds a configuration class decorated with `@fairdm.register`.

2. List the type's own fields in `fields`. Every component of the type shares this list, the API included.

   ```python
   import fairdm
   from fairdm.registry import SampleConfig

   from .models import PlantSample


   @fairdm.register
   class PlantSampleConfig(SampleConfig):
       model = PlantSample
       fields = ["name", "species", "collected_on", "dry_weight_g"]
   ```

   The API returns the common fields, then `species`, `collected_on` and `dry_weight_g`, then the metadata. `name` is already common, so it appears once.

3. To return a different set from the forms and tables, add `serializer_fields`. It applies to the API alone.

   ```python
   fields = ["name", "species", "collected_on", "dry_weight_g"]
   serializer_fields = ["species", "collected_on"]
   ```

4. Include every field the model requires. A field that is editable, has no default and is neither blank nor null must be in the list that applies, or no record can be created through the API.

5. Run the checks.

   ```bash
   uv run python manage.py check
   ```

## The result

The API of the type returns the common fields of its kind, the fields you listed and the metadata. Open `/api/v1/docs/` to see the fields of each operation. A field the API accepts on a write is shown without a read-only mark.

The list is chosen in this order, and the first one that applies is used:

1. `serializer_fields`
2. `fields`
3. The framework's defaults, when the registration names neither. These are the type's editable fields, with `options` and `tags` left out because neither is useful to a caller. Name either in `serializer_fields` or `fields` to have the API return it.

If step 4 was missed, the check reports `fairdm.E600` and names the type and the field. The portal also stops with it when it starts.

```text
plants.PlantSample: (fairdm.E600) The API serializer for plants.PlantSample does not accept the
required field 'species', so no record of this type can be created through the API.
    HINT: Add 'species' to serializer_fields (or fields) in the type's registration, or to the
    serializer it names.
```

Add the field to the list. A field the serializer returns as read-only is reported too. See [Configuration checks](../../administrators/reference/configuration-checks.md).

## Use a serializer of your own

When a list of names is not enough, write the serializer yourself. It must subclass `BaseSampleSerializer` for a sample type, or `BaseMeasurementSerializer` for a measurement type. Those carry the narrowing of the parents a caller may choose, the credit given to the person who creates a record and the manage-level rule for changing visibility or a parent.

1. Write the serializer. Extend the `Meta` of the base so the common fields and the read-only location fields stay.

   ```python
   from fairdm.api.serializers import BaseSampleSerializer, RecordReferenceField

   from .models import PlantSample


   class PlantSampleSerializer(BaseSampleSerializer):
       parent_plant = RecordReferenceField(read_only=True)

       class Meta(BaseSampleSerializer.Meta):
           model = PlantSample
           fields = BaseSampleSerializer.Meta.fields + [
               "species",
               "collected_on",
               "lab_code",
               "parent_plant",
           ]
           read_only_fields = [*BaseSampleSerializer.Meta.read_only_fields, "lab_code"]
   ```

   Declare each relation you add as a `RecordReferenceField` or a `StringRelatedField`. A relation left to Django REST Framework's default is returned as a database number, which the API never exposes elsewhere.

2. Name the serializer in the registration. Do not set `serializer_fields` as well, because the registry refuses a registration that declares both a component's field list and its class.

   ```python
   @fairdm.register
   class PlantSampleConfig(SampleConfig):
       model = PlantSample
       serializer_class = PlantSampleSerializer
   ```

   When the serializer has to be worked out in code, override `get_serializer_class` on the configuration instead. The API uses whatever it returns, and the same rule applies.

   ```python
   def get_serializer_class(self):
       return PlantSampleSerializer
   ```

A serializer that does not subclass the base stops the portal loading its API routes with `ImproperlyConfigured`, naming the serializer and the base to build on.

The shape of what the API returns is in the [REST API reference](../reference/rest-api.md).
