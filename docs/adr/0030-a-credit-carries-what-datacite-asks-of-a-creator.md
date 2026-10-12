# ADR 0030 — A credit on a record carries what DataCite asks of a creator

**Status:** accepted

## Decision

A project, dataset, sample or measurement returned by the REST API lists its credits in full, in
one list, in the order the record keeps them. Each credit carries the properties DataCite defines
for a creator or contributor, named in the API's snake case:

- `name` and `name_type` (`Personal` or `Organizational`)
- `given_name` and `family_name` for a person
- `name_identifiers`, each with `name_identifier`, `name_identifier_scheme` and `scheme_uri`
- `affiliation`, a list holding the organization recorded on the credit, with its name,
  identifier, scheme and scheme address

A credit also carries `roles`, from the portal's own contribution role vocabulary, and the
contributor's `uuid` and `url` in the API. It carries nothing else from the contributor's profile
and never the level of access the credit grants.

Creators are not kept apart from other contributors, and a credit has no DataCite contributor
type. Deciding which roles make someone a creator, and which contributor type each other role
becomes, belongs to whatever exports a record as DataCite metadata.

The affiliation on a credit is the organization stored with that credit. It is never filled in
from where the person works today.

## Why

Attribution is what a record's metadata is for. A credit that only pointed at the contributor made
a caller request every author, and then every author's institution, before it could cite a
dataset.

DataCite's creator is the description of an author that repositories and harvesters already
exchange, so a credit in that shape maps onto it field for field.

The portal's roles are finer than DataCite's contributor types and a portal may add its own.
Putting DataCite's types into every response would fix one mapping into the API for good.

A credit records where someone worked when they did the work. Their profile records where they
work now. Filling one from the other would move old work to an institution that had no part in
it, and the answer would change without the record changing.

## Consequences

- A change to a person's name or identifier appears on every credit they hold, because the credit
  reads it from the contributor.
- A credit held by an account the people list leaves out is still returned, with `uuid` and `url`
  empty, so that a record's attribution stays complete.
- `affiliation` is a list although a credit stores one organization, which leaves room for more
  without changing the shape.
- A DataCite export has to map roles to creators and contributor types itself.
