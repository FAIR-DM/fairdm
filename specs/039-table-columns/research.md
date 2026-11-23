# Research: the columns of a sample or measurement type

The full investigation is done when the feature is planned. This file holds, for now, what the
specification assumes already works, run against `main` before the specification was put up for
review.

## Assumptions checked

Run on 2026-11-23 against the demo portal, on a checkout whose registry, core models and
`fairdm/contrib/import_export/` are identical to `main` at `eed6473e`.

- **`ModelConfiguration.get_resource_class()` exists and answers for every registered type.** It
  does. The demo portal registers five sample types (`customparentsample`, `customsample`,
  `rocksample`, `soilsample`, `watersample`) and three measurement types (`examplemeasurement`,
  `xrfmeasurement`, `icp_ms_measurement`). `get_table_schema()` sits beside it (FR-001).
- **The generated resource has no identifiers.** Confirmed: `rocksample`'s resource reads `name`,
  the four location columns and its own fields, with no portal ID and no Local ID. `customsample`,
  whose configuration lists `resource_fields`, reads exactly that list. This is the gap the
  specification describes under "What exists". Nothing in the resource is changed by this feature
  (decisions D10).
- **`resource_fields` is the configuration attribute the rule in FR-003 reads.** It is, in
  `fairdm/registry/config.py`, documented as the field list for the import and export resource
  alone.
- **No `get_table_schema()` exists yet.** Confirmed on a registered configuration.
- **Only `Sample` has a status field.** `Sample.status` is a concept field in
  `fairdm/core/sample/models.py`. `Measurement` has none (decisions D8).
- **Both samples and measurements carry `local_id` and a location.** Confirmed in both models.
- **A Frictionless validator is available to test FR-017 and FR-018.** It is not: the `frictionless`
  package is not installed in the development environment. The build either adds it as a test-only
  dependency or validates against the Table Schema specification's published JSON Schema. This is a
  planning choice, recorded here so it is not found mid-build.
