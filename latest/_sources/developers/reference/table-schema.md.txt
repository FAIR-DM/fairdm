# Table schema

A registered sample or measurement type knows the columns of its import and export file. This page describes the table schema that holds them, the columns, the widgets that read and write their cells, the import definitions that name a kind of file, the guide component and the public address of the Frictionless Table Schema. For the tasks, see [How to register an import definition](../how-to/register-an-import-definition.md) and [How to import and export locations](../how-to/import-and-export-locations.md). The import formats are set by [`IMPORT_FORMATS`](settings.md#import_formats). The location columns are described in [Location fields](location-fields.md).

Every class, attribute, function and argument is described in the generated API reference for [`schema`](api/fairdm/fairdm.contrib.import_export.schema.md), [`widgets`](api/fairdm/fairdm.contrib.import_export.widgets.md) and [`definitions`](api/fairdm/fairdm.contrib.import_export.definitions.md). This page holds what the docstrings do not: the order of the columns, the kinds, roles and groups, the widget of each kind, how cells are written and read, the guide component and the Table Schema address.

## `ModelConfiguration.get_table_schema()`

Returns the type's `TableSchema`. The default builds it with `build_table_schema`. Override it to build your own.

```python
from fairdm.registry import registry

schema = registry.get_for_model(CoreSample).get_table_schema()
schema.headings  # ["portal_id", "local_id", "name", "depth_m", ..., "status", "latitude", ...]
```

## Column kinds, roles and groups

Each `Column` of a `TableSchema` has a `kind`, a `role` and a `group`.

### Kinds

| Kind | Cell | Frictionless type |
|---|---|---|
| `id` | A portal ID | `string` |
| `text` | Any text | `string` |
| `integer` | A whole number | `integer` |
| `number` | A number | `number` |
| `boolean` | Yes or no | `boolean` |
| `date` | A date | `date` |
| `datetime` | A date and time | `datetime` |
| `time` | A time of day | `time` |
| `partial_date` | A year, a year and month, or a full date | `string` |
| `concept` | One concept of a vocabulary | `string` |
| `choice` | One of the model field's choices | `string` |
| `sample` | A sample, by portal ID or Local ID | `string` |
| `quantity` | A number with a unit | `number` |
| `latitude` | Decimal degrees, WGS 84 | `number` |
| `longitude` | Decimal degrees, WGS 84 | `number` |

A reference to a record of another model has no kind, and that field gets no column.

### Roles

| Role | Meaning |
|---|---|
| `key` | The portal ID. A row with one updates that record. |
| `match` | The Local ID. A row with no portal ID updates the record in the dataset that has it. |
| `field` | A column read on import and written on export |
| `export` | A column written on export and ignored on import, such as `sample_name` |

### Groups

| Group | Section of the guide |
|---|---|
| `ids` | Identifying the record |
| `own` | About the type, which holds the type's own fields |
| `shared` | Shared by every sample or measurement: status and the location columns |

## The order of the columns

The columns come in this order:

1. The identifier columns: `portal_id`, `local_id` and `name`. A measurement also has `sample`, which is required, and `sample_name`, which has the role `export`.
2. The type's own fields, in the order the model declares them.
3. `status`, for a sample.
4. The location columns.

The `resource_fields` of the configuration narrow the schema. When it lists fields, an optional field that it leaves out gets no column. A field that a new record cannot be saved without keeps its column, and so do the identifiers. `exclude` removes optional fields in the same way. `status` and the location columns appear when `resource_fields` is empty or names them. The location columns read by the rules in [Location fields](location-fields.md).

## Which function builds which part

`build_table_schema` walks the order above and calls one function for each part:

- `identifier_columns` for the first group.
- `field_column` for each of the type's own fields. It asks `kind_of` for the field's kind, `is_required` for whether a new record needs it, `stored_range` for the range the field stores and `concept_choices` for the allowed values of a concept field, with `concept_definition` for what each value means.
- `location_columns` for the last group.
- `example_for` for the example of every column, with `number_example` for numbers. The example comes from the column's kind and constraints and never from a stored record.

## Widgets

A widget reads a cell into the value a model field stores and writes a stored value back as a cell. A value written by a widget is read back as the same value. A cell that cannot be read is refused with a message that names the problem, and django-import-export reports it on the row.

Two functions are the way in. `widget_for(column, dataset=None, user=None)` returns the widget of a column, and `Column.widget()` calls it. `render_cell(column, instance)` writes the cell of a record, in the form the widget reads.

### The widget of each kind

A kind with no widget gets the text widget. Subclass `CellWidget` to read a kind of cell of your own.

| Kind | Widget |
|---|---|
| `text`, `id` | `TextCellWidget` |
| `integer`, `number`, `latitude`, `longitude` | `NumberCellWidget` |
| `boolean` | `BooleanCellWidget` |
| `date`, `datetime`, `time` | `DateCellWidget` |
| `partial_date` | `PartialDateCellWidget` |
| `choice` | `ChoiceCellWidget` |
| `concept` | `ConceptCellWidget` |
| `quantity` | `QuantityCellWidget` |
| `sample` | `SampleCellWidget` |

### Cell forms

| Kind | An export writes | An import also reads |
|---|---|---|
| `date` | `2024-06-30` | `30.06.2024` |
| `datetime` | ISO 8601 in UTC with seconds, `2024-06-30T14:05:42Z` | A date and time with no zone, read in the active time zone |
| `time` | `14:05:42` | `14:05` |
| `boolean` | `yes` or `no` | `y`, `true`, `t`, `1`, `ja`, `x` and `✓` for yes, and `n`, `false`, `f`, `0` and `nein` for no |
| `partial_date` | `2024`, `2024-06` or `2024-06-30` | The same three forms |
| `concept` | The concept's preferred label | A label in any language, a code or the concept's web address |
| `quantity` | The number in the field's unit | A number, or a number and a unit that converts to the field's, such as `12 ppm` |
| `sample` | The sample's portal ID | A portal ID, or a Local ID or name in the dataset |

A spreadsheet's own date or time cell reads the same as its text. An empty cell reads as `None`.

A number is written with a point for decimals. A cell such as `12,5` is refused with the message that it uses a comma for decimals and should be written with a point, because a comma could also be a thousands separator. A number is refused too when it has more decimal places than the column allows, or lies outside the column's `minimum` and `maximum`.

A `sample` cell never reveals a sample the person importing may not see. A portal ID or Local ID that matches nothing visible is refused in the same words as one that does not exist.

## Import definitions

An import definition names a kind of file, the record type its rows fill and the formats it is offered in. FairDM builds one for every registered sample and measurement type, named after the model in lower case, such as `rocksample`. The built-in definitions offer the formats of the [`IMPORT_FORMATS`](settings.md#import_formats) setting that can import, by their lower-case titles, such as `csv` and `xlsx`. They are held by `ImportDefinitions`, in `fairdm.contrib.import_export.definitions`, and the portal's one instance is `import_definitions`. `register` and `get_definition` in the same module are its methods of those names. To add one of your own, see [How to register an import definition](../how-to/register-an-import-definition.md).

## The column guide

`<c-import.guide>` lays the columns out as one table for each group. A row shows the heading, whether the column is required, finds the record or is export only, what it holds, how to write it and an example.

| Prop | Type | What it takes |
|---|---|---|
| `schema` | `TableSchema` | The type's table schema, from `get_table_schema()` |

```html
<c-import.guide :schema="schema" />
```

## The Table Schema address

Every definition is published as a [Frictionless Table Schema](https://specs.frictionlessdata.io/table-schema/) at `table-schemas/<name>/`, where `<name>` is the definition's name. The address is open to everyone and answers with a JSON file. An unknown name answers `404`.

| | |
|---|---|
| View | `TableSchemaView` in `fairdm.contrib.import_export.views` |
| Route name | `table_schema` |
| Content-Disposition | `attachment; filename="<name>-table-schema.json"` |

The document has the type's `name`, a `title` and the `fields`, with `missingValues` set to the empty cell:

```json
{
  "name": "rocksample",
  "title": "Rock samples",
  "fields": [
    {
      "name": "portal_id",
      "title": "Portal ID",
      "type": "string",
      "constraints": {"unique": true}
    }
  ],
  "missingValues": [""]
}
```

Each field has a `name`, a `title`, a `type` and a `description`. The following keys appear when they apply:

- `constraints` with `required`, `unique`, `maxLength`, `minimum`, `maximum`, `enum` and, for a partial date, `pattern`.
- `format` set to `default` for a date, a date and time and a time.
- `trueValues` as `["yes"]` and `falseValues` as `["no"]` for a boolean.
- `unit` for a column with a unit.
- `readOnImport` set to `false` for a column that an import ignores.

Only the portal ID is `unique`, and the schema has no `primaryKey`, because a file of new records leaves the portal ID empty.
