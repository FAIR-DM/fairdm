# How to import and export locations

This guide makes the import and export file of a type carry the location of its records as four columns. You would do this when researchers move samples or measurements in and out of the portal as tables.

## Before you start

You need a registered sample or measurement type. This guide uses `CoreSample`, a sample type of your portal. To add one, see [How to add a sample type](add-a-sample-type.md). The columns and the rules for reading them are in [Location fields](../reference/location-fields.md).

## Steps

1. Check that `location` is among the fields the type's resource uses. The resource takes its fields from `resource_fields` and, when that is not set, from `fields`. A configuration built on `BaseSampleConfiguration` lists `location` already.

   ```python
   import fairdm
   from fairdm.core.sample.config import BaseSampleConfiguration
   from myportal.models import CoreSample


   @fairdm.register
   class CoreSampleConfig(BaseSampleConfiguration):
       model = CoreSample
       fields = ["name", "dataset", "local_id", "status", "location", "depth_m"]
   ```

2. Export the type's records and open the file. The single `location` column is replaced by four: `latitude`, `longitude`, `location_elevation` and `location_uncertainty`.

   ```text
   id,name,latitude,longitude,location_elevation,location_uncertainty
   31,Core 14,49.0094,8.4115,112.5,25.0
   32,Core 15,,,,
   ```

   A record with no location has four empty cells. A measurement never writes its sample's location.

3. Prepare a file to import with the same columns. Write each coordinate as a signed decimal number of degrees in WGS 84, such as `49.0094` or `-8.4115`. Convert projected coordinates first, and write degrees, minutes and seconds as decimal degrees.

4. Import the file. A row the location input would refuse is reported with the input's own message and is not saved. The rest of the file is read as usual. A row is refused when:

   - a coordinate is not a number, or lies outside its range,
   - one coordinate is given without the other,
   - an elevation or an uncertainty is given with no coordinates,
   - the uncertainty is negative.

5. If the type uses a resource class of your own, add the location columns to it. A resource that derives from `BaseFairDMResource` has them already. Any other `ModelResource` gets them by inheriting `LocatedResourceMixin` ahead of it.

   ```python
   from fairdm.contrib.import_export.resources import BaseFairDMResource
   from myportal.models import CoreSample


   class CoreSampleResource(BaseFairDMResource):
       class Meta:
           model = CoreSample
           fields = ("id", "local_id", "name", "location", "depth_m")
   ```

   Then name the resource in the configuration with `resource_class = "myportal.resources.CoreSampleResource"`. A configuration declares either `resource_fields` or `resource_class`, never both.

## The result

The type's file has the four location columns wherever its resource lists `location`. A file with none of the four columns leaves every record's location as it was, and a file with only some of them changes only those. An empty cell clears the value. Clearing a point also clears the elevation and uncertainty, so a file that empties `latitude` and `longitude` for a record that holds an elevation or an uncertainty must carry those two columns too, with empty cells.
