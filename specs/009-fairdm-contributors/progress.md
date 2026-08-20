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
