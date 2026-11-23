# Research: the columns of a sample or measurement type

Run on 2026-11-23 against `main` at `eed6473e` (django-mvp 0.36.1, django-mvp-forms 0.11) and the
prototype branch `prototype-import-export`, read with `git show` and never merged.

## Assumptions checked

- **`ModelConfiguration.get_resource_class()` exists and answers for every registered type.** It
  does. The demo portal registers five sample types (`customparentsample`, `customsample`,
  `rocksample`, `soilsample`, `watersample`) and three measurement types (`examplemeasurement`,
  `xrfmeasurement`, `icp_ms_measurement`). `get_table_schema()` sits beside it (FR-001).
- **The generated resource has no identifiers.** Confirmed: `rocksample`'s resource reads `name`,
  the four location columns and its own fields, with no portal ID and no Local ID. `customsample`,
  whose configuration lists `resource_fields`, reads exactly that list. Nothing in the resource is
  changed by this feature (D10).
- **`resource_fields` is the configuration attribute the rule in FR-003 reads.** In
  `fairdm/registry/config.py` it is the field list for the import and export resource alone.
- **No `get_table_schema()` exists yet.** Confirmed on a registered configuration.
- **Only `Sample` has a status field** (`Sample.status`, a `ConceptField`). `Measurement` has none
  (D8). Both models carry `uuid` (`s` or `m` prefix), `local_id`, `location`, `location_elevation`
  and `location_uncertainty`.
- **A Frictionless validator is available.** `frictionless` resolves and installs with the project's
  Python 3.13 environment (checked with `uv pip install --dry-run frictionless`). It is added to the
  `dev` dependency group, so the test suite validates the served Table Schema and a file written in
  the columns' cell form with the standard validator rather than a copy of the published JSON
  Schema.
- **The suite runs on the host.** The host has no GDAL. A worktree's own `.venv` (`uv sync --group
  dev --locked`) run with the micromamba GDAL, GEOS and PROJ libraries and the shared test PostGIS
  on port 55515 passes `tests/test_registry/test_config.py` (106 passed).

## Planning notes, answered

- **N1 (the prototype).** Adopted. The prototype's behaviour is rebuilt test-first and its look is
  ported (N4).
- **N2 (the shared pieces).** Adopted, with one placement decision: the column model, the widgets,
  the import definitions and the guide all live in `fairdm/contrib/import_export/`, the app that
  already owns import and export, and `ModelConfiguration.get_table_schema()` calls the column model
  with a local import, the way `_component_class` imports the factories. The registry itself gains
  one method and no new import at module scope, so `fairdm.registry` keeps importing nothing from
  the contrib apps. `render_cell` is built here, beside the widgets (FR-007).
- **N3 (the pieces this feature does not build).** Adopted. Nothing for the import options form,
  the dataset-bound resource, the export menu or the workbook is written.
- **N4 (the look).** Adopted. The guide becomes the Cotton component
  `fairdm/templates/cotton/import/guide.html`, taking a table schema, and its stylesheet part moves
  into `fairdm/static/css/fairdm.css` as a section of its own. The house prefix for this area is
  `ie-` (import and export), renamed from `tx-`, and the colour variables the guide reads are
  declared once on the guide's root, as `.ov` declares the `--ov-*` ones. Features 040 and 041 reuse
  the prefix and add their own parts.
- **N5 (table roles on divs).** Adopted as decision D7, resolved in the plan: native table elements
  that keep their table roles explicitly, checked in Chrome's accessibility tree at both widths.
- **N6 (duplication to remove).** Adopted. `fairdm/utils/location/resources.py` already knows the
  four location columns. It gains `LOCATION_COLUMNS` and builds `location_fields()` from it, and the
  column model reads the names from there. The column model adds only what the guide needs on top of
  the names (label, description, range, example), which that module has no use for.
- **N7 (departures from the prototype).** Adopted: examples are made from kind and constraints
  (D4), the Table Schema lists every allowed value (D5), a sample the person may not see is refused
  as one that does not exist (D6), and the Table Schema's address depends on the type alone (D3).

## What the prototype provides and how it is rebuilt

| Prototype | Rebuilt as |
|---|---|
| `schema.py` `Column`, `TableSchema`, `schema_for`, `field_column`, `kind_of`, `location_columns`, `default_example` | `fairdm/contrib/import_export/schema.py`. `fill_examples` is not carried over: it read the first stored record (D4). `concept_choices` loses its 40-value cut. |
| `resources.py` widgets and `render_cell` | `fairdm/contrib/import_export/widgets.py`. `SampleWidget` refuses a sample the person may not see as one that does not exist (D6). The resource half (`CellField`, `build_resource`) is #697's and is not read here. |
| `definitions.py` | `fairdm/contrib/import_export/definitions.py`, without `resource()`, `export_rows()` and `definition_for_model()` (#697 and #696 add what they use) and without the `exports.FORMATS` import (see below). |
| `partials/guide.html`, the `tx-guide*` rules | `cotton/import/guide.html`, the `ie-guide*` rules. |
| `plugins.py` `ImportSchema` view | A plain view, `TableSchemaView`, at an address of the type's own (D3). |

The prototype's `exports.FORMATS` does not exist on `main`. A built-in definition's `formats` are the
names of the portal's `IMPORT_FORMATS` setting (`fairdm/conf/settings/addons.py`: CSV, TSV, XLS, XLSX
and ODS), the formats it reads. `IMPORT_EXPORT_FORMATS` also holds the export-only LaTeX, so it is
not used. The setting is read each time the definitions are asked for, never copied.

## What already exists

One line per new piece of code, the first place on the list where the search stopped.

| New piece | Where the search stopped |
|---|---|
| A way to read a number cell | New code. `import_export.widgets.FloatWidget` and `DecimalWidget` accept a decimal comma through Django's number localisation and give no range or places check, so a refusal with the point-written number is new code. `fairdm/utils/location/resources.py` `MeasureWidget` reads finite numbers only and is not reused: it has no range. |
| Boolean, date, time, partial date, choice, concept, sample, quantity cell widgets | New code on `import_export.widgets.Widget`, the package's own base. `BooleanWidget`, `DateWidget` and `ForeignKeyWidget` were read and do not refuse with a reason a person can act on or accept the forms the spec lists. |
| Which fields of a type a person can type into a file | This repo: `fairdm/utils/inspection.py` `FieldInspector.should_exclude_field`, the one rule for it. The prototype's `SKIPPED` set is not carried over. |
| The kind of a model field, the unit in a label, an example from a kind | New code. `kind_of` maps field classes to the spec's thirteen kinds, which nothing in the repo or in django-import-export does. The unit parse is one regular expression. `example_for` is a table of fixed examples. |
| `render_cell` and the text widget | New code on `import_export.widgets.Widget`. `CharWidget` was the candidate for text and does not strip, check the length or give a reason. |
| The four location columns' names | This repo: `fairdm/utils/location/resources.py`, made a constant there. |
| Latitude and longitude ranges | This repo: `fairdm/utils/location/forms.py` `LocationField` holds the rule. The column model takes -90 to 90 and -180 to 180 as written in the specification and the widget does not repeat `LocationField`'s other rules (they apply to the point as a whole, which is #697's). |
| Concept values of a field | `controlled_vocabularies.models.Record` filtered by `ConceptField.resolve_restriction()`, the package's own. |
| Quantity conversion | `quantityfield`'s `ureg` and `base_units` on the field, the package's own. |
| Which samples a person may see | This repo: `fairdm/core/managers.py` `visible_to(user)`. |
| The Frictionless Table Schema document | New code, a dict. `frictionless` is the validator in tests only: the served document is plain JSON and a portal needs no new runtime dependency to serve it. |
| An address and a view for the schema | New code: one `View` returning `JsonResponse`, mounted in `fairdm/contrib/import_export/urls.py`, which exists and registers no routes. |
| A registry of import definitions | New code, a module-level dict and three functions. Nothing in `fairdm/registry/` fits: the registry holds models and their configuration, and a project's own definition has no model registration. |
| The column guide | Cotton component, ported from the prototype. `c-import.guide` beside the components #697 adds under `cotton/import/`. |
| Guide stylesheet | `fairdm/static/css/fairdm.css`, a section of its own, ported. |
| Tags (`Required for new records`, `Finds the record`) | Ported with the guide as `ie-tag` rules. The daisyUI `badge` class was checked and is not used because the prototype's tag is the look to carry (a pill in the status colours). |

## Open points the plan settles

- The Table Schema's address: `table-schemas/<name>/`, the route named `table_schema`
  (`fairdm/conf/urls.py` includes `fairdm.contrib.import_export.urls` at the root with no
  namespace, as the other contrib apps are included). The plan, "The address", gives the rest.
- The guide's table markup (D7): the plan records the choice and how it was checked.
