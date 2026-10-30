# ADR 0010 — Record addresses name the record type in the plural

**Status:** accepted

## Decision

Every address belonging to a record type names that type in the plural, and the singular form does
not answer.

A record sits at `<types>/<identifier>/`, and every page belonging to it is a segment below that:
`<types>/<identifier>/<page>/`. The collection sits at `<types>/`, and creating one at
`<types>/create/`.

Projects follow this now. Samples already did. Datasets and measurements do not yet, and bringing
them across is tracked separately.

## Why

**Both forms were in use, for no reason anyone recorded.** A project was reachable at one prefix
while the pages belonging to it mounted under the other. Nothing chose that; it accumulated. A
reader who learns one address learns nothing about the next.

**The plural is the form already published.** It is the one appearing in links people may have
saved and cited, so keeping it costs nothing and changing it would break references outside our
control. The pages belonging to a record are newer and less likely to have been cited, which makes
them the cheaper side to move.

**A convention that holds for three of four record types is not a convention.** The value is
entirely in its being exceptionless — a developer adding a fifth record type should be able to
derive its addresses without reading any existing ones.

## Consequences

The creation route has to be declared ahead of the record route, or `create` is read as a record
identifier and the creation page resolves to a lookup that fails. This is a real ordering
requirement, not a stylistic one, and it carries its own test.

Pages that already belonged to a project changed address when it moved. That cost is accepted once
per record type, and is the reason for doing the remaining types in a single pass rather than one at
a time.

A record's own address method is the single place any of this is reversed. Nothing outside it should
construct a record's address by name, so that a future move touches one place.
