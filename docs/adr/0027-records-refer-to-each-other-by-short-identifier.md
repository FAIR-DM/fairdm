# ADR 0027 — Records refer to each other by short identifier, never by database number

**Status:** accepted

## Decision

In the REST API a record names another by its short identifier (`uuid`) and its address, as
`{"uuid": "...", "url": "..."}`. A dataset names its project this way, a sample its dataset, a
measurement its sample and dataset, a project its owner, and a credit its contributor and
affiliation. No response contains an `id` or a `pk`, no relation is returned as an integer, and no
request is accepted that names a record by one. A bare identifier, or that object, is accepted
where a request names a record. A database number is refused like any other identifier that names
no record.

One field class, `RecordReferenceField`, does this for every relation. It builds the address from
the record it is given, so a measurement can name a sample of any registered type.

A reference never names a record the caller may not see. It is `null` when the requesting user
could not list the record, by the rule that decides what a list contains. That covers a public
dataset in a private project and a measurement whose sample is in another, private dataset.

Lists are narrowed by the same identifier: `?dataset=` on every sample and measurement list and
`?sample=` on every measurement list, whatever filters the type declares. The filters a type
declares match related records by database number because the portal's own pages share them, so
the API replaces those two with its own and leaves the pages alone.

## Why

A caller holding a dataset's number has no endpoint to look it up with. Database numbers also
differ between two portals holding the same data, and an identifier that is already in a record's
address does not.

Returning only the identifier would have meant a second request to build the address of every
record, and the address of a sample depends on its registered type.

The portal's own pages already leave a hidden project unnamed on a public dataset. An API that
named it would show a caller what the portal withholds.

## Consequences

- A serializer a portal writes for a relation to a project, dataset, sample, measurement or
  contributor declares `RecordReferenceField`. A relation left to Django REST Framework's defaults
  is returned as a database number.
- A page of records is checked for visibility in one query per reference field. A list does not run
  a query per record to decide what to name.
- A client that stored database numbers from an earlier build of the API has to read identifiers
  instead. No release carried the earlier form.
- A filter a registered type declares on one of its own foreign keys still matches on a database
  number. Only the dataset and sample filters are replaced.
