# Implementation Plan: the columns of a sample or measurement type

**Branch**: `039-table-columns` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

`fairdm.contrib.import_export` gains four modules and a component. `schema.py` works out a type's
table schema (its `Column`s, in order) from the model and its configuration each time it is asked
for. `widgets.py` holds one django-import-export widget per kind of column and `render_cell`, the
cell an export writes. `definitions.py` is the lookup of import definitions by name.
`views.py` serves a type's table schema as a Frictionless Table Schema. The column guide is the
Cotton component `c-import.guide`. `ModelConfiguration.get_table_schema()` is the one new method on
the registry.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-cotton components,
  django-import-export widgets.
- **New dependencies**: `frictionless` in the `dev` dependency group only, to validate the served
  Table Schema in tests. No runtime dependency.
- **Storage**: none. A table schema is worked out from the model on every request. No model, no
  migration.
- **Testing**: pytest with pytest-django against PostGIS, from the worktree's own `.venv`. Tests sit
  in `Test<Subject>` classes in the module that mirrors the source file. No test of wording or
  layout.

## Constitution Check

- **Simplicity**: no model and no setting. One method on the configuration, four small modules, one
  component, one view.
- **Privacy first**: examples come from a column's kind and constraints, never a stored record (D4).
  The sample widget refuses a sample the person may not see exactly as one that does not exist (D6).
  The only vocabulary data the Table Schema lists is the portal's public vocabularies and choices.
- **Established packages over custom code**: the widgets extend django-import-export's `Widget`, the
  concept lists are `controlled_vocabularies`' records, units are `quantityfield`'s registry, the
  validator in tests is `frictionless`. What is written is what none of them does: a refusal with a
  reason a person can act on, and the column model that ties them to a type.
- **Works without custom JavaScript**: the guide is plain HTML.

## What is ported

From `prototype-import-export`, read with `git show origin/prototype-import-export:<path>`:

| Prototype | Lands on `main` as |
|---|---|
| `fairdm/contrib/tabular/templates/tabular/partials/guide.html` | `fairdm/templates/cotton/import/guide.html`, taking `schema` (a table schema). Markup, copy and the order of each cell are copied. Changes: the `tx-` classes become `ie-`, the table elements are native (D7, below), the sentences are split so each is one translation call, and "Finds the record" is one branch. |
| `tabular.css` lines 151-153 (`.tx-tag` and its two variants), 53-60 (`.tx-dim`, `.tx-code`, `.tx-code--example`) and 171-201 (`.tx-guide*`, `.tx-alias`, `.tx-allowed*`) | `fairdm/static/css/fairdm.css`, a section headed "Import and export", `tx-` renamed to `ie-`. The `--tx-*` variables the guide reads (`--tx-line`, `--tx-muted`, `--tx-faint`, `--tx-skip`) become `--ie-*`, declared on `.ie` the way `.ov` declares `--ov-*`, with the same values. |

The look is a port and is checked at the merge gate side by side with the prototype's screen
("Import page and guide") at 390 and 1400 wide, with the guide component rendered for `soilsample`
standing in for the page until #697 places it there.

## The column model: `fairdm/contrib/import_export/schema.py`

`Column` is a dataclass: `name`, `label`, `kind`, `role` (`key` for the portal ID, `match` for the
Local ID, `field`, `export` for the sample's name), `required`, `description`, `attribute`,
`model_field`, `unit`, `allowed` (a list of `(value, meaning)`), `max_length`, `decimals`,
`minimum`, `maximum`, `example`, `aliases`, `group` (`ids`, `own`, `shared`). It keeps the
prototype's properties `kind_label`, `importable`, `shown_aliases` and `format_hint`, and adds:

- `widget(dataset=None, user=None)`: the widget that reads and writes this column's cells, from
  `widgets.widget_for`, imported inside the method.
- `as_frictionless()`: this column as a Frictionless field (below).

`TableSchema` keeps `model`, `config`, `columns`, `kind`, `slug`, `name`, `singular`, `importable`,
`required`, `headings`, `get`, `groups`, and `as_frictionless()`. Matching a file's headings to
columns (`match`, `keys` and the prototype's `normalise`) is #697's and is not ported here
(spec Boundary). `shown_aliases` leaves out an alias that equals the heading or the label, compared
case-insensitively.

**Building it.** `build_table_schema(config)` follows the prototype's `schema_for`, with these
changes, each a requirement of the specification:

1. The model and the declared `resource_fields` come from the configuration it is given, not a
   registry lookup, so a configuration that overrides `get_table_schema()` and calls the default
   works. `resource_fields` is read through `flatten_fields`, which already unfolds the list's
   groupings. A name in the configuration's `exclude` is never an own-field column, unless it is a
   field a new record cannot be saved without (every generated component drops `exclude`, and a
   file must stay saveable). Recorded as decision D11.
2. The type's own fields are its concrete fields that are not concrete fields of the base `Sample` or
   `Measurement` and for which `FieldInspector(model).should_exclude_field(name)`
   (`fairdm/utils/inspection.py`, the repo's one rule for fields a person can enter) is false. The
   prototype's `SKIPPED` set is not carried over. The model's `uuid` is offered as the `portal_id`
   column. `status` is read from `Sample` only (D8). A type's own foreign key to another model has
   no kind and is not a column yet (decision D12).
3. `status` and the four location columns appear when `resource_fields` is empty or names them. The
   location columns are named by `fairdm.utils.location.resources.LOCATION_COLUMNS`. A declared
   `location` in `resource_fields` names all four, and a declared `status` names the status column.
   The location columns come as a set: naming `location` in `resource_fields` gives all four, and
   `location_elevation` or `location_uncertainty` named alone gives that column and the
   latitude and longitude it needs.
4. Examples are made by `example_for(column)` from the column's kind and constraints (the first
   allowed value for a list, a value inside the range for a number, a fixed text for the rest). The
   prototype's `fill_examples` and its stored-record read are removed, and no code path in the
   module queries the type's own table (FR-006).
5. A concept column's `allowed` holds every value (no cut, no `allowed_total`). `allowed` entries
   hold the record's `pref_label` as the value, never `str(record)`, which is the label in the
   active language, so the list, the Table Schema's `enum` and the cell an export writes do not
   change with the portal's language. The meaning is the concept's definition. The guide cuts a long list to its first 40 on display only (`allowed|slice:":40"` with a
   count, see "The column guide").
6. `is_required(field)` is false for a field with `blank=True`, for a nullable field that is not a
   `CharField`, for one with a default and for a `BooleanField`, and true otherwise, as the
   prototype has it. It is what makes "a field a new record cannot be saved without".
7. `Column.unit` comes from a unit in brackets at the end of the label (the prototype's
   `UNIT_IN_LABEL`) or the quantity field's base unit. The label without the bracket is one of the
   recognised headings.
8. Locale: labels, descriptions and hints are lazy translations, read at the time a page or the
   Table Schema is built. `Column.name` is the model field's name and is never passed through a
   translation call.

**`ModelConfiguration.get_table_schema()`** in `fairdm/registry/config.py`:

```python
def get_table_schema(self) -> "TableSchema":
    """Return the columns of this type's file. Override to build your own."""
    from fairdm.contrib.import_export.schema import build_table_schema

    return build_table_schema(self)
```

It validates nothing and caches nothing (it is read per request and the vocabularies it reads can
change). `get_table_schema` is not a `COMPONENTS` row because it builds a plain object, not a class.

`fairdm/utils/location/resources.py` gains `LOCATION_COLUMNS = ("latitude", "longitude",
"location_elevation", "location_uncertainty")` and `location_fields()` is built from it (N6).

## The widgets: `fairdm/contrib/import_export/widgets.py`

One widget per kind, each `__init__(self, column, ...)` over `import_export.widgets.Widget` with
`clean(value, row=None, **kwargs)` returning the value the field stores and `render(value,
obj=None, **kwargs)` returning the cell. All refusals are `ValueError` with a lazy-translated reason
(import-export turns a `ValueError` into a row error), never a bare exception.

| Kind | Widget | Notes |
|---|---|---|
| `text`, `id` | `TextCellWidget` | Strips; refuses over `max_length` with the length; an empty cell on a nullable field is `None`. |
| `integer`, `number`, `latitude`, `longitude` | `NumberCellWidget` | A decimal comma is refused with the number written with a point. A non-finite number (`nan`, `inf`) is refused, as `MeasureWidget` does. Range from the column. `Decimal` column: more decimal places than `decimals` is refused. Spreadsheet floats that are whole numbers read as whole numbers. |
| `boolean` | `BooleanCellWidget` | yes/no, true/false, 1/0 (and `ja`, `nein`). Anything else refused. |
| `date`, `datetime`, `time` | `DateCellWidget` | A spreadsheet's own date or datetime object reads the same as text. Text: ISO forms (a minute-precision `YYYY-MM-DD HH:MM` and `HH:MM` too) and `DD.MM.YYYY`. A naive cell is read in the active time zone. `render` writes a date as `YYYY-MM-DD`, a datetime as ISO 8601 with seconds in UTC (`YYYY-MM-DDTHH:MM:SSZ`) and a time as `HH:MM:SS`, so a stored value with seconds reads back to the same value. Refusal names the form. |
| `partial_date` | `PartialDateCellWidget` | `YYYY`, `YYYY-MM`, `YYYY-MM-DD`; returns the string `partial_dates` stores. |
| `choice` | `ChoiceCellWidget` | By stored value or its meaning, case-insensitive. Refusal lists up to 8 values. |
| `concept` | `ConceptCellWidget` | By label in any language, code or URI. The lookup is built once per widget. Empty vocabulary: refused with a reason. |
| `sample` | `SampleCellWidget(column, dataset, user)` | Order: portal ID among `Sample.objects.visible_to(user)` (any dataset); then Local ID in the dataset; then the name in the dataset. All three lookups read one queryset, `Sample.objects.visible_to(user)`, where `None` means a visitor (`fairdm/core/managers.py`): the portal ID across it, then the Local ID, then the name, within `.filter(dataset=dataset)`. A sample the person may not see, and a portal ID nobody holds, raise the same message (D6). Duplicate Local ID or name in the dataset: the message asks for the portal ID. |
| `quantity` | `QuantityCellWidget` | A bare number is in the column's unit. A number and a unit is converted with `ureg`. An unconvertible unit is refused. |

`widget_for(column, dataset=None, user=None)` returns the widget for `column.kind`.
`render_cell(column, instance)` is the cell an export writes: the portal ID (`uuid`), the sample's
name, the point's latitude or longitude, or the attribute through its widget.

The prototype's `SampleWidget` and the registry-generated resource stay out of reach of these
widgets (D10): `fairdm.contrib.import_export.resources.SampleWidget` is unchanged.

## The import definitions: `fairdm/contrib/import_export/definitions.py`

```python
@dataclass(frozen=True)
class ImportDefinition:
    name: str
    model: type
    formats: tuple[str, ...]     # the names of settings.IMPORT_FORMATS when built in
    kind (property)              # "sample" or "measurement"
    def table_schema(self)       # registry.get_for_model(self.model).get_table_schema()
```

`register(definition)` raises `ValueError` for a name already known (built-in or added) and for a
model that is not registered (the public Table Schema route reads the model's configuration).
`definitions(kind=None)` and `get_definition(name)` (returns `None` for an unknown name).
The formats are `settings.IMPORT_FORMATS`, the formats the portal reads, not
`IMPORT_EXPORT_FORMATS`, which holds the export-only LaTeX. Built-in definitions are built from `registry.samples` and
`registry.measurements` on each call, named by `model._meta.model_name`, so a portal's type has one
with no work. `ImportDefinition.columns()` is not carried over: `table_schema()` is the name the
specification uses.

## The Table Schema: `as_frictionless`, the view, the address

`Column.as_frictionless()` and `TableSchema.as_frictionless()` as the prototype, with these changes:

- `enum` lists every `allowed` value, always (D5).
- `format`: `default` for `date`, `datetime` and `time`, which is what `render_cell` writes (see the
  widgets), so a file in the cell form validates (FR-018). `boolean` carries
  `trueValues: ["yes"]` and `falseValues: ["no"]`. `partial_date` carries a `pattern` constraint
  `^\d{4}(-\d{2}(-\d{2})?)?$`.
- The column written on export only carries `"readOnImport": false` (a custom descriptor property
  the standard permits) as well as the sentence in its description, so a machine can see it.
- `unit` is a custom property as in the prototype. `title` and `description` are strings in the
  active language. `name` never changes with the language.
- `primaryKey: ["portal_id"]` and `missingValues: [""]` as the prototype.

The view is `TableSchemaView(View)` in `fairdm/contrib/import_export/views.py`:
`get(request, name)` looks the definition up with `get_definition(name)`, answers 404 (`Http404`) for
`None`, and otherwise returns `JsonResponse(definition.table_schema().as_frictionless(),
json_dumps_params={"indent": 2})` with `Content-Disposition: attachment;
filename="<name>-table-schema.json"`. No login, no permission. The route is
`path("table-schemas/<slug:name>/", TableSchemaView.as_view(), name="table_schema")` in
`fairdm/contrib/import_export/urls.py`.

**The address.** It depends on the type's name alone. A registered type's definition name is its
model name, which the registry already assumes is unique.

## The column guide

`fairdm/templates/cotton/import/guide.html`, `<c-import.guide :schema="schema" />`. One `<section>`
(`ie-guide`) with one group per `schema.groups`: a heading and a table.

**D7, the table markup, decided.** Each group is a native `<table>` with a `<caption>`, a `<thead>`
with `<th scope="col">` and a `<tbody>` of `<tr>` rows whose first cell is a `<th scope="row">` (the
heading). To keep the prototype's look, the rows are laid out as a grid at wide widths and stacked
below 1024px with CSS, and the table elements carry explicit ARIA roles
(`role="table"`, `rowgroup`, `row`, `columnheader`, `rowheader`, `cell`), because Safari and older
Chrome drop table semantics from an element whose `display` is changed. The build checks the result
twice: a test that each group renders one table with its column headers, and a read of Chrome's
accessibility tree at 390 and 1400 wide that finds a table with column headers for every group. The
decision and the result are recorded in `decisions.md` at S5 (SC-005, task T010).

**Long lists.** `<details>` with the first 40 values and the total, in the component, never in the
column. The Table Schema lists them all.

Props: `schema:TableSchema`. Slots: none. The component is the whole guide, so the import page
(#697) places it and passes the schema.

## Dependencies and settings

`pyproject.toml`: `frictionless` (>=5,<6) in the `dev` dependency group, then `uv lock` and
`uv sync --group dev --locked`. No `INSTALLED_APPS` change.

## Specifications and documents edited

- `specs/039-table-columns/` itself (`decisions.md` gains D11 onward as the build decides).
- `docs/`: a developer reference page for the table schema, the import definitions and the Table
  Schema address, and a how-to for registering an import definition. Placement follows the existing
  `docs/developers/` layout, found when the page is written.
- `CHANGELOG.md`: one line under Unreleased.

## Tests

Mirroring the source tree:

- `tests/test_contrib/test_import_export/test_schema.py`: `TestColumnOrder` (FR-002, scenarios 1-3),
  `TestResourceFieldsRule` (FR-003), `TestColumnContents` (FR-004, 005, scenario 4 and 5),
  `TestExamples` (FR-006, with a stored private record whose value must not appear), a concept
  column's allowed values equal under two languages,
  `TestLocationColumns`, `TestPortalConfig` (FR-015, a registered type with no work).
- `tests/test_registry/test_config.py`: `TestGetTableSchema` (FR-001: it is there, it can be
  overridden).
- `tests/test_contrib/test_import_export/test_widgets.py`: `TestRoundTrip` (SC-002, one case per
  kind, the datetime and time cases with non-zero seconds), `TestRefusals` (FR-008, including a `nan` latitude), `TestConceptWidget`, `TestSampleWidget` (FR-010, the same message
  for unseen and absent, with `user=None` too, duplicates), `TestQuantityWidget`.
- `tests/test_contrib/test_import_export/test_definitions.py`: `TestLookup`, `TestRegister`
  (FR-011-013).
- `tests/test_contrib/test_import_export/test_views.py`: `TestTableSchemaView` (FR-016, 017, a
  valid Frictionless Schema, Content-Type `application/json` and the Content-Disposition file name,
  anonymous access, 404, language).
- `tests/test_contrib/test_import_export/test_schema.py`, `TestFrictionlessValidation` (SC-003: every
  registered type's schema is valid, parametrised over `registry.samples` and
  `registry.measurements`, a file written by `render_cell` validates, a file of new records with an
  empty portal ID validates, a file outside the range fails).
- `tests/test_templates/test_import_guide.py`: `TestGuideComponent` (one table per group with column
  headers, required and key tags by column, the long list cut on display only, the example, and
  one render over every registered type).

## Risks

- **A concept column queries the vocabulary on every build.** The guide and the Table Schema read it
  on each request. The vocabularies are small in the demo portal and the Table Schema is a download.
  A cache is not added until a measurement says it is needed.
- **`frictionless` rejects a custom descriptor property.** If the validator refuses `unit` or
  `readOnImport`, they move into `description` text and the machine-readable flag is dropped, and
  this is recorded as a decision.
- **Column names of a project's own `resource_fields` can name a field that is not a model field.**
  The registry already validates these at registration, so the column model reads them as given.
