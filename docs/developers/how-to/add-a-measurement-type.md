# How to add a measurement type

A measurement type is a model that extends `Measurement` with the fields of one kind of analysis. You add one for each method that records data on a sample, such as a grain size analysis or a spectrometer run.

## Before you start

You need a portal app listed in `fairdm.setup(apps=[...])`. This guide uses an app called `sediments`. See [Configuration](../reference/configuration.md).

## Steps

1. Subclass `Measurement` in the app's `models.py`. Add the fields of the analysis, and name the result `value` and its uncertainty `uncertainty`.

   ```python
   # sediments/models.py
   from fairdm.core.measurement.models import Measurement
   from fairdm.db import models


   class GrainSizeMeasurement(Measurement):
       """The median grain size of a sediment sample."""

       method = models.CharField(
           max_length=50,
           help_text="How the grain size was determined.",
       )
       value = models.DecimalQuantityField(
           "micrometer",
           max_digits=10,
           decimal_places=2,
           null=True,
           blank=True,
           help_text="The median grain size.",
       )
       uncertainty = models.DecimalQuantityField(
           "micrometer",
           max_digits=10,
           decimal_places=2,
           null=True,
           blank=True,
           help_text="The uncertainty of the median grain size.",
       )

       class Meta:
           verbose_name = "grain size measurement"
           verbose_name_plural = "grain size measurements"
   ```

   Every measurement already has `name`, `sample`, `dataset`, `location` and the other fields on [Measurement model](../reference/measurement-model.md). Do not declare a field with one of those names. The field classes are described on [Model fields](../reference/model-fields.md).

   FairDM reads `value` and `uncertainty` to show the result, so you write no method for it. A type with no single result leaves both out.

2. Create the migration and apply it.

   ```bash
   python manage.py makemigrations sediments
   python manage.py migrate
   ```

3. Register the type in the app's `config.py`. FairDM finds this module when the portal starts.

   ```python
   # sediments/config.py
   from fairdm.core.measurement.config import BaseMeasurementConfiguration
   from fairdm.registry import register

   from .models import GrainSizeMeasurement


   @register
   class GrainSizeMeasurementConfig(BaseMeasurementConfiguration):
       model = GrainSizeMeasurement
       fields = [
           "name",
           "sample",
           "dataset",
           "method",
           "value",
           "uncertainty",
       ]
   ```

   `fields` is the list every generated component uses. List `name`, `sample` and `dataset` too, because the serializer, the import and export resource and the administration page read only this list. The options are on [Model configuration](../reference/model-configuration.md).

4. Check that the portal knows the type.

   ```bash
   python manage.py shell -c "from fairdm.registry import registry; print(registry.is_registered('sediments.grainsizemeasurement'))"
   ```

   The command prints `True`.

## The result

The portal has a grain size measurement type. In the administration interface, adding a measurement offers the type in its list of types, and the form shows the fields you named. The type has a table, a filter set and a serializer too. See [What registering a type produces](../explanation/what-registering-a-type-produces.md).

A measurement with `value` set to 48.25 micrometres and `uncertainty` set to 0.5 micrometres reads `48.25 ± 0.50 μm` wherever the portal shows its result, including `str(measurement)` and the result on the measurement's page. A measurement with no value shows its name. The rules are in [How a measurement reports its value](../explanation/how-a-measurement-reports-its-value.md).

A measurement always names a sample, and the sample may belong to another dataset. The base `Measurement` is not registered, only its types.

To change the admin page, the form, the filter set or the queryset of the type, see [How to customise the admin for a measurement type](customise-the-admin-for-a-measurement-type.md), [How to write a custom form or filter for a measurement type](write-a-custom-form-or-filter-for-a-measurement-type.md) and [How to add queryset methods to a measurement type](add-queryset-methods-to-a-measurement-type.md). To test the type, see [How to test a portal with FairDM factories](test-a-portal-with-fairdm-factories.md).
