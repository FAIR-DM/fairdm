# ADR 0029 — People and organizations have their own API endpoints

**Status:** accepted

## Decision

The REST API serves people at `/api/v1/people/` and organizations at `/api/v1/organizations/`.
There is no endpoint that lists the two together. Each endpoint has one shape for a list entry and
a fuller one for a single record, and the list entry is a subset of the single record.

A person or an organization has one address in the API. Every reference to a contributor, such as
a project's owner, a credit on a record or a member of an organization, gives the address of the
endpoint for that contributor's kind.

Both endpoints are read-only and open to anyone. They return what a contributor's public page
shows a visitor who is not signed in, and nothing about a person's account.

## Why

A mixed list has two shapes. Its generated documentation has to describe each entry as one of two,
and every client reads a type field before it reads anything else. Two endpoints give each list
one documented shape.

Keeping a mixed list beside two typed ones would give every person two addresses. Each reference
would then have to pick one, and a caller could not tell that two addresses name the same person
without requesting both.

The one question only a mixed list answers is who is credited on a record, people and
organizations together. A record answers that itself, through its nested credits
([ADR 0030](0030-a-credit-carries-what-datacite-asks-of-a-creator.md)).

## Consequences

- `/api/v1/contributors/` does not exist. No release carried it.
- A serializer a portal writes for a relation to a person or an organization still declares
  `RecordReferenceField`, which builds the address from the record's real type.
- A feature that lets the API create or change contributors adds its writes to these two
  endpoints, one kind at a time.
- A caller who wants both kinds makes two requests.
