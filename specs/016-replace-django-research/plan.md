# Implementation Plan: Controlled vocabularies replace django-research-vocabs

**Branch**: `016-replace-django-research` · **Spec**: `spec.md` · **Research**: `research.md` · **Decisions**: `decisions.md`

**Epic**: #195 · **Stories**: #305–309 · **Pull request**: #310

## Summary

Six controlled-term surfaces split two ways. Four closed sets — sample status and the description,
date and identifier types — become Python-declared choice sets whose members each carry a value, a
label and a definition, built on a fifteen-line subclass of Django's own choices metaclass. Their
stored values do not change, so they need no data conversion. Two open surfaces — contribution roles
and keywords — become concept references held by `django-controlled-vocabularies`, with FairDM's own
vocabularies shipping as SKOS files in the package and loading through a framework command. One
atomic data migration carries existing roles and keywords across, resolving every term before it
writes anything. The retired library is then removed entirely.

## Technical Context

**Language**: Python 3.13 · **Framework**: Django, `>=5.2` after this change (see D-016)
**New runtime dependencies**: `django-controlled-vocabularies>=0.1.0,<0.2.0` and its mandatory
`django-tomselect`. **Retained as a migration-only dependency**: `django-research-vocabs` (a git
dependency, never on an index), which nothing imports after this change but which the existing
migration graph still needs installed — see D-019.
**Storage**: PostgreSQL in production, SQLite in the suite. **Testing**: pytest, Article I test-first.

### What the plan rests on

| Fact | Source |
|---|---|
| All 98 existing terms already carry a `gettext_lazy` definition | `research.md` §2 |
| A metaclass subclass carries a third member attribute; a naive three-tuple crashes | `research.md` §3, run in this environment |
| `ConceptsField` forces `PROTECT`, refuses `through=`, and generates its through table on Django's standard `<owner_table>_<field>` name — the same one the current field uses | `research.md` §4, §6 |
| Twelve migration files carry a graph edge on the retired library, which needs it installed rather than merely importable | `research.md` §1 |
| The package's import is an idempotent upsert by address, inside one transaction | `research.md` §4 |
| `django-tomselect`, its middleware and a mounted route are mandatory, not optional | `research.md` §4 |
| The package requires Django `>=5.2`; FairDM still tests 5.1 | `research.md` §5 |

## Constitution Check

| Article | Bearing on this feature | Verdict |
|---|---|---|
| I — Test-First | Every behaviour change is driven by a failing test first. The data migration gets a test that populates the old shape, migrates, and asserts the new one. | Complies |
| II/III — Simplicity, Anti-Abstraction | Fifteen lines of metaclass rather than two new dependencies (D-015). One rich-choices mechanism, not one per surface. | Complies |
| VI — Documentation | Public surface changes ship their docs in the same pull request. An upgrade guide is required by FR-023, and the six pages naming the retired library are rewritten. | Complies |
| VII — Dependency discipline | Two dependencies added, one removed. `django-controlled-vocabularies` is the feature; `django-tomselect` arrives with it and is not optional. `deptry` must stay green. Justification recorded in D-018. | Complies, with a justification |
| VIII — Internationalization | Labels and definitions carry across already wrapped in `gettext_lazy`. No new hard-coded user-facing string. | Complies |
| IX — Data-model conventions | Both converted fields are foreign-key shaped and get their index from the key. `verbose_name` and `help_text` are restated on every field this feature touches. Branch migrations are consolidated at convergence; the data migration is exempt from regeneration and stays standalone. | Complies |
| X/XI — Test structure, cohesion | New tests mirror the source tree and group into classes. | Complies |
| XIII — Declarative modelling | The closed sets stay declarative; the open ones become data a research team can curate, which is the article's own example. | Complies |
| XV — Production-grade defaults | The four closed sets need no database, so a fresh portal has working metadata before any import runs. | Complies |

No entry in Complexity Tracking: nothing here needs a constitutional exception.

## Design

### 1. The rich-choices mechanism (US-1)

A new module `fairdm/utils/choices.py` gains a metaclass subclassing Django's `ChoicesType`, plus a
`TextChoices` base built on it. A member is declared in the natural order:

```
STORED = "stored", _("Stored"), _("The specimen is held in long-term storage.")
```

The metaclass pops the third element before delegating, then attaches it to the member. `.choices`,
`.labels`, `.values` and `.names` keep Django's exact semantics, so `choices=` on a plain
`CharField` behaves as it does today and migrations render identically.

Because `choices=` flattens to two-tuples, definitions are reached two ways: by iterating the class
in a template, and through a `definitions()` mapping plus a template filter for the case where only
a stored value is in hand. Both are needed — the form path has the class, the detail-page path
often has only the value.

`fairdm/utils/choices.py` already holds `Visibility`; the new base joins it rather than starting a
new module.

### 2. The closed sets (US-1)

Five vocabulary classes become rich-choices classes, keeping every member name and stored value:

| From | To | Members |
|---|---|---|
| `FairDMSampleStatus` | `SampleStatus` | 5 |
| `FairDMDescriptions` | `DescriptionTypes` | 17 |
| `FairDMDates` | `DateTypes` | 17 |
| `FairDMIdentifiers` | `IdentifierTypes` | 10 |
| `DataciteContributorRoles` | `DataciteContributorTypes` | 14 |

The per-record-type groupings (`Project`, `Dataset`, `Sample`, `Measurement`, `Contributor`) are
today expressed as SKOS collections read through `from_collection(...)`. They become explicit
subsets declared on each class and returned as a plain choices list, which is what the generic
models already consume. `DataciteContributorRoles`'s groupings are dangling and are rebuilt
correctly rather than carried across (`research.md` §2).

`DatasetDescriptions` is dead and is deleted rather than converted.

FR-001 and US-1 acceptance scenario 5 — a portal author finds no supported route to add a member —
are satisfied by construction rather than by a test. The closed sets are module-level Python enums
with no registry and no settings hook, and T038 deletes the two settings that previously let a
portal substitute its own vocabulary classes (D-004).

The generic model machinery that pushes `VOCABULARY.choices` onto a `type` column keeps working
unchanged — it receives a choices list either way. What changes is where the list comes from.

### 3. Vocabularies as shipped files (US-2)

`FairDMRoles` becomes `fairdm/vocabularies/fairdm-roles.ttl`, a SKOS Turtle file carrying all 29
concepts with their labels, definitions and the four groupings as collections.

A management command `load_vocabularies` wraps the package's import and defaults to every file in
that directory (D-009). It supports `--dry-run` by passing through, and it is idempotent because
the underlying import upserts by address.

A read-only admin for schemes and concepts is registered by FairDM, replacing what the retired
library provided (`research.md` §4).

Settings work, all of it mandatory: `controlled_vocabularies` and `django_tomselect` in
`INSTALLED_APPS`, `TomSelectMiddleware` in `MIDDLEWARE`, the autocomplete route mounted behind a
login requirement (D-022), and `CONTROLLED_VOCABULARIES_BASE_URI` set from the portal's own address.
The retired library's `preload` step comes out of the always-run setup tooling in the same change.

FairDM registers one system check of its own, because the package's checks do not cover three of
this feature's requirements:

- FR-010 requires the startup warning to name the command that loads the vocabularies. The
  package's warning cannot, since the command is FairDM's.
- FR-014 requires a warning when a portal names no keyword vocabularies. The package returns early
  on an empty set, and a field naming no vocabulary is a supported shape there, so nothing fires.
- `CONTROLLED_VOCABULARIES_BASE_URI` defaults to `http://localhost:8000/vocabularies`, and that
  value is not cosmetic — it composes the address that *is* a concept's external identity, is
  persisted on the row and is carried into exported metadata. A portal that forgets the setting
  mints permanent localhost identities. Safe as a package default, unsafe as a portal one.

### 4. Roles and keywords become concepts (US-3, US-4)

`Contribution.roles` becomes a `ConceptsField(vocabulary="fairdm-roles")`. FairDM's own
`m2m_changed` receiver enforcing vocabulary membership is deleted — the field's own receiver does
it (`research.md` §4). Narrowing to a per-record-type collection stays out of scope (D-013).

`keywords` on all five models becomes `ConceptsField(vocabulary=<the configured slugs>)`, read from
a new portal-wide setting. The setting replaces `FAIRDM_DATASET["keyword_vocabularies"]`;
`FAIRDM_PROJECT["keywords"]` is deleted.

Neither conversion happens in place. The new field arrives under a temporary name —
`roles_concepts`, `keywords_concepts` — because the target field's through table takes the same name
as the one the current field already uses, so the two cannot coexist under the original name
(D-020). The rename happens after the upgrade has copied the rows.

Forms, filters, admin narrowing, the autocomplete view and the table renderer all move from the old
concept model to the new one. The old autocomplete view and widgets are deleted rather than
repointed: the package supplies its own, and keeping a second one is the duplication Article III
refuses.

### 5. The upgrade (US-3, US-4)

Three steps in order, of which the middle one is the data migration:

1. **Add**, per owning application: the concept field under its temporary name, which creates a new
   through table alongside the old one.
2. **Convert**, once, in a single atomic data migration.
3. **Drop and rename**, per owning application: the old field goes and the temporary one takes its
   name, which renames its through table onto the original.

The data migration lives in `fairdm.contrib.contributors` (D-021), which is a real installed
application and the furthest downstream of the six that own an affected join table. It declares
`dependencies` on the latest migration of each of `contributors`, `identity`, `project`, `dataset`,
`sample` and `measurement`, plus `controlled_vocabularies`, and `run_before` on each step-3
migration. It:

1. Loads FairDM's shipped vocabularies if the roles vocabulary is absent, so concepts exist
   regardless of operator sequencing and a replay of history is a no-op rather than a re-import of
   whatever the file says at that later date (`research.md` §6).
2. Reads every row of the six old join tables and resolves each concept name against the target
   vocabulary, scoped per source vocabulary (FR-018).
3. If anything fails to resolve, collects **all** failures, then raises with the complete list. The
   migration is atomic, so nothing is written.
4. Otherwise writes every membership row into the new through tables.

It is a data migration, so convergence leaves it standalone rather than regenerating it.

### 6. Retirement (US-5)

Every import, the template override at `fairdm/utils/templates/research_vocabs/base.html`, the
`preload` wiring and every live reference in models, forms, filters, admin classes, tables, settings
and documentation go. The three contaminated migration files are edited to stop naming the library's
field classes and the retired `SampleStatus` stub, which is the minimum that lets that stub be
deleted (D-017). The history is otherwise untouched, per D-007.

What stays, and only until the deferred squash: the distribution and the `INSTALLED_APPS` entry,
each with a comment naming D-019 as the reason. Twelve migration files hold a graph edge on the
application, and a graph edge needs it installed, not merely importable — so uninstalling it would
break a migrate from empty and the test suite with it. The old concept table stays populated as a
side effect, which is worth having: the upgrade's source data survives it.

Six documentation pages name the retired library and are rewritten. The upgrade guide is new.

## Project Structure

### Documentation (this feature)

```
specs/016-replace-django-research/
├── spec.md              # approved at the spec gate
├── decisions.md         # D-001 to D-018
├── research.md          # this plan's evidence
├── plan.md              # this file
├── tasks.md             # the task graph
├── design-review.md     # S3R findings
├── progress.md          # stage log
└── feature-state.json   # the ledger
```

### Source code

```
fairdm/
├── utils/choices.py                     # rich-choices metaclass + base (joins Visibility)
├── vocabularies/                        # NEW: shipped SKOS files
│   └── fairdm-roles.ttl
├── core/
│   ├── vocabularies.py                  # five vocabularies → rich-choices classes
│   ├── choices.py                       # DatasetDescriptions + retired stub deleted
│   ├── abstract.py                      # keywords → ConceptsField
│   ├── sample/models.py                 # status → rich choices
│   └── project/filters.py               # concept filters repointed
├── contrib/
│   ├── contributors/                    # roles → ConceptsField; receiver deleted
│   │   └── migrations/                  # the data migration (D-021)
│   ├── identity/models.py               # keywords → ConceptsField
│   ├── autocomplete/                    # concept view and widgets deleted
│   ├── generic/forms.py                 # keyword form repointed
│   └── collections/tables.py            # renderer dispatch repointed
├── conf/settings/                       # apps, middleware, urls, new keyword setting
├── management/commands/load_vocabularies.py   # NEW
└── admin.py                             # read-only concept admin

docs/
├── portal-development/                  # six pages rewritten
└── upgrading/016-controlled-vocabularies.md   # NEW, required by FR-023
```

## Sequencing

US-1 is independent of everything else and can land first or in parallel. US-2 precedes US-3 and
US-4 because both need concepts to exist. US-5 is last by construction.

The upgrade migration needs both converted fields to exist, so it belongs to exactly one story
rather than to both: **US-4 owns it**, as the later of the two, and US-3 lands the roles conversion
without it. Without that, either both stories author it and collide at convergence, or neither
does and it is never dispatched.

```
US-1 ────────────────────────────────► (independent)
US-2 ──┬──► US-3 ──────────┐
       └──► US-4 + upgrade ─┴──► US-5
```

## Risks

| Risk | Handling |
|---|---|
| The Django 5.1 drop needs a workflow edit and a required-check change, neither of which is mine | Raised with Sam before implementation (D-016). Blocks US-2 onward, not US-1. |
| A term recorded in the live portal resolves to nothing | The upgrade reports all failures and converts nothing (D-011). Failure is visible and safe, not silent. |
| The package's autocomplete does not scale to a large domain vocabulary | Does not affect FairDM's own vocabularies (largest is 29 terms). Raised upstream, not worked around (`research.md` §4). |
| Editing three frozen migration files | The narrowest change that lets the retired stub go, touching no applied state (D-017). Confirmed sound and bounded by the design review: field classes only, no graph edges. |
| The retired library cannot actually be uninstalled | Twelve migration files hold a graph edge on it. The retirement is narrowed to the running framework and the distribution stays declared with a stated reason until the squash (D-019). |
| The converted fields' through table takes the same name as the old one | The new field is added under a temporary name and renamed after the upgrade copies the rows (D-020). An in-place conversion would silently re-point credit at unrelated concepts. |
| `ConceptsField` wraps `full_clean` on the models it is added to | Both fields are `blank=True`, so the added requirement never fires. Verified by test rather than assumed. |

## Complexity Tracking

No constitutional exception is required by this feature.
