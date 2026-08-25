# Decisions — 014, managing a dataset through the portal

The previous specification was written on 2026-05-12, before the project's equivalent pages were
rewritten, and describes four standalone views. This records what was found when it was checked
against the code on 2026-08-25, which way each disagreement was settled, and why.

The short version: the code does very nearly what the old specification said, and the old
specification asked for the wrong thing. The four views work and are tested. What they are not is
part of the portal — no page links to them, they sit under two different address prefixes, and the
record's own metadata pages each take a navigation entry of their own. The project's pages had all
the same faults and were repaired in 013. This feature applies that repair to datasets.

---

## D1 — Visibility joins the feature, and what "public" means is settled

**Previous specification**: FR-018 and the assumptions excluded `visibility` from both forms
deliberately, deferring it to "a dedicated publish/unpublish workflow outside the scope of this
feature".

**Code**: agrees. Neither form carries the field, and the model defaults a dataset to private.

**Settled**: visibility is edited on the creation page and on the update page, and the
specification now states what it means. A **public** dataset is one whose *metadata* anyone using
the portal may read. The *data* beneath it is a separate matter, reached and published through a
process that portal administrators or peer review control, and that process is a later feature.

**Why**: the workflow the exclusion deferred to is R22 and does not exist, so the effect of the
exclusion was that a dataset created through the portal was private permanently, with no portal
page able to change it. That is not a deferral, it is a dead end. The deeper reason is that the two
things were conflated: saying what you are working on is a community act and belongs to the
researcher, while releasing data is a publication act and belongs to a reviewed process. One switch
cannot serve both, and the one this feature offers is the first.

**ADR**: to be decided during planning — the metadata/data distinction is a framework-wide idea and
outlives this feature.

---

## D2 — No deletion refusal for datasets, a warning instead

**Previous specification**: assumptions said "no model-level deletion guard is required for
datasets", protected only by name confirmation and the permission check.

**Code**: agrees.

**Settled**: the old specification's outcome stands and its reasoning is replaced. A **published**
dataset may not be deleted, because others may cite it and reuse its data. Publication is the later
feature above, and no such state exists yet, so nothing in this feature refuses a deletion — not
even for a public dataset, and not for one holding samples and measurements. What the deletion page
gains is a prominent warning naming what will go with the record: how many samples, how many
measurements, and that descriptions, dates and identifiers go too.

**Why**: the right question is not whether a record is visible but whether anything outside the
portal has come to depend on it, and today nothing can. Refusing to delete a public dataset would
punish the researcher for having advertised their work, and would make the visibility switch a trap
— flip it once and the record can never be removed. The real protection arrives with publication.
Meanwhile the honest defence against an accidental deletion is telling someone what they are about
to destroy, which is exactly what the page never did.

---

## D3 — The project's deletion refusal is left standing, and left wrong

**Previous specification**: silent; this is the project's page.

**Code**: `Delete.get_context_data` and the signal behind it refuse to delete a project while any
of its datasets is public, and name them.

**Settled**: unchanged by this feature, and FR-067 says so explicitly. The inconsistency is
recorded as its own issue.

**Why**: under D1 that refusal is keyed on the wrong state. It stops a project being deleted
because a dataset's *metadata* is public, which by the definition just settled is no reason at all,
and it contradicts D2 one level up: a dataset that may itself be deleted freely can still make its
project undeletable. Correcting it is a change to the project's behaviour, decided in 013 and
merged, and reopening it inside a dataset feature would put a second specification's requirements
in play with no gate of their own. The two candidate answers are recorded on the issue: refuse
while any dataset is attached at all, or detach the datasets before deleting.

---

## D4 — The keywords page is removed, not carried over

**Previous specification**: silent on keywords.

**Code**: a `Keywords` page is registered against the dataset with a navigation entry of its own,
built on a form that reads vocabularies out of portal settings. It is the only registration of that
page anywhere — no other record type has one.

**Settled**: the page is removed. Keyword editing is rebuilt whole, against the controlled
vocabularies, in a later specification.

**Why**: it had to move or go, because a record's pages now carry one navigation entry between them
(D7). Moving it would mean adopting an interface that is going to be replaced entirely, and paying
to relocate it first. The project side reached the same conclusion from the other direction: 013
deferred keywords rather than building them. This leaves the two record types consistent, at the
cost of a capability that was reachable only by someone who knew the address.

**Consequence**: the shared base page and its form become unused once this registration goes. That
is left as a finding rather than absorbed here — removing framework surface nothing registers is a
different kind of work with a different risk.

---

## D5 — The DOI box becomes identifier rows

**Previous specification**: FR-028 and the key entities described a dedicated `doi` field on the
form, format-hinted, which created and cleared an identifier record on save.

**Code**: agrees, and the mechanism is more delicate than the specification suggests — the field
writes through `update_or_create` on save and deletes the row when the box is emptied, none of
which is visible from the form.

**Settled**: the box goes. Identifiers are edited as typed rows on the update page, the same
facility the project's page uses.

**Why**: a dataset's identifier vocabulary holds DOI alone today, so the two arrangements are
equivalent right now and the bespoke one is strictly more code. The moment a second identifier type
is admitted, the box has to be replaced anyway, and until then it is a second way of writing the
same records that has to be kept in step with the first. The capability the researcher loses is
none; the format hint the box carried belongs to the identifier vocabulary, not to this page.

---

## D6 — The creation form asks for four things

**Previous specification**: FR-011 required `name`, `project` and `license`, with the project
optional.

**Code**: disagrees with the specification and with itself. The view sets its own field list of
`name`, `project` and `license` while the form class the specification names is commented out above
it, so the declared form — with its labels, help text, widgets and project filtering — is not used
at all. The form class it names, meanwhile, lists `name` and `license` and omits the project.
`get_form_kwargs` has its one meaningful line commented out, so the project field is never narrowed
to the researcher's own projects.

**Settled**: the specification wins on every point, and gains visibility. The creation page asks
for name, visibility, licence and project, uses the declared form narrowed to those four fields,
and passes the request so the project field offers the researcher's own projects and nothing else.

**Why**: the direction of this drift is that the code is wrong, and it is wrong in a way that
matters — an unfiltered project field on a form is a list of every project's name, private ones
included, handed to anyone who opens the creation page. Beyond that, a view that declares a field
list bypasses every label, help text and widget the form declares, which is why the creation page
looks unlike the update page today. FR-022 states the rule that prevents it recurring: one declared
form, narrowed, never a second field list.

**Also settled**: a second route into creation, from a record that already implies the project and
fills the field in advance, is a later feature. The old specification's FR-009a removed a
query-parameter version of exactly that, and removing it was right — it is worth building properly
or not at all.

---

## D7 — A dataset's pages are one registered collection, not one registration each

**Previous specification**: specified four independent views and never mentioned navigation, the
dataset's own page, or how anyone would reach anything.

**Code**: the dataset's own page is a standalone view; its update and deletion pages are standalone
views; its descriptions and key dates are separate registrations, each taking a navigation entry.
Nothing links any of them to anything. No overview page is registered for a dataset at all, which
is why a template written for one sits in the app unused.

**Settled**: the dataset's own page becomes its registered overview, and the update, descriptions
and deletion pages belong to that registration rather than taking entries of their own. The strip
carries one entry for the whole collection, and the dataset's page draws the links.

**Why**: this is 013's D10 applied to datasets, and the argument is unchanged: a page per
navigation entry does not scale past a handful, and a record's management pages are one collection
from the reader's point of view. It also fixes the reason none of these pages was reachable — an
address nobody links to is a page nobody has.

---

## D8 — One address prefix, and it is the plural one

**Previous specification**: FR-029 to FR-031 named the four routes and required the plural form,
silently, by naming them.

**Code**: both forms answer. The dataset itself and its standalone pages sit under `datasets/`,
while its registered pages sit under `dataset/`. The two were never reconciled.

**Settled**: the plural form, throughout. A dataset keeps the address it has and its pages become
segments below it, so the pages registered against a dataset change address.

**Why**: 013's D11, and the convention it settled, applied here. The singular form leaving the
codebase is tracked separately as an issue covering the record types this feature does not touch.

---

## D9 — The listing's filters are this feature's business after all

**Previous specification**: the assumptions disclaimed the filter set entirely — "requires no new
filtering fields", "its internal implementation is outside this feature's scope".

**Code**: one of the filters the listing offers raises an error every time it is applied, because it
filters on a Python property rather than a column. Another offers a choice between visibilities on a
listing that shows public datasets only, so neither choice can change anything. A third offers every
project in the portal by name, private ones included, to anyone who opens the page. The only test
touching the broken one asserts that it appears on the form, which never runs a query.

**Settled**: the listing owes working filters. The broken one is repaired, the meaningless one is
removed, and the project filter is narrowed to projects the visitor may see. FR-006 and FR-007 state
the requirement in a form that does not depend on today's filter set.

**Why**: the old disclaimer drew the line in the wrong place. Whether a filter class is this
feature's to design is a different question from whether the page may offer a control that errors,
does nothing, or discloses the names of private records. Those are properties of the listing, and
the listing is this feature's page.

---

## D10 — Undocumented behaviour, now written down

Behaviour the code has and the old specification never mentioned. All of it is kept.

- **A dataset nobody may see answers "not found", not "refused"**, on every page, so that the portal
  does not confirm a private dataset exists to someone guessing addresses. The API does the same.
  Worth stating, because the obvious reading of a permission requirement is the other answer.
- **The listing shows public datasets because the default way of asking for datasets excludes
  private ones**, rather than because the listing filters them out. The old FR-003 named the filter
  the listing used to apply. The mechanism changed when the model was rewritten and the outcome is
  unchanged and better — a page that forgets to filter now shows nothing rather than everything.
- **The licence carries a portal-configured default**, applied when a dataset is created, and the
  form pre-selects the same value. Both are deliberate.
- **The publication reference field removes itself** when the portal is running without the
  literature app installed. The page works either way.

---

## D11 — Requirements state behaviour, not the code that produces it

**Previous specification**: nineteen of its twenty-seven requirements named a class, an attribute or
a module — which base class a view inherits from, which attribute it sets, which file a form lives
in. One required an override to be removed.

**Settled**: rewritten to state what a person can do and what the portal guarantees. Where the
requirement really is to use an existing facility rather than build a second one, it says so in
those terms, per Article XIV.

**Why**: 013's D8, unchanged. A requirement naming a class is satisfied by a view that inherits it
and does nothing, and is broken by a rename that changes no behaviour. It also pre-empts the design
— several of the old requirements are now false not because the behaviour regressed but because the
right structure turned out to be different.

---

## D12 — Two pre-existing test files were edited while building the update page, and both edits are approved

**Flagged**: the guardrail on modifying tests that already existed raised two flags for the update
page's work, one per file.

**Settled**: both are legitimate, and neither weakens an assertion.

- `tests/test_core/test_dataset/test_forms.py` — six tests covering the DOI text box and the form's
  save override were deleted, both of which the plan retires: a dataset's external identifiers,
  DOI included, are now edited as rows on the update page, the same way every other record edits
  them. Four tests covering the visibility field that replaced it were added. Three unrelated tests
  had `visibility` added to their submitted data, since it is now a required field — their
  assertions are untouched.
- `tests/test_core/test_dataset/test_views.py` — the update page's tests were repointed from the
  retired standalone address to the new one, which is the same repair 013 made on the project side.
  One case changed subject: a signed-out visitor is now sent to sign-in from a *public* dataset's
  update page, because on a private one the page answers "not found" instead, which is a new
  assertion of its own rather than a replacement.

**Why it matters**: a deleted test is the cheapest way to make a red suite green, so deleting one
has to be justified against something written down beforehand. Here it is: the requirement the
deleted tests covered was withdrawn at the specification gate.

---

## D13 — A measurement's link to its sample became a restriction rather than a protection

**Flagged**: FR-049 requires that deleting a dataset takes the samples and measurements beneath it.
It could not, and this was not a defect in the deletion page. `Measurement.sample` was
`on_delete=PROTECT`, and Django's collector raises against a protected row even when that row is
itself scheduled for deletion in the same operation. Samples with measurements recorded on them is
the ordinary shape of a dataset carrying data, so in practice no dataset holding data could be
deleted at all — through this page, through the project's page, or through the shell.

**Settled**: `on_delete=RESTRICT`, with a migration. It refuses the same thing at the level the
protection was placed to defend — a sample cannot be deleted out from under a measurement that
needs it, whether the measurement belongs to the same dataset or another one — and permits the
cascade when the measurement is going too. The existing assertions that a sample cannot be deleted
while measured are unchanged in substance; only the exception they expect differs.

**Why it matters**: the requirement said data attached to a dataset is deleted with it and warned
about beforehand, not that its presence blocks the deletion. Refusing was not a stricter reading of
the requirement, it was a different one, and it would have shipped as a page that works on empty
datasets and fails on real ones.

**Consequence**: `RestrictedError` is a sibling of `ProtectedError` under `IntegrityError`, not a
subclass, and the shell catches only the latter. A dataset whose samples are measured by another
dataset therefore raised out of the deletion page rather than drawing the refusal the template
already has. Handled in `FairDMDeleteView`, so the project's deletion page is covered by the same
path rather than by a copy, and raised upstream as django-mvp#308 to be removed when that lands.
