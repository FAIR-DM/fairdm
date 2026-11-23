# Table schema

A registered sample or measurement type knows the columns of its import and export file. This page describes the table schema that holds them, the columns, the widgets that read and write their cells, the import definitions that name a kind of file, the guide component and the public address of the Frictionless Table Schema. For the tasks, see [How to register an import definition](../how-to/register-an-import-definition.md) and [How to import and export locations](../how-to/import-and-export-locations.md). The import formats are set by [`IMPORT_FORMATS`](settings.md#import_formats). The location columns are described in [Location fields](location-fields.md).

The names on this page are in `fairdm.contrib.import_export.schema`, `fairdm.contrib.import_export.widgets` and `fairdm.contrib.import_export.definitions`. Their docstrings give every argument.

## `ModelConfiguration.get_table_schema()`

Returns the type's `TableSchema`. The default builds it with `build_table_schema`. Override it to build your own.

```python
from fairdm.registry import registry

schema = registry.get_for_model(CoreSample).get_table_schema()
schema.headings  # ["portal_id", "local_id", "name", "depth_m", ..., "status", "latitude", ...]
```

## `TableSchema`

Every column of one record type's file, in order.

| Attribute | Type | What it holds |
|---|---|---|
| `model` | `type` | The sample or measurement model |
| `config` | `ModelConfiguration` | The configuration the schema was built from |
| `columns` | `list[Column]` | The columns, in the order a file has them |

| Property or method | Returns |
|---|---|
| `kind` | `sample` or `measurement` |
| `slug` | The model's lower-case name, which names the Table Schema and the definition |
| `name` | The type's plural name, capitalised, in the active language |
| `singular` | The name of one record, in the active language |
| `importable` | The columns read on import, which are all but those with the role `export` |
| `required` | The columns a new record needs a value in |
| `headings` | The name of every column, in order |
| `get(name)` | The column with that name, or `None` |
| `groups()` | A `(key, title, columns)` triple for each group that has columns |
| `as_frictionless()` | The Frictionless Table Schema as a `dict` |

## `Column`

One column of a type's file.

| Attribute | Type | Default | What it holds |
|---|---|---|---|
| `name` | `str` | — | The heading an export writes. It is the model field's name and is never translated. |
| `label` | `str` | — | What the column is called on screen |
| `kind` | `str` | — | How its cells are read. See [Kinds](#kinds). |
| `role` | `str` | `"field"` | What the column is for. See [Roles](#roles). |
| `required` | `bool` | `False` | Whether a new record needs a value |
| `description` | `str` | `""` | What goes in it, which is the model field's help text unless set |
| `attribute` | `str` or `None` | `None` | The model attribute it fills |
| `model_field` | `Field` or `None` | `None` | The model field behind it |
| `unit` | `str` | `""` | The unit numbers are given in |
| `allowed` | `list[tuple[str, str]]` | `[]` | For a list, `(value, meaning)` pairs. The value is what a cell holds. |
| `max_length` | `int` or `None` | `None` | The most characters a text cell may hold |
| `decimals` | `int` or `None` | `None` | The most decimal places a number may have |
| `minimum` | `float` or `None` | `None` | The smallest number allowed |
| `maximum` | `float` or `None` | `None` | The largest number allowed |
| `example` | `str` | `""` | A value as a cell would hold it |
| `aliases` | `list[str]` | `[]` | Other headings the column is recognised by |
| `group` | `str` | `"own"` | Which part of the guide it belongs to. See [Groups](#groups). |

| Property or method | Returns |
|---|---|
| `widget(dataset=None, user=None)` | The widget that reads and writes the column's cells |
| `as_frictionless()` | The column as a field of a Frictionless Table Schema |
| `kind_label` | What the kind is called on screen |
| `importable` | `False` for a column written on export only |
| `shown_aliases` | The aliases worth listing, without the heading or label again |
| `format_hint` | How a cell is written, in a few words |

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

`kind_of(model_field)` returns the kind of a model field. It returns an empty string for a reference to a record of another model, and that field gets no column.

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

## Building a schema

### `build_table_schema(config)`

Works out the columns of a type from its `ModelConfiguration`. Nothing is read from the type's own table, so a stored record and who may see it never change the result. Only the vocabularies that a concept column lists are queried.

The columns come in this order:

1. The identifier columns.
2. The type's own fields, in the order the model declares them.
3. `status`, for a sample.
4. The location columns.

The `resource_fields` of the configuration narrow the schema. When it lists fields, an optional field that it leaves out gets no column. A field that a new record cannot be saved without keeps its column, and so do the identifiers. `exclude` removes optional fields in the same way. `status` and the location columns appear when `resource_fields` is empty or names them.

### `identifier_columns(model, is_measurement)`

Returns the columns every type starts with: `portal_id`, `local_id` and `name`. A measurement also gets `sample`, which is required, and `sample_name`, which has the role `export`.

### `field_column(model_field, role="field", group="own", description=None, aliases=())`

Builds the column for one model field. The label is the field's verbose name. A unit in brackets at the end of the label, such as `Weight (grams)`, becomes the column's `unit`. The column also takes its length, decimal places and minimum from the field, its choices as `allowed` and an example from `example_for`.

### `is_required(model_field)`

Says whether a new record cannot be saved without a value in the field. It is false for a field that may be blank, a nullable field that is not a `CharField`, a field with a default and a `BooleanField`.

### `example_for(column)`

Makes an example cell from a column's kind and constraints. The example never comes from a stored record, because a record may be private and the example is shown to people who may not see it. A column with a list uses its first value.

### `number_example(column)`

Makes an example number that lies inside the column's range and decimal places. It is what `example_for` gives a column of kind `integer`, `number` or `quantity`.

### `concept_choices(model_field)`

Lists the `(preferred label, definition)` pairs that a concept field allows. The value is the preferred label, which is the same in every language.

### `concept_definition(record)`

Returns a concept's definition, or an empty string when it has none.

### `location_columns(is_measurement, declared)`

Builds `latitude`, `longitude`, `location_elevation` and `location_uncertainty`. All four appear when `declared` is empty or names `location`. Otherwise only the elevation or uncertainty that is named appears, with the latitude and longitude it needs. For the rules these columns read by, see [Location fields](location-fields.md).

## Widgets

A widget reads a cell into the value a model field stores and writes a stored value back as a cell. A value written by a widget is read back as the same value. A cell that cannot be read is refused with a message that names the problem, and django-import-export reports it on the row.

### `CellWidget`

The base class of every widget, over `import_export.widgets.Widget`. It keeps the `column` whose cells the widget reads and writes, and it treats a missing value, an empty string and text of only spaces as an empty cell. Subclass it to read a kind of cell of your own.

### `widget_for(column, dataset=None, user=None)`

Returns the widget for the column's kind. A kind with no widget gets the text widget. `dataset` and `user` matter to the `sample` kind only.

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

### `render_cell(column, instance)`

Writes one column of one record as the cell an export holds. The `portal_id` column gives the record's portal ID. The `sample_name` column gives the sample's name. The latitude and longitude columns give the point's coordinates. Any other column gives its attribute as its widget writes it.

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

An import definition names a kind of file, the record type its rows fill and the formats it is offered in. FairDM builds one for every registered sample and measurement type, named after the model in lower case, such as `rocksample`.

### `ImportDefinition`

A frozen dataclass.

| Attribute | Type | What it holds |
|---|---|---|
| `name` | `str` | The name pages and addresses know the definition by. It is a slug. |
| `model` | `type` | The registered sample or measurement model its rows fill |
| `formats` | `tuple[str, ...]` | The names of the file formats it is offered in |

| Property or method | Returns |
|---|---|
| `kind` | `sample` or `measurement` |
| `table_schema()` | The table schema of the registered model, from its configuration's `get_table_schema()` |

### `register(definition)`

Adds a project's own definition and returns it. It raises `ValueError` when a definition of that name exists or when the model is not registered.

### `definitions(kind=None)`

Lists the definitions, the built-in ones first. `kind` set to `sample` or `measurement` keeps only that kind.

### `get_definition(name)`

Returns the definition with that name, or `None`.

### `built_in()`

Builds one definition for each registered type, samples first, named by the model's lower-case name.

### `import_format_names()`

Returns the lower-case title of each format in the [`IMPORT_FORMATS`](settings.md#import_formats) setting that can import.

### `IMPORT_FORMATS`

The built-in definitions offer the formats of the [`IMPORT_FORMATS`](settings.md#import_formats) setting that can import, by their lower-case titles, such as `csv` and `xlsx`.

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
