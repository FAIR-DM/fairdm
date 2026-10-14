
## 2026-10-14T21:48:43Z · Forge · PLAN

Did: research, plan and tasks written after the sketch was approved. Ledger initialised at PLAN.
Verified: lat-lon-parser 1.3.1 tried against the notations in the spec.
Next: design review.
Watch: US1 is large: fields, removal of Point and the input.

## 2026-10-14T22:15:52Z · Implementer US1 · T001

Did: added lat-lon-parser 1.3.1 (pyproject, uv.lock) and parse_coordinate(text, axis) in fairdm/contrib/location/forms.py, with TestParseCoordinate* tests written first (seen failing on import). The dependency landed here, not in T006, because the function needs it.
Verified: uv run pytest -q -n0 tests/test_contrib/test_location/test_forms.py -> 60 passed. pre-commit on the changed files passed.
Next: T002, LocationField, Location and the widget class.
Watch: the package refuses whole degrees above 180 itself, so the range check reads the first number before calling it, otherwise 181 reports as unreadable.

## 2026-10-14T22:18:20Z · Implementer US1 · T002

Did: Location named tuple, LocationWidget (decompress, part names) and LocationField (compress, read_point) in fairdm/contrib/location/forms.py, with TestLocationField, TestLocationFieldPointOnly and TestLocationWidget written first (seen failing on import). The widget class landed here because the field instantiates it; its template context and json_script systems list are T007.
Verified: uv run pytest -q -n0 tests/test_contrib/test_location/test_forms.py -> 97 passed. pre-commit on the changed files passed.
Next: T003, the model fields and constraints.
Watch: PROJ wraps longitudes for Web Mercator and UTM instead of returning values above 180, so a projected point is "outside WGS 84" only when GDAL raises (outside the projection's domain). The decompressed coordinates are written out in full so resaving an unchanged form does not move the stored point.

## 2026-10-14T22:37:39Z · Implementer US1 · T003

Did: LocatedRecord (location PointField 4326, location_elevation, location_uncertainty) in fairdm/contrib/location/models.py, applied to Sample and Measurement, with the two check constraints and the geography index in each model's own Meta, and migrations sample 0012 and measurement 0015 (the sample's foreign key is a RemoveField then an AddField). TestSampleLocation and TestMeasurementLocation were written first. The pre-existing TestSampleLocationRelation test (deleting a shared Point is refused) is replaced by TestSampleLocation, since no shared row exists (D16 explains where the constraints live).
Verified: uv run pytest -q -n0 --create-db tests/test_core/test_sample/test_models.py::TestSampleLocation tests/test_core/test_measurement/test_models.py::TestMeasurementLocation -> 12 passed.
Next: T004, the sample edit page.
Watch: a type with no Meta of its own inherits the abstract parent's Meta, so constraints on LocatedRecord.Meta would be created on child tables (D16).

## 2026-10-14T22:37:39Z · Implementer US1 · T004

Did: LocationFormMixin in fairdm/contrib/location/forms.py, used by SampleFormMixin, which replaces `location` with a full LocationField and moves elevation and uncertainty onto the instance on clean. The registry's table factory leaves geometry fields out. The demo's RockSample registration lists location. Tests: TestSampleFormMixinWidgets (the select2 test for the location is replaced by a LocationField test), TestRegisteredSampleTypeLocationInput and TestSampleEditPageLocation (notations, projected systems, every FR-008 case, stored location shown back, a type without location).
Verified: uv run pytest -q -n0 tests/test_core/test_sample/test_forms.py -> all passed.
Next: T005 and T009, the sample page and the card.
Watch: a Location is a tuple, which MultiWidget would take for the inputs' own values, so the widget turns it into its parts first.

## 2026-10-14T22:37:40Z · Implementer US1 · T005

Did: the sample overview template passes sample.location_elevation and sample.location_uncertainty to c-card.location (the card already took them). Tests: TestOverviewLocation gains the five-places case and the elevation/uncertainty-only-where-recorded case; TestLocationCard gains the given/not-given/zero cases. The two PointFactory tests in those files now pass a GEOS point and keep what they assert.
Verified: uv run pytest -q -n0 tests/test_core/test_sample/test_plugins.py::TestOverviewLocation tests/test_templates/test_cards.py::TestLocationCard -> passed.
Next: T006, contributors and migrations.
Watch: the measurement overview's sample card now reads the sample's location_elevation and location_uncertainty instead of sample.options, which no longer exists.

## 2026-10-14T22:37:40Z · Implementer US1 · T006

Did: Contributor.location is removed and Organization.location is a PointField with its own geography index (contributors 0024). RORTransform.import_location sets a GEOS point, and as_geojson, lat, lon, the ROR export address and the organization page's has_map read the point. fairdm_location 0002 deletes Point. lat-lon-parser was added under T001.
Verified: uv run python manage.py makemigrations --check --dry-run --settings=config.settings reports only the third-party orbit app (it did before). tests/test_smoke.py and tests/test_contrib/test_contributors pass in the full run.
Next: T007 wiring checks, then T008.
Watch: migration 0023's data step is tested against historical models on the latest schema, so it now defers the dropped column (D19).

## 2026-10-14T22:37:40Z · Implementer US1 · T007

Did: LocationWidget.get_context supplies full, parts by name, systems (code, name, geographic from GDAL) and an id for the json_script element; the approved template reads the systems from that element instead of its own list, and its datalist ids are per widget. TestLocationWidgetRendering covers the inputs, the point-only variant, the stored value and the systems list.
Verified: uv run pytest -q -n0 tests/test_contrib/test_location/test_forms.py -> 102 passed.
Next: T008, removals.
Watch: nothing in the template's markup or copy changed besides the list's source.

## 2026-10-14T22:37:40Z · Implementer US1 · T008

Did: removed the Point model, location views, urls, plugin, address declaration, admin, utils.py, location_detail.html, PointFactory, the three settings, and tests/test_contrib/test_location/test_views.py. Changed the references the grep lists: sample managers' select_related, the collections view, the sample admin's autocomplete_fields, the tables (latitude and longitude read y and x and are not orderable, the location link column is gone), demo seeds, demo plugins and docs. Tests changed (named per the brief): test_api/test_viewsets.py, test_contrib/test_collections/test_tables.py (deleted the location icon column tests and the header tests for it, the leading-column test asserts the dataset only), test_contributors test_models/test_overview/test_update/test_tasks/test_transforms, test_demo seed_profiles (location_id -> location is None), test_core test_measurement/test_plugins, test_core/test_sample/test_config.py (location among the rock form's fields). Two plugin tests whose subject was the location page were deleted (D18).
Verified: full suite once, before the last two fixes: 6825 passed, 22 failed (21 in test_migrations, 1 in test_config), both fixed and re-run: 37 passed.
Next: T010, docs.
Watch: Dataset.bbox now aggregates sample points directly (D17).

## 2026-10-14T22:37:40Z · Implementer US1 · T009

Did: nothing beyond T005: c-card.location already takes elevation and uncertainty, the sample overview passes the three fields, the component docs list the attributes.
Verified: see T005.
Next: T010.
Watch: none.

## 2026-10-14T22:37:40Z · Implementer US1 · T010

Did: docs/portal-development/locations.md (fields, input, notations, reference systems, upgrade notes), linked from the portal development table of contents; CONTEXT.md defines Location and Reference system; CHANGELOG lists the new fields and each removal; FS-005's spec text describes the location as the sample's own; docs that named Point or a person's location (base views guide, contributors guides, plugin guide, overview pages, card library) are corrected. The page's snippets were run against this branch.
Verified: parse_coordinate and LocationField examples run and print the values the page gives.
Next: full verify and the report.
Watch: CONTEXT.md gains Spatial coverage in the story that adds it.
