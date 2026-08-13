# Progress — 001 portal configuration

Append-only. One entry per stage transition or gate outcome.

---

**2026-08-13 — A1 ASSESS.** Read the January specification against the code. 13 functional
requirements: 10 verified with implementing code and a covering test, 1 drifted (FR-012), 1 absent
(FR-009), 1 untested (FR-002). Three baseline faults found outside the specification's scope, all
security-relevant: a published fallback secret key, a silent SQLite fallback and a silent
local-memory cache fallback, each of which lets a production portal start misconfigured.

**2026-08-13 — A2 GRILL.** Retrospective grilling with Sam. Scope narrowed to the `fairdm.setup()`
contract. Twelve adjudications recorded in `decisions.md`, four of which change scope: staging
removed, checks returned to this feature but production-only, container deployment moved to R26,
addon contract moved to R27. Two additions accepted: portal apps take template precedence, and the
resolved configuration becomes interrogable.

**2026-08-13 — S1 SPECIFY.** `spec.md` rewritten in place at the same number and slug. Six stories,
24 functional requirements, 7 success criteria, citing G7 and R1. The previous version's four
adoption-rate and incident-rate success criteria dropped as unobservable from this repository.
`stage-exit S1` green.

**2026-08-13 — S2 SETUP.** Epic #80 reopened and promoted rather than duplicated; it had been closed
COMPLETED on 2026-08-11 against a specification this audit found only partly built. Story sub-issues
#130, #131, #132, #135, #133, #134 created and linked. Draft PR #136 opened as `app/fairdm-bot`.
`stage-exit S2` green. GitHub returned intermittent 502s and GraphQL errors throughout; every write
was verified by a follow-up query rather than trusted from its response.

**2026-08-13 — GATE_SPEC: APPROVED.** Sam approved the specification gate in session, after the
decision brief was posted to epic #80. Three risks were stated and accepted at approval: removing
the fallback secret key and site domain is a breaking change for a portal relying on them, removing
the `**overrides` keyword argument breaks any portal passing settings that way, and reordering
`INSTALLED_APPS` may begin serving a portal template that was previously inert.

**2026-08-13 — S3 PLAN.** `research.md` resolves nine unknowns, the load-bearing one being that the
check framework does not exist at the moment `setup()` returns, so the production-critical subset
executes from `FairDMConfig.ready()` instead. `plan.md` sets out three phases over the six stories.
`tasks.md` written greenfield, without reference to the implementation, ahead of reconciliation.

**2026-08-13 — A3 RECONCILE.** Each of the 105 greenfield tasks checked against the current
codebase, blind to the task list until this pass. 12 satisfied outright with existing code and a
passing test (all in US-1 and US-3, mostly the checks framework). Of the remaining 93: 56 never
built, 15 built differently from the task's description, 15 partially covered, 7 implemented with
no covering test. `feature-state.json` generated from this pass — the 12 satisfied tasks marked
`done` with their evidence, the rest `todo`. Confirms A1's assessment: the checks framework exists
and passes, but the layering contract itself (environment resolution, portal overrides, the
security-critical env defaults) is still the January design, not this spec's.

**2026-08-13 — S3R DESIGN REVIEW.** One reviewer, four lenses, the fourth challenging every task the
reconciliation had ticked. The counts above are superseded: the task list settled at **104**, and
the reviewer reopened three of the twelve, leaving **9 proven done and 95 open**. Two of the three
were genuinely over-ticked — the cache check is a two-item deny list rather than a test that a
shared cache is configured, and check registration sits inside the method the environment guard is
about to wrap, so it cannot be treated as already satisfying its task.

One blocking finding, and it was in the plan rather than the code: removing the fallback secret key
by letting the read raise would kill development startup and the whole test suite, because the
baseline is layer 1 and the development override is layer 2. The variables take an unusable sentinel
instead, and the production-critical checks stay the only thing that refuses a boot. Four further
remedies applied to `plan.md`, `research.md` and `tasks.md`: the production-critical subset needs its
own tag or a missing Celery worker blocks a boot, the interrogation command moves to the directory
Django actually scans, the provenance record holds setting names rather than values, and one task
said "confirm" where it meant "delete".

**2026-08-13 — reconciliation evidence verified.** The nine closed tasks were re-checked rather than
accepted: all seven cited tests were run and pass, and a `file.py:line` citation was added to each,
which the ledger schema had no field for. `evidence.code` added to
`kit/schemas/feature-state.schema.json` — optional elsewhere, but the audit lane closes a task on
code *and* test, and a rule with nowhere to record its evidence is not enforceable.

**2026-08-13 — US-2 IMPLEMENTED (`c2de13b`..`5d04ca4`).** `setup()` composes five declared layers,
`DJANGO_ENV` is read literally with no allowlist, both override layers are selected by file
existence, `staging.py` is deleted and the `**overrides` kwarg is gone. Verified independently:
1325 tests pass, and three mutations red the suite — restoring the allowlist (3 tests), disabling
the portal-override layer (4), swapping the two override layers (1).

One regression the implementer missed: wiring `config/production.py` in as a real portal override
broke startup, because it narrows `LANGUAGES` while the baseline hardcodes `PARLER_LANGUAGES` with
a language it removes, and django-parler validates one against the other at import. Nothing caught
it because every test imports `tests/settings.py` — the bundled example portal was untested. T106
now boots it under both environments, and T107 holds the underlying coupling as work for US-5.

**2026-08-13 — US-3 IMPLEMENTED (`65262af`..`2673b0a`).** The seventeen assigned tasks closed:
`FairDMConfig.ready()` refuses a production boot naming every production-critical failure at once,
the guard silences everything outside production, check registration moved to module import so
`check --deploy` is unaffected by it, the cache check became an allowlist, the secret-key check
rejects a published or short key, a malformed database URL fails distinctly from an absent one, and
`validate_services()` is gone with its 39 test references.

Three defects found at convergence rather than accepted from the report:

1. **The suite was passing on a leak.** `TestBundledPortalBoots[production]` was green only because
   an addon test cleared and repopulated `os.environ` without restoring it, leaking a working
   `DATABASE_URL` and `REDIS_URL` into every later test in the process. Run alone it failed on E101
   and E200 — correctly, since it supplied neither. Both tests now own their environment, and the
   bundled-portal test builds its subprocess environment from a sanitised copy rather than
   inheriting whatever the shell or an earlier test left behind. Mutation-checked: breaking
   `config/production.py` still reds it.
2. **The mypy hook failure was not pre-existing.** The report recorded it as an environment issue
   because it reproduced on untouched files. It was caused by this story: django-stubs imports
   `tests/settings.py` with no `DJANGO_ENV` set, that resolves to production, and production now
   refuses to boot on a development-shaped configuration. pytest hid it by supplying the value
   through pytest-env. The module now declares its own environment and a test boots it with
   `DJANGO_ENV` unset.
3. **Coverage deleted with `validate_services()` was not replaced.** Its tests required a secret key
   of 50+ characters; the new check tested only absence and the insecure prefix, so a three-character
   key would have passed a production boot. Django reports the same condition as `security.W009`, a
   warning, which cannot block. Restored at error severity. The cache check's hint also named
   `CACHE_URL`, a variable nothing reads — the settings module reads `REDIS_URL`.

Verified at convergence: 1326 tests pass, pre-commit clean including mypy, four mutations red the
suite.

**2026-08-13 — US-1 IMPLEMENTED (`4a4bcf1`..`69cde46`, squashed to `02695c9`).** The thirty-two
assigned tasks closed. Every module under `fairdm/conf/settings/` states what it owns and what it
leaves to the portal, and none of them branch on the resolved environment: `database.py` always
composes a PostgreSQL URL, `cache.py` always composes a Redis-shaped `CACHES`, and `security.py`
applies its HTTPS, cookie and HSTS headers unconditionally. `DJANGO_SECRET_KEY`,
`DJANGO_SITE_DOMAIN` and `DJANGO_SUPERUSER_PASSWORD` lose their working fallbacks — the secret-key
default was a value published in this package's own source. `ALLOWED_HOSTS` composes from truthy
entries only, which makes `fairdm.E003` reachable for the first time. Portal apps register ahead of
FairDM's own and the third-party set, and `SPECTACULAR_SETTINGS` moves out of the entry point into
`settings/api.py`.

The Implementer's session died on an API error at the final verification step, after committing all
thirty-two tasks. Both craft-skill receipts were read out of its transcript rather than a report it
never sent: `craft-tdd/2026-08-05/eae3b6c7` and `craft-increments/2026-08-05/d3dce07f`, both
matching the registry.

Verified at convergence, none of it accepted from a report: 1391 tests pass (up from 1326), 70
skipped, pre-commit clean across all 32 touched files including mypy, and five mutations red the
right tests —

1. restoring the published fallback secret key and the `localhost:8000` site domain reds 6;
2. reverting `ALLOWED_HOSTS` to `[domain] + hosts` reds 2, including the E003 reachability test;
3. moving portal apps back to the end of `INSTALLED_APPS` reds 3, one of which asserts that a portal
   template at the same path as FairDM's is the one actually served;
4. dropping the placeholder-`LOCATION` condition from `check_cache_backend` reds 1;
5. turning off `SESSION_COOKIE_SECURE` in the baseline reds 2.

`tamper-check` flagged four pre-existing test files. Three are purely additive (`test_checks.py`,
`test_conf/conftest.py`, `test_setup.py`). The fourth changes one assertion: `test_apps.py`'s
production-boot test expected `fairdm.E101` (the SQLite fallback), and the baseline no longer has
one, so an unconfigured database now fails as `fairdm.E102` (malformed) instead. E101 keeps its own
unit test for a portal that configures SQLite explicitly. Adjudicated as a consequence of FR-003,
not a weakened test.

**Bookkeeping defect found and fixed in the same pass.** The US-3 convergence updated `tasks.md`
and `progress.md` but never `feature-state.json`, which still had US-3 at `in_progress` with 17
tasks open — two sources of truth disagreeing, with the machine-readable one wrong. Closed here
with the same derived evidence, so the ledger and the task list now agree at 83 of 107.

**2026-08-13 — US-4 IMPLEMENTED (`1bdb73e`..`3ac5e06`).** The provenance record and `show_config`.
Written up in full in `decisions.md` D15 and D16 and in `tasks.md`; this entry was missed at the
time and is added here with the US-5 pass, alongside the same omission it repeats.

**2026-08-14 — US-5 IMPLEMENTED (`e0623d7`..`0ec4fb6`).** T091, T092 and T093 needed no production
code — the layering they assert had already landed in US-1 and US-2, and both A3 citations against
`setup.py` were stale. What they add is tests that can actually fail: the pre-existing override
tests named two settings no baseline module sets, so they would have passed against a `setup()`
that skipped the baseline entirely. The new ones resolve each baseline module's own value first and
assert the portal's differs from it. T107 gave the `LANGUAGES` / `PARLER_LANGUAGES` coupling the
named error FR-012 implies, reproduced red first.

Verified at convergence, none of it accepted from the report: 1415 tests pass (up from 1401), 70
skipped, `forge verify` green end to end, and four mutations red the right tests —

1. removing the `setup()` call site reds the portal-parler-app test;
2. removing the `import_models()` call site reds the post-`setup()`-assignment test;
3. restoring the whole-`Tags.translation` run reds the translation.E004 test;
4. dropping the `PARLER_LANGUAGES["default"]["code"]` branch reds its unit test.

**Two gaps in T107 as delivered, found at convergence and closed as T110.** Both are in D17. The
check ran Django's entire `translation` tag rather than its own, which turned `translation.E004`
into a refusal to boot in every environment; and its single call site in `import_models()` is too
late for a portal whose own apps import `parler.models`, because US-1 moved portal apps ahead of
FairDM's. The second one is the more instructive: the implementer's code comment asserted `fairdm`
precedes "every other parler-model app", which was true of FairDM's own apps and false of a
portal's, three stories after this feature itself changed that ordering.

**One test fixture corrected rather than its assertion.** `test_base_subtag_match_is_accepted_like_django_parler_accepts_it`
configured `LANGUAGES = [("fr", …)]` while leaving `PARLER_DEFAULT_LANGUAGE_CODE = "en"` — a state
parler itself rejects, confirmed by calling `add_default_language_settings` directly. The fixture
was made consistent; the assertion it makes is unchanged.

**`forge verify` was red before this pass, and neither of the two convergences that made it red
said so.** `tests/test_conf/test_conf_init.py` (added in US-3) and `tests/test_management/test_show_config.py`
(added in US-4) both failed the conformance gate's mirror rule. Fixed here: the first folded into
`test_setup.py` as another `Test*` class, since `setup()` is its subject; the second moved to
`tests/test_management/test_commands/`, mirroring `fairdm/management/commands/show_config.py`.
US-3 and US-4 were reported verified on `pytest` and `pre-commit` alone, which do not include it.

## US-6 — an addon contributes settings at a defined point (2026-08-14)

Implemented in `fairdm-us6`, converged onto the feature branch at `4688cb5`. T094–T102 closed, plus
T111–T113 added and closed at convergence. 110 of 112 tasks now closed; the two open are T105
(README and CHANGELOG) and T108 (the surviving January spec artefacts), both held by the orchestrator.

**Four of the nine tasks needed no production code**, and the reconciliation notes saying otherwise
were stale rather than wrong at the time: A3 recorded that no portal environment override layer
existed and that the production failure path was unimplemented, both of which US-2 and US-4 have since
built. Closed on a reading of the current code plus tests that prove the position rather than assume
it — the fixture addon sets a value FairDM's own `development.py` also sets, so the test fails if the
order changes.

**One defect found at convergence, and it is the one the isolation was for.** The scratch scope an
addon executes against copied every mutable container in the caller's scope and merged all of them
back on success — lowercase names and `__builtins__` included. A portal sharing a list or dict with
one of its own modules would have found its post-`setup()` mutations landing on a copy. Fixed by
confining the copy to uppercase names (T111). Full reasoning in D18.

**One claim in the implementer's report was true but untested.** It argued a deep copy over a shallow
one because an addon's in-place `+=` would otherwise reach the real scope even when discarded. That is
correct, and no test in the delivered set could tell the two apart, because the fixture addon rebinds a
name rather than mutating a container. T113 adds one that does; a shallow scratch scope reds it.

**A second vacuous skipped test was still in the file.** The brief permitted replacing one, and the
implementer replaced it. `test_addon_without_setup_module_logs_warning` had the same shape — skipped
for a path-escaping problem, body beginning with a bare `pass` before dead code — and covers this
story's own subject. Restored as T112. D19.

**Verification run independently of the implementer's report:** `poetry run pytest` — 1423 passed,
68 skipped; `poetry run pre-commit run --files <5 touched files>` — every hook green including mypy
and deptry; `forge verify --base 446f493` — conformance, lint, typecheck, test and build all green.
Six mutations red the tests that should catch them: restoring the unguarded
`include(*paths, scope=caller_globals)` reds both partial-failure tests, reverting the non-production
log to DEBUG reds T099's, removing the production raise reds the production partial-failure test,
moving the addon layer ahead of FairDM's override reds two, moving it after the portal's reds one,
and making the scratch scope a shallow copy reds T113's.

`forge tamper-check` flagged `tests/test_conf/test_addons.py`; adjudicated in D19 — three
pre-existing tests changed, all three strengthened.
