# Progress — 009-fairdm-contributors, US9

## 2026-08-20T11:00:00Z · US9 · T118

Did: Added the `contributor_population` fixture to
`tests/test_contrib/test_contributors/conftest.py`: a superuser, the django-guardian anonymous
placeholder (`guardian.utils.get_anonymous_user()`), a person in each of the four account states
(ghost via `create_unclaimed`, invited, claimed, inactive - built from the raw `is_active`/
`is_claimed`/`email` fields each state is defined by, not from a state-accessor that does not
exist), a current and an ended `Affiliation`, and two `Contribution` credits under the pre-seeded
`fairdm-roles` vocabulary's own `Creator` and `Contributor` concepts (not new ad-hoc concepts,
because `Concept.uri` is unique with no default and a second blank-uri concept collides).

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -q -p
no:randomly` → 14 passed (pre-existing tests only; the fixture had no consumer yet).

Next: T119 — TestRealContributors against this fixture.

Watch: none.

## 2026-08-20T11:05:00Z · US9 · T119

Did: Added `TestRealContributors` to `test_managers.py` — `real()` excludes the superuser and the
anonymous placeholder, and keeps a person in every other account state.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py::TestRealContributors
-q -p no:randomly` → 2 passed, against the pre-refactor `managers.py` (real() already existed at
`managers.py:109`, called by no test — T122's "built-without-tests" gap).

Next: T120 — TestActiveAccounts.

Watch: none.

## 2026-08-20T11:08:00Z · US9 · T120

Did: Added `TestActiveAccounts` to `test_managers.py` — `active()` keeps the ghost/invited/claimed
population members and drops the inactive one.

Verified: `poetry run pytest
tests/test_contrib/test_contributors/test_managers.py::TestActiveAccounts -q -p no:randomly` → 1
passed, against the pre-refactor `managers.py` (active() already existed at `managers.py:120` -
T123's gap).

Next: T121 — TestQuerysetManagerParity.

Watch: none.

## 2026-08-20T11:10:00Z · US9 · T121

Did: Added `TestQuerysetManagerParity` to `test_managers.py`, parametrised across every FR-041/
FR-042 query that exists (`real`, `active`, `claimed`, `unclaimed`, `ghost`, `invited` on Person;
`current`, `past` on Affiliation; `by_role` on Contribution): each returns identical rows from
`Model.objects.<method>()` and `Model.objects.all().<method>()`.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -q -p
no:randomly` → 26 passed, against the pre-refactor `managers.py` (the six hand-written
`UserManager` proxies, `AffiliationManager`'s three proxies and `ContributionManager`'s three
proxies all already forwarded correctly - this run is the before-picture that T124's refactor must
keep green).

Next: T122/T123 — confirm `real()`/`active()` already satisfy FR-041's substance (no code change);
then T124.

Watch: FR-041 also names "each of the four account states". The three that exist as named queryset
methods (`ghost`, `invited`, `claimed`) are covered above. A fourth, matching D8's corrected
"inactive" state (deactivated takes precedence over claimed), does not exist as a queryset method
anywhere in the codebase - only the raw `is_active=False` field does. D8/the account-state
derivation is story US3's work, not running yet; per the brief I did not build it here. The
`contributor_population` fixture still carries an "inactive" person as fixture *data* (T118 asks
for one person in each of the four states), and `TestActiveAccounts` proves `is_active=False`
excludes them from `active()` - but no test asserts a queryset method named `inactive()` because
none exists.

## 2026-08-20T11:15:00Z · US9 · T122/T123

Did: No code change. `PersonQuerySet.real()` (`managers.py:109`) already excludes
`is_superuser=True` and `email="AnonymousUser"` (FR-041's real-contributors filter, T122), and
`PersonQuerySet.active()` (`managers.py:120`) already filters `is_active=True` (FR-041's
active-accounts filter, T123). Both tasks' "Open" annotations say "built-without-tests" - the gap
was the test, not the filter, and T119/T120 close it.

Verified: covered by T119's and T120's runs above; no new command run for these two task IDs.

Next: T124 — sweep both managers onto `from_queryset`.

Watch: none.

## 2026-08-20T11:20:00Z · US9 · T124

Did: Rewrote `fairdm/contrib/contributors/managers.py` so every FR-041/FR-042 query is defined once
on its queryset and reaches the manager through `from_queryset`, matching
`fairdm.core.dataset.models.DatasetManager` (D14):
- `UserManager(BaseUserManager, PrefetchPolymorphicManager.from_queryset(PersonQuerySet))` -
  removed the manual `get_queryset()` override (redundant with the `queryset_class` that
  `PolymorphicManager.from_queryset` sets) and all six hand-written proxy methods (`real`,
  `active`, `claimed`, `unclaimed`, `ghost`, `invited`).
- `AffiliationManager(models.Manager.from_queryset(AffiliationQuerySet))` - removed the three
  hand-written proxies (`primary`, `current`, `past`). `primary()` returns `.first()` rather than a
  queryset; verified directly (see decisions.md D23) that `Manager.from_queryset` copies a method's
  forwarding call regardless of return type, so this does not block composition, and left `primary()`
  as-is rather than changing its return type or any caller.
- `ContributionManager(OrderedModelManager.from_queryset(ContributionQuerySet))` - removed the
  three hand-written proxies (`by_role`, `for_entity`, `by_contributor`). `OrderedModelManager` is
  itself `models.Manager.from_queryset(OrderedModelQuerySet)`, so ordered-model methods
  (`get_max_order()`, etc.) are unaffected.

Reordered `PersonQuerySet` above `UserManager` in the file because `from_queryset()` needs the
queryset class to already exist at class-definition time (a forward reference inside a method body,
as the old `get_queryset()` override used, no longer applies once `get_queryset` itself is gone).

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -q -p no:randomly` → 26
  passed (T119/T120/T121 stayed green through the refactor - no assertion changed).
- `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 222 passed.
- `poetry run ruff check fairdm/contrib/contributors/managers.py` → all checks passed.
- `DJANGO_SETTINGS_MODULE=tests.settings poetry run python manage.py makemigrations --check
  --dry-run` → No changes detected.

Next: T125 — document the manager/queryset API.

Watch: none.

## 2026-08-20T11:35:00Z · US9 · T125

Did: Fixed `docs/portal-development/contributors.md`'s "Unified Manager Approach" section, which
described `real()` as excluding "ghosts" in two places (the code comment and the "Portal Queries"
callout) - it excludes `is_superuser=True` and the anonymous placeholder, and says nothing about
claim status. Rewrote both with testable one-line comments, added the missing `active()` example
(it existed in code but nowhere in the doc), fixed the same "Exclude ghosts" claim in the "Manager
Method Summary" table and added its `active()` row, and added a `Contribution.objects.by_role()`
example to the Contribution section (FR-042's credits-by-role query had no example anywhere in the
page). Left the Affiliation section's `current()`/`past()`/`primary()` examples as they were -
already accurate. Left the state-machine/privacy sections untouched - out of this task's scope
(US3/D9's territory) even though they carry their own known drift.

Verified: every rewritten/added example run directly against a throwaway pytest against this
branch (not committed) - `real()`, `active()`, `claimed()`, `unclaimed()`, `ghost()`, `invited()`,
`real().claimed()` chaining, `Affiliation.objects.current()`/`.past()`/`person.affiliations.primary()`,
and `Contribution.objects.by_role("Creator")` all ran without error and returned what the prose
says. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 222 passed
(doc-only change, no production code touched).

Next: none — all eight tasks complete. Full-suite verify remains for the completion report.

Watch: T122 and T123 required no code change (see the entry above) - `feature-state.json` records
that explicitly rather than pointing at a commit that does not exist.

## 2026-08-20T13:00:00Z · Implementer US3 · T041

Did: Added `AccountState(models.TextChoices)` to `fairdm/contrib/contributors/choices.py` - GHOST,
INVITED, CLAIMED, INACTIVE, each with a translatable label (D8). No test file targets choices
classes directly in this app; the class is exercised through `Person.account_state` (T043) and
`PersonQuerySet`'s filters (T044).

Verified: `poetry run ruff check fairdm/contrib/contributors/choices.py` → all checks passed.

Next: T042 - index the stored claim flag.

Watch: none.

## 2026-08-20T13:05:00Z · Implementer US3 · T042

Did: Added `db_index=True` to `Person.is_claimed` (`fairdm/contrib/contributors/models.py`) and
extended its `help_text` to say why (Article IX - the state filters and the admin claim-status
filter both read it). No migration generated (see T045 below).

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -q -p no:randomly`
→ 74 passed (`TestFieldMetadata` continues to see a non-empty verbose_name/help_text on the field).

Next: T037/T038/T039/T043 - derive `Person.account_state` against a failing test first.

Watch: none.

## 2026-08-20T13:20:00Z · Implementer US3 · T037/T038/T039/T043

Did: Wrote `TestAccountState`, `TestAccountStatePrecedence` and `TestClaimIsStoredOnce` in
`tests/test_contrib/test_contributors/test_models.py` against the not-yet-existing
`Person.account_state` and ran them - 8 failures, all `AttributeError`/`KeyError` on
`account_state`, confirming RED for the right reason. Then added `Person.account_state` as a
`@property` on `fairdm/contrib/contributors/models.py`, deriving `AccountState.INACTIVE` /
`.CLAIMED` / `.INVITED` / `.GHOST` from `is_active`, `is_claimed` and `email` in that fixed
precedence (D8) - no new field, no `state_history`, nothing written on save. `TestAccountState`
uses the `contributor_population` fixture (already covers all four states, built in US9);
`TestAccountStatePrecedence` builds its own two persons because it needs a deactivated+claimed
combination the population fixture does not carry. `TestClaimIsStoredOnce` asserts `is_claimed` is
a concrete `BooleanField`, `"account_state"` is absent from `Person._meta.get_fields()`, and
`Person.__dict__["account_state"]` is a `property` object, not an attribute set in `__init__`/`save`.

Verified:
- Pre-implementation: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
  "TestAccountState or TestClaimIsStoredOnce" -q -p no:randomly` → 8 failed, 2 passed (RED).
- Post-implementation: `poetry run ruff check fairdm/contrib/contributors/models.py` → all checks
  passed. `poetry run pytest tests/test_contrib/test_contributors/test_models.py -q -p no:randomly`
  → 84 passed.

Next: T040/T044 - the matching queryset filters.

Watch: `fairdm/contrib/contributors/admin.py:206`'s `PersonAdmin.account_state` display method
already duplicates this exact precedence by hand, with a comment saying it is standing in until
US3 lands. `admin.py` is out of this story's scope (owned by US10) - flagged as a `concern`, not
touched.

## 2026-08-20T13:45:00Z · Implementer US3 · T040/T044

Did: Wrote `TestAccountStateFilters` in `tests/test_contrib/test_contributors/test_managers.py`
and ran it against the pre-existing queryset - 3 of 5 cases failed: `inactive` with
`AttributeError` (no such method), `claimed` because `Person.objects.claimed()` (`is_claimed=True`
alone) wrongly included the population's deactivated-but-claimed member - exactly the defect D8
names at `managers.py:132`. `ghost`/`invited` happened to pass pre-fix only because the
population's ghost/invited members are both active. Confirmed RED for the right reason, then
added `PersonQuerySet.inactive()` (`is_active=False`) and added `is_active=True` to `ghost()`,
`invited()` and `claimed()` so all four now mirror `account_state`'s precedence exactly -
deactivation decided first. Left `real()`, `active()` and `unclaimed()` untouched; they are not
part of the four-state partition. `UserManager` already composes from `PersonQuerySet` via
`from_queryset` (D14, US9's T124), so no manager-side change was needed - `inactive()` reaches
`Person.objects` for free.

Verified:
- Pre-fix: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -k
  TestAccountStateFilters -q -p no:randomly` → 3 failed, 2 passed (RED).
- Post-fix: `poetry run ruff check fairdm/contrib/contributors/managers.py` → all checks passed.
  `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -q -p no:randomly` → 31
  passed. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 261 passed
  (no regression in `test_admin.py` or elsewhere from narrowing `ghost`/`invited`/`claimed`).

Next: T045 (skip - no migration) and T046 (docs).

Watch: none.

## 2026-08-20T13:55:00Z · Implementer US3 · T045

Did: Skipped. The brief prohibits generating a migration this story: four sibling stories are
changing contributor models concurrently and Forge consolidates one migration per model at
convergence. `is_claimed` already exists as a column (migration 0014); only its index is new, and
the test settings stub `MIGRATION_MODULES` so the suite builds tables straight from the models
without one. No code change, no commit.

Verified: N/A - nothing to run.

Next: T046 - documentation.

Watch: The task's literal text names a migration filename
(`migrations/0003_person_claim_flag.py`) that doesn't match this repository's actual migration
sequence (currently at 0026) - the task list was written as though the app were empty (brief,
prohibitions). Not acted on beyond skipping the migration itself.

## 2026-08-20T14:05:00Z · Implementer US3 · T046

Did: Added an "Account States" section to
`docs/portal-administration/managing-unclaimed-profiles.md` (already in the toctree, so no index.md
change needed): a table of the four states in precedence order, how a person arrives in each, and
the queryset method that filters for it. Reworded the existing "Banned Profiles" section to
"Inactive Profiles", pointing at the new section and D8's renaming, while leaving the literal
`"Person is banned (is_active=False)."` failure-reason string untouched and explicitly noted as
not yet updated - that string is emitted by `services/claiming.py`, out of this story's scope
(D2/D3/D11-adjacent prohibition).

Verified: read through the rendered Markdown; every code sample (`Person.objects.ghost()`,
`.invited()`, `.claimed()`, `.inactive()`, `person.account_state`) matches a name this story just
tested. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 261 passed
(doc-only change).

Next: none - all ten tasks complete. Full-suite verify remains for the completion report.

Watch: `fairdm/contrib/contributors/admin.py`'s claim-status filter and `account_state` display
method duplicate logic this story now provides on the model; recommend a follow-up story sweep
`admin.py` to call `Person.account_state` directly instead. Left untouched - `admin.py` is owned by
US10, out of this story's scope.
## 2026-08-20T11:48:00Z · Implementer US4 · T047/T052

Did: Added `OrganizationType(models.TextChoices)` to `fairdm/contrib/contributors/choices.py`
with the nine ROR schema 2.1 organisation types (`education`, `funder`, `healthcare`, `company`,
`archive`, `nonprofit`, `government`, `facility`, `other`), read from research.md R1 rather than
re-derived. Cited the schema as the source in the module docstring. Added
`TestOrganizationTypeVocabulary` (`tests/test_contrib/test_contributors/test_choices.py`, new
file), asserting every member by name and a count bound, not by iterating the class.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_choices.py -q -p no:randomly` →
  first run (before the class existed) failed on `ImportError`, the right reason; after adding the
  class, 2 passed.
- `poetry run ruff check fairdm/contrib/contributors/choices.py
  tests/test_contrib/test_contributors/test_choices.py` → all checks passed.

Next: T048/T053 — the `type` field on `Organization` itself.

Watch: none.

## 2026-08-20T11:48:00Z · Implementer US4 · T048/T053

Did: Added `Organization.type` — `CharField`, `choices=OrganizationType.choices`, `null=True`,
`blank=True`, `db_index=True` — plus `Meta.default_related_name = "organizations"` on
`Organization` (FR-016, Article IX). Added `TestOrganizationTypeValidation`
(`tests/test_contrib/test_contributors/test_models.py`): a type outside the ROR set is refused by
`full_clean()`, every ROR member is accepted (asserted by name, not iterated), and the field
carries the index.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestOrganizationTypeValidation
  tests/test_contrib/test_contributors/test_models.py::TestOrganizationCreationAndValidation -q
  -p no:randomly` → first run (before the field existed) failed on `FieldDoesNotExist`, the right
  reason; after adding the field, 10 passed.
- `poetry run ruff check fairdm/contrib/contributors/models.py
  tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T050/T054 — the parent-deletion defect.

Watch: none.

## 2026-08-20T11:48:00Z · Implementer US4 · T050/T054

Did: Reproduced the data-loss defect named in the brief — `Organization.parent` was
`on_delete=CASCADE`, so deleting a university deleted every department beneath it, their
affiliations and their credits (decisions.md D12). Changed to `SET_NULL` (the field was already
`null=True`, nothing else changed). Added `TestOrganizationParentDeletion`
(`tests/test_contrib/test_contributors/test_models.py`): a department with a member (affiliation)
and a credit (contribution) survives its university's deletion with no parent, its affiliation and
its contribution untouched.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestOrganizationParentDeletion
  tests/test_contrib/test_contributors/test_models.py::TestOrganizationCreationAndValidation -q
  -p no:randomly` → first run (against CASCADE) failed reproducing the exact defect
  (`Organization.DoesNotExist` on the child after the parent's deletion); after `SET_NULL`, 8
  passed.
- `poetry run ruff check fairdm/contrib/contributors/models.py
  tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T051/T055 — location field indexing.

Watch: none.

## 2026-08-20T11:48:00Z · Implementer US4 · T051/T055

Did: Added `db_index=True` to `Organization.city` and `Organization.country` (FR-019, Article IX
— neither was indexed). Added `TestOrganizationLocation`
(`tests/test_contrib/test_contributors/test_models.py`): city and country are optional (an
organisation with neither still validates), round-trip through a save and a `refresh_from_db()`,
and both are indexed.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestOrganizationLocation
  tests/test_contrib/test_contributors/test_models.py::TestOrganizationCreationAndValidation -q
  -p no:randomly` → the optional/round-trip cases passed immediately against the pre-existing
  fields (T051 is a test-only gap); the index assertion failed first (`db_index` was `False`), the
  right reason, then passed after adding `db_index=True`. 10 passed overall.
- `poetry run ruff check fairdm/contrib/contributors/models.py
  tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T056 (skipped, see Watch) and T059 — documentation.

Watch: T056 asked for a new migration file
(`fairdm/contrib/contributors/migrations/0004_create_organization.py`). Per the brief's
prohibition, no migration file was added — test settings stub `MIGRATION_MODULES`, and Forge
generates one consolidated migration across all four concurrent stories at convergence. Confirmed
the model changes are migration-consistent with
`poetry run python manage.py makemigrations --check --dry-run contributors`, which reports exactly
the expected operations (`Add field type`, `Alter field city/country/parent`, `Change Meta options`)
against `0027_alter_organization_options_organization_type_and_more.py` — not written to disk.

## 2026-08-20T11:48:00Z · Implementer US4 · T059

Did: Added an "Organization" section to `docs/data_models/contributors.md`: the `type` field and
the ROR set it draws from (and the deliberate single-value narrowing), the `parent`/
`sub_organizations` hierarchy, what happens to a sub-organisation when its parent is deleted, and
the `city`/`country` location fields. Worked example: a department under a university, the
university then deleted, the department left with no parent.

Verified: the worked example was copied into a throwaway test file inside
`tests/test_contrib/test_contributors/` (not committed), run with
`poetry run pytest -q -p no:randomly` → 1 passed, then deleted.

Next: none — all ten tasks (T047, T048, T050-T056, T059) addressed. Full-suite verify remains for
the completion report.
## 2026-08-20T14:00:00Z · Implementer US5 · T061

Did: Added `TestAffiliationUniqueness` to `test_models.py` (FR-021, SC-008): a second membership
of the same organisation by the same person is refused both at `full_clean()` validation, with a
readable, field-scoped message, and at the database. Observed the validation test fail against
the pre-existing code first - Django's automatic `unique_together` message ("Affiliation with
this Person and Organization already exists.") is technically readable, but not the friendlier,
person/organization-named message this task asks for - then let T069's `clean()` make it pass.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestAffiliationUniqueness -q -p no:randomly` → 2 passed (green only after T069 landed; see that entry).

Next: T067.

Watch: none.

## 2026-08-20T14:10:00Z · Implementer US5 · T067

Did: Added `db_index=True` to `Affiliation.type` (ownership lookups filter on it - Article IX) and
`default_related_name = "affiliations"` to `Affiliation.Meta`. No FK currently points at
`Affiliation` without its own explicit `related_name`, so the default is currently inert but
present per the task's text. Added `TestAffiliationSchema` asserting both.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestAffiliationSchema -q -p no:randomly` → 2 passed.

Next: T069.

Watch: none.

## 2026-08-20T14:20:00Z · Implementer US5 · T069

Did: Replaced `Affiliation.Meta.unique_together = ("person", "organization")` with a named
`models.UniqueConstraint(fields=["person", "organization"], name="unique_affiliation_person_organization")`,
and added `Affiliation.clean()` raising a field-scoped `ValidationError` ("<person> is already a
member of <organization>.") when a duplicate membership exists, excluding self on update. This is
what turns T061's validation test green.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestAffiliationUniqueness tests/test_contrib/test_contributors/test_models.py::TestAffiliationUniqueConstraints -q -p no:randomly` → 9 passed. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 250 passed.

Next: T070.

Watch: none.

## 2026-08-20T14:35:00Z · Implementer US5 · T070

Did: `Affiliation.save()` now wraps the demotion of the person's other primary affiliation and
the save itself in one `transaction.atomic()` block (FR-024), rather than running the demotion
`.update()` and the save as two independent statements. Added
`TestPrimaryAffiliationDemotionIsAtomic`, which monkeypatches `django.db.models.Model.save` (the
base `save()` at the bottom of `Affiliation`'s MRO) to raise, then asserts the demotion of the
other affiliation was rolled back too - proving the two are one unit, not proving a call sequence.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestPrimaryAffiliationDemotionIsAtomic tests/test_contrib/test_contributors/test_models.py::TestPrimaryAffiliationConstraint -q -p no:randomly` → 4 passed.

Next: T071.

Watch: none.

## 2026-08-20T14:45:00Z · Implementer US5 · T071

Did: Added a second constraint to `Affiliation.Meta.constraints` - a partial
`models.UniqueConstraint(fields=["person"], condition=models.Q(is_primary=True), name="unique_primary_affiliation_per_person")`
- so a write that bypasses `Affiliation.save()` (a queryset `.update()`, specifically) cannot leave
two primary memberships for the same person. Added
`TestPrimaryAffiliationDatabaseConstraint`, which writes `is_primary=True` on two rows via
`Affiliation.objects.filter(pk=...).update(...)` directly (not `.save()`) and asserts the second
raises `IntegrityError`.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::TestPrimaryAffiliationDatabaseConstraint tests/test_contrib/test_contributors/test_models.py::TestPrimaryAffiliationConstraint tests/test_contrib/test_contributors/test_models.py::TestPrimaryAffiliationDemotionIsAtomic -q -p no:randomly` → 5 passed. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 252 passed.

Next: T073 (skipped, see below), then T074.

Watch: T073 asks for `fairdm/contrib/contributors/migrations/0005_create_affiliation.py`. Per the
brief's prohibitions, no migration is generated in this story - Forge consolidates one migration
per model at convergence, and test settings stub `MIGRATION_MODULES` so the suite builds tables
from the models regardless. No code change was made for T073; `feature-state.json` leaves it
`todo` rather than marking it done or blocked.

## 2026-08-20T15:00:00Z · Implementer US5 · T074

Did: `AffiliationFactory` now declares `type = Affiliation.MembershipType.MEMBER` explicitly
(matching the model's own default, made explicit per Article X) and `start_date = "2020"` so the
factory default is a current membership (a start date, no end date) rather than a bare row with
neither declared. Added `TestAffiliationFactory` to `tests/test_factories/test_contributors.py`
(mirrors `fairdm/factories/contributors.py`, Article X).

Verified: `poetry run pytest tests/test_factories/test_contributors.py::TestAffiliationFactory -q -p no:randomly` → 2 passed. `poetry run pytest tests/test_contrib/test_contributors tests/test_factories -q -p no:randomly` → 328 passed (no regression from the new factory defaults).

Next: T076.

Watch: none.

## 2026-08-20T15:15:00Z · Implementer US5 · T076

Did: Documented memberships in `docs/portal-development/contributors.md`: what makes a membership
current (no `end_date`, the only rule), the readable-message-then-database-constraint uniqueness
behaviour (T061/T069), the atomic primary-membership demotion and its database constraint
(T070/T071), what the primary membership is used for
(`Contribution.set_default_affiliation`, `fairdm/contrib/contributors/models.py:1153`, reads it
for the crediting-organisation default), and a worked example of a researcher moving from a
university to a research institute across two periods at different date precisions.

Verified: every snippet in the new sections run against this branch via a throwaway pytest (not
committed, deleted after the check) exercising the exact calls shown in the doc - `current()`,
`past()`, `primary()`, the duplicate-membership `full_clean()` message, and the two-institution
example end to end. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` →
252 passed (doc-only change, no production code touched).

Next: none - all seven implemented tasks complete (T073 skipped per prohibition). Full-suite
verify remains for the completion report.
## 2026-08-20T12:05:00Z · Implementer US7 · T089/T098

Did: Fixed the story's headline defect (design review SPEC-001): `Contributor.add_to` and
`Contribution.add_to` both called `contribution.roles.set(roles_qs)`, which replaces every role
recorded on a prior credit the moment a second role is added, against FR-031's accumulation
requirement. Both call sites now use `contribution.roles.add(*roles_qs)`. Added
`TestContributionUniqueness` to `test_models.py` and wrote the reproduction test first per
`craft-tdd`: it failed with the accumulated set missing the first role before the fix, and passed
after.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
  TestContributionUniqueness -q -p no:randomly` → 3 passed (after fix; 2 of 3 failed before it,
  for the accumulation assertion specifically).
- `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 250 passed.
- `poetry run ruff check fairdm/contrib/contributors/models.py
  tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T097 - name the uniqueness constraint and give it a matching `clean()` message.

Watch: none.

## 2026-08-20T12:10:00Z · Implementer US7 · T097

Did: Replaced `Contribution.Meta.unique_together` with a named `UniqueConstraint` carrying a
`violation_error_message`, added a supporting composite index on `(content_type, object_id)` for
the `for_entity()` lookup, and added `Contribution.clean()` raising the same message for a
duplicate pairing - so `full_clean()` refuses a duplicate the same way a raw insert does, instead
of Django's generic multi-field message. Wrote the `full_clean()` test first: it failed against
the generic message before the `clean()` override existed.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
  "TestContributionUniqueness or TestContributionGFKRelationships" -q -p no:randomly` → 12 passed.
- `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 250 passed.
- No migration added - `MIGRATION_MODULES` is stubbed for tests per the story brief; a single
  consolidated migration is generated at convergence.

Next: T090/T098 - refuse a role from outside the roles vocabulary.

Watch: none.

## 2026-08-20T12:20:00Z · Implementer US7 · T090/T098

Did: Extended `Contribution.clean()` to refuse a role Concept drawn from any vocabulary other
than `fairdm-roles` (FR-032), completing T098 alongside the T089 accumulation fix. Added
`TestContributionRoles` with a positive case (an in-vocabulary role passes `full_clean()`) and a
negative case (a Concept created under a throwaway `Vocabulary` row is refused) - the negative
case failed with "DID NOT RAISE" before the check existed. Also fixed the one pre-existing test
the story brief named explicitly: `test_contribution_multiple_roles` deferred to a
try/except/skip if the `fairdm-roles` vocabulary had fewer than 2 concepts, but the session-scoped
`django_db_setup` fixture (`tests/conftest.py`) already seeds it via `Concept.preload()` for every
test - the skip path was dead code guarding a scenario that cannot happen, and the brief was
explicit that a test which may silently skip is not coverage. Removed the try/except/skip; the
test now asserts directly.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
  "TestContributionRoles or TestMultipleRolesPerContribution" -q -p no:randomly` → 3 passed.
- `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 252 passed.
- `poetry run ruff check fairdm/contrib/contributors/models.py
  tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T088 - cover crediting a dataset, a measurement and an organisation-as-contributor.

Watch: modified a pre-existing test not authored this story - explicitly directed by the story
brief's prohibitions list, not a self-authorized change. Noted in the completion report.

## 2026-08-20T12:30:00Z · Implementer US7 · T088

Did: Added `TestContributionTargets` covering the three FR-030 cases that had no coverage - a
person credited on a dataset, a person credited on a measurement, and an organisation credited as
a contributor - through the existing `Contributor.add_to`/`Organization.add_to`. The sample case
was already covered by `TestSampleContributions` in
`tests/test_core/test_sample/test_models.py` and is cited rather than rewritten, per the story
brief. All four assertions passed against the existing implementation with no production change -
this task was a coverage gap, not a defect.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
  TestContributionTargets -q -p no:randomly` → 4 passed.
- `poetry run ruff check tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T092/T100 and T093/T101 - credited-outputs and co-contributor reporting.

Watch: none.

## 2026-08-20T12:45:00Z · Implementer US7 · T092/T100/T093/T101

Did: `TestContributorCredits` (T092), testing the full FR-034 scenario for the first time,
surfaced that `Contributor.samples`/`.measurements` were always empty for any real credit: Sample
and Measurement can only be instantiated as a concrete subclass (the polymorphic base cannot be
created directly), so every credit is stored under that subclass's own content type, and a
`GenericRelation` reverse query from the polymorphic base can only match its own content type -
never a subclass's. Added `Contributor.credited_object_ids(base_model)`, which checks each of the
contributor's distinct content types against the base model via `issubclass()` and relies on
Django's multi-table inheritance sharing one primary key across the hierarchy, and rewired
`samples`/`measurements` through it. `projects`/`datasets` were already correct (Project and
Dataset have no polymorphic subclasses) and were left untouched. Added
`Contributor.get_credit_counts()` for the counts-by-kind FR-034 asked for, resolved in a bounded
number of queries (one grouping query plus one per distinct content type, at most four) and
guarded by a `django_assert_max_num_queries` test.

`TestCoContributors` (T093) surfaced a second, independent defect in `get_co_contributors()`
(T101's target): it filtered `contributions__content_type_id__in=[...]` and
`contributions__object_id__in=[...]` as two separate `.filter()` calls, which Django joins
independently - so a contributor could read as a co-contributor by matching one of my content
types on one object and one of my object ids on a completely different, unrelated object, without
sharing any actual object with me. Reproduced with a test that forces exactly that cross-match via
directly constructed `Contribution` rows (not relying on coincidental primary-key collisions).
Rebuilt the method as a single OR of exact `(content_type, object_id)` `Q` pairs, counted via a
filtered, distinct `Count`, so a contributor only appears when at least one pair genuinely
matches, and ordering by `collaboration_count` still holds.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
  "TestContributorCredits or TestCoContributors" -q -p no:randomly` → 6 passed (all 4 initially
  failed for the reasons above; a `test_reports_each_kind_of_credited_output` sub-failure on
  `person.datasets` was traced separately to `DatasetFactory()`'s default `visibility=PRIVATE`
  being excluded by `Dataset.objects`, which is pre-existing, correct manager behaviour unrelated
  to this story - fixed in the test by requesting `Visibility.PUBLIC` explicitly, not in
  production code).
- `poetry run pytest tests/test_contrib/test_contributors tests/test_core/test_sample
  tests/test_core/test_measurement tests/test_core/test_dataset tests/test_core/test_project -q
  -p no:randomly` → 1121 passed, 12 skipped, 1 pre-existing failure
  (`test_contribution_can_be_added_from_the_specimens_own_page`, reproduced identically on the
  pre-T092 commit and in `admin.py`, which this story is prohibited from touching).
- `poetry run ruff check fairdm/contrib/contributors/models.py
  tests/test_contrib/test_contributors/test_models.py` → all checks passed.

Next: T102 - withdraw rights on a queryset-deleted credit.

Watch: pre-existing admin test failure unrelated to this story, named above and in the completion
report's concerns.

## 2026-08-20T13:00:00Z · Implementer US7 · T102

Did: RECON-002 - `Contribution.remove_user_perms` is a django-lifecycle `AFTER_DELETE` hook,
which only runs from the model instance's own `delete()`; `QuerySet.delete()` bypasses that
entirely, so the withdrawal never fired for a credit removed in bulk, against FR-036's
unqualified wording. Wrote `TestWithdrawRightsOnCreditDeletion` first, including a queryset-delete
case: it failed (right still held) before any implementation existed. Added
`withdraw_rights_on_credit_deletion` as a genuine Django `post_delete` receiver in the new
`fairdm/contrib/contributors/receivers.py`, connected from `ContributorsConfig.ready()` with an
explicit `dispatch_uid`. Left the existing lifecycle hook in place rather than removing it -
`remove_all_model_perms` is idempotent, so the two run harmlessly alongside each other on an
instance delete, and this keeps the change additive and the existing instance-delete test
(`TestContributionRevocationIsNormalised::test_deleting_the_contribution_removes_the_grant`)
undisturbed.

Verified:
- `poetry run pytest tests/test_contrib/test_contributors/test_receivers.py -q -p no:randomly` →
  3 passed (queryset delete, instance delete, and an organisation credit that must not error).
- `poetry run pytest tests/test_contrib/test_contributors
  tests/test_core/test_sample/test_permissions.py -q -p no:randomly` → 286 passed.
- `poetry run ruff check fairdm/contrib/contributors/receivers.py
  fairdm/contrib/contributors/apps.py tests/test_contrib/test_contributors/test_receivers.py` →
  all checks passed.

Next: T107 - document crediting.

Watch: none.

## 2026-08-20T13:15:00Z · Implementer US7 · T107

Did: Rewrote the "Contribution Model" section of `docs/portal-development/contributors.md`,
whose own example did not run (`Concept.objects.get(vocabulary=FairDMRoles, label="Author")` is
not a valid call against the real API) and said nothing about the one-credit-per-pairing rule,
role accumulation, the crediting-organisation default, or that deleting a credit withdraws rights
while creating one grants none. Split it into four parts matching FR-031/032/033/036 plus the
credited-outputs reporting methods (FR-034/035), Articles VI and XVII. Also fixed the "Person
Properties" section's `person.add_to(my_project, roles=["Author", "Data Collector"])` example,
which named role strings that are not members of the `fairdm-roles` vocabulary and so would have
been silently dropped by `add_to`'s `name__in=roles` filter rather than credited - replaced with
real vocabulary names (`"Creator"`, `"DataCollector"`).

Verified: every new/changed example run against this branch in a scratch pytest test, not
committed (Article VI) - the accumulation example, the vocabulary-refusal `full_clean()` call, the
`by_role()` query, the affiliation default, all four reporting properties,
`get_credit_counts()` and `get_co_contributors()` all ran without error.

Next: none - all eleven tasks complete. Full-suite verify remains for the completion report.

Watch: none.
## 2026-08-20T11:50:00Z · Implementer US2 · T023

Did: Added `TestPersonIsTheAccount` to `test_models.py` asserting `get_user_model()` is `Person`
by name and that no other installed model declares a `USERNAME_FIELD`.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestPersonIsTheAccount -q -p no:randomly` → 2 passed. Both assertions already held against
today's code - this task is pure gap-filling coverage, no production change.

Next: T024.

Watch: none.

## 2026-08-20T11:52:00Z · Implementer US2 · T024

Did: Added `TestAttributionOnlyPerson` to `test_models.py` asserting an attribution-only
(`unclaimed_person`) has no email, reports `has_usable_password()` False, and that
`authenticate()` against them returns None.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestAttributionOnlyPerson -q -p no:randomly` → 2 passed. Already-correct behaviour, coverage only.

Next: T025.

Watch: none.

## 2026-08-20T11:54:00Z · Implementer US2 · T025

Did: Added `TestPersonActivationEligibility` to `test_models.py`. Beyond the plain
`is_active is True` assertion (which the annotation notes "holds by Django's own default"), added
a second test that actually exercises `django.contrib.auth.forms.PasswordResetForm.get_users()`
after giving the ghost an email - that form filters on `is_active=True`, so this is the real
differentiator that proves `create_unclaimed()`'s explicit `is_active=True` matters.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestPersonActivationEligibility -q -p no:randomly` → 2 passed.

Next: T026.

Watch: none.

## 2026-08-20T11:56:00Z · Implementer US2 · T026

Did: Added `TestPersonEmailUniqueness` to `test_models.py`: a duplicate address is refused at
`full_clean()` and at `Person.objects.create()` (IntegrityError), and any number of people may
carry `email=None`.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestPersonEmailUniqueness -q -p no:randomly` → 3 passed. Passes against today's field-level
`unique=True` - the case-insensitive gap is T031's, not this task's.

Next: T027.

Watch: none.

## 2026-08-20T11:59:00Z · Implementer US2 · T027

Did: Replaced `test_person_clean_prevents_claimed_email_null` (authorised by the brief - it set
`has_usable_password()` and `is_active` True *together with* `is_claimed=True`, so it could not
tell which of the two `clean()` actually reads) with `TestClaimedPersonEmailRemoval`, carrying two
tests: a claimed person refused with a message on the `email` field, and a ghost who has a usable
password (`is_claimed=False`) who is *not* refused - the differentiator.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestClaimedPersonEmailRemoval -q -p no:randomly` → 1 passed, 1 failed. The failure is the
ghost-with-password case, RED for the right reason: today's `clean()`
(`fairdm/contrib/contributors/models.py`) reads `has_usable_password()`/`is_active`, not
`is_claimed` (RECON-001, D21). T032 fixes it.

Next: T028, then T029-T032 to turn this red test green.

Watch: this commit intentionally leaves one test red pending T032, landing in the same session.

## 2026-08-20T12:00:00Z · Implementer US2 · T028

Did: Added `TestPersonManagerCreation` to `test_managers.py`: `create_user` normalises the
email and sets a usable password when given one; without a password it's unusable;
`create_superuser` sets both flags and still refuses `is_staff=False`; `create_unclaimed`
produces the ghost shape (no email, unclaimed, active, unusable password).

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -k
TestPersonManagerCreation -q -p no:randomly` → 2 failed, 3 passed. RED for the right reason:
`create_user` does not exist yet (`AttributeError`). `create_superuser`/`create_unclaimed` were
already correct and passed immediately.

Next: T029 (already landed), then T030 to turn the two red tests green.

Watch: this commit intentionally leaves two tests red pending T030, landing next in this session.

## 2026-08-20T12:05:00Z · Implementer US2 · T030

Did: Added a public `create_user(email, password=None, **extra_fields)` to `UserManager`
(`fairdm/contrib/contributors/managers.py`), mirroring `create_superuser`'s
`is_staff`/`is_superuser` defaulting (False instead of True) and delegating to the existing
`_create_user`. No separate "unusable password when none supplied" branch was needed -
`AbstractBaseUser.set_password(None)` already sets one, so `_create_user` already had that
behaviour; `create_user` just needed to exist with an optional `password` parameter. Also gave
`create_superuser`'s `password` parameter the same `=None` default for signature symmetry.

Did not rename `UserManager` to `PersonManager`, or restructure it around a fresh
`Manager.from_queryset(PersonQuerySet)` call — the annotation's "hand-written proxies rather than
from_queryset" was already stale: `UserManager(BaseUserManager,
PrefetchPolymorphicManager.from_queryset(PersonQuerySet))` already composes via `from_queryset`
(landed by the US9/US10 manager-composition work, commit `efeefa9`, merged into this branch ahead
of my run). The substance T030 asks for — a from_queryset-composed manager mixing
`BaseUserManager` — was already there; only `create_user` was genuinely missing.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -k
TestPersonManagerCreation -q -p no:randomly` → 5 passed. `poetry run ruff check
fairdm/contrib/contributors/managers.py` → all checks passed. `poetry run pytest
tests/test_contrib/test_contributors -q -p no:randomly` → 262 passed, 1 failed (the T027/T032
pending test, expected).

Next: T031.

Watch: none.

## 2026-08-20T12:10:00Z · Implementer US2 · T031

Did: Added `Person.Meta(AbstractUser.Meta)` with a case-insensitive `UniqueConstraint(Lower(
"email"), condition=Q(email__isnull=False))` and removed the field-level `unique=True` from
`email` (the two mechanisms would otherwise overlap - one case-sensitive DB index and one
case-insensitive one for the same column). Subclassed `AbstractUser.Meta` rather than declaring a
bare `class Meta` so `verbose_name`/`verbose_name_plural` ("user"/"users", inherited implicitly
today since Person declares no Meta of its own) don't silently change to Django's
`Person`-derived defaults as a side effect of adding one - verified before and after with a Python
shell read of `Person._meta.verbose_name`.

Added two tests to `TestPersonEmailUniqueness`: a case-insensitive collision refused at
`full_clean()`, and the same refused when created directly through the manager (`Person.objects.
create()`, which never calls `clean()` and so never lowercases) - the acceptance criterion
explicitly requires the second one, since the DB-level constraint is the only thing that can catch
it.

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestPersonEmailUniqueness -q -p no:randomly` → 5 passed. `poetry run ruff check
fairdm/contrib/contributors/models.py` → all checks passed. `poetry run pytest
tests/test_contrib/test_contributors -q -p no:randomly` → 264 passed, 1 failed (T027/T032
pending, expected). Confirmed the case-insensitive collision is real evidence, not a collation
accident: `tests/settings.py` runs against real PostGIS/Postgres, whose default text comparison is
case-sensitive.

Next: T032.

Watch: no migration generated (prohibited by the brief - four sibling stories are changing models
concurrently; a single consolidated migration lands at convergence). `makemigrations --check`
would report this change pending; the test settings' `MIGRATION_MODULES` stub means the suite
doesn't need it.

## 2026-08-20T12:15:00Z · Implementer US2 · T032

Did: Rewrote the claimed-email-removal guard in `Person.clean()` to read `self.is_claimed`
instead of `self.has_usable_password() and self.is_active` (design review RECON-001, decisions.md
D8/D21 - this was the fourth site deciding claim status from the wrong thing, alongside the three
D8 already named and fixed elsewhere).

Verified: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -k
TestClaimedPersonEmailRemoval -q -p no:randomly` → 2 passed (the ghost-with-password test that was
red since T027 is now green). `poetry run ruff check fairdm/contrib/contributors/models.py` → all
checks passed. `poetry run pytest tests/test_contrib/test_contributors -q -p no:randomly` → 265
passed - the whole US2 test scope is green.

Next: T033 (migration - prohibited, skipping), T034.

Watch: none.

## 2026-08-20T12:16:00Z · Implementer US2 · T033

Did: Nothing. The brief prohibits generating a migration this run - four sibling stories are
changing models concurrently in their own worktrees, and one migration each would fan out into
leaves Forge would have to merge by hand; a single consolidated migration lands at convergence
instead. Test settings stub `MIGRATION_MODULES`, so the suite builds tables straight from the
models and needs nothing here to stay green.

Verified: n/a - no change made.

Next: T034.

Watch: this task is recorded as skipped-by-brief-instruction in the completion report, not done.

## 2026-08-20T12:20:00Z · Implementer US2 · T034

Did: Fixed `PersonFactory` (`fairdm/factories/contributors.py`): `is_active` was
`Faker("boolean", chance_of_getting_true=80)` (issue #227) and is now a plain `True`; added a
`password` post_generation hook (mirroring `UserFactory`'s existing one) that calls
`set_unusable_password()` when nothing is supplied, since a factory-built Person previously ended
up with an empty-string password field, against which `has_usable_password()` misleadingly
returns True - the same footgun T032 exists to guard against. `is_claimed` needed no change: the
model's own field default (`False`) already made "unclaimed" the common case; no factory
declaration would have added anything.

Added two tests to `tests/test_factories/test_contributors.py`: the default instance is unclaimed
with an unusable password and `is_active=True`, and `PersonFactory(password=...)` produces a
genuinely checkable password.

Verified: `poetry run pytest tests/test_factories/test_contributors.py -q -p no:randomly` → 20
passed. `poetry run ruff check fairdm/factories/contributors.py
tests/test_factories/test_contributors.py` → all checks passed. `poetry run pytest
tests/test_contrib/test_contributors -q -p no:randomly` → 265 passed. Given how widely
`PersonFactory()` is used outside this app (force_login fixtures across the codebase), also ran
`poetry run pytest tests/test_core/test_project tests/test_core/test_dataset
tests/test_core/test_sample tests/test_core/test_measurement -q -p no:randomly` → 860 passed, 12
skipped (skips pre-exist, unrelated to this change).

Next: T036.

Watch: none.

## 2026-08-20T12:25:00Z · Implementer US2 · T036

Did: Fixed the two inaccuracies the annotation named in `docs/portal-development/contributors.md`
("Account States and is_claimed" section): the `create_unclaimed()` comment claimed
`is_active=False`, which is backwards (it is explicitly `True`, so the ghost stays reachable for a
later invitation - the whole point of T025); and the `create_user()` example claimed it
"automatically" sets `is_claimed=True`, which it does not (claiming is `services/claiming.py`'s
job, a workflow of its own, out of this story's scope per D1/D2). The page was already listed in
the "Defining models" toctree (`docs/portal-development/index.md:77`) - no toctree change needed.

Left the rest of the page untouched - the "Privacy Controls" section still documents
`privacy_settings`/`get_visible_fields`, which D9 already removed from `models.py` in an earlier,
already-merged story. That staleness is not what my task's annotation named and is not this
story's models to fix; recorded in `concerns` for whoever owns that page next.

Verified: ran both corrected code snippets directly against this branch (`Person.objects.
create_unclaimed()` then `Person.objects.create_user()`, asserting the stated defaults) via a
throwaway pytest file, not committed - both passed. `poetry run pytest
tests/test_contrib/test_contributors -q -p no:randomly` → 265 passed (doc-only change, no
production code touched).

Next: none - all thirteen tasks complete (T033 skipped by brief instruction). Full-suite verify
remains for the completion report.

Watch: see concerns in the completion report for the Privacy Controls doc staleness and the two
template/view call sites (`object_card.html`, `views/generic.py`) whose `.username` fallback
behaviour changed now that `username = None` genuinely removes the field (T029) rather than
shadowing it with a callable.

## 2026-08-20T13:03:00Z · Implementer US0 · T001/T002/T003

Did: Checked each annotation against the current code before believing it. The app package,
its migrations package, its `INSTALLED_APPS` registration and `AUTH_USER_MODEL` all already
existed and `manage.py check` was already clean with them - the annotations' "built-without-
tests" was accurate, "no default_auto_field" was not: Django's `AppConfig.default_auto_field`
already resolves from the project-wide `DEFAULT_AUTO_FIELD` setting
(`fairdm/conf/settings/database.py:26`) when an app doesn't declare its own, verified by
reverting the declaration and re-running the new test - it still passed. Added the declaration
anyway for consistency with every sibling FairDM app, which does declare it explicitly. Added
a comment to `AUTH_USER_MODEL` recording FR-008. What was genuinely missing in all three cases
was the test.

Verified: `poetry run pytest -q -p no:randomly tests/test_contrib/test_contributors/test_apps.py
tests/test_conf/test_settings/test_apps.py tests/test_conf/test_settings/test_auth.py` → 16
passed.

Next: T005.

Watch: none.

## 2026-08-20T13:10:00Z · Implementer US0 · T005

Did: The substance T005 asks for - "credit tests have real concepts to attach" - was already
true suite-wide before this task: `tests/conftest.py:33`'s session-scoped `Concept.preload()`
seeds the `fairdm-roles` vocabulary once for the whole run, and several existing tests
(`TestContributionRoles`, `TestMultipleRolesPerContribution`) already rely on it directly.
Added the `contribution_roles` fixture anyway, per the task's literal text and because it is
genuinely additive (a convenience wrapper naming the query, not a competing mechanism) - I did
not retrofit it onto the existing tests that predate it, since editing tests I did not author
is prohibited. Added one new test proving the fixture holds more than one concept and that a
role drawn from it round-trips through `full_clean()`.

Verified: `poetry run pytest -q -p no:randomly
tests/test_contrib/test_contributors/test_models.py::TestContributionRoles` → 3 passed.

Next: T006.

Watch: none.

## 2026-08-20T13:15:00Z · Implementer US0 · T006

Did: `fairdm/factories/__init__.py` already exports every contributor factory and lists them in
`__all__` - only the module docstring named by the task was actually missing. Added one matching
`fairdm/factories/core.py`'s layout: purpose, the six factories the module provides, and the
"defaults satisfy full_clean()" convention T138 then verifies.

Verified: `poetry run ruff check fairdm/factories/contributors.py` → all checks passed. Smoke-
imported the module and every re-export directly (not committed).

Next: T138.

Watch: none.

## 2026-08-20T13:25:00Z · Implementer US0 · T138

Did: Added `TestContributorFactoriesPassFullClean` (one test per factory - `UserFactory`,
`ContributorFactory`, `PersonFactory`, `OrganizationFactory`, `AffiliationFactory`,
`ContributionFactory` - all six in `fairdm/factories/contributors.py`) and
`TestContributorFactoryBatchUniqueness` (`UserFactory`/`PersonFactory`, the only two factories
whose model carries a database-level uniqueness constraint - `Person.email`) to
`tests/test_factories/test_contributors.py`. All eight passed on the first run; the annotation's
"never calls full_clean; three factories untouched" held exactly - grepped the file first and
confirmed zero existing `full_clean()` calls anywhere in it.

Verified: `poetry run pytest -q -p no:randomly tests/test_factories/test_contributors.py` → 30
passed (22 pre-existing + 8 new).

Next: T140.

Watch: none.

## 2026-08-20T13:30:00Z · Implementer US0 · T140

Did: Ran both commands the task names. `manage.py check` is clean (1 silenced, unrelated to
this app). `makemigrations --check --dry-run` scoped to `contributors` is clean (exit 0, "No
changes detected"). Run unscoped across every app it is **not** clean (exit 1): `identity` and
the third-party `orbit` package both show drift. Neither is caused by this feature or touched by
any of its nine landed stories - `fairdm/contrib/identity` was last touched at `a1a39f4`, long
before `009-fairdm-contributors` existed, and `orbit`'s migration lives inside the installed
package's own site-packages directory, outside this repository's version control entirely.
Reproduced on the branch point commit before any of this story's own commits, to confirm it
predates this story. No code changed; nothing to fix within this story's scope. Recorded as a
concern for the completion report rather than a task deviation, since T140's own annotation
("They currently are [clean]") is the thing that turned out stale, not the code.

Verified: `poetry run python manage.py check` → clean. `poetry run python manage.py
makemigrations --check --dry-run contributors` → exit 0. `poetry run python manage.py
makemigrations --check --dry-run` (unscoped) → exit 1, `identity` and `orbit` only.

Next: T141.

Watch: the identity/orbit migration drift, for whichever lane owns those apps.

## 2026-08-20T13:40:00Z · Implementer US0 · T141

Did: `CHANGELOG.md` had no Feature 009 entry at all - confirmed by grep, not just by the task
annotation. Added one, in the file's own established format (bold names, prose bullets, one
`#### <Feature> (Feature NNN)` block per section): Added names every model, field and public
method this app introduces; Changed and Removed name the behaviour changes and the two removed
surfaces (`privacy_settings`/`get_visible_fields`, `weight`/`calculate_weight`) against the
actual current code, not the original spec's aspirations - grepped the whole app for both pairs
of names first and confirmed zero production references remain.

Verified: read the new entry back against `models.py`, `managers.py`, `choices.py` and
`permissions.py` line by line for accuracy. No test scope applies to a changelog.

Next: T142.

Watch: none.

## 2026-08-20T13:55:00Z · Implementer US0 · T142

Did: Opened every page under `docs/` that mentions a contributor concept
(`grep -rl -i "contributor\|Person\b\|Organization\b\|Affiliation\b\|Contribution\b" docs`) and
checked each against the current models, managers, choices, permissions and transforms modules.
`docs/data_models/contributors.md`, `docs/overview/contributors.md` and
`docs/portal-administration/managing-unclaimed-profiles.md` were already true - the first two
were written accurately already, and the third's `is_claimed` explanation and exact failure-
reason strings were verified word for word against `services/claiming.py`.

The two pages the brief named as most likely wrong were: both still documented
`privacy_settings`/`get_visible_fields` (removed by an earlier, already-merged story per D9;
`US2 T036`'s progress entry above explicitly left this section for "whoever owns that page
next"). Beyond that specific defect, found and fixed, in `docs/portal-development/
contributors.md`: `person.orcid` called as a property when it is a method;
`get_full_name_display`'s format list named a format (`family_given_comma`) that does not
exist; the Organization Ownership section described a lifecycle hook syncing
`manage_organization` and pointed at a views import, when the permission is derived
(`permissions.py`, D13) and the real entry point is `Organization.transfer_ownership()`; the
TransformRegistry section documented a `to_internal`/`to_external` classmethod interface that
was never built (D11) instead of the real `export()`/`import_data()` instance contract; a role-
lookup example passed a vocabulary class where the ORM expects `vocabulary__name=` and `label=`
where the field is `name=`; a stale line reference. In `docs/portal-administration/
managing_contributors.md`: the "Creating Claimed User Accounts" workflow claimed the admin's
Add-person form both leaves email blank and auto-sets `is_claimed=True` - verified against
`admin.py`'s `add_fieldsets` and `AdminUserCreationForm` that neither is true, and rewrote the
whole subsection; the Affiliation Verification Workflow's "lifecycle hooks sync permissions"
directly contradicted the correct "Ownership is derived, not stored" section later in the same
file; the Manual Sync section used the same never-built transform API; the Bulk Privacy
Settings Update section used the removed field entirely (removed the section); the Database
Indexing list claimed `Person.is_active` and `Affiliation.end_date` carry an index - neither
does, verified against Django's `AbstractUser` source and the field declarations; the Security
Considerations section repeated the same removed-privacy claims.

Verified: `poetry run sphinx-build -b html docs <out>` before and after these edits - zero
warnings against either file in both runs. The build's own exit code (2) is an unrelated,
pre-existing `pydata-sphinx-theme` `TemplateNotFound` error on `index.html`; reproduced
identically with these two files stashed back to their pre-story state, and `docs/conf.py` was
last touched at `cb3df2f`, long before this feature - not in this story's scope to fix.

Next: full-suite verify for the completion report.

Watch: the pre-existing `identity`/`orbit` migration drift (T140) and the pre-existing Sphinx
theme build failure (T142) are both environment/tooling issues outside every one of this
feature's ten stories, not just this one.
