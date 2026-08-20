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

Watch: none.
