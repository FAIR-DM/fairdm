# How to register an import definition

This guide gives a kind of file of your own a name, so that it has its own column guide and its own public Table Schema. You would do this when a team fills the same sample type from a file that differs from the type's built-in definition, for example with a shorter list of formats.

## Before you start

You need a registered sample or measurement type. This guide uses `CoreSample`, a sample type of your portal. To add one, see [How to add a sample type](add-a-sample-type.md). FairDM already builds a definition for every registered type, named after the model in lower case, so you need this guide only for an extra one. The definition and the table schema are described in [Table schema](../reference/table-schema.md).

## Steps

1. Choose a name for the definition. It must be a slug and must not be the name of a definition that exists. The built-in ones are named after the models, such as `coresample`.

2. Create the definition and register it where your portal starts, in the `ready` method of your app's configuration. `register` raises `ValueError` when the name is taken or the model is not registered.

   ```python
   # myportal/apps.py
   from django.apps import AppConfig


   class MyPortalConfig(AppConfig):
       name = "myportal"

       def ready(self):
           from fairdm.contrib.import_export.definitions import (
               ImportDefinition,
               register,
           )

           from myportal.models import CoreSample

           register(
               ImportDefinition(
                   name="field-cores",
                   model=CoreSample,
                   formats=("csv", "xlsx"),
               )
           )
   ```

3. Check that the portal knows the definition. Its columns come from the type's configuration, so a change to `resource_fields` changes them.

   ```python
   from fairdm.contrib.import_export.definitions import get_definition

   definition = get_definition("field-cores")
   definition.kind  # "sample"
   definition.table_schema().headings
   ```

4. Show its guide on a page of your own. Pass the table schema to the component.

   ```html
   <c-import.guide :schema="schema" />
   ```

   In the view, set `schema` to `get_definition("field-cores").table_schema()`.

5. Open its Table Schema at `table-schemas/field-cores/` on your portal. The browser downloads `field-cores-table-schema.json`.

## The result

The portal lists `field-cores` among its import definitions, and the guide and the Table Schema describe the columns of `CoreSample`. The built-in `coresample` definition is unchanged. For every column and key of the Table Schema, see [Table schema](../reference/table-schema.md#the-table-schema-address).
