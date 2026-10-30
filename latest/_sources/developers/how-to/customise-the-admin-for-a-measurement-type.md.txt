# How to customise the admin for a measurement type

The registry generates an administration page for each measurement type. You replace it with your own class when the list needs other columns, filters or search fields, or the form needs a different layout.

## Before you start

You need a registered measurement type. This guide uses `GrainSizeMeasurement` from [How to add a measurement type](add-a-measurement-type.md).

## Steps

1. Subclass `MeasurementChildAdmin` in the app's `admin.py`. Start each list from the base class's list, so the columns, filters and search fields every measurement has stay in place.

   ```python
   # sediments/admin.py
   from fairdm.core.measurement.admin import MeasurementChildAdmin


   class GrainSizeMeasurementAdmin(MeasurementChildAdmin):
       list_display = [*MeasurementChildAdmin.list_display, "method"]
       list_filter = [*MeasurementChildAdmin.list_filter, "method"]
       search_fields = [*MeasurementChildAdmin.search_fields, "method"]
   ```

   The base class lists `name`, `sample`, `dataset`, the measurement type, `added` and `modified`. Its dataset filter offers private datasets too, so keep the base `list_filter` rather than writing `"dataset"` yourself. The base class also adds inlines for descriptions, dates, identifiers and credits.

2. To lay out the form yourself, set `fieldsets`. A field you leave out is not shown.

   ```python
   class GrainSizeMeasurementAdmin(MeasurementChildAdmin):
       ...
       fieldsets = [
           (None, {"fields": ["name", "sample", "dataset", "image"]}),
           ("Grain size", {"fields": ["method", "value", "uncertainty"]}),
           (
               "Location",
               {
                   "fields": [
                       "location",
                       "location_elevation",
                       "location_uncertainty",
                   ],
                   "classes": ["collapse"],
               },
           ),
           (
               "Metadata",
               {"fields": ["uuid", "added", "modified"], "classes": ["collapse"]},
           ),
       ]
   ```

   Without `fieldsets`, the form shows the base fields first, then your type's own fields under "Contents", then the metadata.

3. Name the class in the type's configuration with `admin_class`.

   ```python
   # sediments/config.py
   from .admin import GrainSizeMeasurementAdmin


   @register
   class GrainSizeMeasurementConfig(BaseMeasurementConfiguration):
       model = GrainSizeMeasurement
       fields = ["name", "sample", "dataset", "method", "value", "uncertainty"]
       admin_class = GrainSizeMeasurementAdmin
   ```

   `admin_class` also takes the class's dotted path as a string. The class must subclass `MeasurementChildAdmin`, or the portal refuses to start with a `ConfigurationError`. Do not set `admin_list_display` alongside it, because a field list and a class for the same component are refused together.

## The result

The administration page of the type uses your class, and the registry generates none for it. The other generated components, the form, table, filter set and serializer, are unchanged.

You can register the admin class yourself instead with `@admin.register(GrainSizeMeasurement)` in `admin.py`. The registry leaves a model that is already registered with the admin alone. Naming the class in `admin_class` keeps every choice about the type in its configuration, which is why this guide uses it.

The base class's attributes follow [Measurement model](../reference/measurement-model.md#admin-form-and-filter-bases). The options of the configuration are on [Model configuration](../reference/model-configuration.md).
