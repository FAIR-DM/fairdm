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

- **One box per coordinate, typed as text.** A number input would refuse °, ′ and ″. Typing
  stays free and the parser does the work. *(Convention: a number input cannot hold a degree
  sign.)*
- **Latitude before longitude**, in ISO 6709 order, in the form and on the card. The first box
  stays first when a projected system turns it into Northing. *(Order: convention. Keeping the
  boxes in place: taste.)*
- **The reference system is a short text box with suggestions**, prefixed "EPSG", defaulting to
  4326, rather than a select of a few systems with an "other" option. Any code can be typed.
- **A "Reads as 48.93530° N" line under each coordinate**, so a researcher sees how the portal
  read what they typed before saving.
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
