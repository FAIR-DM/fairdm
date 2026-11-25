# ADR 0048 — The site search matches with each list's own search

**Status:** accepted

## Decision

The portal's site search finds a record by running the `q` filter of the record type's own list
over the records the person may open. Each record type is one `RecordKind` in `fairdm/search.py`,
which names the list's filter set, the records a person may open, the order and the line shown
under a result. Nothing is indexed, and no list of matching fields is kept beside the lists'.

## Why

- A person never finds a record from the header that its own list will not find for the same text,
  and never the other way round. Two lists of fields would drift.
- django-mvp's model kind searches through a model's default manager. `Dataset.objects` leaves out
  private datasets, so a person holding a level on one could never find it, and the polymorphic
  sample, measurement and contributor models and the literature package's `Item` do not fit its
  indexed model either.
- Improving matching and ranking in the list searches, the planned work on an index, improves the
  site search at the same time.

## Revisit if

The list searches are backed by an index. The site search then follows it, and this decision is
replaced by one that names the index.
