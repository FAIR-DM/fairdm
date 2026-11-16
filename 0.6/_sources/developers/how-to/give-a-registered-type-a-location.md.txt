# How to give a sample or measurement a location

This guide adds the location input to the form of a sample type or a measurement type, and shows how to set a location in code. You would do this when the records of a type are taken at a place that people should be able to record and search by.

## Before you start

You need a registered sample or measurement type. This guide uses `CoreSample`, a sample type, and `GrainSizeMeasurement`, a measurement type. Both are types of your portal. To add them, see [How to add a sample type](add-a-sample-type.md) and [How to add a measurement type](add-a-measurement-type.md).

Every sample and measurement already has the three location fields. You add no field to your model. For what the fields hold, see [Location fields](../reference/location-fields.md).

## Steps

1. For a sample type, check that `location` is in the configuration's `fields`. A configuration built on `BaseSampleConfiguration` has it already. If you set `fields` yourself, include it.

   ```python
   import fairdm
   from fairdm.core.sample.config import BaseSampleConfiguration
   from myportal.models import CoreSample


   @fairdm.register
   class CoreSampleConfig(BaseSampleConfiguration):
       model = CoreSample
       fields = ["name", "dataset", "local_id", "status", "location", "depth_m"]
   ```

2. For a measurement type, add `location` to its own `fields`. Most measurements are made where their sample was taken and need no location of their own, so add it only for a type whose readings are taken elsewhere, such as in the field some distance from the core.

   ```python
   import fairdm
   from fairdm.core.measurement.config import BaseMeasurementConfiguration
   from myportal.models import GrainSizeMeasurement


   @fairdm.register
   class GrainSizeConfig(BaseMeasurementConfiguration):
       model = GrainSizeMeasurement
       fields = ["location", "d50_um"]
   ```

3. If you write the form yourself, build it on the mixin for the record kind. Both include `LocationFormMixin`.

   ```python
   from django import forms

   from fairdm.core.sample.forms import SampleFormMixin
   from myportal.models import CoreSample


   class CoreSampleForm(SampleFormMixin, forms.ModelForm):
       class Meta:
           model = CoreSample
           fields = ["name", "dataset", "location", "depth_m"]
   ```

   For a `ModelForm` of any other model that has the three fields, use `LocationFormMixin` from `fairdm.utils.location.forms`.

4. To set a location in code, pass a GEOS point in WGS 84, with the longitude first.

   ```python
   from django.contrib.gis.geos import Point

   sample.location = Point(8.4115, 49.0094, srid=4326)
   sample.location_elevation = 112
   sample.location_uncertainty = 5
   sample.save()
   ```

## The result

The type's form shows a location input: a latitude and a longitude, an elevation and an uncertainty. The input reads signed decimal degrees in WGS 84 and refuses anything else with a message. A form without `location` among its fields shows no input.

A measurement's location is its own. Changing its sample's location leaves it where it was, and the reverse. A measurement with none of its own takes its sample's location for a viewer who may open the sample. To find records by their place, see [How to find records by where they are](find-records-by-where-they-are.md). For why each record keeps its own copy, see [How locations are stored and protected](../../explanation/how-locations-are-stored-and-protected.md).
