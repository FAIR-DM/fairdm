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
