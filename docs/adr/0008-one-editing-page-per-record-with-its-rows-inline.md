# ADR 0008 — One editing page per record, with its related rows inline

**Status:** accepted

## Decision

A record has exactly one page offering its own attributes, and that page also edits the related
rows that belong to the record rather than describing it — its dates and its external identifiers,
each as a row set on the same form, saved in the same submission.

The page is registered against the record as an additional view of the record's own page, not as a
separate route. Prose about the record — its abstract and the other passages — is the exception and
keeps a page of its own, because it is a fixed set of labelled areas rather than rows to add and
remove.

The row sets are built with the interface layer's own inline formsets (`mvp.views.inline`). The
project's pages no longer reach for `django-extra-views`.

## Why

**There were two editing pages, and only one of them could be reached.** A registered tab offered
three of the project's fields; a separate route offered the full set, carried the tests, and had no
link pointing at it anywhere in the portal. Two surfaces editing one record is a standing invitation
for them to drift, and the one a user could actually find was the poorer of the two.

**A record's dates are a row set even when there are only two of them.** A project has a start and
an end, and modelling those as two ordinary fields would have been simpler for the project alone. It
would also have been the wrong shape for every record type that follows: datasets, samples and
measurements each have several dates, and their vocabularies differ. Adding a date type should be a
row a user adds, not a field a developer inserts.

**The same editing interaction across record types is worth more than a per-record optimisation.**
Projects, datasets, samples and measurements are edited by the same people, and a researcher who has
learned one record's editing page should recognise the next. That argument is what settles the date
question above, and it is the reason the row-set declaration and the date-ordering rule are shared
pieces parameterised per record rather than written out per record.

The one thing deliberately not shared is the permission each page states. Deriving it from the model
breaks on the polymorphic record types, where a concrete sample would derive a permission nothing
grants.

## Revisit if

A record type appears whose related rows are numerous enough that editing them alongside the
record's own fields makes the page unusable — a hundred identifiers, say. The answer then is a
page of its own for that row set on that record type, not a different mechanism for all of them.
