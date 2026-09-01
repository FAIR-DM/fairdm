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
