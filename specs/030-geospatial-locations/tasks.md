# Tasks: capture, store and query locations as geospatial data

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [sketch.md](sketch.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code that
makes them pass is written. Pages are tested through the test client on the real routes, forms
through the real form classes. Wording and appearance get no tests.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, then US3 and US2, then US4, US5 and US6, each from the previous story's
accepted commit.

## Phase 1: US-1, a researcher records where a sample was taken (P1)

This story also carries the foundation every other story reads: the fields, the removal of
`Point`, and the input. The prototype's Python code on this branch is replaced, not extended: the
approved templates and copy stay, and every line behind them is rewritten test first. The
prototype's `options` handling and the demo seeds that use it go.

- [ ] T001 [US1] `tests/test_contrib/test_location/test_forms.py`, `TestParseCoordinate`: decimal
  degrees, degrees and decimal minutes, and degrees, minutes and seconds, with symbols or spaces,
  with a hemisphere letter or word in front or behind, all read to the same value within 1e-5
  degrees (SC-001). A latitude beyond 90, a longitude beyond 180, a latitude ending in E or W, a
  longitude ending in N or S, minutes written with `m`, and unreadable text are refused.
- [ ] T002 [US1] `tests/test_contrib/test_location/test_forms.py`, `TestLocationField`: a full
  field cleans decimal degrees in 4326 to that point. EPSG 25832 northing and easting convert to the
  point GDAL gives within one metre (SC-001). An unknown code, one coordinate without the other, an
  elevation or uncertainty with no coordinates, a negative uncertainty, and a projected result
  outside WGS 84 are refused, each with a message. All empty cleans to `None`. A point-only field
  takes no reference system, elevation or uncertainty. `decompress` gives back decimal degrees for a
  stored location (AS 1.10).
- [ ] T003 [US1] `tests/test_core/test_sample/test_models.py`, `TestSampleLocation`: the database
  refuses an elevation or uncertainty without a location, and a negative uncertainty. Two samples at
  the same coordinates are changed independently (AS 1.7, SC-002). Clearing the location with the
  form clears the elevation and uncertainty (AS 1.8). Deleting a sample leaves nothing behind.
- [ ] T004 [US1] `tests/test_core/test_sample/test_forms.py`: replace the two existing tests that
  expect a `ModelSelect2Widget` for the location with tests that the location input is a
  `LocationField` when the type's fields list `location`, and absent when they do not (FR-009).
  The sample edit page saves a location typed in each notation and in a projected system, and
  refuses each case of FR-008 without saving (AS 1.1 to 1.6).
- [ ] T005 [US1] `tests/test_core/test_sample/test_plugins.py` and
  `tests/test_templates/test_cards.py`: the sample page gives latitude and longitude to five places
  and the elevation and uncertainty where recorded (AS 1.9). Change the existing tests that build a
  `PointFactory` to pass a point, keeping what they assert.
- [ ] T006 [US1] Add `lat-lon-parser` to `pyproject.toml` and `uv.lock`. Write
  `LocatedRecord` (plan D1), apply it to `Sample` and `Measurement`. Move the contributor's
  location to `Organization.location` and point `RORTransform.import_location`, `as_geojson` and
  the ROR export at it (plan D2), because `Point` cannot be dropped while a contributor refers to
  it. Write the migrations: sample and measurement fields, the contributor and organization change,
  then `fairdm_location` `0002` deleting `Point`. Each foreign key that becomes a point is a
  `RemoveField` then an `AddField`, never an `AlterField`. The geography indexes are listed in each
  model's own `Meta.indexes` (plan D1). Squashed later at convergence.
- [ ] T007 [US1] `parse_coordinate`, `Location`, `LocationField`, `LocationWidget`,
  `LocationFormMixin` and the widget template (plan D3). Wire `SampleFormMixin`. The template is the
  approved one, reading its systems from a `json_script` element.
- [ ] T008 [US1] Remove `Point` and everything around it (plan D7, D8): model, views, URLs,
  plugin, address declaration, admin, `utils.py`, the old form and widgets, the location templates,
  the three settings, `PointFactory`, and `tests/test_contrib/test_location/test_views.py`. Change
  every other reference listed by `git grep -n -E "Point\b|PointFactory|fairdm_location\.Point|location\.latitude|location\.longitude|FAIRDM_(CRS|X_COORD|Y_COORD)"`
  across `fairdm/`, `demo/` and `tests/` to the new fields, keeping what each test asserts. Also
  `select_related("location")` in `fairdm/core/sample/managers.py`,
  `select_related("sample__location")` in `fairdm/contrib/collections/views.py`, and the location
  in `autocomplete_fields` in `fairdm/core/sample/admin.py`, none of which the grep finds.
- [ ] T009 [US1] `c-card.location` with `elevation` and `uncertainty`, and the sample overview
  passing them (plan D7).
- [ ] T010 [US1] Docs: `docs/portal-development/locations.md` with the fields and the input,
  linked from the table of contents. `CONTEXT.md` Location and Reference system. Changelog entries
  for the new fields and every removal. FS-005 edited where it describes a sample's location.

## Phase 2: US-3, a researcher records where a measurement was made (P2)

- [ ] T011 [US3] `tests/test_core/test_measurement/test_forms.py` and `test_plugins.py`: a
  measurement type listing `location` gets the input, one that does not gets none. A location typed
  on the measurement form is saved like a sample's (AS 3.1). The page shows the measurement's own
  location as its own (AS 3.2), its sample's as the sample's when the viewer may open the sample
  (AS 3.3), and none when the viewer may not (AS 3.4, FR-014). Changing the sample's location
  leaves the measurement's own unchanged (AS 3.5).
- [ ] T012 [US3] `MeasurementFormMixin` on `LocationFormMixin`. `Measurement.effective_location_for`
  and `MeasurementQuerySet.with_effective_location` (plan D5). The measurement overview template as
  approved. The XRF registration in the demo lists `location`.
- [ ] T013 [US3] Docs: the measurement's own location and its effective location on the locations
  page. FS-018 edited where it describes a measurement's location.

## Phase 3: US-2, a portal developer finds records by where they are (P1)

- [ ] T014 [US2] `tests/test_contrib/test_location/test_managers.py`: for samples and for
  organizations, `inside` with a box and with a polygon returns exactly the records inside, edge
  included (AS 2.1, 2.2, 2.7). `within_distance` returns exactly those within the distance, in
  metres and in `D(km=...)`, checked at the equator and at 70° N (AS 2.3). `nearest` orders by
  distance and carries it (AS 2.4). Each combines with `visible_to()` (AS 2.8).
- [ ] T015 [US2] Same file, measurements: own location wins (AS 2.6), the sample's location is used
  when the measurement has none (AS 2.5) only for a viewer who may open the sample (AS 2.8, SC-004).
- [ ] T016 [US2] Same file, `TestQueryPlan`: with 2,000 located samples and `ANALYZE` run, the plan
  of `inside` and of `within_distance` uses an index scan, not a sequential scan of the sample table
  (SC-005, FR-020). The same for organizations, and for each branch of the measurement `inside`.
- [ ] T017 [US2] `tests/test_contrib/test_location/test_coverage.py` and
  `tests/test_core/test_dataset/test_models.py`, `tests/test_core/test_project/test_models.py`: a
  dataset's coverage holds every location and is `None` with none (AS 2.9). Locations within 5° of
  the 180th meridian on both sides give a box less than 10° wide with `west > east` (AS 2.10,
  SC-006). A project's coverage holds its datasets' locations (AS 2.11). Records the viewer may not
  open do not count, measurements placed by a hidden sample included (FR-023). Replace the existing
  `bbox` test.
- [ ] T018 [US2] `LocatedQuerySet`, the measurement lookups and `coverage.py` (plan D4 to D6). The
  geography cast index in `LocatedRecord`. `Dataset.spatial_coverage` and
  `Project.spatial_coverage`. `Dataset.bbox` removed.
- [ ] T019 [US2] The collection tables: `MeasurementTable` on the effective location, the
  collections view annotating it, the table factory leaving out geometry fields. Tests in
  `tests/test_contrib/test_collections/test_tables.py`: latitude under Latitude, longitude under
  Longitude, no location link column, a measurement row showing its effective location, and
  sorting the table by another column still answering. Change the
  existing tests that expect the location column, keeping what else they assert.
- [ ] T020 [US2] Docs: the lookups and the spatial coverage on the locations page, with examples
  that run. `CONTEXT.md` Spatial coverage.

## Phase 5: US-4, a developer's script reads a record's location from the API (P2)

- [ ] T023 [US4] `tests/test_api/test_viewsets.py` and `test_schema.py`: a sample returns a GeoJSON
  point, longitude first, with the elevation third where there is one and `location_uncertainty`
  beside it (AS 4.1 to 4.3). A sample with none and a measurement with no location of its own
  return `null` (AS 4.4, 4.5). An organization returns its point (AS 4.6). A person returns no
  location (AS 4.7). The schema describes the field as a GeoJSON point. A create or partial change
  that sends a location or an uncertainty leaves the stored location as it was. Change the existing
  `located sample` case to pass a point.
- [ ] T024 [US4] `GeoJSONPointField` and the serializer fields (plan D9).
- [ ] T025 [US4] Docs: the API shape on the locations page and the API page. FS-011 edited.

## Phase 6: US-5, a researcher imports and exports locations with their samples (P2)

- [ ] T026 [US5] `tests/test_contrib/test_import_export/test_resources.py`: export writes the four
  columns, `latitude`, `longitude`, `location_elevation` and `location_uncertainty`, empty for a record with none (AS 5.1). Export then import into an empty dataset gives the
  same locations (AS 5.2). Degrees and minutes and DMS import as decimal degrees (AS 5.3). A bad row
  is reported with the value and not saved (AS 5.4). A measurement row carries only its own location
  (AS 5.5).
- [ ] T027 [US5] The four columns and their widgets (plan D10), expanded by the resource factory.
- [ ] T028 [US5] Docs: the import and export columns on the locations page.

## Phase 7: US-6, a profile maintainer places an organization (P2)

- [ ] T029 [US6] `tests/test_contrib/test_contributors/`: a ROR record's coordinates become the
  organization's point (AS 6.1), changing the existing ROR tests to read the point. The profile form
  saves a point typed in any notation (AS 6.2) and moving one organization leaves another at the
  same coordinates unchanged (AS 6.3). A person is placed at their primary affiliation's point
  (AS 6.4). The overview shows the map when the organization has a point.
- [ ] T030 [US6] The point-only input on the organization profile form and on both forms in
  `forms/organization.py`, and the overview's map condition (plan D3, D7). The field and the ROR transform came with US1.
- [ ] T031 [US6] Docs: the organization's point on the locations page and the contributors page.
  FS-019 edited.
