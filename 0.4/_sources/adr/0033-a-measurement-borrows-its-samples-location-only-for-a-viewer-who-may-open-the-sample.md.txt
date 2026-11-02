# ADR 0033 — A measurement borrows its sample's location only for a viewer who may open the sample

**Status:** accepted

## Decision

A measurement with no location of its own is treated as being where its sample was taken, but only
for a viewer who may open that sample. For anyone else it has no location. This effective location
is written once, in `Measurement.objects.with_effective_location(user)`, and the measurement page,
the measurement lookups, the collection tables and a dataset's spatial coverage all read it.

The REST API returns only a measurement's own location, never its sample's.

## Why

Most measurements are made where their sample was taken, so asking for the same coordinates on
every measurement would be repetition. A measurement can belong to a different dataset from its
sample, though, so it can be public while the sample is not. Without the check, a visitor could
read where an unpublished sample was taken from a public measurement, or work it out from which
area searches return the measurement.

Writing the rule in one annotation keeps every surface agreeing about what a viewer may see.

The API leaves the fallback out because a measurement's response would otherwise change when its
sample changed, with nothing in the response to say so, and every serializer would need the
viewer's rule. A script that wants the sample's location follows the sample link.

## Consequences

- Searching measurements by place, and the spatial coverage of a dataset, give different answers
  to different viewers.
- Anything built later on measurement locations, such as maps or area tagging, reads the effective
  location for the viewer rather than the sample's field.
