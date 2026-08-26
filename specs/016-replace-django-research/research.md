# Research — FS-016: Controlled vocabularies replace django-research-vocabs

Everything here was read from source in this working tree or measured in this project's virtual
environment on 2026-08-26. Version numbers and counts are readings, not recollections.

---

## 1. What the retired library actually holds

Six surfaces, and they do not share a storage shape.

| Surface | Model | Storage today |
|---|---|---|
| `Sample.status` | `Sample` | `ConceptField`, a `CharField` subclass storing the member's attribute name |
| `*Description.type` | four generic models | plain `CharField(max_length=50)`, choices pushed at class construction |
| `*Date.type` | four generic models | same |
| `*Identifier.type` | five generic models | same |
| `Contribution.roles` | `Contribution` | many-to-many to `research_vocabs.Concept` |
| `keywords` | `Project`, `Dataset`, `Sample`, `Measurement`, `Identity` | many-to-many to `research_vocabs.Concept` |

The first four carry no database dependency on the library at all — they are plain character
columns whose `choices` happen to be generated from a vocabulary at import time. Only the last two
hold foreign keys into `research_vocabs_concept`.

`research_vocabs` owns two tables plus a through table. Their contents are derived: `Concept.preload()`
walks the in-memory vocabulary registry and upserts rows, and the framework wires that into its
always-run setup tooling. The rows are regenerable; the join tables pointing at them are not.

### Migration contamination

Three migration files freeze the library's field classes *and* a FairDM vocabulary class object:

- `fairdm/core/sample/migrations/0001_initial.py:12,101` — `ConceptField(..., vocabulary=fairdm.core.choices.SampleStatus)`
- `fairdm/core/sample/migrations/0007_...py:5,20` — `ConceptField(..., vocabulary=fairdm.core.vocabularies.FairDMSampleStatus)`
- `fairdm/contrib/contributors/migrations/0001_initial.py:14,619` — `ConceptManyToManyField(to="research_vocabs.concept", vocabulary=...FairDMRoles)`

Ten further migrations across six apps depend only on the library's app label. Per D-007 the
history is not rewritten, so those import paths must stay resolvable. That is what forces the
retired `SampleStatus` stub at `fairdm/core/choices.py:305` to survive in some form — see §6.

---

## 2. The definitions already exist, all of them

This was the largest open risk in the plan and it is closed.

| Vocabulary | Location | Members | With a definition |
|---|---|---|---|
| `FairDMIdentifiers` | `core/vocabularies.py:6` | 10 | 10 |
| `FairDMDescriptions` | `core/vocabularies.py:230` | 17 | 17 |
| `FairDMDates` | `core/vocabularies.py:407` | 17 | 17 |
| `FairDMRoles` | `core/vocabularies.py:572` | 29 | 29 |
| `FairDMSampleStatus` | `core/vocabularies.py:813` | 5 | 5 |
| `DatasetDescriptions` | `core/choices.py:47` | 6 | 6 |
| `DataciteContributorRoles` | `core/choices.py:89` | 14 | 14 |
| **Total** | | **98** | **98** |

Every label and every definition is already wrapped in `gettext_lazy`. No term needs writing, and
the internationalisation requirement (FR-003) is satisfied by carrying the existing text across
unchanged rather than by new translation work.

Consequence for the spec: the clause in FR-002 covering terms with no definition has no subject.
It stays in the spec as a guard, and the plan allocates no work to it.

### Two defects the audit surfaced

- **`DataciteContributorRoles`'s collections are dangling.** Its two collections list member names
  in CamelCase (`ContactPerson`) while its actual members are declared in upper snake case
  (`CONTACT_PERSON`). The retired library builds collections by mapping names through a URI helper
  with no existence check, so both collections resolve to zero concepts, silently. Six of the
  listed names additionally refer to members that are commented out.
- **`DatasetDescriptions` is dead.** Nothing outside its own definition refers to it.

Neither is load-bearing. Both are removed by US-5 rather than ported.

`DataciteContributorRoles` itself is *not* dead — `fairdm/core/project/transforms.py:80` maps
contribution roles onto DataCite contributor types through it, and a test asserts the two name sets
agree. It converts with the rest.

---

## 3. Rich choices: the mechanism

Measured against Django 5.2.16 in this project's environment.

Django's `ChoicesType` metaclass (`django/db/models/enums.py:32-52`) takes the label off the **end**
of the member tuple, and only when the last element is a string or a lazy promise. Everything
before it becomes the member value. Three consequences were confirmed by running them:

1. A naive three-element member `X = "x", _("Ex"), _("Definition")` **crashes** with
   `TypeError: encoding must be a string`. The metaclass strips the definition as the label and
   hands the remainder to `str.__new__`.
2. Overriding `__new__` to take a third argument **crashes** with a missing-argument error, because
   the metaclass has already consumed the last element before `__new__` runs.
3. `.choices` is hard-coded to emit two-tuples (`enums.py:68-71`), and `.labels`/`.values` unpack it
   into exactly two names. A definition therefore cannot ride inside `choices` — it has to be
   reached off the member.

Django 5.2 refuses a choices tuple longer than two (`fields/__init__.py:317-375`, error `fields.E005`),
so widening the tuple is not available either.

**Two mechanisms work, and both were run in this environment.**

- **Reorder the declaration** to `value, definition, label` and override `__new__`. Works, but the
  order is a maintenance trap.
- **Subclass the metaclass**: pop the third element into a mapping before calling
  `super().__new__`, then attach it to each member afterwards. Roughly fifteen lines, keeps the
  natural `value, label, definition` order, `choices=` on a plain `CharField` behaves exactly as it
  does today, and `gettext_lazy` works for both label and definition.

The plan takes the second. `Choices` sets `do_not_call_in_templates`, which a subclass inherits, so
iterating the class in a template yields value, label and definition together — verified by
rendering it.

**The one design consequence:** passing the class as `choices=` flattens it to two-tuples, so a form
field's bound `choices` has lost the definitions. Templates must reach the class itself, or go
through a lookup helper. The plan provides the helper.

### Prior art, and why it is not used

| Package | Latest release | Per-member metadata | Verdict |
|---|---|---|---|
| `django-enum` (+`enum-properties`) | 2.5.0, 2026-07-31 | yes | Credible, actively maintained, but two dependencies for fifteen lines |
| `django-choices-field` | 4.0.0, 2025-12-27 | no | Solves a different problem (returning enum instances) |
| `django-model-utils` `Choices` | 5.0.0, 2024-09-04 | no | Third tuple slot is an identifier, not metadata; slated for deprecation |
| `django-enumfields` | 2.1.1, 2021-02-23 | no | Last commit 2022; Django 3.1 at the newest |

`django-enum` is the only real alternative. Article VII asks a new runtime dependency to justify
itself, and fifteen lines of metaclass with no new dependency is the simpler answer to a closed
problem. Recorded as D-015.

`django-mvp` was checked for an existing rendering surface: its `cotton/form/field.html` component
carries field-level `help_text` only, with no per-option hook, and whole-form rendering delegates to
crispy-forms. There is nothing to reuse, so the definition is surfaced by the framework's own
templates.

---

## 4. What the controlled-vocabularies package requires

Version 0.1.0, on PyPI, Django `>=5.2`, Python `>=3.11`.

### Field API

`ConceptField` (a foreign key) and `ConceptsField` (a many-to-many) share a signature:
`(vocabulary=None, collection=None, concepts=None, branch=None, **kwargs)`.

- `vocabulary` accepts a single scheme slug, an iterable of slugs, or nothing. Keywords can
  therefore name several vocabularies from one setting.
- A restriction (`collection`, `concepts`, `branch`) requires exactly one vocabulary, and at most
  one restriction may be given.
- `on_delete` is forced to `PROTECT` and cannot be overridden, which is what satisfies FR-015.
- `ConceptsField` **refuses `through=`** and generates its own through model, named
  `<Model>_<field>` on Django's standard `<owner_table>_<field>` table, with `PROTECT` on the
  concept side and `CASCADE` on the owner side. It is `auto_created`, so migrations render it as a
  plain many-to-many.
- Both contribute accessors to the host model — `get_<field>_label()` / `get_<field>_uri()`, and the
  plural forms for the many-to-many.

Two behaviours a consumer inherits and must plan around:

- `ConceptsField` connects an `m2m_changed` receiver that refuses concepts outside the declared
  restriction. FairDM already has its own receiver doing exactly this for contribution roles
  (`fairdm/contrib/contributors/receivers.py:60-98`). One of them is redundant after the move.
- `ConceptsField` replaces the host model's `full_clean` to require at least one concept when the
  field is not `blank`. Both target fields are `blank=True`, so this does not bite, but it means
  anything overriding `full_clean` on those models now sits under a wrapper.

### Hard runtime requirements

`django_tomselect` is a mandatory runtime dependency, not an option — the package imports it at
module scope in both its views and its forms. A consumer must add it to `INSTALLED_APPS`, add
`django_tomselect.middleware.TomSelectMiddleware` to `MIDDLEWARE`, and mount
`include("controlled_vocabularies.urls")`. If the route is missing, form rendering raises
`ImproperlyConfigured`; if the middleware is missing, the field renders as an empty select with no
search control and **nothing raises**.

Five system checks, all at warning level: an unresolvable vocabulary slug (`W001`), an unresolvable
restriction target (`W005`), the autocomplete route not mounted (`W002`), `django_tomselect` absent
(`W003`), and its middleware absent (`W004`). The last three fire unconditionally, whether or not
the project declares a concept field. `W001` is what FR-010 and D-008 rest on: an unloaded portal
warns rather than failing.

### Import

`import_skos(file, *, serialization=None, scheme=None, base_uri=None) -> ImportReport` takes a local
filesystem path only — the package's own management command is what handles URLs. The whole run is
one transaction, and re-import upserts by URI: a matched record is updated, an unmatched one
created, and records the file no longer mentions are left alone and listed as absent from source.
That is FR-009's idempotency, already provided.

The command supports `--dry-run`, which runs the full import inside a transaction that is then
unwound, reporting exactly what a live run would report.

### Gaps this feature works around, and gaps it does not

- **No `ModelAdmin` is registered by the package at all.** FairDM registers its own read-only admin
  for schemes and concepts, which is the replacement for what the retired library provided.
- **No vocabulary export**, and no serving of concept addresses as machine-readable data. Neither is
  needed by this feature, and both are tracked in that package.
- **The autocomplete query is effectively unindexed.** `Concept.label` carries no index, and the
  search is a contains-match with a leading wildcard, so no b-tree index can serve it. There is a
  `distinct()` over a join on top. On a scheme of tens of thousands of concepts this degrades. It
  does not affect FairDM's own vocabularies, the largest of which is 29 terms, but it will affect a
  portal that loads a large domain vocabulary. **Raised upstream rather than worked around here**,
  per the standing rule on upstream gaps.
- **`branch=` walks the hierarchy one query per depth level and inlines every descendant key.** Not
  used by this feature, and named here so a later feature does not adopt it unaware.

---

## 5. The Django version conflict

**FairDM declares `django = ">=5.1,<6.0"` and its required checks test Django 5.1 and 5.2. The
controlled-vocabularies package requires Django `>=5.2`.**

Adopting it therefore drops Django 5.1 from FairDM's support matrix, which means editing
`.github/workflows/tests.yml` to narrow `django-versions`, and removing the now-absent
`call-tests / Test Python 3.13, Django 5.1` from the repository's required checks.

Django 5.1 reached the end of extended support in April 2026, so FairDM is currently testing against
an unsupported Django and the narrowing is correct on its own merits. It is nevertheless a support
matrix change with a workflow edit and a repository settings change behind it, so it is raised
rather than assumed. Recorded as D-016.

---

## 6. The upgrade

Two conversions carry data.

**Contribution roles.** The existing through table holds foreign keys into `research_vocabs_concept`.
The target field generates its own through table under a different name. The conversion joins the
old rows to the retired library's concept rows, reads each concept's name, resolves it to a concept
in the imported roles vocabulary, and writes the new membership rows.

**Keywords.** Five join tables, all pointing at `research_vocabs_concept`, converting the same way.
Keywords are unscoped today, so a stored concept may belong to any vocabulary the portal loaded.
Resolution is therefore scoped per source vocabulary rather than matched on label across the whole
table, which is FR-018.

`Sample.status` and every `type` column need no data conversion at all: the stored strings are the
member names, and the replacement sets keep the same members with the same values. This is what
makes US-1 cheap.

**All-or-nothing (D-011, FR-017).** Resolution runs as a read-only pass over every affected row
before any write. If any term fails to resolve, the pass reports every failure and the migration
raises, so the transaction rolls back and nothing is converted. Both conversions run inside one
atomic migration.

Note the ordering constraint this creates: the concepts must exist before the data migration runs.
The plan therefore has the migration load FairDM's own vocabulary files itself rather than relying
on an operator having run the command first, and the command remains the route for re-import and for
a portal's own vocabularies.

### The retired stub

`fairdm/core/choices.py:305` holds a four-member class that exists only so
`sample/migrations/0001_initial.py` stays importable. FR-020 requires its removal, and D-007 keeps
the history. Both hold only if the migration stops naming it — which means editing that one frozen
migration to drop the vocabulary argument from a field whose class is also going away.

That is not a history rewrite in the sense D-007 refused. It edits a frozen file rather than
squashing the history, it changes no applied state, and it is the minimum needed to delete a class
whose only purpose is to be imported. Recorded as D-017, and called out for the design review
because it is the one place this plan touches migration history at all.
