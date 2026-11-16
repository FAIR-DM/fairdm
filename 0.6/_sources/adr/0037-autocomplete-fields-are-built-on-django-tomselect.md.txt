# ADR 0037 — Autocomplete fields are built on django-tomselect

**Status:** accepted

## Decision

Every searchable field in FairDM that chooses a record is a django-tomselect field backed by a
view in `fairdm.contrib.autocomplete`, drawn by django-mvp-forms. FairDM does not use
django-autocomplete-light, django-select2 or django-addanother, and a new field does not bring one
of them back. The Django admin uses its own `autocomplete_fields`. Vocabulary concepts are the
exception until django-controlled-vocabularies provides a concept field: they use
django-mvp-forms' `TomSelectMultiple`, which needs no view.

Where django-tomselect or django-mvp-forms falls short, FairDM keeps the smallest override in
`fairdm/templates/django_tomselect/` and tracks it in #554, rather than bringing in a second
library.

## Why

FairDM drew searchable selects with three libraries at once. None filtered by visibility, several
had stopped rendering, and two asked for addresses that no longer existed. One library styled by
django-mvp-forms gives every portal the same control, with the same groups, counts and look, and
one place to fix it.

## Revisit if

django-tomselect stops being maintained, or django-mvp-forms drops its support for it.
