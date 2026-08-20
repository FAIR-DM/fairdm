# Decisions — 009 contributors and contributions

Every disagreement between the specification written on 2026-02-18 and the code as it stands on
2026-08-20, and how each was settled. Decisions marked **ruled** were settled by the maintainer.
Decisions marked **self-resolved** were settled against the repository's own conventions, the
sibling specifications, or evidence in the code, and are recorded here for veto.

The original text was accompanied by a task list of 174 items, every one of them marked complete.
Those marks are not treated as evidence anywhere below. The clearest reason why: the whole of its
Phase 7, "Organisation Ownership by Authenticated Users", is marked complete, and the mechanism it
describes was deleted by migration `0017_remove_manage_organization_permission`.

---

## D1 — Views, plugins and portal editing leave; administration stays

**Ruled.**

The original text scoped itself to "developer-facing aspects: data models, managers, utilities, and
templatetags". The application ships a great deal more than that with no requirement covering any of
it: two browse pages and two create pages (`views/person.py:14`, `:49`, `views/organization.py:15`,
`:36`), nine plugins registered against contributor and record pages (`plugins/person.py`,
`plugins/shared.py`), two filter sets, a bulk spreadsheet importer that calls the live ROR and ORCID
services (`resources.py:9`), ten forms, five widgets and a component library of some twenty
templates.

Views, plugins and anything that creates, edits or deletes through the portal are deferred to a
later specification. The Django administrative interface stays in scope, because with the portal's
own editing pages deferred it is the only way this data is maintained at all.

The template tags `by_role` and `has_role` (`templatetags/contributor_tags.py:7`, `:22`) go with the
views despite the original text naming template tags in its scope line. They exist to render a
contribution list on a page. They are tested and working, and nothing is done to them here.

## D2 — The specification is not split by contributor type; two concerns are lifted out

**Ruled**, against a proposal to split it into one specification for people and one for
organisations.

The seam is wrong. Almost everything the specification is about lives on the shared base
(`models.py:48`) — name, other names, image, related resources, location, configuration, credits,
identifiers. `Person` (`:518`) adds the account, and `Organization` (`:876`) adds a parent, a city
and a country. A split would produce one large specification and one thin one, and the relationships
cross both types: an affiliation *is* the person-to-organisation link, and a contribution links the
base rather than either subclass.

What made the document large was that it bundled four unrelated concerns. Deferring views removes
one. Two more are lifted into specifications of their own:

- External identifier synchronisation, which serves G15, has its own external dependencies and its
  own failure modes.
- Contributor metadata export, which serves G10 and G14.

Both are routed out as feature requests rather than renumbered, so this specification keeps its
number and the branch and issue history that cites it stays valid.

## D3 — The identifier record stays; what fills it leaves

**Ruled.**

`ContributorIdentifier` (`models.py:1200`) is two things: a record in the contributor family — a
person has an ORCID, an organisation has a ROR — and the trigger point for fetching from those
registries, through a lifecycle hook at `models.py:1212`.

The record stays here. The hook, the task, the HTTP clients, the refresh schedule and the outcome of
a fetch belong to the synchronisation specification, and so do the two fields that hold what was
fetched and when (`last_synced` at `models.py:143`, `synced_data` at `:154`), which mean nothing
without it. Those fields are left in place untouched.

## D4 — The polymorphic base is specified for the first time

**Self-resolved.**

The original document's Key Entities section describes Person, Organization, Contribution and
Affiliation. It does not mention `Contributor` at all, although it is a concrete model with its own
table from which both Person and Organization inherit (`models.py:48`), and although it holds most
of the fields the specification's own requirements describe. The repository's glossary has had it
right the whole time (`CONTEXT.md`, "Contributor, Person, Organization").

Specified as it is built. This is the single largest omission the audit found, and it is the reason
several requirements read as though they applied to one subclass when they apply to both.

## D5 — There was never a model called `OrganizationMembership`

**Self-resolved.**

A clarification in the original text records a "critical constraint": that production databases
already use `OrganizationMembership`, and that migrating those records to `Affiliation` must be
planned so that no data is lost. FR-003a made that migration a requirement, and an edge case asked
how a partial failure would be detected and rolled back.

No model of that name has ever existed in this repository. The string appears nowhere in any Python
file. What existed was `OrganizationMember`, created in `migrations/0001_initial.py:452` and renamed
by `migrations/0012_rename_to_affiliation.py:14` — a single `RenameModel` operation, which is a
table rename. No rows are copied, so no rows can be lost, and there is no partial state to detect.
An alias `OrganizationMember = Affiliation` remains at `models.py:873`.

The requirement and the edge case are dropped as premised on a model that was not there. This is the
clearest instance in the audit of a specification describing an imagined system rather than the
built one.

## D6 — An organisation's logo and URL are wording; its type is real work

**Ruled.**

The original FR-002 names seven fields for an organisation. Three are absent under those names, and
they are not equally absent:

- **Logo** is the shared profile image (`models.py:97`), which the organisation form already labels
  as a logo in its help text. Wording.
- **URL** is served by the shared list of related resources (`models.py:127`), an unvalidated JSON
  list. Loose, but present. Wording.
- **Organisation type** does not exist in any form — no field, no vocabulary, no choices, nothing in
  the models, `choices.py` or any migration.

The first two are corrected in the specification's language. Organisation type is unbuilt work that
stays, and it takes its values from the controlled set the ROR registry defines, since ROR is
already the identifier an organisation carries.

## D7 — An affiliation carries a membership type, not a position

**Ruled.**

The original FR-003 requires "role and time period tracking" on an affiliation. The period is real.
There is no role field. What exists is `type` (`models.py:799`): pending, member, administrator,
owner — an authorisation level, not a job title. A portal cannot record that someone is a professor
or a technician at an institution.

No position field is added. "Role" already means something specific and load-bearing here — the
controlled vocabulary on a contribution saying what someone did on a record, which `CONTEXT.md`
defines as the house meaning. A second, unrelated "role" on affiliation would collide with it. The
requirement is reworded to say membership type. If a portal ever needs positions, that is a later
addition under a different name.

## D8 — The account state is derived, and "banned" becomes "inactive"

**Ruled.**

The original FR-007 requires a "4-state machine (Ghost → Invited → Claimed → Banned)". Three of the
states are real and derived — the queryset methods `ghost()`, `invited()` and `claimed()` exist
(`managers.py:150`, `:161`, `:128`) — and none of the machinery does. There is no state field, no
enumeration and no transition guard anywhere in the application. "Banned" is an ad-hoc check of
`is_active` inside the claiming services (`services/claiming.py:70`, `:153`, `:220`).

No stored state is added: three fields already determine the answer, and a stored copy beside them
would be a second truth to drift out of step. The state becomes a readable accessor with a matching
filter, so that a developer does not need to know which fields to combine. "Banned" is reworded to
"inactive", which is what the flag actually means.

The four states are made a total function so they cannot overlap: inactive if the account is
deactivated, otherwise claimed, otherwise invited if an email address is present, otherwise ghost.

Three places currently decide claim status from something other than the stored value, and all three
are corrected: the administrative filter reads the email address (`admin.py:23`), the default
privacy branch reads the email address and the active flag (`models.py:546`), and `claimed()`
includes deactivated accounts by accident rather than by decision (`managers.py:132`).

## D9 — Privacy settings become a general configuration store

**Ruled.**

The original FR-009 requires privacy controls "enforced" on sensitive fields. The data half is
built: a `privacy_settings` field (`models.py:184`) and `get_visible_fields(viewer)` (`models.py:473`)
resolving public, authenticated and private per field. The enforcement half does not exist. Nothing
in the codebase calls `get_visible_fields` — not a view, a serializer, a template or the
administrative interface. Every test calls it directly on the model. There is also no `phone` field
anywhere, so one of the two fields the requirement names is imaginary.

`privacy_settings` becomes a general-purpose `config` store whose contents this specification does
not define, and `get_visible_fields` is removed along with the default-seeding branch in
`Person.save()`. What belongs in the configuration store, including any privacy policy and its
enforcement at a response boundary, is a later specification's work. `phone` is dropped rather than
added: nothing references it, and collecting researchers' telephone numbers is a liability no
requirement justifies.

Removing the method is safe to the extent that anything is: it has no callers outside the model and
its own tests, verified across the whole tree.

## D10 — Portal administrative roles are a later specification

**Ruled.**

The original FR-010g requires portal administrators to keep full management access to every
organisation. The code does not give it to staff who are not superusers.
`OrganizationPermissionBackend.has_perm` (`permissions.py:98`) delegates to guardian with a comment
claiming it "handles staff/superuser"; guardian short-circuits for superusers only, and Django's
model backend returns nothing at all for an object-level check. The test suite asserts the refusal is
correct (`test_permissions.py:274`).

The result is incoherent in the administrative interface: a staff administrator can open an
organisation's page, because that is a model-level permission, and is then refused the ownership
action on it (`admin.py:451`).

The requirement's intent is right and its home is wrong. Which portal-wide administrative roles exist
and what they may do waits on the specification that defines them, and this document says nothing
about it. Nothing is changed in the code beyond the comment at `permissions.py:98`, which is
corrected so that it stops describing behaviour that does not happen.

## D11 — Metadata export and citations leave, and citations were never built

**Ruled** on the departure; **self-resolved** on the finding.

FR-011, FR-012, FR-012a and FR-012b covered DataCite and Schema.org export and a public interface for
defining further formats. FR-019 required formatted citations "following standard academic styles
(APA, Chicago)". Two findings go with them into the export specification, because they are that
specification's work and not this one's:

- **Nothing generates a citation.** There is no citation renderer, no CSL processor and no style
  handling anywhere in the repository. `CSLJSONTransform.export` (`utils/transforms.py:374`) emits a
  single CSL-JSON author fragment, which is an input to a citation processor rather than a citation.
  APA and Chicago appear only in the specification.
- **The documented interface does not exist.** `docs/portal-development/contributors.md:293`
  documents a `TransformRegistry` and `to_internal` / `to_external` class methods. No such name
  exists in the codebase; the real contract is instance methods `export` and `import_data`. Every
  code sample on that page would raise. The base class the page tells developers to subclass is also
  excluded from the package's advertised interface (`utils/__init__.py:52`).

Also carried across: the Schema.org output sets no `@context` (`utils/transforms.py:224`), so it is a
Schema.org-shaped fragment rather than the JSON-LD the requirement asks for, and the project-level
transform in the same repository does set one (`fairdm/core/project/transforms.py:193`). And
`BaseTransform.validate` returns `isinstance(data, dict)` (`utils/transforms.py:103`) with no
subclass overriding it, so malformed input passes validation and yields empty strings.

## D12 — Deleting a parent organisation no longer deletes its children

**Ruled.**

`Organization.parent` is declared `on_delete=CASCADE` (`models.py:894`). Deleting a university
deletes every department beneath it, their contributor records, and every affiliation pointing at
them. Nothing in the specification says that should happen, and the loss is not recoverable.

Changed to `SET_NULL`, which the field already permits. A deleted parent leaves its children with no
parent, and their members and credits untouched.

## D13 — Ownership is derived, not granted, and the specification follows the code

**Self-resolved.**

The original text requires ownership to be a `django-guardian` object-level permission granted to a
person, synchronised with an owner affiliation by a lifecycle hook. None of that is how it works.
Migration `0017_remove_manage_organization_permission` deleted the permission itself, the stored
guardian rows for it, and the declaration on the model. `Affiliation` carries no lifecycle hook at
all. `OrganizationPermissionBackend` (`permissions.py:102`) instead answers the question at check
time by looking for an owner affiliation.

Settled in the code's favour, and the specification is rewritten to describe derivation. A stored
permission is a copy of a fact, and a copy can fall out of step with what it copied; deriving it
means the two can never disagree, and a demotion takes effect on the next check with no revocation
step to forget. The migration's own docstring gives this reasoning, so the change was deliberate
rather than drift.

Two tests still describe the old mechanism in their names and docstrings while passing because of the
new one (`test_models.py:259`, `:271`), and two comments claim lifecycle hooks are involved
(`test_permissions.py:48`, `:208`). All four are corrected.

## D14 — The manager is composed from the queryset

**Self-resolved.**

FR-013 required a queryset composed onto the manager "via the `UserManager.from_queryset` pattern".
The pattern is not used. `UserManager` overrides `get_queryset` and then hand-writes six one-line
proxy methods (`managers.py:19`, `:77`–`:99`), with the queryset class defined below the manager
that references it. The repository uses the real pattern in every core model
(`core/dataset/models.py:159`, `core/sample/models.py:134`, `core/measurement/models.py:50`), so the
contributors application is the outlier.

Settled in the specification's favour. Conforming removes six methods that exist only to forward, and
removes the possibility of the two surfaces disagreeing.

## D15 — Duplicate detection belongs to the claiming specification

**Self-resolved.**

FR-014 required duplicate detection "based on names and identifiers". The code that does it —
`find_duplicate_candidates` (`services/matching.py:18`), fuzzy name matching at a 0.85 threshold — is
already required verbatim by `010-profile-claiming` FR-013, and its only consumer is the duplicate
panel on the administrative person screen, which feeds that specification's merge flow.

The requirement is dropped here rather than duplicated. Its identifier half is genuinely absent —
neither the service nor the periodic task looks at an identifier — and that gap is recorded against
010, whose requirement it is.

## D16 — The contributor weight is removed

**Self-resolved.**

`Contributor.weight` (`models.py:165`) is a stored ranking score, and `calculate_weight`
(`models.py:305`) computes one from credit count, profile completeness and whether an identifier is
present. Nothing calls `calculate_weight`, nothing orders by `weight`, and no test touches either.
Every row therefore carries the default, permanently.

Removed, along with `calculate_weight` and `calculate_profile_completion`, which serves only it. The
field exists to sort contributors in public lists, and public lists are deferred by D1. A ranking
that is never recalculated is not a head start for that later work; it is a value that looks
meaningful and is not. The model docstring also advertises a lifecycle hook, `update_weight`, that
does not exist.

## D17 — Search by expertise is dropped

**Self-resolved.**

FR-013 required the manager to support "search by expertise". There is nothing to search: the
contributor docstring at `models.py:67` advertises a `keywords` field of controlled-vocabulary terms,
and no such field is defined anywhere in the application. The person filter set offers active, staff,
name, city, country and affiliation, and nothing resembling expertise.

Dropped. Adding a keyword vocabulary to contributors is a capability in its own right rather than a
manager method, and no requirement here justifies it. The misleading docstring is corrected along
with the several other stale claims in it.

## D18 — Internationalisation is kept for what this specification owns

**Self-resolved**, following the line `003-core-projects` D-014 already drew.

FR-020 required internationalisation for names in non-Latin scripts. What exists is that the fields
are `CharField`s and Python strings are Unicode. Five tests cover Chinese, Arabic, Cyrillic, mixed
and apostrophe-bearing names, and each asserts only that the stored name equals the two inputs joined
by a space, which tests string concatenation. Nothing reads the language field when rendering a name,
and the display helper hard-codes given-then-family ordering and takes a name's first code point as
its initial (`models.py:682`).

Kept for the surfaces this specification owns: field labels and help text, vocabulary labels,
administrative labels and validation messages, all translatable. Name rendering by script is a
display concern and goes with the views deferred by D1. The requirement is reworded so that it stops
claiming more than it delivers.

## D19 — Tests that assert a defect, or pass for the wrong reason, are rewritten

**Self-resolved.**

The audit reconciled each requirement against a passing test, and several tests turned out not to
cover what their names claim. Each is rewritten as part of the work that touches its subject:

- `test_models.py:76` asserts a person is not claimed after an email address is set. `is_claimed` is
  a plain field that nothing recomputes, so the assertion holds however the code behaves.
- `test_admin.py:223` claims to cover the sub-organisation inline and asserts that the page contains
  either "parent" or "sub". The parent form field alone satisfies it, so it passes with no inline
  present — which is the current state.
- `test_tasks.py:231` claims to cover a 500 from the ROR service. Its mock never raises on
  `raise_for_status`, so the retry path is never entered and the test passes through an unrelated
  branch. Carried to the synchronisation specification with the code it covers.
- `test_transforms.py:47` is named for exporting a person's affiliation and asserts nothing about
  affiliation, behind a comment saying affiliations are not exported. They are. Carried to the export
  specification.
- `test_managers.py:61` claims `claimed()` excludes inactive people. It filters on the claim value
  only, and the test passes because its fixture never sets that value.
- `test_transforms.py:218`, `:228` "validate" a stub by passing it well-formed dictionaries. They
  would pass if the method were deleted. Carried to the export specification.

`ghost()`, `invited()`, `real()` and `active()` have no tests at all, and no test links a credit to a
sample or a measurement.

## D20 — Deleting a credit withdraws rights, and the asymmetry is routed

**Self-resolved.**

Deleting a person's credit on an object withdraws every object-level right that person holds over
that object (`models.py:1168`). Nothing grants any right when a credit is created. So a person who
holds rights by some other route — as the creator of the record, say — loses them if an unrelated
credit of theirs on the same object is removed.

The behaviour is specified as it stands, because it is coherent as cleanup and removing it would
leave rights behind after the credit that justified them. The asymmetry is a policy question about
which contribution roles confer which rights, which is exactly what issue #169 already asks, and it
is recorded there rather than answered here.

---

## Routed out

Findings that are real and are not this specification's work.

- **External identifier synchronisation** — a specification of its own (D2, D3). Carries: the sync
  fires only when an identifier row is created and never when its value changes, because the only
  lifecycle hook is `AFTER_CREATE` (`models.py:1212`); the periodic refresh task exists
  (`tasks.py:166`) and nothing schedules it, there being no beat schedule anywhere in the repository
  and the beat service commented out at `docker-compose.yml:53`; no field records whether a fetch
  succeeded or failed, so a permanently failing identifier is indistinguishable from one never
  tried; `Retry-After` is read into a warning string and discarded (`utils/transforms.py:495`); and
  the task writes `last_synced` twice, the second overwriting the first (`tasks.py:81` against
  `models.py:219`).
- **Contributor metadata export and citations** — a specification of its own (D2, D11).
- **The contributor configuration store, including privacy** — a later specification (D9).
- **Portal administrative roles** — a later specification (D10).
- **The Datasets tab on every contributor page returns a server error.** `ContributorDatasets`
  (`plugins/person.py:74`) sets no page title, so the title falls through to a model attribute the
  class never sets. Confirmed by request against a running portal, not by reading. A view, and so
  deferred by D1, but a live fault and raised as a bug.
- **The administrative claim-link action raises `NoReverseMatch`.** The claiming routes are commented
  out (`urls.py:12`) and the application is included without a namespace
  (`fairdm/conf/urls.py:18`), while the action reverses `contributors:claim-profile`
  (`admin.py:295`). Belongs to `010-profile-claiming`; raised as a bug.
- **A second, undocumented claiming path.** `SocialSignupForm.try_save` (`forms/account.py:63`) is
  wired into the live authentication settings and reuses an existing inactive account sharing an
  email address, bypassing the conflict check. It keys on the active flag rather than the claim
  value, writes no audit entry, and matches no requirement in `010-profile-claiming`. Raised against
  010.
- **Dead code left in place.** Seven names are defined and never imported anywhere, including tests:
  `ContributorFilter`, `PersonSelect2Widget`, `OrganizationSelect2Widget`, `UserIdentifierForm`,
  `UserIdentifierFormSet`, `OrganizationProfileForm` and `UserProfileForm`. One of them,
  `AffiliationForm` (`forms/forms.py:89`), carries a real access-control policy that runs nowhere:
  a new membership is pending if the organisation already has an owner or an administrator, and a
  member otherwise. All are view-layer and are left alone by D1, to be settled by the specification
  that inherits them.
- **A registered plugin with no content and an empty module.** The Network tab
  (`plugins/person.py:118`) renders an empty page, and `plugins/organisation.py` is a zero-byte file
  that `plugins/__init__.py:1` imports. Deferred by D1.

---

## D21 — What the design review changed

**One reviewer, four lenses, one round.** The fourth lens exists to challenge the reconciliation,
because deciding a task is already done is the judgement in this work most likely to be wrong and
the only one whose error is silent. It found six ticks that should not have been there, and both of
the two judgement calls it was asked to test came back with an answer worth having.

**Three findings that are defects in the code, not in the plan.**

- **Crediting replaces roles instead of accumulating them.** Both entry points call
  `roles.set()` (`models.py:470` and `models.py:1127`). Crediting the same person a second time
  under a new role silently discards the role recorded the first time. FR-031 requires
  accumulation, `CONTEXT.md` states it as a standing principle, and the test ticked against it
  asserted only that a duplicate pairing raises. Folded into the task that owns the roles field.
- **A fourth site decides claim status from the wrong thing.** D8 listed three; `Person.clean()`
  (`models.py:572`) is a fourth, refusing removal of an email address when the account has a usable
  password and is active rather than when it is claimed. A person who claimed through social login
  can therefore clear their address, and a ghost who was given a password cannot. The test named
  for this behaviour never claims anyone, so it passes whichever way the code reads.
- **The lifecycle hook that withdraws rights does not fire on a queryset delete.** django-lifecycle
  runs `AFTER_DELETE` from the model's own `delete()`, which `QuerySet.delete()` bypasses
  altogether. FR-036 does not qualify how the credit is deleted. Verified in the installed library
  rather than assumed.

**One finding that would have widened access.** The task rewriting the ownership-transfer
administrative action named no authorisation check, while the code it replaces gates on the
object-level right (`admin.py:451`). An implementer working from a task list deliberately written as
though the repository were empty would have dropped the gate. The clause is now in the task.

**Both judgement calls, answered.**

- Striking the two tasks that asked for a stored permission record was **right**. The reviewer
  traced every consumer of the permission name: nothing performs a database lookup of the
  permission row, and nothing assigns it, so re-declaring it would reintroduce precisely what
  FR-027 forbids.
- Ticking the credit-withdrawal task was **half right**. The argument that renaming working code to
  match an invented file name is churn holds. The argument that a lifecycle hook and a signal
  receiver are the same mechanism does not, which is the finding above.

**And three that removed work**, which is the direction this review is cheap in: a task asking for
an identifier mapping that already exists and that no requirement asks for is struck; a task adding
three administrative screens is narrowed to the one the story actually describes, which also removes
the bulk-delete surface that made the lifecycle gap reachable; and a clause asking for a related-name
default is dropped from a task that is otherwise complete, because the accessor is already declared
explicitly.

The plan's ordering paragraph said migrations were written first in a single task while the task
list wrote one per story. The task list was right and the paragraph is corrected.

**After the review: 30 of 143 reconciled done, 110 open, 3 struck.**

## D22 — US1 accepted on independent verification, without receipts

**Self-resolved**, and recorded because it is a gap rather than a clean pass.

The process running US1 was killed after its last commit and before it wrote its completion report,
so the story produced no craft-skill receipts and no self-reported evidence. Re-running the story
would discard seventeen commits of sound work; accepting it on the strength of those commits would
be accepting a story on its own say-so, which is the one thing the reporting gate exists to prevent.

So it was verified independently instead, and this entry records exactly what that verification
covered:

- The full suite: **2016 passed, 13 skipped**, against a baseline of 2011 passed, 13 skipped.
- `tamper-check` raised one flag, on `tests/test_contrib/test_contributors/test_models.py`. It is
  fully accounted for: fifteen tests were removed and all fifteen are the privacy tests T144
  authorises by name, D9 having removed the behaviour they cover. Comparing every test function
  present in both `main` and the branch, **no surviving test body changed** — so nothing was
  weakened, only the dead set deleted. The flag is approved on that basis, per the tamper-check
  contract's provision for a legitimate refactor.
- `makemigrations --check` reports no changes for the contributors application. The seven
  migrations the story added are consistent with the models, and T139 consolidates them at
  convergence.
- The two removals were confirmed in the source: the configuration store exists at `models.py:180`,
  and `privacy_settings`, `get_visible_fields`, `weight`, `calculate_weight` and
  `calculate_profile_completion` are gone from a file that carried sixteen references to the first
  two on `main`.

**What is not covered:** whether the implementer loaded its craft skills. That is unprovable now,
and no receipt is recorded rather than a receipt being assumed. Every later story in this feature
carries its receipts normally.

## D23 — `AffiliationQuerySet.primary()` composes onto the manager despite returning an instance

**Self-resolved**, per T124's brief prohibition to decide deliberately rather than silently.

`AffiliationQuerySet.primary()` (`managers.py`) returns `.filter(is_primary=True).first()` - an
`Affiliation` instance or `None`, not a queryset. The brief's prohibition read this as meaning
`primary()` "cannot be composed by `from_queryset` as it stands" and required a deliberate choice:
make it return a queryset and adjust its callers, or leave it as a manager method and say why.

Checked directly rather than assumed: `Manager._get_queryset_methods` (`django/db/models/manager.py`)
copies any public function defined on the queryset class and wraps it as
`getattr(self.get_queryset(), name)(*args, **kwargs)` — it never inspects the return type. A
`python -c` probe building `models.Manager.from_queryset(DummyQuerySet)` against a queryset whose
method returns `.first()` confirmed the wrapper is copied and callable exactly like any other. So
`primary()` **can** be composed via `from_queryset`, and `AffiliationManager` now is
`models.Manager.from_queryset(AffiliationQuerySet)` like the other two managers this story
touches — no special case.

What does not change: `primary()`'s return type, or any of its three callers (`managers.py`'s own
docstring, `docs/portal-development/contributors.md`, and the two tests in
`TestAffiliationQuerysetMethods` that already asserted `person.affiliations.primary()` returns an
instance or `None`). FR-042 does not name `primary()` — only "current" and "ended" memberships — so
it is outside T121's parity test scope; `TestAffiliationQuerysetMethods`'s pre-existing tests are
the regression net for it instead, and they stayed green through the refactor.

**Revisit if:** a future caller wants to chain a further queryset method after `.primary()` — that
caller needs a queryset, not an instance, and `primary()` would need either a rename (e.g.
`primary_qs()`) or a genuine return-type change with its callers updated, which this story does not
do.

## D24 — T122 and T123 needed no code change

**Self-resolved.**

T122 ("Add the real-contributors filter to `PersonQuerySet`") and T123 ("Add the active-accounts
filter to `PersonQuerySet`") both carry a "built-without-tests" annotation, not a "never-built" one.
`real()` already existed at `managers.py:16` (excluding `is_superuser=True` and the anonymous
placeholder, exactly FR-041's real-contributors filter) and `active()` already existed at
`managers.py:27` (`is_active=True`, exactly FR-041's active-accounts filter) before this story
touched anything. Neither method's substance needed to change - only the missing tests, which T119
and T120 add.

Per the brief's prohibition against rewriting code that already exists, T122 and T123 are recorded
as `done` with no accompanying commit: their evidence points at the pre-existing code and at
T119's/T120's test commits, rather than at a commit that does not exist for a change that was never
required.

**Revisit if:** a future review finds `real()` or `active()` do not in fact match FR-041's wording -
that would mean the "built-without-tests" annotation was wrong, not that this decision was.

## D25 — `ghost()`, `invited()` and `claimed()` were corrected in place, not replaced

**Self-resolved**, per T044's brief prohibition against renaming existing methods merely because a
task names them differently.

T044 needed a filter for every one of `account_state`'s four states, mirroring its precedence
exactly. Three of the four names already existed (`ghost()`, `invited()`, `claimed()`), and D8 had
already named their defect: none of them checked `is_active`, so a deactivated person with an
email, for example, matched `invited()` as well as (now) `inactive()` - not the mutually exclusive
partition FR-014 and T040 require. Rather than leave these three as they were and add three more
differently-named methods, `is_active=True` was added to each of the three, and `inactive()` was
added as the fourth, new method. This is the same correction D8 names for `claimed()`
(`managers.py:132`) applied consistently to its two siblings, not a new decision.

What did not change: `real()`, `active()` and `unclaimed()`. None of the three belongs to the
four-state partition - `unclaimed()` is a coarser, two-way claim split that several other tests
still rely on (`tests/.../test_managers.py::TestPersonQuerysets`), and narrowing it would have
changed behaviour no task in this story asked for.

The pre-existing test `test_claimed_excludes_inactive_with_email`
(`tests/test_contrib/test_contributors/test_managers.py`) was not touched - it happened to pass
before this change for the wrong reason (its inactive fixture defaulted `is_claimed=False`, so
`is_claimed=True` alone already excluded it) and continues to pass for the right one now.

**Revisit if:** a future story wants `unclaimed()` to also respect deactivation - that is a
deliberate widening of its contract, not a bug in this one, because nothing today asks `unclaimed()`
to be part of the four-state partition.

## D26 — No migration generated for the indexed claim flag

**Self-resolved**, per the brief's explicit prohibition (T045).

T045 asked for a migration adding the claim column and its index. The column already exists
(migration 0014); only `db_index=True` (T042) is new, and the brief forbids generating a migration
for it — four sibling US stories are changing contributor models concurrently in their own
worktrees, and one migration per story would produce a fan of leaves Forge would otherwise have to
merge by hand. The consolidated migration is Forge's work at convergence (plan.md "Ordering and
parallelism", T139). The test settings stub `MIGRATION_MODULES` for this app, so the suite builds
tables straight from the models and every test in this story passes with no migration present.

**Revisit if:** convergence's consolidated migration is generated and `makemigrations --check`
still reports a pending change for `contributors.Person.is_claimed` afterward - that would mean the
index was missed rather than deferred.
