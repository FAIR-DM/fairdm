# How to customise a generated component

A registered type gets six generated components: a form, a table, a filter set, a serializer, an import and export resource and an administration page. You change one of them when its fields, its class or its behaviour is not what the type needs, and the other five stay as they are.

## Before you start

You need a registered type. See [How to register a sample or measurement type](register-a-sample-or-measurement-type.md). This guide uses `PlantSample`, a sample type in an app named `fieldwork`, with the fields `species`, `collected_on` and `notes`. Use the first of the three sections below that does what you need.

## Give one component its own fields

1. Add the component's field list to the configuration. Here the table shows three columns while every other component still uses `fields`.

   ```python
   # fieldwork/config.py
   from fairdm.core.sample.config import BaseSampleConfiguration
   from fairdm.registry import register

   from .models import PlantSample


   @register
   class PlantSampleConfig(BaseSampleConfiguration):
       model = PlantSample
       fields = [
           *BaseSampleConfiguration.fields,
           "species",
           "collected_on",
           "notes",
       ]
       table_fields = ["name", "species", "collected_on"]
   ```

2. Restart the portal and open the type's listing.

The table has the columns you listed, with the dataset icon, **Latitude** and **Longitude** that every sample table carries. The names of the lists are `form_fields`, `table_fields`, `filterset_fields`, `serializer_fields`, `resource_fields` and `admin_list_display`. To leave a field out of every component, add its name to `exclude` instead. See [Component field lists](../reference/model-configuration.md#component-field-lists).

## Replace a component with a class of your own

1. Write the class on the base that the component builds on. The base tables are `SampleTable` and `MeasurementTable` in `fairdm.contrib.collections.tables`. Extend the base's `Meta` so the table keeps its classes, its column order and its sorting.

   ```python
   # fieldwork/tables.py
   from fairdm.contrib.collections.tables import SampleTable

   from .models import PlantSample


   class PlantSampleTable(SampleTable):
       class Meta(SampleTable.Meta):
           model = PlantSample
           fields = ["id", "dataset", "name", "species", "collected_on"]

       def render_species(self, value):
           return value.upper()
   ```

2. Name the class in the configuration, and remove the same component's field list. A component can have a field list or a class, and the registry refuses both.

   ```python
   # fieldwork/config.py
   from fairdm.core.sample.config import BaseSampleConfiguration
   from fairdm.registry import register

   from .models import PlantSample
   from .tables import PlantSampleTable


   @register
   class PlantSampleConfig(BaseSampleConfiguration):
       model = PlantSample
       fields = [
           *BaseSampleConfiguration.fields,
           "species",
           "collected_on",
           "notes",
       ]
       table_class = PlantSampleTable
   ```

3. If the configuration extends `BaseMeasurementConfiguration`, set the component's own list to `None` as well. That base sets `form_fields`, `table_fields` and `filterset_fields`, and the registry counts an inherited list.

   ```python
   table_fields = None
   table_class = LeafAreaMeasurementTable
   ```

4. Restart the portal and open the type's listing.

The table shows the species in capitals. A class option also accepts a dotted path such as `"fieldwork.tables.PlantSampleTable"`. Each component builds on its own base, which the reference lists under [Component classes](../reference/model-configuration.md#component-classes).

## Build a component in code

Use this when a declaration cannot say what you need, because the answer has to be worked out.

1. Override the component's accessor in the configuration. Here the filter set offers only the fields in `FILTERABLE`, chosen from the fields the filter set would use. A field added to `fields` later does not gain a filter by accident.

   ```python
   # fieldwork/config.py
   from fairdm.core.sample.config import BaseSampleConfiguration
   from fairdm.registry import register
   from fairdm.registry.factories import FilterFactory

   from .models import PlantSample


   @register
   class PlantSampleConfig(BaseSampleConfiguration):
       model = PlantSample
       fields = [
           *BaseSampleConfiguration.fields,
           "species",
           "collected_on",
           "notes",
       ]

       FILTERABLE = {"species", "collected_on"}

       def get_filterset_class(self):
           names = [
               name
               for name in self.resolve_fields("filterset")
               if name in self.FILTERABLE
           ]
           return FilterFactory(
               model=self.model,
               fields=names,
               search_fields=self.get_search_fields(),
           ).generate()
   ```

2. Restart the portal and open the type's listing.

The filter panel offers **Species** and **Collected on**. Every part of the framework reaches the filter set through `get_filterset_class()`, so the listing and the API both receive yours. The accessors are on [Methods](../reference/model-configuration.md#methods).

To change the administration page of a measurement type, see [How to customise the admin for a measurement type](customise-the-admin-for-a-measurement-type.md). To change a form or a filter set with the framework's mixins, see [How to customise a sample form](customise-a-sample-form.md) and [How to write a custom form or filter for a measurement type](write-a-custom-form-or-filter-for-a-measurement-type.md).
