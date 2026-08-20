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
