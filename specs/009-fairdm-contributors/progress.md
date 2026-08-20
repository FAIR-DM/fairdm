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

Watch: none.
