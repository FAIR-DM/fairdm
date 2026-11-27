# How to add a sample type

A sample type is a model that extends `Sample` with the fields your research needs. You add one when the samples in your portal carry measurements or properties that the base model does not.

## Before you start

You need a portal app listed in `fairdm.setup(apps=[...])`. This guide uses an app called `sediments`. See [Configuration](../reference/configuration.md).

## Steps

1. Subclass `Sample` in the app's `models.py` and add your fields. Take field classes from `fairdm.db.models`.

   ```python
   # sediments/models.py
   from django.core.validators import MinValueValidator

   from fairdm.core.sample.models import Sample
   from fairdm.db import models


   class SedimentSample(Sample):
       """A sediment sample taken from a core."""

       core_number = models.CharField(
           max_length=50,
           help_text="The number printed on the core tube.",
       )
       depth = models.QuantityField(
           "meter",
           validators=[MinValueValidator(0)],
           null=True,
           blank=True,
           help_text="Depth in the core at which the sample was taken.",
       )
       collected_on = models.PartialDateField(
           null=True,
           blank=True,
           help_text="A year, a year and month, or a full date.",
       )

       class Meta:
           verbose_name = "sediment sample"
           verbose_name_plural = "sediment samples"
   ```

   Every sample already has `name`, `dataset`, `local_id`, `status`, `location` and the other fields on [Sample model](../reference/sample-model.md). Do not declare a field with one of those names. The field classes are described on [Model fields](../reference/model-fields.md).

2. Create the migration and apply it.

   ```bash
   python manage.py makemigrations sediments
   python manage.py migrate
   ```

3. Register the type in the app's `config.py`. FairDM finds this module when the portal starts.

   ```python
   # sediments/config.py
   from fairdm.core.sample.config import BaseSampleConfiguration
   from fairdm.registry import register

   from .models import SedimentSample


   @register
   class SedimentSampleConfig(BaseSampleConfiguration):
       model = SedimentSample
       fields = [
           *BaseSampleConfiguration.fields,
           "core_number",
           "depth",
           "collected_on",
       ]
   ```

   `fields` is the list every generated component uses: the form, table, filter set, serializer, import and export resource and the administration page. Starting from `BaseSampleConfiguration.fields` keeps the fields every sample has. The options are on [Model configuration](../reference/model-configuration.md).

4. Check that the portal knows the type.

   ```bash
   python manage.py shell -c "from fairdm.registry import registry; print(registry.is_registered('sediments.sedimentsample'))"
   ```

   The command prints `True`.

## The result

The portal has a sediment sample type. In the administration interface, adding a sample offers the sediment sample type in its list of types, and the form shows the fields you named. The type has a table, a filter set and a serializer too. See [What registering a type produces](../explanation/what-registering-a-type-produces.md).

The base `Sample` cannot be saved, so every sample in the portal is of a registered type. The reason is in [How sample and measurement types are stored](../../explanation/how-sample-and-measurement-types-are-stored.md).

To describe the same sample with terms from a fixed list, see [How to use a controlled vocabulary in a model](use-a-controlled-vocabulary-in-a-model.md). To relate one sample to another, see [How to record sample relationships](record-sample-relationships.md). To test the type, see [How to test a portal with FairDM factories](test-a-portal-with-fairdm-factories.md).
