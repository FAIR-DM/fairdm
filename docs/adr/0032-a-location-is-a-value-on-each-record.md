# ADR 0032 — A location is a value on each record, not a shared row

**Status:** accepted

## Decision

Every sample and every measurement holds its own location in three fields: `location`, a WGS 84
point, `location_elevation` in metres above sea level, and `location_uncertainty` in metres. An
organization holds a plain `location` point. A person holds none. No location is stored as a row
of its own that several records point to.

This replaces the `Point` model, which every sample and contributor at the same coordinates
shared.

## Why

Records shared a `Point` row only when their numbers matched exactly. Coordinates converted from a
projected system differ in the last digits, and an elevation or uncertainty would have split one
site into several rows. The sharing meant "the same numbers", not "the same site", and correcting
one sample's coordinates in place would have moved every record that shared them.

A field on the model is how GeoDjango expects a location to be held. The registry builds forms,
tables, filters, the API and import and export from it with no code that turns a foreign key into
coordinates and back. IGSN sample metadata and Darwin Core also put the coordinates on the sample
itself.

The questions a shared row seemed to answer cheaply are answered as cheaply without it:

- **A map layer.** It has to be filtered to the records the viewer may open either way. Grouping
  the visible samples by point is one indexed query.
- **The records at a place.** A within-distance lookup, which also gathers a site whose
  coordinates arrived in two systems.
- **Tagging places with areas.** One spatial join either way.

A place that is a thing in its own right, such as a borehole or a station, is modelled as a parent
sample with the samples taken from it as children.

## Consequences

- Changing one record's location never changes another's.
- Code that read `Point.x`, `Point.y` or `Point.crs`, filtered on `location__x`, or used the
  location page has to change.
- A portal's own sample type cannot declare a field named `location`, `location_elevation` or
  `location_uncertainty`.
- Lookups (`inside`, `within_distance`, `nearest`) and a dataset's or project's spatial coverage
  run on the fields directly, through the spatial indexes.
