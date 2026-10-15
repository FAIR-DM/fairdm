# Sketch: capture, store and query locations as geospatial data

The screens a person sees for FS-030, prototyped before the feature is planned. Everything behind
them is replaced when the feature is built, test first.

## What exists

- **Data.** `Point` holds `x` and `y` as five-place decimals and a `crs` label, and every sample
  and contributor at the same coordinates shares one row. There is nowhere to keep an elevation,
  an uncertainty or a measurement's own location. Samples and measurements both carry an `options`
  JSON field that nothing uses, which the sketch borrows.
- **The input today.** `SampleFormMixin` swaps the location for a Select2 search over `Point`,
  on a `name` field `Point` does not have, so it never finds anything. No demo sample type lists
  the location among its registered fields, so no form in the demo shows it at all. The
  organization profile form has no location input, only city and country.
- **Forms.** crispy-forms with django-mvp's daisyUI templates. Each field is a `.fieldset` with
  a `fieldset-legend` label. A multi-part widget is drawn as a `<fieldset>` with a `<legend>`,
  which is the grouping WCAG asks for. Alpine.js is on every page.
- **Display.** `c-card.location` draws a MapLibre map and the coordinates as "Longitude (x)" and
  "Latitude (y)", with the `crs` label. The sample, measurement and organization overview pages
  all use it. The measurement page already falls back to the sample's location, and hides it when
  the sample's dataset is not published.
- **Tables.** The sample and measurement collection tables have latitude and longitude columns,
  with the two values swapped, and an icon linking to the location page.
- **GeoDjango** is installed since #500, so GDAL can convert from any EPSG system.
- **Planning notes.** The one note, a survey of the available packages, bears on the
  coordinate parsing and the input, and is for research.

## What the screens need from the code

- The sample form needs a location input that reads decimal degrees, degrees and decimal minutes,
  and degrees, minutes and seconds, with or without N, S, E and W, and converts from any EPSG
  code to WGS 84 before saving.
- The input needs to know whether a reference system is typed in degrees or in metres, to label
  its two boxes Latitude and Longitude or Northing and Easting.
- The input needs the stored location back, as WGS 84 decimal degrees, when the form is opened
  again.
- The sample page needs the elevation and the uncertainty with the coordinates.
- The measurement form needs the same input, for the measurement's own location.
- The measurement page needs the measurement's own location, or its sample's only for a viewer
  who may open the sample, and needs to know which of the two it is showing.
- The organization form needs a latitude and a longitude in WGS 84, with no reference system,
  elevation or uncertainty.
- The collection tables need the latitude under Latitude and the longitude under Longitude. The
  measurement table needs the measurement's effective location.
- A table built from a registration that lists the location needs no extra Location column.

## What the sketch faked

- **Elevation and uncertainty** are kept in the sample's `options` JSON, not in fields.
- **A measurement's own location** is kept whole in the measurement's `options` JSON.
- **The sample's and the organization's point** still go into the shared `Point` table, found or
  created at five decimal places. Changing one record never edits a shared row, but the build
  replaces the table with fields on each record.
- **The measurement location input is on every measurement form**, whatever the registration
  lists, because a registration cannot list a field the model does not have.
- **The rock sample's registration lists the location**, so that the demo shows the input. The
  water sample's does not, so the form without it can be seen too.
- **The list of geographic reference systems** that decides the labels is hard-coded in the
  widget's script. Any code not on it is treated as projected.
- **The "Reads as" line under each coordinate** parses in the browser, separately from the
  server's parser.
- **The registry's table factory drops a `location` column** by field name.
- **The measurement collection table** still shows the sample's location, not the measurement's
  effective one.
- **The seeded data**: the rock core has an elevation of 155 m and an uncertainty of 10 m, and
  the fully described XRF measurement has its own location.
- **The location page** at `/location/<lon>/<lat>/` still exists. Only the tables' link to it is
  gone.

## What was ruled by eye

Taste calls made for the first round. Sam's eye rules on each.

- **One number box per coordinate.** The sketch took text so that °, ′ and ″ could be typed. The
  maintainer asked for decimal degrees only, so each box is a number input with a range of -90 to
  90 or -180 to 180. Other notations are #513. *(Convention: a number input holds a signed
  decimal.)*
- **Latitude before longitude**, in ISO 6709 order, in the form and on the card. The first box
  stays first. *(Order: convention.)*
- **There is no reference-system box.** The sketch had a short text box prefixed "EPSG", defaulting
  to 4326. The maintainer removed it after the walkthrough: every coordinate is entered in WGS 84,
  and the boxes are always Latitude and Longitude. Other systems are #512.
- **No "Reads as" line under each coordinate.** The sketch showed how the portal read a typed
  notation. With decimal degrees only there is nothing to read back, and the maintainer removed it
  with the notations. A line under the two boxes says "Decimal degrees in WGS 84" and that south
  and west are negative.
- **Elevation and uncertainty sit side by side below the coordinates**, with "m" and "± … m" in
  the boxes, so the unit is never typed or guessed.
- **The location fields are grouped in one bordered panel** inside the form's own Location
  fieldset, so they read as one answer.
- **The card shows signed decimal degrees to five places**, not hemisphere letters, so the
  values can be copied straight into a GIS. A line under them says "Decimal degrees, WGS 84".
- **The measurement card is titled "Measurement location" for its own location and "Sample
  location" for its sample's.**
- **On the organization form the input is labelled "Coordinates"**, under the existing Location
  heading beside city and country, to avoid two headings that say Location.

## Review

Approved by the maintainer on 2026-10-14 after the first round, with no changes.

- He asked why the water sample's form has no location input. The reason is that its
  registration does not list the location, and a sample type's generated screens show only the
  fields its registration lists. He was content with that rule, so it stands as FR-009 says.
