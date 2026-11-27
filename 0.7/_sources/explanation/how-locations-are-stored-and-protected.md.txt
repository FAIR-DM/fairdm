# How locations are stored and protected

This page explains how a FairDM portal holds the place a sample, measurement or organization is, why each record keeps its own copy, and how the portal keeps the position of an unpublished sample from leaking through something that is public. It covers the reasoning. It does not list the fields, lookups and file columns, which are in [Location fields](../developers/reference/location-fields.md), and it does not describe how to use them, which is in [How to give a sample or measurement a location](../developers/how-to/give-a-registered-type-a-location.md) and [How to find records by where they are](../developers/how-to/find-records-by-where-they-are.md).

## Each record holds its own location

A sample and a measurement each carry three fields of their own: a point in WGS 84, an elevation in metres above mean sea level, and an uncertainty in metres. An organization carries a point only. A person carries none.

Nothing is shared. Two samples taken at the same coordinates each hold their own copy, and correcting one never moves the other. No location is stored as a row of its own that several records point to.

### Why not share a row

Sharing a location row sounds economical, because it answers "what else was taken here?" with a join. It does not hold up in practice.

- Records would share a row only when their numbers matched exactly. Coordinates typed to a different number of decimal places differ in their last digits, and a different elevation or uncertainty would split one site into several rows. Sharing would mean "the same numbers", not "the same site".
- Correcting a coordinate in place would move every record that happened to share it.
- A field on the model is how GeoDjango expects a location to be held. Forms, tables, filters, the API and import and export are all built from the field with no code to turn a foreign key into coordinates and back.
- Standards that describe samples, such as IGSN metadata and Darwin Core, put the coordinates on the sample itself.

The questions that a shared row seems to answer cheaply are answered as cheaply without it. The records at a place are found with a within-distance lookup, which also gathers a site whose coordinates arrived in two systems. A map layer has to be filtered to the records the viewer may open either way.

A place that is a thing in its own right, such as a borehole or a station, is modelled as a parent sample with the samples taken from it as children. See [ADR 0032](../adr/0032-a-location-is-a-value-on-each-record.md).

### The three fields hang together

The database enforces that an elevation or an uncertainty cannot stand without a point, and that an uncertainty is never negative. All three fields are optional. The rule exists so a record is never left with an uncertainty that is a radius around nothing.

### Organizations and people

An organization's point places its page on a map. A person has no location of their own. Where a person appears on a map, the portal uses the point of the organization of their primary affiliation, and shows none when that organization has none. A person's place is therefore a fact about the organization, which they can change by changing their affiliation.

## A measurement's effective location

Most measurements are made where their sample was taken, so asking for the same coordinates on every measurement would be repetition. A measurement can record its own location for the reading taken at a site away from the sample.

A measurement's **effective location** is its own where it has one, and its sample's otherwise. This is the location the measurement's page, the lookups, the collection tables and a dataset's spatial coverage all read. It is worked out once, in one place, so every surface agrees about what a viewer sees.

### The sample's location is borrowed only for a viewer who may open the sample

A measurement can belong to a different dataset from its sample. It can be public while the sample is not. If the effective location always fell back to the sample, a visitor could read where an unpublished sample was taken from a public measurement. They could also work it out from which area searches return the measurement.

So the sample's location counts only for a viewer who may open the sample, which is the rule that decides who may see a sample at all. For anyone else, a measurement with no location of its own has none, and no area contains it. A published measurement never gives away where an unpublished sample was taken. The rule for who may open a sample is in [How access to a record is decided](how-access-to-a-record-is-decided.md).

A consequence is that the same question has different answers for different viewers. A search for measurements by place, and the spatial coverage of a dataset, differ between a visitor and a member of the team. That is the point.

### The API returns only the measurement's own location

The REST API returns only a measurement's own location, never its sample's. If it did, a measurement's response would change when its sample changed, with nothing in the response to say so, and every serializer would need to know about the viewer's rule. A script that wants the sample's location follows the sample link. See [ADR 0033](../adr/0033-a-measurement-borrows-its-samples-location-only-for-a-viewer-who-may-open-the-sample.md).

## Why the lookups are fast

Finding records inside an area, within a distance or nearest a point reads a spatial index rather than the whole table. Distances are measured on the ground, so a kilometre is a kilometre near the equator and near a pole. To measure on the ground, the lookups cast the point to a geography, and the index is built on exactly the same cast. PostgreSQL does not use an index whose expression differs from the query's, so the two have to match.

A measurement's location lookups need both the measurement's own point and its sample's. A single query with an OR across the join would use neither index. The portal instead builds two subqueries, each on one table and each using its own index, and joins their results. This is why measurement lookups take the viewer as an argument: the second subquery applies the sample rule above.

## Boxes that cross the antimeridian

A dataset's spatial coverage is the smallest box that holds the locations of the samples and measurements the viewer may see. A box is written as west, south, east and north in degrees.

Samples at 176 and -176 degrees of longitude lie four degrees apart across the 180th meridian. A naive box from -176 to 176 spans almost the whole globe. The portal reads each set of locations twice, once as longitudes from -180 to 180 and once as longitudes from 0 to 360, and keeps the narrower box. Where the box crosses the meridian, the west bound is greater than the east bound. This is the form DataCite uses, and lookups that take a box read it the same way.

## What DataCite output says about place

A dataset's DataCite metadata describes its spatial coverage as a single box, so a repository receiving the metadata can index the dataset by place. The metadata is published, so the box is the coverage for a visitor, whoever asks for it. A location the public may not see does not count towards it. A dataset with nothing a visitor may see located has no geographic section at all. See [Dataset publication, DOIs and DataCite metadata](dataset-publication-dois-and-datacite-metadata.md).

## Limits

- Coordinates are entered as signed decimal degrees in WGS 84. A portal does not convert from other systems or notations.
- A box is a coarse description. It tells a repository roughly where a dataset is, and it is not a substitute for the records' own locations.
- The privacy rule protects the location of an unpublished sample. It does not stop a team from publishing a dataset whose samples have precise coordinates. Whether to publish a location is a decision for the team, and uncertainty is the field for saying how precisely a position is known.
