# ADR 0018 — Publication is a queryset method, not a default manager

**Status:** accepted

## Decision

Filtering by publication is a queryset method: `Sample.objects.published()`,
`Measurement.objects.published()`, `Dataset.all_objects.published()`. It is not applied by a
default manager, and `Sample.objects` and `Measurement.objects` return what they always returned.

## Why

**Those managers are read everywhere.** The API, the admin and the demo app all go through them
today. Narrowing the default would silently change every one of those call sites, and the audit
that would make that safe is larger than the feature that wanted it.

**A queryset method is opt-in at the one call site that needs it.** It also composes with a
generated filterset without a manager override fighting it, which a narrowed default does not.

**The dataset case shows why the manager choice matters in the other direction too.** `Dataset`
already has a privacy-first default manager. A choice list built from it comes back empty for
exactly the published-but-private datasets whose rows sit beside it in the listing (ADR 0015), so
publication scoping there runs through the unfiltered manager instead.

## Consequences

A page that must show published records only says so. Nothing is filtered on its behalf, and code
that forgets returns too much rather than too little, which a test can state directly.

`published()` carries no eager loading. The joins a page needs belong to the page, because the same
method is also called to scope filter choice lists, where those joins are waste.
