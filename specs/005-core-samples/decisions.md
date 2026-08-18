# Decisions — 005 Core Samples

The original specification was written on 2026-01-16, before most of the sample app existed. It
described five layers at once — the polymorphic record, the querysets, the forms, the filters and
the admin — and its file is physically damaged: user stories 3, 4 and 5 each appear twice with
different content, and the `## Requirements` and `### Edge Cases` headings appear twice apiece.

What sets this rewrite apart from the two before it is that most of the disagreement is not about
which document owns what. It is that the code does not work. Nine of its requirements are
implemented by code that cannot run, or that runs backwards, or that validates against a vocabulary
it was never given.

This file records what the old text said, what the code does, which way each disagreement was
settled, and why. It is the reason the specification now says what it says.

Every decision was taken on 2026-08-18. Where one was settled without the maintainer present it is
marked **self-resolved**, and it stands unless he says otherwise.

## D-001 — Scope: the record and the reusable mixins, not the portal pages

**Settled by the maintainer, 2026-08-18.**

The original text owned the `Sample` model, its related records, its querysets, its forms, its
filters, its admin and its permissions. The portal pages that create, list and edit samples do not
exist yet — the roadmap's R16 covers them — so unlike projects and datasets there is no sibling
specification to hand the surface to.

The line drawn for projects and datasets was "the record here, the pages and the forms behind them
in the CRUD specification". Applied literally to samples that would push the form and filter
*mixins* out to a document nobody has written. The maintainer settled it on the principle rather
than the wording: **a CRUD specification owns what its pages construct.**

**In scope** — the `Sample` model and its fields, the polymorphic base and its integration with the
registry, the related description, date, identifier and relation records, their controlled
vocabularies, the querysets, the administrative interface, the permission backend that derives a
sample's access from its dataset, and `SampleFormMixin` and `SampleFilterMixin` together with their
wiring into what the registry generates.

**Out of scope, owned by the CRUD specification for samples (R16)** — the list, detail, create,
edit and delete pages, the concrete `SampleForm` and `SampleFilter` those pages would instantiate,
and the view-level permission checks.

The distinction is not arbitrary. `SampleFormMixin` and `SampleFilterMixin` have callers today —
`fairdm_demo`'s `RockSampleForm` and `RockSampleFilter` inherit from them
(`fairdm_demo/forms.py:478`, `fairdm_demo/filters.py:506`). `SampleForm` and `SampleFilter` have
none outside their own docstrings and their tests. The mixins are the live extension point a portal
developer touches; the concrete classes are what a page would build.

## D-002 — The sample status vocabulary describes data collection, not specimens

**Settled by the maintainer, 2026-08-18. This is a defect.**

`Sample.status` is a `ConceptField` over `SampleStatus` (`fairdm/core/sample/models.py:74`), which
is a `RemoteVocabulary` fetched over plain HTTP from `vocabulary.odm2.org/api/v1/status/`
(`fairdm/core/choices.py:305`). Fetched directly on 2026-08-18, that vocabulary contains four terms:
Complete, Ongoing, Planned and Unknown. Those describe the state of a data-collection activity. None
of them describes a physical specimen — calling a rock "ongoing" carries no meaning.

The old FR-004 named a `FairDMSampleStatus` containing available, in use, stored, destroyed and
unknown. No such class exists anywhere in the repository. It was named in the specification and
never written.

Three further faults follow from this one, which is why settling it unblocks several requirements:

- The form defaults status to `"available"` (`fairdm/core/sample/forms.py:90`), which is not a term
  the vocabulary contains, and a test asserts that string (`tests/…/test_forms.py:135`), so the
  invalid default is pinned in place.
- The status filter draws its choices from `Concept.objects.filter(vocabulary__name=…)` where the
  name resolves to the empty string (`fairdm/core/sample/filters.py:157`), so the filter is
  permanently empty and its test is skipped.
- Every existing row holds an ODM2 term with no equivalent in a custody vocabulary.

Settled in the specification's favour: a FairDM sample status vocabulary is introduced with the
specimen states, `unknown` remains the default, and existing values migrate to `unknown`. None of
Complete, Ongoing or Planned maps onto a custody state, and inventing a mapping would assert
something about the data that nobody knows. The remote fetch goes with it — a core model field
should not depend on a third-party host being reachable, over plain HTTP, at import time.

## D-003 — Sample identifiers use the wrong vocabulary, and a sample cannot carry an IGSN

**Self-resolved. This is a defect, not drift.**

`SampleIdentifier.VOCABULARY` is `FairDMIdentifiers()` unscoped (`fairdm/core/sample/models.py:349`).
That vocabulary contains ORCID, ResearcherID, ROR, Wikidata, ISNI, the Crossref Funder ID, DOI, a
grant number and a proposal identifier (`fairdm/core/vocabularies.py:6`). Six of the nine identify
people or organisations, and three were added for projects. **None identifies a sample.**

There is no IGSN member at all. `IGSN` exists only on `DataCiteIdentifiers`
(`fairdm/core/choices.py:292`), a `TextChoices` class this model does not use — the line that would
have wired it in is commented out at `fairdm/core/sample/models.py:49`.

So the IGSN format check at `models.py:376` is unreachable: the membership test above it rejects
`type="IGSN"` first. The specification requires a sample to carry an IGSN, and today it cannot.

This is the third instance of the same defect — projects (003 D-003) and datasets (004 D-003) each
found their record pointing at the person-and-organisation vocabulary. Settled the same way: a
sample identifier collection is introduced, containing **IGSN and DOI**. IGSN because it is what
portals mint for specimens today; DOI because of the direction described in D-005.

The pre-existing global uniqueness of an identifier value (`fairdm/core/abstract.py:316`) is kept.

## D-004 — A sample has one relationship type, and it stays that way

**Settled by the maintainer, 2026-08-18.**

The old FR-008 required a controlled vocabulary of relationship types carrying parent-child,
derived-from and split-from. `SampleRelation.type` is a plain `CharField` with a single hardcoded
choice, `child_of` (`fairdm/core/sample/models.py:405`).

The maintainer declined to expand it: "at most child of and maybe derived from. Anything else is
overreaching for this spec." Taking the maybe as no, the shipped single type stays, with no
vocabulary and no migration.

The reasoning behind reading "maybe" as "no": nothing in the repository writes or reads a second
type, and adding one forces every traversal helper to rule on whether it counts as parentage —
`get_children`, `get_parents` and `get_descendants` all match `type="child_of"` exactly
(`models.py:204`, `:222`, `:257`). That ruling is the design work being declined.

A derived-from type is recorded here deliberately, so that adding it later is a decision rather
than a rediscovery.

## D-005 — IGSN stays the reference schema, and that is what keeps the record domain-neutral

**Settled by the maintainer, 2026-08-18. This corrects a reading of mine, not the code.**

The old text organises the record around the IGSN metadata schema, and its FR-017 makes alignment a
requirement in its own right. Reading that as a geoscience bias, this rewrite initially proposed
demoting IGSN to one identifier scheme among several and widening the sample identifier collection
to Handle, ARK and URL.

That was wrong. IGSN is the International **Generic** Sample Number, and has been deliberately
domain-independent since it stopped standing for "geo sample number". It is the reference guideline
for specimen metadata precisely because it is not tied to one science — which makes alignment with
it the domain-neutral choice rather than a departure from one.

The requirement stays, and the identifier collection is trimmed to IGSN and DOI rather than widened.

The DOI is there because IGSN's custody is reported to be moving to DataCite, which would mint DOIs
for samples. That is unconfirmed, and nothing here depends on it resolving one way or the other: a
sample can carry both types today, and if IGSN identifiers become DOIs the record already has
somewhere to put them.

## D-006 — The three vocabulary validators have never run

**Self-resolved. This is a defect.**

`SampleDescription.clean()`, `SampleDate.clean()` and `SampleIdentifier.clean()`
(`fairdm/core/sample/models.py:294`, `:325`, `:352`) each build their valid-type list with
`[item["id"] for item in self.VOCABULARY]`. Iterating a vocabulary yields `(name, label)` tuples,
not dictionaries, and the iteration itself raises `TypeError` before the subscript is reached.

So `full_clean()` on any typed sample metadata record raises an attribute error rather than a
validation error, and has always done so. The three requirements the validators exist to satisfy —
old FR-014, FR-015 and FR-016 — have never held. Nothing caught it because every test that creates
one of these records goes through `objects.create()`, which does not call `clean()`.

The requirements are kept and the code is treated as wrong. This is the same blind spot 003 D-015
identified: a type field is a plain character field, and Django does not validate choices on save,
so a create-a-row test proves nothing about the vocabulary binding.

## D-007 — The queryset traversal methods run backwards

**Self-resolved. This is a defect.**

The edge convention the model sets is `source = child`, `target = parent`: `get_children` filters
`target=self` and returns sources (`models.py:204`), `get_parents` filters `source=self` and returns
targets (`:222`).

`SampleQuerySet.get_descendants` walks `source → target` (`managers.py:153`), which is child to
parent, so it returns ancestors. `SampleQuerySet.get_ancestors` walks `target → source`
(`managers.py:203`) and returns descendants. The two are swapped.

Neither has a caller or a test, which is why it has never surfaced. Settled in the model's favour —
the model's direction is the one the data uses. The duplication is the real fault: two
implementations of one traversal, in two files, disagreeing. The queryset keeps one traversal and
the model's helpers delegate to it.

## D-008 — The filter mixin declares filters that are silently discarded

**Self-resolved. This is a defect.**

`SampleFilterMixin` is a plain class, not a `FilterSet` (`fairdm/core/sample/filters.py:19`).
django-filter collects declared filters in `FilterSetMetaclass`, which a plain mixin never passes
through, so the `image` filter it declares is dropped and an inheriting filter set receives only
`Meta.fields`.

Confirmed on the demo: `RockSampleFilter` — which inherits the mixin — carries status, dataset,
polymorphic type and its own three fields, and none of the search, description or date filters the
mixin's docstring promises.

The clarification session on the original specification called this mechanism "very important for
proper integration", and it delivers a fraction of what it claims. The requirement is kept and the
mixin is made a real base whose declared filters survive inheritance.

The cross-relationship filters themselves do not come with it. `description` points at
`descriptions__text` and the date filters at `dates__date` (`filters.py:121`, `:128`); the field on
both abstracts is `value` (`fairdm/core/abstract.py:280`, `:297`), so all three raise `FieldError`
whenever used, and all three tests are skipped. They are declared on `SampleFilter`, which leaves
under D-001, and they leave with it.

## D-009 — Preventing direct instantiation of the base record is enforced in one place and bypassed in another

**Self-resolved.**

The old FR-001 requires that only polymorphic subclasses be created, and that forms and the admin
enforce it. The block lives in `Sample.clean()` (`models.py:118`) and in `SampleForm.clean()`
(`forms.py:176`) — both validation-time only. `Sample.objects.create()` is unaffected, and the
framework's own factory does exactly that (`fairdm/factories/core.py:475` declares `model = Sample`).

Kept, and the enforcement moved to where it cannot be walked past. A rule that the test fixtures
break every time they run is not a rule.

## D-010 — Sample access derives from the dataset, and none of it is tested

**Self-resolved.**

The old FR-058 to FR-060 require declared permissions, guardian object-level enforcement, and
inheritance from the parent dataset. All three are implemented — `SamplePermissionBackend`
(`fairdm/core/sample/permissions.py:10`), registered at `fairdm/conf/settings/auth.py:52`, with a
permission map at `permissions.py:81`.

Every test of it is skipped. Both classes in `tests/test_core/test_sample/test_permissions.py`
carry class-level skips covering ten test functions, so the file executes nothing.

The requirements are kept unchanged and the work is the proof. This is the case the reconciliation
rule exists for: code with no executing test does not satisfy its task.

## D-011 — A query-count target that nothing can measure

**Self-resolved.**

The old FR-021 required querysets to "reduce database queries by at least 80% compared to naive ORM
usage". There is no naive baseline to compare against, so the number is unfalsifiable; the test that
claims to cover it asserts that one count is lower than another and at most five
(`tests/…/test_models.py:220`).

Restated as the guarantee that actually matters and can be checked: loading samples with their
related records takes a number of queries that does not grow with the number of samples or the
number of related records. That is the same wording 004 settled on (its FR-030).

The success criteria asserting developer minutes, percentage boilerplate reduction and "95% of
custom sample types" go the same way, for the same reason.

## D-012 — The material field is dropped rather than deferred

**Self-resolved, on the maintainer's instruction not to overreach.**

The old FR-004 said the record SHOULD carry a material field using a controlled vocabulary where
available, and FR-017 listed material among the fields IGSN alignment needs. No such field exists.

Adding it means a new field and a controlled vocabulary spanning every science the framework serves
— rock, water, soil, sediment, tissue, air and whatever a discipline not yet using FairDM records.
That is the same class of work as the relationship vocabulary the maintainer declined in D-004, and
it is declined here for the same reason.

Recorded rather than silently dropped: a sample's material is not represented, and a portal that
needs it today adds a field to its own sample type.

## D-013 — The base registry configuration has no users

**Self-resolved.**

`BaseSampleConfiguration` (`fairdm/core/sample/config.py:25`) exists to be inherited by sample type
configurations. Nothing inherits it — every sample configuration in the demo subclasses
`ModelConfiguration` directly (`fairdm_demo/config.py:51`, `:88`, `:212`, `:265`, `:343`), while the
measurement equivalent *is* used (`fairdm_demo/config.py:151`). No test imports it.

Kept and wired up rather than removed. It is the mechanism by which a sample type gets sensible
component defaults without restating them, which is this specification's own registry requirement,
and the demo is the reference a portal developer copies. A base class the reference implementation
ignores is advice nobody takes.

## Routed out

Findings that are real but are not this feature's work:

| Finding | Where it goes |
|---|---|
| The permission gate on every sample management plugin returns `True` unconditionally (`fairdm/core/sample/plugins.py:19`), so Edit, Descriptions, Keywords and Key Dates are ungated | Filed — a view-level check, and D-001 puts those in the CRUD specification |
| `SampleForm`'s `Meta.help_text` should be `help_texts`; all seven help strings are inert (`forms.py:155`) | Leaves with `SampleForm` under D-001 |
| The dataset "add another" widget reverses `admin:core_dataset_add`, which does not exist — `NoReverseMatch` whenever the form renders (`forms.py:60`) | Leaves with `SampleForm` under D-001 |
| `SampleFilter`'s description and date filters name fields that do not exist and raise `FieldError` (`filters.py:121`, `:128`) | Leaves with `SampleFilter` under D-001 (D-008) |
| The polymorphic type filter's choices are hardcoded to `app_label__in=["fairdm_core", "fairdm_demo"]` — `fairdm_core` is not a real app label, and a portal's own app is excluded (`filters.py:150`) | Leaves with `SampleFilter` under D-001 |
| `tests/…/test_admin.py:48` has unreachable code after a `return`, referencing two undefined names | Repaired here — it is a test for a surface in scope |
| Sample list, detail, create, edit and delete pages | R16, the CRUD specification for samples |
| A sample's material (D-012) | Filed as a request in its own right |
| A second relationship type (D-004) | Filed as a request in its own right |

## D-014 — What to validate in an IGSN is settled by research, not by this document

**Self-resolved.**

The old FR-016 hardcodes the IGSN Handle pattern `10273/[A-Z0-9]{9,}`. If sample identifiers are
moving to DataCite (D-005), that prefix stops describing every IGSN.

Freezing a regex into the specification on the strength of an unverified report would be the same
mistake as the ODM2 vocabulary: a plausible external reference, adopted without checking what it
contains. The specification requires that an IGSN be validated against the format its issuing
authority defines, and which format that is gets settled from the IGSN and DataCite documentation
during research.
