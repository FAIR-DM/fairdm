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
