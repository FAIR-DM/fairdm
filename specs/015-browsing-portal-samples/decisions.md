# Decisions — 015, browsing a portal's samples and measurements by type

The specification says what a reader gets. This records the judgements behind it: what was
ambiguous, which way it was settled, and why. Rationale short enough to sit in a requirement is in
the specification instead.

The short version: `fairdm/contrib/collections` already tries to be this feature and is not trusted
to be any part of it. It has no tests, no page template of its own, a redirect view resolving to
addresses that do not exist, a plugin no registration reaches, and a README describing a
configuration style the registry stopped using. More seriously, it serves records from private
datasets to anonymous visitors today. This feature owns the app and is judged on behaviour, not on
what it preserved.

---

## D1 — A collection shows public data only, for everyone

**Ambiguity**: a listing could show what the viewer is entitled to see, which is what most portals
do and what a naive reading of "collection view" suggests.

**Settled**: it shows published data, identically for every viewer. A signed-in researcher does not
see their own unpublished records mixed into a listing.

**Why**: the entitlement reading costs more than it gives. It makes every listing viewer-dependent,
so nothing about it can be cached, every filter's choice list has to be computed per viewer, and
every future addition to the page inherits the obligation to get the same rule right again. The
value it buys is small — a researcher browsing their own unpublished records is looking at their
dataset's page, not at a portal-wide listing of every ice core in the portal. The uniform rule also
turns a leak into a test: one assertion, made once, covers every viewer.

**What it does not settle**: whether a dataset-scoped listing showing a researcher their own
records should exist. It should, and it is R18's plugin work.

**ADR:** docs/adr/0013-a-listing-shows-published-records-only-for-everyone.md

---

## D2 — The published flag, and why it is not a workflow

**Ambiguity**: `014-dataset-crud-views` FR-066 forbade introducing a published state, and R22 owns
publication. A listing needs *something* to decide what is public, and a dataset's visibility is
already spoken for — it governs metadata, settled in that feature's D1.

**Settled**: a boolean on `Dataset`, added here, set in the Django admin and nowhere else.
FS-014's FR-066 is annotated in place as superseded rather than deleted.

**Why a new field rather than reusing visibility**: they answer different questions. Visibility
answers "may anyone read that this dataset exists and what it is about", which a researcher decides
about their own work as a community act. Published answers "may anyone read the data beneath it",
which is a release and belongs to a reviewed process. FS-014 already drew that line in prose. This
feature is where the line needs a field, because it is the first thing that shows the data.

**Why the admin and nothing else**: the alternative recommended during grilling was a control on
the dataset's own attributes page, which is where a researcher would look for it. Sam chose the
admin, and the choice is the right one for a reason worth recording: a control on the researcher's
own page makes publishing a click, and R22 exists precisely because publishing should not be a
click. An administrator-only flag is a deliberately awkward placeholder, and its awkwardness is
what stops it hardening into the workflow before the workflow is designed.

**The cost, accepted**: a portal upgrading to this version finds its listings empty until an
administrator publishes something. That is correct — the alternative is defaulting existing
datasets to published, which publishes data nobody chose to publish. The migration leaves every
dataset unpublished.

**ADR:** docs/adr/0014-publication-is-a-separate-flag-from-visibility.md

---

## D3 — A record's own dataset decides, and a link is not a loophole

**Ambiguity**: a measurement may belong to a different dataset than the sample it was made on —
`CONTEXT.md` names provenance crossing dataset boundaries as a principle, not an accident. So a
published measurement can reference an unpublished sample, and a measurement listing links each row
to its sample.

**Settled**: a record appears if and only if its own dataset is published. Where a row would name or
link a record whose own dataset is not published, it shows neither the name nor the link.

**Why**: the two halves are separate decisions and both matter. Deciding by the record's own dataset
is the only rule that stays true as the graph grows, because any rule reaching through a relation
has to be re-derived for every new relation. Suppressing the name and the link is the part that is
easy to miss: without it, a listing that correctly excludes an unpublished sample from the sample
listing hands out that sample's name and address from the measurement listing instead. Membership of
a listing must never become a route to a record that is not itself published.

**Extended at design review**: the rule is *no link to a record the visitor cannot read*, which is
one word wider than "not published". The case that forced the widening is the ordinary one. Dataset
visibility defaults to private and publication is independent of it (D1, FR-003), so the common
shape is a **published but private** dataset: its records belong in every listing, and the dataset
column on those rows would link to a page the same visitor is refused. The rows stay — publication
alone decides presence, and that is settled — but the dataset link is suppressed on the same test
the sample link uses. The rows themselves were never the defect, so nothing in the requirement
changes; only D3's existing link rule reaches one relation further.

**ADR:** docs/adr/0015-a-records-own-dataset-decides-and-a-row-never-links-past-it.md

---

## D4 — Search is declared per type, and the defaults are indexed

**Ambiguity**: R17 owns search, sorting and filtering across the portal. A listing with no search
is unusable, but building search here risks doing R17 badly and early.

**Settled**: this feature takes the declaration and the indexes. A registration says which fields
its type's search covers, the record's name is searched where it says nothing, and every field the
framework searches by default is indexed. Ranking, tolerance of partial or misspelled words, and
search spanning more than one record type stay with R17.

**Why the split falls there**: the part R17 cannot retrofit is the declaration and the schema. If
each type has not said what it means to search it, R17 has nothing to upgrade, and adding indexes
to a populated portal later is a migration nobody wants to run. The part R17 must own is the
matching itself, because a ranked, typo-tolerant, cross-type search is one mechanism serving every
listing, and building a lesser version of it per listing now is how a portal ends up with two.

**What the shell already gives**: the application shell searches across declared field paths,
related paths included, with OR semantics across words. This feature configures that from the
registration rather than building anything equivalent, per Article XIV.

**Where the index obligation stops**: on the fields the framework itself searches by default. A
field a model author adds is the author's to index, and the documentation says so. Enforcing it
would mean the framework rejecting a registration over a performance property, which is a rule that
fires on correct code.

**ADR:** docs/adr/0016-the-framework-indexes-the-fields-it-searches-by-default.md

---

## D5 — Ordering lives on the table, not the view

**Ambiguity**: sorting was not discussed during grilling, and R17 claims it.

**Settled**: a listing sorts on the columns its registration produces as sortable, and has a stable
default order. This is what a table gives, not a mechanism built here.

**Why it is not a choice**: the application shell's table view refuses a view that declares its own
ordering, and raises while importing the module that declares it. A table already has a whitelisted
ordering mechanism, and a second competing surface for the same thing is what that refusal exists to
prevent. So ordering is declared on the table class. This is recorded because it is the kind of
constraint an implementer discovers by hitting it.

**ADR:** none - records a constraint the application shell imposes rather than a choice made here; the shell refuses a view that declares its own ordering, and says so on import.

---

## D6 — The switching control does not carry terms across

**Ambiguity**: a reader who has narrowed a sample listing and jumps to a measurement listing might
reasonably expect their search to follow.

**Settled**: the destination opens unnarrowed.

**Why**: the terms are chosen against a different type's fields. A filter on an ice core's drill
depth means nothing on a heat-flow measurement, and a search term that matched a sample's name will
usually match no measurement at all. Carrying them across produces an empty listing that looks
broken. Carrying only the ones that happen to exist on both types produces a listing narrowed by a
rule the reader cannot see, which is worse.

**ADR:** none - the behaviour of one control, with nothing downstream inheriting it.

---

## D7 — Addresses and their names

**Ambiguity**: the existing listings sit under `collections/samples/<slug>/` and
`collections/measurements/<slug>/`, named `<slug>-collection`. ADR 0010 governs record addresses,
and the portal's other listings are named `project-list` and `dataset-list`.

**Settled**: listings keep an address prefix of their own, distinct from the record addresses ADR
0010 governs, and their URL names follow the `<name>-list` convention the portal's other listings
already use. A duplicate address is refused at import naming both types.

**Why**: a listing is not a record, so ADR 0010's record-address convention does not reach it, and
folding listings in beside `samples/<uuid>/` would put a slug and an identifier at the same position
in the path. The naming change is the part with an argument against it. It is churn with nothing
visible to show, and it is made anyway because a break with the repository's own convention is
treated here as a defect rather than a preference, and one reverse lookup is the whole cost.

**ADR:** docs/adr/0017-listings-are-addressed-and-named-apart-from-records.md

---

## D8 — What is deleted, and why it is specified rather than assumed

**Settled**: the redirect view, the unreached plugin, the orphaned template, the export machinery
and the README's account of a configuration style the registry no longer uses are all removed, as a
story of its own.

**Why a story**: "the feature owns the app" was Sam's answer at grilling, and an owner that leaves
its predecessor's unreachable code in place has not taken ownership, it has added a layer. Making it
a story rather than an implicit tidy means it has acceptance criteria and can be verified, and means
that if the run runs short the thing dropped is the one with no reader-visible cost.

**Export specifically**: the current page offers eight formats, generated in the request, untested.
R21 specifies export as dataset-scoped and run outside the request, and names in-request execution
as one of the faults it exists to fix. Keeping a faster wrong version alive until then would make
R21's job removing a feature people had started to rely on.

**ADR:** none - a scope decision about this feature's own deletions, spent once they landed.

---

## D9 — Publication is a queryset method, not a default manager

**Ambiguity**: `Dataset.objects` already excludes private rows by default. `Sample.objects` and
`Measurement.objects` could get the same treatment for `published`.

**Settled**: `published()` is a queryset method — `Sample.objects.published()`,
`Measurement.objects.published()` — not a default-manager filter.

**Why**: `Sample.objects` and `Measurement.objects` are read everywhere in the codebase today — the
API, the admin, the demo app — and FR-006 forbids this feature from changing behaviour outside the
listings it specifies. Narrowing the default manager would silently change every one of those call
sites without the audit that would take. A queryset method is opt-in at the one call site that
needs it and composes with the registry-generated filterset without a manager override fighting it.

**ADR:** docs/adr/0018-publication-is-a-queryset-method-not-a-default-manager.md

---

## D10 — `search_fields` is a plain attribute, not a seventh generated component

**Ambiguity**: `ModelConfiguration` generates six components — form, table, filterset, serializer,
resource, admin — through one `COMPONENTS` table and one factory pattern each. Search could be
added the same way.

**Settled**: `search_fields` is a plain declared list, validated the same way `fields` already is,
consumed directly by the view.

**Why**: the six existing components each produce a class through a factory. Search produces
nothing to instantiate — it configures the application shell's own `SearchMixin`, which already
takes a plain `search_fields` list on any view. Forcing it into the `COMPONENTS` shape would build
a factory that generates nothing, which is the wrong abstraction for what is otherwise a two-line
pass-through, per Article XIV.

**ADR:** none - an application of the existing rule to configure the shell rather than rebuild it; the registry gains no new pattern from it.

---

## D11 — What the design review changed before any code was written

The plan was reviewed against the approved specification, the existing code and the constitution
before implementation began. Thirteen findings were raised and every one is settled below, with the
artefact that now carries it. Two were high severity, and both were verified against the resolved
package in this project's environment rather than taken on the review's word — which changed the
remedy twice.

**Applied to the design.**

- *Suppressing a sample's name did not suppress its link.* django-tables2 composes the `linkify`
  anchor around whatever a render method returns, so a placeholder string still shipped an address
  for an unpublished record. The column drops `linkify=True` and builds its own anchor only when the
  sample's dataset is published (research.md R2, tasks.md T026), and the test asserts the absence of
  the anchor, not just of the name.
- *The measurement listing kept a per-row query.* Three of its columns read through
  `sample.location`, which the planned `select_related` did not cover. The queryset now names
  `sample__location`, the redundant `prefetch_related("sample")` goes with it, and the flat-query
  proof covers the measurement listing as well as the sample listing (research.md R3, T009, T025).
- *A queryset method was called but never defined.* Scoping generated filter choice lists to
  published records touches three querysets, not two, because every registered type has a foreign
  key to `Dataset`. `DatasetQuerySet.published()` is now specified (data-model.md) and built before
  any story runs (T067, T068).
- *The switcher had no template to render into.* Deleting the app's unused table template left the
  view falling back to the shell's own, which has no seam for the control. The app keeps one page
  template of its own, `listing.html`, created before the switcher tasks (research.md R12, T069).
- *The name index reaches four models, not two.* `name` is declared once on the shared abstract
  base, so indexing it there also indexes `Project` and `Dataset`. Both already search that column
  from their own listings, so the reach is recorded as intended under Article IX and all four
  migrations are named deliverables (data-model.md), rather than narrowed to leave two live
  listings searching an unindexed column.
- *The index check could never pass.* It introspected a multi-table-inheritance child's table, where
  an inherited column does not live. It now introspects the parent tables (quickstart.md §7, T010,
  T038).
- *The empty state set a hook the reader never sees.* The table attribute gates the block; the words
  come from two view attributes. Both are now overridden and the test asserts the rendered words
  (research.md R11, T027).
- *Declaration validation was narrower than the requirement.* A misspelled path was refused, but a
  number or a date resolved cleanly and would have failed on the visitor's first search. Validation
  now also requires the resolved field to be a text field (research.md R4, T013, quickstart.md §3).
  D12 records why it is a test of the field's type and not of the lookup it supports.
- *An empty navigation group would still render.* The menu library only evaluates suppression for a
  node that has children to process, so a portal with no registered types of a kind kept the
  heading. Each node gets its own check, and the test uses a registry with no such types
  (research.md R8).
- *Four stories write the same two modules.* They land in sequence rather than concurrently, and the
  shared surfaces are listed where the dependency order is stated (tasks.md).
- *A deferral could be settled now, and removes work.* Nothing outside the app references the three
  overview routes, so the views, templates and routes are deleted outright rather than deferred
  (research.md R12, tasks.md).
- *The research described existing behaviour wrongly.* The sample render method already exists and
  returns the type's verbose name; it is quoted verbatim now, so its body is replaced rather than
  duplicated (research.md R2).

**Settled inside the existing requirement.** The one remaining finding held that publishing a
dataset that is still marked private exposes its records. The requirement is explicit that
publication is independent of visibility and is the sole test for a record's presence in a listing,
and that was gated deliberately — so the rows are correct and no filter is added. The real defect
was the dataset column's link, which is now suppressed under D3's extension above.

**ADR:** none - a record of what the design review changed, not a decision with a life beyond this run. The four findings that were architectural are carried by ADRs 0015, 0016 and 0018.

---

## D12 — Searchability is a question about a field's type, not about its lookups

The check that decides whether a declared `search_fields` entry is acceptable asks
`isinstance(field, (models.CharField, models.TextField))`. The obvious alternative — asking whether
the field supports the case-insensitive substring lookup that search actually performs — reads as
the more principled test and does not work at all.

Django registers `IContains` on `Field` itself, not on the text field classes. So
`get_lookup("icontains")` returns a lookup class for a `DecimalField`, a `BooleanField`, a
`DateField` and an `IntegerField` alike, verified against all of them in this project's own
environment. A validator written that way accepts every field there is, and the requirement it
exists to enforce would be silently unenforceable — the failure mode that matters, because the
declaration is refused at import precisely so nobody discovers the problem on a visitor's first
search.

The type test also has a precedent in the codebase. `FilterFactory._get_search_fields`
(`fairdm/registry/factories.py:648-656`) already decides which of a model's fields are searchable,
and it decides it this way. Two different answers to "is this field searchable" in one framework is
the more expensive outcome than either answer being imperfect, so the new validator matches the
existing one. Where the line should sit — whether a `SlugField` or a `UUIDField` belongs on the
text side — is one decision in one place, and moving it later moves both.

**ADR:** none - folded into docs/adr/0016-the-framework-indexes-the-fields-it-searches-by-default.md, which states the type test and why a lookup test cannot work.

---

## D13 — Where the listing's eager loading lives

`DataTableView.get_queryset()` adds `select_related("sample__dataset", "sample__location")` for a
measurement type. Not `MeasurementQuerySet.published()`, and not `with_related()`.

There were three candidates and each of the other two costs something. `with_related()` documents
itself as deliberately *not* prefetching nested relationships, and tells callers needing them to
chain their own — widening it would break that contract for every existing caller in order to serve
one page. `published()` is also called to scope the generated filter choice lists, which read none
of these columns, so putting the joins there pays for them on a query that cannot use them.

The view is the only layer that knows it is about to render three columns off the sample's location
and read the sample's dataset for the link suppression. Asking for the data where the need is known
is also what keeps the requirement testable: the flat-query assertion covers the measurement listing
specifically, and it is asserting a property of that page rather than of a queryset method used in
several places for different reasons.

**ADR:** none - folded into docs/adr/0018-publication-is-a-queryset-method-not-a-default-manager.md, under consequences.

---

## D14 — Comparing a page across `published` states means blanking the CSRF token first

**Decision:** T015's "renders identically" tests (`TestNonCollectionPagesIgnorePublished`,
`tests/test_core/test_dataset/test_views.py`) compare two responses to the same page, one fetched
with the record `published=False` and the other `published=True`, with each response's
`csrfmiddlewaretoken` value blanked before the comparison.

**Why:** the first run of the update-page test failed on a page that has nothing to do with
`published`, at the point where `csrfmiddlewaretoken` differs. Django's CSRF middleware masks the
token afresh per response by design, so two GETs to the same form-carrying page from the same
session are never byte-identical even with no feature code involved. Comparing raw response bodies
across any page with a form will trip on this the same way, so every test in the class blanks the
token rather than only the one that first surfaced it.

**Revisit if:** a later story (US-2 onward) adds its own "renders identically" or snapshot-style
comparison against a page carrying a form — reach for the same helper rather than re-discovering
this.

**ADR:** none - test construction, local to the test that carries it.

---

## D15 — Proving the migration's effect on existing rows without replaying it

**Decision:** T002's second assertion (`TestDatasetPublished.test_every_existing_dataset_reads_back_unpublished`,
`tests/test_core/test_dataset/test_models.py`) proves "every existing row reads back unpublished"
by creating several datasets through the ordinary factory route, none of them naming `published`,
and reading them back through `Dataset.all_objects`. It does not replay `0012_dataset_published.py`
against a database that already held rows.

**Why:** the suite runs with `--no-migrations` (plan.md, Technical Context), so the test database's
schema is built directly from current model state — there is no window in which the migration can
be applied to a database that already held pre-feature rows. `0012_dataset_published.py` is a bare
`AddField` with no data-migration callable to invoke directly either, unlike the forward-rewrite
migration `TestStatusMigration` exercises in `test_sample/test_models.py`. What the acceptance
criterion is actually asking for — that a row nobody touched ends up `False` — is fully expressed by
the field's own default, so a batch of untouched rows read back through the unfiltered manager is
the closest available proof.

**Revisit if:** the project ever drops `--no-migrations` from its test configuration, or this
migration grows a data-migration step — either would make a direct replay both possible and the
stronger test.

**ADR:** none - test construction, local to the test that carries it.

---

## D16 — The empty-state message overrides the hook, not just the attribute

**Decision:** `DataTableView` (T027) overrides `get_empty_state_message()` itself, returning its
own string unconditionally, rather than only setting the `empty_state_message` class attribute the
brief's own wording named.

**Why:** `MVPListViewMixin.get_empty_state_message()` — the base hook — only returns
`self.empty_state_message` when `self.show_action("create")` is true, since the shell's own copy is
written to point at a create button. `DataTableView` declares no `show_create_action` (this is a
read-only listing), so `show_action("create")` is always `False`, and setting the attribute alone
would leave the message permanently suppressed — `get_empty_state_heading()`/`message()` are also
built per-instance from `self.model_config`, which a class attribute cannot express either way.
T022's acceptance criterion requires both the heading and the message to actually render, which only
overriding the hook satisfies.

**Revisit if:** this view ever gains a create action of its own - re-check whether the show-gate
should apply once there is a button for the message to point at.

**ADR:** none - an override site inside one view, discoverable from the base hook it overrides.

---

## D17 — Two things a page-level query count has to control for

**Decision:** `TestQueryCount` (T024, `tests/test_contrib/test_collections/test_views.py`) measures
`CaptureQueriesContext` around a real `client.get()` of the listing, and controls for two sources of
noise before it counts: `orbit` is disabled for the class through `settings.ORBIT`, and the page is
fetched once before either measurement. One row and a full page then both cost 9 queries.

**Why:** FR-020 and SC-006 are claims about the listing *page*, so the count has to be taken around
the request. Two things obscure it, and neither is the feature's.

The first is `orbit`. It writes a row per recorded request, and it reaches signals by monkey-patching
`Signal.send` globally and `repr()`ing every kwarg — which, under Django's
`instrumented_test_render`, reprs the render context and re-evaluates whatever queryset it still
carries. Its writes land in the same count as the page's own. Setting `RECORD_SIGNALS: False` is not
enough, because the request recorder is a separate switch; `ENABLED: False` covers both, and
`orbit.conf.get_config()` reads `settings.ORBIT` at call time, so the override takes effect without
touching the dependency.

The second is first-request warmup. The first request in a test process populates the site cache and
creates the identity records, with their savepoints — around fifteen queries that the second request
never repeats. Uncontrolled, that makes the *one-row* count the larger of the two, so the assertion
fails in the direction opposite to the defect it is looking for.

Both controlled, the test does its job: removing the `select_related` from
`DataTableView.get_queryset()` takes the sample listing from 16 queries to 92 and fails both cases.

**Revisit if:** `orbit` gains a documented test-mode switch — prefer it to disabling the app — or the
listing grows a genuinely per-page query whose count moves with something other than row volume.

**ADR:** none - measurement hygiene for one test, recorded in that test's own docstring.

---

## D18 — Testing a related-record filter for a relation the schema doesn't have

**Decision:** `TestPublishedChoiceLists` (T036, `tests/test_registry/test_factories.py`) tests the
sample and dataset branches of `FilterFactory._get_smart_filters`'s new publication scoping against
a real model (`ExampleMeasurement`, with `fields=["name", "sample"]` / `["name", "dataset"]` passed
directly to `FilterFactory`), but declares a throwaway model for the measurement branch:

```python
class MeasurementReferrer(models.Model):
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)

    class Meta:
        app_label = "test_app"
```

**Why:** no registered type anywhere in the schema has a foreign key to `Measurement` — samples
reference datasets and locations, measurements reference samples and datasets, nothing points the
other way. T040's given/when/then names all three relation targets explicitly, so the branch needs
a real test rather than an inference from the other two. `tests/test_registry/conftest.py` already
carries an autouse fixture that clears every `test_app`-labelled model after each test, the same
mechanism `test_config.py`'s fuzzy-match tests use for their own throwaway models — this reuses it
rather than inventing a second convention.

The sample/dataset cases deliberately do **not** use `MeasurementFilterMixin`'s own `sample`/
`dataset` declared filters (visible on `ExampleMeasurement`'s generated filterset when those field
names are left out of the explicit `fields` list): those are set dynamically in the mixin's own
`__init__` and are unrelated to `_get_smart_filters`, which T040 is scoped to. Passing `fields=
["name", "sample"]` / `["name", "dataset"]` explicitly is what makes `_get_smart_filters` generate
its own override for that name, shadowing the mixin's version — the same pattern
`TestFilterFactoryMeasurementBranch` (pre-existing, same file) already relies on for `"dataset"`.

**Revisit if:** a future feature gives some type a real foreign key to `Measurement` — the
throwaway model can then be replaced with that registration, the way `TestPublishedChoiceLists`'s
sample/dataset cases already use `ExampleMeasurement` directly.

**ADR:** none - test construction, local to the test that carries it.

---

## D19 — Pinning `table.order_by` directly, not just page disjointness

**Decision:** T037's `TestOrdering.test_unsorted_order_is_stable_and_repeatable_across_pages`
forces every created row to one `added` timestamp (rather than staggering them, as `TestPaging`
does) and asserts both that two pages of the same listing never repeat or skip a row, *and* that
`response.context["table"].order_by` contains `id`.

**Why:** the page-disjointness half of this test passed before T041 existed. Postgres returns tied
rows from repeated, unmodified queries in the same session consistently in practice, so the forced
tie did not reproduce a visible repeat-or-skip in this environment even with no tie-break declared —
confirmed by running it against the pre-T041 tree. A test that already passes proves nothing was
just built (`craft-tdd`), so `TestOrdering` also pins the actual mechanism directly: before T041,
`table.order_by` was `None` (`self.data.ordering` inspects `queryset.query.order_by`, which stays
empty for a queryset that only ever inherits ordering from `Model.Meta.ordering` — the table library
never sees it, and applies no explicit order of its own at all). After T041, `Meta.order_by =
("added", "id")` (`SampleTable`) means `id` reliably survives `order_by`'s column-membership check,
because `id` is declared on `BaseTable` and inherited by every generated table regardless of which
fields a type registers, while `"added"` itself is filtered out for any type that does not list it.

**Revisit if:** `django-tables2`'s `TableData.ordering` starts consulting `Model.Meta.ordering`
directly — the `order_by is None` case would then need re-checking, since a currently-`None`
`table.order_by` would report the model's own (still non-unique) order instead.

**ADR:** none - test construction, local to the test that carries it.

---

## D20 — T045/T046 swap `AppMenu` for an isolated `Menu`, not `override_settings(INSTALLED_APPS=...)`

**Decision:** T045's empty-registry test and T046's missing-node test both monkeypatch
`fairdm.contrib.collections.apps.AppMenu` to a fresh, detached `flex_menu.Menu` instance for the
duration of the test, rather than using `override_settings` to remove `fairdm.contrib.collections`
from `INSTALLED_APPS` as the acceptance criteria's wording suggested.

**Why:** `fairdm.menus.menus` — the module whose import declares the real `Samples`/`Measurements`
nodes on the real `AppMenu` — is only ever imported as a side effect of
`fairdm.contrib.collections.apps` importing `fairdm.menus` at module load. By the time any test
runs, that import has already happened once, for the whole test process; Python's module cache
means a second, mid-test `apps.set_installed_apps()` call (`override_settings`'s actual mechanism
for `INSTALLED_APPS` — confirmed in `django/test/utils.py`) does not re-run that side effect for
whichever apps stay installed, and does not undo it for the one being removed either, because the
already-created `MenuItem` objects are mutated in place, not rebuilt. The real `AppMenu` singleton
would carry its already-populated children throughout the override, and a test built on that
mechanism would pass or fail independently of anything this story built. Swapping in an isolated
`Menu` gives full control over exactly what nodes exist before `populate_data_collection_menu()`
runs — pre-created-empty for T045 (FR-040, mirroring `menus.py`'s unconditional declaration),
entirely absent for T046 (FR-041/R8's "renamed or absent node") — and is provably free of
cross-test leakage: the swap is a `monkeypatch.setattr`, reverted automatically, and the isolated
`Menu` is detached (`.parent = None`) from the real `flex_menu` root immediately after construction.

**Revisit if:** a later story needs to prove FR-041's literal claim (the *entire* navigation, not
only Samples/Measurements, renders with `collections` uninstalled) — that would need the
`fairdm.menus import` moved off `fairdm.contrib.collections.apps` so it stops depending on that
app's install status at all, which is a change to `fairdm/menus/menus.py` / `apps.py`'s import
graph outside this story's scope (prohibited: "Do not edit `fairdm/menus/menus.py`").

**ADR:** none - test construction, local to the tests that carry it.

---

## D21 — FR-041, what was fixed and what is only asserted statically

**Decision:** `fairdm/apps.py` now imports `fairdm.menus` at module level, so the site navigation is
declared by the framework's own app config rather than as a side effect of
`fairdm.contrib.collections.apps`. `TestNavigationDoesNotDependOnThisApp`
(`tests/test_contrib/test_collections/test_apps.py`) asserts that import is present, that the menu
module is loaded once the framework config is, and that the core headings exist. It does **not**
boot a portal with the collections app uninstalled.

**Why the fix:** `fairdm.menus.menus` declares Home, Projects, Datasets, Literature, Community and
Documentation as well as the two headings this feature populates, and until now the single module
importing it anywhere in the codebase was the collections app's own `apps.py`. A portal that dropped
that optional app would have got no navigation at all — not a crash, simply an empty tree. FR-041
names exactly this: loading the navigation must not depend on that application's start-up. The
import is at module level rather than in `ready()` because `fairdm.menus.menus` imports no models,
only translation, `flex_menu` and `mvp.menus`.

**Why the assertion is static:** the honest test is a boot that never loads the app, and neither
route to one works here. `override_settings(INSTALLED_APPS=...)` calls `apps.set_installed_apps()`,
which re-runs no module imports and undoes no import side effects, so the already-declared menu
would still be standing and the test would pass with or without the fix. A subprocess boot on a
settings module with the app filtered out does not get far enough to answer the question: it fails
in `research_vocabs`, which reads a cache alias (`vocabularies`) that `tests/settings.py` does not
define, at a point in app loading it apparently does not reach in the ordinary configuration. That
is a property of the test settings, unrelated to the navigation, and chasing it belongs in its own
piece of work rather than inside this story.

**Revisit if:** the test settings gain a `vocabularies` cache alias, or the suite gains a fixture
that boots a second settings module — either makes the real test cheap, and it should replace the
source-level assertion at that point.

**ADR:** none - a defect with one correct answer, not a choice between options; the import is guarded by its own test.

---

## D22 — T054 landed inside T069's commit, not its own

**Decision:** the switcher's rendering, its count-gate (`{% if %}` only past one combined entry) and
its two translated group headings all went into `listing.html` at T069, not held back for a
separate T054 commit.

**Why:** T069 creates one file, and its own acceptance criterion already names the switcher's
placement ("so the switcher renders under the heading") as part of what makes T069 done. A Django
`{% block %}` cannot be committed half-written across two commits when the second half is the body
of an `{% if %}` the first half opens — there is no intermediate state of that template that parses
without also deciding the gate and the headings. T053 (the same commit boundary as always) is what
made the block's data real; T069's structure was already complete before T053 landed, verified by
running the pre-existing (non-switcher) view tests against it while `sample_listings`/
`measurement_listings` were still absent from context (they render as an empty, ungated switcher via
`{% with sample_count=sample_listings|length ... %}`, never raising).

**Revisit if:** a future story needs to add a second gate to the same block independent of T069's
placement — at that point the file has enough independent history that a further change is its own
commit again, this one just could not be split at the seam the task list drew.

**ADR:** none - a commit-boundary note, spent on the commit it describes.

## D23 — The eight test files flagged across the feature diff were appended to, never edited

**Decision:** the guardrail that flags changes to tests which existed before this branch reports
eight files at convergence — `tests/test_core/test_abstract.py`, four under
`tests/test_core/test_dataset/`, `tests/test_core/test_measurement/test_managers.py`,
`tests/test_registry/test_config.py` and `tests/test_registry/test_factories.py`. All eight are
approved.

**Why:** the flag is raised per file, and every one of these files gained lines and lost none. The
whole feature diff deletes zero lines anywhere under `tests/`, checked directly rather than read
off the report: `git diff 8c9290f..HEAD -- 'tests/**'` has no removed line at all. What the eight
have in common is that this feature adds a `Test*` class to an existing module, which is what the
testing structure standard asks for — a cross-cutting test belongs in the module of its subject,
not in a new file named after the concern.

**What would not be approvable:** a changed assertion, a narrowed parametrisation, a deleted case.
None of those appear, at convergence or after the review round. Re-run the check against the merge
base rather than trusting this entry if the branch is rebased.

**ADR:** none - a triage record for one run's guardrail output, spent when the branch merges.

## D24 — The review found a publication leak in the filter dropdowns, and the fix belongs to the view

**Found:** every listing's related-record filters offered the names of unpublished records to
anonymous readers. `SampleFilterMixin.__init__` assigns its `dataset` choice list from
`Dataset.all_objects.all()`, and `MeasurementFilterMixin.__init__` assigns `dataset` from
`Dataset.objects.all()` and `sample` from `Sample.objects.all()` - none of which applies
publication. Those assignments run at instantiation, after the class-level scoping T040 added, so
they overwrote it. Four of the demo's eight registered types were affected. This is FR-030 and
SC-002 stated plainly, and the leak was live.

**A second hole, wider than the one reported:** `CustomSample` supplies its own `filterset_class`,
which is a documented tier of the configuration API, and a registration may also override
`get_filterset_class()` outright. In either case the factory never runs, so a fix inside the
factory reaches neither. Scoping the generated filters at build time is not enough on its own.

**Settled:** `PublishedChoicesMixin` (`fairdm/registry/factories.py`) narrows every filter whose
own queryset is over `Sample`, `Measurement` or `Dataset`, and `DataTableView.get_filterset_class`
applies it to whatever it is handed. That is the one place every listing's filter set passes
through, whichever tier produced it.

**Why it reads each filter's queryset rather than the model field:** the same pass then covers a
many-to-many field or a reverse relation that django-filter generated a choice list for itself,
which the review's second finding raised as a gap that would open the moment a portal registered
such a relation. Reading the queryset also leaves alone a relation publication says nothing about:
the measurement mixin's `polymorphic_ctype` filter is already scoped to the registered types and
comes through untouched, which is asserted.

**Why the view and not the two core mixins:** those mixins are inherited by pages outside this
feature, and FR-006 forbids changing behaviour outside the listings specified here.

**Proof:** five tests in `TestFilterChoicesOnTheRenderedPage` measure the filter set on the
rendered page, not the generated class - the existing class-level test never runs the `__init__`
that caused this, and passed throughout. Removing the fix turns four of the five red. The fifth is
the negative control.

**ADR:** none - the rule it enforces is already ADR 0015, which gained a paragraph saying the
choice lists are covered by it and that the scoping belongs where the listing resolves its filter
set.

---

## D25 — A test comment that excused the defect, and what it cost

**Decision:** `tests/test_contrib/test_collections/test_tables.py` carried a comment reading "a
filter widget elsewhere on the page legitimately lists every sample by name, published or not
(FR-030's scoping is a later story)". It is corrected, and it points at the tests that now cover
the filters.

**Why this is worth a decision rather than a silent edit:** the comment is a written statement that
FR-030 belonged to a later story. FR-030 is in this feature's own specification and says the
opposite. Between them, the comment and the guardrail's own report made the leak in D24 look
settled: the guardrail reported no weakened test, the suite was green, and the one place the
behaviour was described in writing said it was out of scope. Nothing was going to fail. Only
reading the requirement against the code found it.

**Not a guardrail concern.** Both of the test modules revised at the review round -
`test_tables.py` and `test_apps.py`, whose stand-in menu moved with the check in T079 - are files
this branch created. No test that existed before the branch was changed or removed by this feature,
which is what D23 records.

**ADR:** none - a note about one comment in this feature's own tests, spent when the branch merges.
