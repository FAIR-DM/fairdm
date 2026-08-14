# Tasks — 001 portal configuration

Generated from `spec.md`, `plan.md` and `research.md` **as though the repository were empty**
(plan.md, "Task generation"). Numbering is sequential across the whole file; `[P]` marks a task
that can run in parallel with its siblings; `[US-k]` names the user story a task serves.

## Phase 0: Foundational

Package skeletons and shared test scaffolding that every story's tests import.

- [x] T001 [P] [US-1] Create `fairdm/conf/__init__.py` as an empty package pending the public `setup()` re-export (FR-001)  
  **Done (A3):** `fairdm/conf/__init__.py:8` · `tests/test_conf/test_addons.py::TestAddonDiscovery::test_addon_with_setup_module_is_loaded` — Package exists and re-exports setup(); the cited test imports fairdm and calls setup().
- [x] T002 [P] [US-1] Create `fairdm/conf/settings/__init__.py` as an empty package for the baseline concern modules (FR-002)  
  **Done (A3):** `fairdm/conf/settings/__init__.py:1` · `tests/test_conf/test_addons.py::TestAddonDiscovery::test_addon_with_setup_module_is_loaded` — Empty package holding eleven concern modules; the cited test resolves a full settings scope through them.
- [x] T003 [P] [US-1] Create `tests/test_conf/__init__.py` mirroring `fairdm/conf/` (Article X)  
  **Done (A3):** `tests/test_conf/__init__.py:1` · `tests/test_conf/test_addons.py::TestAddonDiscovery::test_addon_with_setup_module_is_loaded` — Package exists and the 60 passing tests are collected from inside it.
- [x] T004 [P] [US-1] Create `tests/test_conf/test_settings/__init__.py` mirroring `fairdm/conf/settings/` (Article X)  
  **Open (A3, never_built):** tests/test_conf/test_settings/ does not exist.
- [x] T005 [US-1] Write `tests/test_conf/conftest.py`: an env-var isolation fixture (saves/restores `DJANGO_ENV` and related variables per test), a fixture that builds a throwaway portal settings module on `tmp_path` with a real `__file__`, and a scope-snapshot helper reused by the provenance tests in Phase 2 (Article X)  
  **Open (A3, partial):** `tests/test_conf/conftest.py:14` — conftest holds only production_env; no tmp_path portal-settings fixture, no scope-snapshot helper, and the env fixtures that exist are duplicated inside individual test modules.
- [x] T006 [US-1] Write `tests/test_conf/test_environment.py::TestEnv` asserting the shared `Env` declares `DJANGO_SECRET_KEY`, `DJANGO_SITE_DOMAIN`, the database, cache and admin-credential variables with no *working* default — each resolves to an explicitly unusable sentinel when the variable is unset, and the read itself never raises (FR-004, FR-006, research R6)  
  **Open (A3, never_built):** tests/test_conf/test_environment.py does not exist.
- [x] T007 [US-1] Implement `fairdm/conf/environment.py`: the shared `django-environ` `Env()` declaration for every deployment-varying value, every security-critical variable declared with an unusable sentinel default rather than a working one (FR-004, FR-006, research R6)  
  **Open (A3, built_differently):** `fairdm/conf/environment.py:3` — The shared Env supplies working defaults for the security-critical values FR-004 forbids: DJANGO_SECRET_KEY (:15), DJANGO_SITE_DOMAIN (:19), DJANGO_SUPERUSER_PASSWORD (:10), DJANGO_ALLOWED_HOSTS=[] (:11).

## Phase 1: US-2 — vary configuration by environment through layered overrides (P1)

Establishes the layering mechanism the rest of the feature composes over (plan.md: US-2 before US-1).

- [x] T008 [US-2] Write `tests/test_conf/test_setup.py::TestResolvedEnvironment` asserting `DJANGO_ENV` unset resolves to `production` (FR-007)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T009 [US-2] Implement environment resolution in `fairdm/conf/setup.py`: read `DJANGO_ENV`, default to `production` (FR-007)  
  **Open (A3, no_test):** `fairdm/conf/setup.py:57` — Default-to-production is implemented, but every test sets DJANGO_ENV explicitly, so the unset path is never exercised.
- [x] T010 [US-2] Extend `TestResolvedEnvironment` with cases for `DJANGO_ENV` set to an empty string and to a name differing only in case from a shipped one, asserting each is looked up literally with no normalisation (edge case, FR-007, FR-010)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T011 [US-2] Implement literal, non-normalising environment-name handling in `setup.py` (edge case, FR-007)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:58` — DJANGO_ENV is validated against a fixed allowlist (production, staging, development); anything else is warned about and rewritten to production, so the name is normalised and staging is first-class.
- [x] T012 [US-2] Write `tests/test_conf/test_setup.py::TestLayerOrder` asserting the five layers apply in FR-008's order: baseline, FairDM's environment override, addon settings, the portal's environment override, then post-call assignment (FR-008)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T013 [US-2] Implement layer composition in `setup.py` using `django-split-settings` `include()` calls in FR-008's order (FR-008)  
  **Open (A3, partial):** `fairdm/conf/setup.py:132` — Four layers compose (baseline :132, FairDM env override :145, addons :151, post-call assignment); the portal env override layer is absent and an extra **overrides layer (:156) that FR-012 forbids is applied.
- [x] T014 [US-2] Extend `TestLayerOrder` with a case asserting an override module is selected by existence, not from a fixed allowlist of permitted environment names (FR-010)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T015 [US-2] Implement the existence probe for `fairdm/conf/<environment>.py`, replacing any fixed profile list (FR-010)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:135` — Selection is a hard-coded dict {development, staging}; the .exists() call at :143 is a secondary guard on an already-allowlisted name, not an existence probe.
- [x] T016 [US-2] Extend `TestLayerOrder` with a case asserting an environment for which neither FairDM nor the portal ships a module resolves to the baseline unchanged and raises nothing (FR-010, scenario 3)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T017 [US-2] Implement the skip-without-error path when a layer's module does not exist (FR-010)  
  **Open (A3, partial):** `fairdm/conf/setup.py:143` — The exists guard protects only the two allowlisted FairDM modules; an unknown environment never reaches it because :58 has already coerced the name.
- [x] T018 [US-2] Write `tests/test_conf/test_setup.py::TestShippedOverrides` asserting FairDM ships exactly one override module, `development`, and none for any other environment name (FR-009)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T019 [US-2] Create `fairdm/conf/development.py` as FairDM's sole shipped override module, empty pending the baseline-audit values added in T057 (FR-009)  
  **Open (A3, built_differently):** `fairdm/conf/development.py:1` — development.py exists but is not the sole shipped override: fairdm/conf/staging.py is still shipped and wired in at setup.py:137.
- [x] T020 [US-2] Write `tests/test_conf/test_setup.py::TestProductionVsDevelopmentDiff` asserting settings resolved for production and for development differ only in the keys `development.py` names, by diffing the two resolutions (SC-002)  
  **Open (A3, never_built):** SC-002 unverified.
- [x] T021 [US-2] Write `tests/test_conf/test_setup.py::TestPortalOverride` asserting the portal's override module is resolved beside its settings module regardless of directory name, using the `tmp_path` settings-module fixture (FR-011, scenario 5)  
  **Open (A3, never_built):** No portal override mechanism exists to test.
- [x] T022 [US-2] Implement capture of the caller's settings-module directory in `setup.py`, taken before `__file__` is overwritten for `split_settings`'s relative-include resolution, and derive the portal override path from it (FR-011)  
  **Open (A3, partial):** `fairdm/conf/setup.py:68` — caller_globals is captured before __file__ is overwritten, but only base_dir (.parent.parent) is derived and it is used solely to locate stack.env files; the settings-module directory is not retained.
- [x] T023 [US-2] Extend `TestPortalOverride` with a case where the portal's settings module has no usable `__file__` — the portal-override lookup is skipped with a warning, not an exception (edge case, FR-011)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T024 [US-2] Implement the no-`__file__` fallback: skip the portal-override lookup and emit a warning (edge case, FR-011)  
  **Open (A3, never_built):** With no base_dir argument, a missing __file__ raises KeyError at setup.py:72 rather than warning.
- [x] T025 [US-2] Extend `TestLayerOrder` with a case where FairDM and the portal both ship a module for the same resolved environment, asserting both apply in the declared order (edge case, FR-008, FR-010)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T026 [US-2] Write `tests/test_conf/test_setup.py::TestEntryPointSignature` asserting `setup()` accepts no settings keyword arguments and raises `TypeError` if any are passed (FR-012)  
  **Open (A3, never_built):** The existing TestSetupOverrides asserts the opposite — that keyword overrides are accepted.
- [x] T027 [US-2] Implement `setup()`'s public signature in `fairdm/conf/setup.py`, re-exported from `fairdm/conf/__init__.py`, with no `**overrides`-style parameter (FR-001, FR-012)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:21` — setup() is re-exported but still carries **overrides (:26), applied at :156; five tests in TestSetupOverrides assert this forbidden behaviour and must be rewritten.
- [x] T028 [US-2] Write `tests/test_conf/test_setup.py::TestEnvFiles` asserting env files are read in order — `stack.env`, then `stack.<environment>.env`, then an explicit `env_file=` argument with `overwrite=True` — and that the first two respect variables already set in the process environment (FR-006)  
  **Open (A3, partial):** `tests/test_conf/test_setup.py::TestEnvFileParameter::test_custom_env_file_is_loaded` — Covers only the explicit env_file leg; stack.env ordering and process-env precedence are unasserted, and test_env_file_takes_precedence is skipped.
- [x] T029 [US-2] Implement env-file loading in `setup.py` in that order and with that precedence (FR-006)  
  **Open (A3, partial):** `fairdm/conf/setup.py:78` — Order and overwrite flag are implemented (:80-101) but the stack.env and stack.<env>.env legs have no test.
- [x] T030 [P] [US-2] Document the env-file precedence and the five-layer order in `setup.py`'s module docstring (FR-006)  
  **Open (A3, never_built):** `fairdm/conf/setup.py:1` — The module docstring documents neither the env-file precedence nor the layer order.

## Phase 1: US-1 — obtain a complete settings baseline from one call (P1)

One task pair per named concern (US-1's acceptance scenario names: database, cache, background
tasks, static/media, authentication, email, logging, security headers, REST API), plus the app
ordering and the baseline-wide audits.

- [x] T031 [P] [US-1] Write `tests/test_conf/test_settings/test_database.py::TestDatabase` asserting the baseline configures a production-grade database from the environment with no environment branching (FR-002, FR-003)  
  **Open (A3, never_built):** Such a test would fail today: settings/database.py:45 branches to SQLite.
- [x] T032 [P] [US-1] Implement `fairdm/conf/settings/database.py`, with a docstring stating what it owns and what it leaves to a portal (FR-002, FR-003)  
  **Open (A3, built_differently):** `fairdm/conf/settings/database.py:26` — Branches three ways on env-var presence (DATABASE_URL, POSTGRES_*, SQLite fallback at :45-54), so the baseline is not unconditionally production-grade.
- [x] T033 [P] [US-1] Write `tests/test_conf/test_settings/test_cache.py::TestCache` asserting the baseline configures a shared cache from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T034 [P] [US-1] Implement `fairdm/conf/settings/cache.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, built_differently):** `fairdm/conf/settings/cache.py:22` — Redis only when DJANGO_CACHE and REDIS_URL are both set; falls back to LocMem (:52) then Dummy (:71).
- [x] T035 [P] [US-1] Write `tests/test_conf/test_settings/test_celery.py::TestCelery` asserting the baseline configures background-task (Celery) settings from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T036 [P] [US-1] Implement `fairdm/conf/settings/celery.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/celery.py:58` — Implemented with an ownership docstring and no environment branching; untested.
- [x] T037 [P] [US-1] Write `tests/test_conf/test_settings/test_static_media.py::TestStaticMedia` asserting the baseline configures static and media handling from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T038 [P] [US-1] Implement `fairdm/conf/settings/static_media.py` with an ownership docstring — the module `setup.py` already includes under that name (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/static_media.py:71` — Implemented as static_media.py rather than storage.py (name difference only); switches to S3 when the S3_* vars are set.
- [x] T039 [P] [US-1] Write `tests/test_conf/test_settings/test_auth.py::TestAuth` asserting the baseline configures authentication (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T040 [P] [US-1] Implement `fairdm/conf/settings/auth.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/auth.py:29` — Argon2, validators, allauth and guardian backends configured; untested.
- [x] T041 [P] [US-1] Write `tests/test_conf/test_settings/test_email.py::TestEmail` asserting the baseline configures email from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T042 [P] [US-1] Implement `fairdm/conf/settings/email.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/email.py:37` — Reads EMAIL_* from the shared env; untested.
- [x] T043 [P] [US-1] Write `tests/test_conf/test_settings/test_logging.py::TestLogging` asserting the baseline configures logging using the shared `Env`, with no environment branching (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T044 [P] [US-1] Implement `fairdm/conf/settings/logging.py` using the shared `Env` declaration, with an ownership docstring (FR-002, FR-003)  
  **Open (A3, built_differently):** `fairdm/conf/settings/logging.py:20` — Builds its own environ.Env('localenv') for SENTRY_* rather than using the shared Env, and gates Sentry on `if SENTRY_DSN and not DEBUG` (:30).
- [x] T045 [P] [US-1] Write `tests/test_conf/test_settings/test_security.py::TestSecurity` asserting the baseline sets production-grade security headers (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T046 [P] [US-1] Implement `fairdm/conf/settings/security.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/security.py:40` — SSL redirect, secure cookies, HSTS and nosniff sit behind `if env('DJANGO_SECURE')` (:49), so one flag strips the production headers.
- [x] T047 [P] [US-1] Write `tests/test_conf/test_settings/test_api.py::TestApi` asserting the baseline configures the REST API, including the API-schema finalisation, entirely within this module rather than in the entry point (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T048 [P] [US-1] Implement `fairdm/conf/settings/api.py`, including the API-schema finalisation moved out of `setup.py`, with an ownership docstring (FR-002, FR-003)  
  **Open (A3, partial):** `fairdm/conf/settings/api.py:17` — api.py is a re-export shim over fairdm.api.settings; the API-schema finalisation is still performed in setup.py:162-170.
- [x] T049 [US-1] Write `tests/test_conf/test_settings/test_apps.py::TestInstalledApps` asserting portal apps are composed ahead of FairDM's own apps and the third-party set, while staying behind the Django contrib apps that must load first (FR-005)  
  **Open (A3, never_built):** The only INSTALLED_APPS assertions in the suite are membership checks, never ordering.
- [x] T050 [US-1] Implement `fairdm/conf/settings/apps.py`: an explicit, commented `INSTALLED_APPS` composition in that order, accepting the portal's `apps=[...]` (FR-005)  
  **Open (A3, built_differently):** `fairdm/conf/settings/apps.py:122` — Portal apps are spliced LAST, after every FairDM and third-party app, so portal templates and static files lose — the inverse of FR-005.
- [x] T051 [US-1] Extend `test_apps.py` with `TestTemplateAndStaticPrecedence` asserting that when a portal and FairDM both define a template or static file at the same path, the portal's earlier app position makes its file win (FR-005, scenario 3)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T052 [US-1] Write `tests/test_conf/test_setup.py::TestBaselineCompleteness` asserting a settings module whose entire content is `fairdm.setup()` produces a configuration where every FairDM-owned setting is present and `manage.py check` raises nothing (FR-001, SC-001)  
  **Open (A3, never_built):** SC-001 unverified.
- [x] T053 [US-1] Write `tests/test_conf/test_setup.py::TestBaselineModuleAudit`, a static audit over every module in `fairdm/conf/settings/` — all eleven, `settings/addons.py` included — asserting none contains a conditional on the resolved environment and each carries a module docstring naming what it owns and what it leaves to a portal (FR-002, FR-003, US-1 scenario 2)  
  **Open (A3, never_built):** No module branches on DJANGO_ENV by name, but several branch on environment-derived state (logging.py:30, security.py:49, database.py:26, cache.py:22).
- [x] T054 [US-1] Write `tests/test_conf/test_environment.py::TestNoSecurityDefaults` asserting that with `DJANGO_SECRET_KEY`, `DJANGO_SITE_DOMAIN` and the administrative password unset, the baseline resolves to values nothing accepts — no published literal, no `localhost` domain, no `admin` password — and that settings import still succeeds so development and the test suite can run (FR-004, SC-006)  
  **Open (A3, never_built):** environment.py ships defaults for every variable this would assert on, so unset values resolve silently instead of raising.
- [x] T055 [US-1] Implement the sentinel reads in `settings/security.py`, composing `ALLOWED_HOSTS` from truthy entries only so an unset domain yields `[]` rather than `[""]` — otherwise `check_allowed_hosts_configured`'s emptiness test can never fire (FR-004, SC-006)  
  **Open (A3, never_built):** security.py:19 and :23 call env() bare; the defaults mean django-environ never raises for these variables.
- [x] T056 [US-1] Write `tests/test_conf/test_development.py::TestDevelopmentDefaults` asserting `development.py` supplies a clearly-marked development-only secret key and a `localhost` allowed-hosts list, and that neither value exists in the production baseline (FR-004, FR-009)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [x] T057 [US-1] Implement `development.py`'s development-only secret key and host list (FR-004, FR-009)  
  **Open (A3, built_differently):** `fairdm/conf/development.py:30` — Supplies a marked dev key but sets ALLOWED_HOSTS = ['*'] (:36); the 'not in the production baseline' half fails because environment.py already ships an insecure default key.
- [x] T058 [US-1] Write `tests/test_conf/test_setup.py::TestDevelopmentLayerApplies` asserting `DJANGO_ENV=development` applies `development.py` on top of the baseline and leaves every setting neither module names unchanged (scenario 2, FR-009)  
  **Open (A3, never_built):** nothing implements it and no test covers it.

## Phase 2: US-3 — a misconfigured production portal refuses to start (P1)

- [x] T059 [US-3] Write `tests/test_apps.py::TestFairDMConfigReady` asserting `setup()` records the resolved environment somewhere `FairDMConfig.ready()` can read once `django.setup()` has populated the app registry (R1)  
  **Done (US-3):** `tests/test_apps.py:1` · `tests/test_apps.py::TestFairDMConfigReady`
- [x] T060 [US-3] Implement the resolved-environment record in `setup.py`, read by `fairdm/apps.py::FairDMConfig.ready()`  
  **Done (US-3):** `fairdm/apps.py:13` — `FairDMConfig.resolved_environment()` reads the `DJANGO_ENV` setting `setup()` injects at `fairdm/conf/setup.py:146`, defaulting to production · `tests/test_apps.py::TestFairDMConfigReady`
- [x] T061 [US-3] Write `tests/test_conf/test_checks.py::TestDatabaseCheck` asserting a production-critical error when no production-grade database is configured (FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:29` · `tests/test_conf/test_checks.py::TestDatabaseChecks::test_check_database_configured_missing` — Not-production-grade half covered by TestDatabaseChecks::test_check_database_production_ready_sqlite.
- [x] T062 [US-3] Implement the database production-critical check in `fairdm/conf/checks.py`, tagged for the deployment check run (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:28` · `tests/test_conf/test_checks.py::TestDatabaseChecks::test_check_database_production_ready_sqlite` — Registered @register(Tags.database, DeployTags.deploy, deploy=True); nothing yet marks it as a production-critical subset distinct from the rest.
- [x] T063 [US-3] Extend `TestCacheChecks` with the case the existing deny list misses: `CACHES` absent, `CACHES['default']` empty, and a backend that is neither locmem nor dummy but still not shared (e.g. `filebased.FileBasedCache`) each produce a production-critical error (FR-017)  
  **Done (US-3):** `tests/test_conf/test_checks.py::TestCacheChecks` — absent `CACHES`, empty `default` and `filebased.FileBasedCache` each produce fairdm.E200
- [x] T064 [US-3] Extend the cache production-critical check to assert a shared backend rather than deny two development ones, covering the absent and unsuitable cases (FR-016, FR-017)  
  **Done (US-3):** `fairdm/conf/checks.py:112` — `SHARED_CACHE_BACKENDS` allowlist replaces the two-item deny list · `tests/test_conf/test_checks.py::TestCacheChecks`
- [x] T065 [US-3] Write `TestSecretKeyCheck` asserting a production-critical error both when the secret key is absent and when it carries an insecure or published value (FR-017, SC-006)  
  **Done (US-3):** `tests/test_conf/test_checks.py::TestSecretKeyChecks` — absent, `django-insecure-` prefixed, and shorter than 50 characters
- [x] T066 [US-3] Implement the secret-key production-critical check as FairDM's own error-severity check, not delegated to Django's warning-severity one (FR-017)  
  **Done (US-3):** `fairdm/conf/checks.py:163` — FairDM's own Error-severity `check_secret_key_exists`, rejecting the published prefix at :159 and a short key at :160 · `tests/test_conf/test_checks.py::TestSecretKeyChecks`
- [x] T067 [US-3] Write `TestAllowedHostsCheck` asserting a production-critical error when allowed hosts is empty or wildcarded (FR-017, SC-006)  
  **Done (A3):** `fairdm/conf/checks.py:145` · `tests/test_conf/test_checks.py::TestAllowedHostsChecks::test_check_allowed_hosts_configured_empty` — Wildcard half covered by TestAllowedHostsChecks::test_check_allowed_hosts_secure_wildcard.
- [x] T068 [US-3] Implement the allowed-hosts production-critical check (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:144` · `tests/test_conf/test_checks.py::TestAllowedHostsChecks::test_check_allowed_hosts_secure_wildcard` — Two checks: fairdm.E003 (empty) at :145 and fairdm.E004 (wildcard) at :167, both deploy-tagged.
- [x] T069 [US-3] Write `TestDebugCheck` asserting a production-critical error when `DEBUG` is on (FR-017, SC-006)  
  **Done (A3):** `fairdm/conf/checks.py:194` · `tests/test_conf/test_checks.py::TestDebugChecks::test_check_debug_false_enabled`
- [x] T070 [US-3] Implement the debug-off production-critical check (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:193` · `tests/test_conf/test_checks.py::TestDebugChecks::test_check_debug_false_disabled`
- [x] T071 [US-3] Write `tests/test_apps.py::TestProductionBoot` asserting that with `DJANGO_ENV=production` and several production-critical values missing at once, `FairDMConfig.ready()` raises an error naming every failure, not the first (FR-013, SC-003)  
  **Done (US-3):** `tests/test_apps.py::TestProductionBoot::test_boot_fails_naming_every_missing_or_unsafe_value` — boots a subprocess and asserts every failure is named
- [x] T072 [US-3] Implement aggregation of every production-critical check failure into a single raised error in `FairDMConfig.ready()`, selecting the subset by a dedicated production-critical tag applied to the five checks research R5 names and withheld from the Celery checks — `deploy=True` alone would block a boot on a missing worker, which R5 rejects (FR-013, FR-016)  
  **Done (US-3):** `fairdm/apps.py:43` — `_check_production_configuration()` runs the `production_critical` tag and raises one `SystemCheckError` naming every serious issue; the tag is applied to 8 check functions and withheld from both Celery checks · `tests/test_apps.py::TestProductionBoot`
- [x] T073 [US-3] Write `TestNonProductionBoot` asserting the same missing values under `development` start successfully with no configuration-check output emitted, **and** that FairDM's check ids are still present in Django's check registry in that environment, so the FR-014 guard cannot suppress registration (FR-014, FR-015, SC-004)  
  **Done (US-3):** `tests/test_apps.py::TestNonProductionBoot` — silent boot, and the check ids stay registered
- [x] T074 [US-3] Implement the environment guard in `FairDMConfig.ready()` so checks run only when the resolved environment is production (FR-014)  
  **Done (US-3):** `fairdm/apps.py:50` — the environment guard, returning before any check runs outside production · `tests/test_apps.py::TestNonProductionBoot`
- [x] T075 [US-3] Write `tests/test_conf/test_checks.py::TestDeployCommand` asserting `manage.py check --deploy` reports the full check set against production standards regardless of the current resolved environment (FR-015)  
  **Done (US-3):** `tests/test_conf/test_checks.py::TestDeployCommand::test_deploy_check_reports_the_same_failure_regardless_of_django_env`
- [x] T076 [US-3] Move check registration out of `FairDMConfig.ready()`'s body to module import, so the full set participates in the deployment check command independently of the FR-014 guard T074 adds (FR-015, FR-016)  
  **Done (US-3):** `fairdm/apps.py:7` — registration moved to module import, outside the guarded method body · `tests/test_conf/test_checks.py::TestDeployCommand`
- [x] T077 [US-3] Write `TestSyntacticallyUnusableValue` asserting a production-critical value that is present but syntactically unusable (e.g. a malformed database URL) fails its check distinctly from an absent value (edge case, FR-017)  
  **Done (US-3):** `tests/test_conf/test_checks.py::TestSyntacticallyUnusableValue::test_malformed_database_url_fails_distinctly_from_absent`
- [x] T078 [US-3] Implement the syntactic-validity branch of the affected production-critical check(s) (edge case, FR-017)  
  **Done (US-3):** `fairdm/conf/checks.py:78` — `check_database_usable` (fairdm.E102), a distinct id from E100 (absent) · `tests/test_conf/test_checks.py::TestSyntacticallyUnusableValue`
- [x] T079 [US-3] Write `tests/test_conf/test_conf_init.py::TestNoSecondValidationPath` asserting `fairdm.conf`'s public API exposes no second configuration-validation entry point beyond the check framework (FR-018)  
  **Done (US-3):** `tests/test_conf/test_conf_init.py::TestNoSecondValidationPath`
- [x] T080 [US-3] Delete the second validation path: `validate_services()` at `fairdm/conf/checks.py:269`, the comment at `setup.py:172-174`, its documented migration note, and all 51 test references (research R7) — `TestStagingSetup` goes in full per D1, and `validate_addon_module` stays because FR-022 still needs it (FR-018)  
  **Done (US-3):** `validate_services()` and its 39 test references deleted; `grep -rn validate_services fairdm/ tests/` returns only the assertion that it is gone. `validate_addon_module` retained for FR-022 · `tests/test_conf/test_conf_init.py::TestNoSecondValidationPath`

## Phase 2: US-4 — see which layer produced a setting (P2)

- [x] T081 [US-4] Write `tests/test_conf/test_setup.py::TestProvenance` asserting `setup()` records, per layer, an ordered `(layer name, path, found, settings written)` structure captured by diffing the scope's uppercase keys before and after each layer's `include()` call (FR-019, FR-020)  
  **Done (US-4):** `fairdm/conf/setup.py:237-305` — a `record.add_layer()` call per layer with name, path, found and the settings it wrote · `fairdm/conf/__init__.py:25` `Layer` · `tests/test_conf/test_setup.py::TestProvenance::test_records_one_entry_per_layer_with_name_path_found_and_settings`
- [x] T082 [US-4] Implement the provenance record as a module-level structure in `fairdm.conf`, populated by a snapshot-and-diff around each layer (~~shallow-copy~~ — corrected to a deep copy of mutable containers at US-4 convergence, see T109), recording **setting names per layer and never their values** — the scope holds `SECRET_KEY`, the database password and the email password (FR-019, FR-020)  
  **Done (US-4):** `fairdm/conf/__init__.py:77` — `record`, a module-level `Provenance` populated by a snapshot-and-diff around each layer, storing the setting-name tuple only. In `fairdm.conf` itself rather than a `provenance.py` submodule, per research R2 and because a submodule breaks the infrastructure-module allowlist `TestShippedOverrides` enforces · `tests/test_conf/test_setup.py::TestProvenance::test_record_never_holds_secret_values_only_their_names`
- [x] T083 [US-4] Extend `TestProvenance` with a case asserting a layer with no module for the resolved environment is recorded as absent, not omitted (FR-019, scenario 3)  
  **Done (US-4):** `fairdm/conf/setup.py:253-267` and `:287-305` — both override layers call `add_layer()` unconditionally, `found=False` when no module exists · `tests/test_conf/test_setup.py::TestProvenance::test_absent_layers_are_recorded_as_absent_not_omitted`
- [x] T084 [US-4] Extend `TestProvenance` with a case asserting that for a setting written by more than one layer, the record names the layer that produced the final value (FR-020, scenario 2)  
  **Done (US-4):** `fairdm/conf/__init__.py:57` — `producer()` returns the last layer in application order whose settings include the name · `tests/test_conf/test_setup.py::TestProvenance::test_producer_names_the_layer_that_wrote_the_final_value`
- [x] T085 [US-4] Write `tests/test_management/test_show_config.py::TestShowConfigCommand` asserting a management command lists every layer in application order, each marked found or absent (FR-019)  
  **Done (US-4):** `tests/test_management/test_show_config.py::TestShowConfigCommand::test_lists_every_layer_in_order_marked_found_or_absent`
- [x] T086 [US-4] Implement `fairdm/management/commands/show_config.py` — the directory Django scans for the installed `fairdm` app, beside the three existing commands — reading the provenance record after `django.setup()` and reporting the layer list (FR-019)  
  **Done (US-4):** `fairdm/management/commands/show_config.py:18` — beside the three existing commands in the directory Django's app scan actually reads; the A3 note's `fairdm/conf/management/` does not exist and was never the convention · `tests/test_management/test_show_config.py::TestShowConfigCommand`
- [x] T088 [US-4] Extend `TestShowConfigCommand` with a case: given a setting-name argument, the command reports its resolved value and the layer that produced it (FR-020)  
  **Done (US-4):** `tests/test_management/test_show_config.py::TestShowConfigNamedSetting::test_reports_resolved_value_and_producing_layer`
- [x] T089 [US-4] Implement the named-setting lookup mode of `show_config`, reading the value from `django.conf.settings` at report time and passing it through `SafeExceptionReporterFilter().cleanse_setting()` so a secret is never printed (FR-020)  
  **Done (US-4):** `fairdm/management/commands/show_config.py:44` — `_report_setting` reads `django.conf.settings` at report time and passes the value through `SafeExceptionReporterFilter().cleanse_setting()` · `tests/test_management/test_show_config.py::TestShowConfigNamedSetting::test_cleanses_a_known_secret_so_it_never_reaches_stdout`
- [x] T090 [US-4] Write `tests/test_conf/test_setup.py::TestProvenanceCoversEverySetting` asserting that for every setting any baseline module sets, the provenance record names a producing layer (SC-005)  
  **Done (US-4):** `tests/test_conf/test_setup.py::TestProvenanceCoversEverySetting::test_every_baseline_setting_names_a_producing_layer` — the per-layer diff is general, not hardcoded to the five entries
- [x] T110 [US-5] Apply the `fairdm.E400` rule at the end of `setup()` as well, on the composed settings scope, and narrow the `import_models()` call site to FairDM's own check (FR-012)  
  **Why:** two gaps in T107 as delivered. Running the whole `Tags.translation` set also ran Django's own translation checks, so `translation.E004` (LANGUAGE_CODE not among LANGUAGES) became a hard boot failure in every environment — a `manage.py check` finding, not something FairDM refuses a boot over. And `import_models()` alone is too late for a portal whose *own* apps import `parler.models`, since portal apps are registered ahead of FairDM's (D11). `setup()` is ahead of every app; `import_models()` is the only point after a portal's post-`setup()` assignments; both are needed. Also covers `PARLER_LANGUAGES["default"]["code"]`, which falls back to `PARLER_DEFAULT_LANGUAGE_CODE` and is the first thing parler rejects.
- [x] T109 [US-4] Attribute a setting to a layer that mutates its container in place, not only to one that rebinds the name — `INSTALLED_APPS += [...]` calls `list.__iadd__`, and FairDM's own `development.py` extends both `INSTALLED_APPS` and `MIDDLEWARE` that way (FR-020)  
  **Done (US-4, found at convergence):** `fairdm/conf/setup.py:64` — `_snapshot_scope` deep-copies mutable containers so the mutation is visible on one side of the diff only; `_written_keys` compares those by value and everything else by identity. Before the fix, `show_config INSTALLED_APPS` under `DJANGO_ENV=development` named `baseline` as the producer of a list holding `django_browser_reload`, which the baseline never put there · `tests/test_conf/test_setup.py::TestProvenance::test_producer_names_a_layer_that_appended_to_an_existing_list` and `::test_shipped_development_override_is_the_producer_of_what_it_appends`, both proven red against the identity diff first


## Phase 3: US-5 — override any FairDM default without editing FairDM (P2)

- [x] T091 [US-5] Write `tests/test_conf/test_setup.py::TestPostSetupOverridesEveryBaselineModule` asserting a portal that assigns one representative setting from each of the eleven baseline modules after the `setup()` call sees its own value, regardless of which module originally set it (FR-012, scenario 1)  
  **Done:** ~~nine~~ eleven baseline modules — the task text undercounted; `fairdm/conf/settings/` was read directly. Each override is compared against that same setting's own baseline-resolved value, from a second override-free `settings_module()` call, so the assertion is meaningless unless the baseline actually produced it. The SPECTACULAR_SETTINGS special case named in the A3 citation is already gone (D10, US-1).
- [x] T092 [US-5] Write `TestComposedSettingsCanBeFullyRebound` asserting a setting FairDM composes from several inputs (e.g. `INSTALLED_APPS` or the logging dict) can be overridden by name after `setup()` with no special-case handling in the entry point (FR-012, scenario 2)  
  **Done:** the pre-existing tests only mutate the composed value in place (`+=`, one nested key), which proves the containers are mutable rather than that a rebind by name is unimpeded. The two new tests rebind `INSTALLED_APPS` and `LOGGING` to brand-new objects.
- [x] T093 [US-5] Confirm `setup.py` contains no per-setting special-casing for post-call overrides — a design constraint verified by T092 rather than new code (FR-012)  
  **Done:** the A3 citation is stale — `setup.py` was read end to end and carries no `**overrides` kwarg and no setting-name branch of any kind; every `if` in it is structural (file existence, key case, container mutation, `portal_settings_dir` presence). D9 and D10 both landed in earlier stories. Closed on that reading plus T092, with no code change.

## Phase 3: US-6 — an addon contributes settings at a defined point (P3)

- [x] T094 [US-6] Write `tests/test_conf/test_addons.py::TestAddonPosition` asserting an addon named in `setup()` applies its settings after FairDM's environment override and before the portal's environment override (FR-008, FR-021, scenario 1)  
  **Closed (US-6):** `tests/test_conf/test_addons.py::TestAddonPosition::test_addon_setting_beats_fairdm_environment_override` · `fairdm/conf/setup.py:305` — the fixture addon sets `DEBUG`, which FairDM's own `development.py` also sets, so the test proves the order rather than merely that the addon's settings land. Passed without a code change: layer 3 already applied after layer 2. Mutation: moving the addon block ahead of the FairDM override reds it.
- [x] T095 [US-6] Implement addon settings application at that position in `fairdm/conf/addons.py`, wired into `setup.py`'s layer composition (FR-021)  
  **Closed (US-6):** `fairdm/conf/setup.py:305` — the A3 note is stale. The portal override layer it says is missing was built at US-4, and addons already apply between the two overrides. Closed on that reading plus T094's test, with no code change.
- [x] T096 [US-6] Extend `TestAddonPosition` with a case asserting a portal's override of a setting the addon also set wins (FR-021, scenario 1 tail)  
  **Closed (US-6):** `tests/test_conf/test_addons.py::TestAddonPosition::test_portal_environment_override_beats_addon_setting` · `fairdm/conf/setup.py:337` — the portal ships a `development.py` setting the same `DEBUG` the addon sets. Mutation: moving the addon block after the portal override reds it.
- [x] T097 [US-6] Write `TestAddonFailureProduction` asserting an addon that cannot be loaded prevents startup in production and names the addon in the error (FR-022, scenario 2)  
  **Closed (US-6):** `tests/test_conf/test_addons.py::TestAddonValidation::test_broken_addon_fails_fast_in_production` — the pre-existing test was strengthened in place from `pytest.raises(Exception)` to `ImproperlyConfigured` plus an assertion the message names the addon, and moved onto a fixture that restores `os.environ`.
- [x] T098 [US-6] Implement the production failure path for an unloadable addon (FR-022)  
  **Closed (US-6):** `fairdm/conf/checks.py:499` — `validate_addon_module` already raised `ImproperlyConfigured` naming the addon. Closed on that reading plus T097's strengthened test, with no code change.
- [x] T099 [US-6] Write `TestAddonFailureNonProduction` asserting the same failure in a non-production environment emits a warning, skips the addon, and lets the portal start (FR-022, scenario 3)  
  **Closed (US-6):** `tests/test_conf/test_addons.py::TestAddonDiscovery::test_addon_with_invalid_module_fails_gracefully_in_development` — replaces the skip whose body was a bare `pass` before dead code, using the `settings_module` fixture and the `tests/test_conf/unloadable_addon` package. Red before T100 for the right reason: no warning at the old DEBUG level.
- [x] T100 [US-6] Implement the non-production warn-and-skip path for an unloadable addon (FR-022)  
  **Closed (US-6):** `fairdm/conf/checks.py:502` and `:512` — both non-production `except` clauses log at WARNING rather than DEBUG. Mutation: reverting either to `logger.debug` reds T099's test.
- [x] T101 [US-6] Write `TestAddonPartialFailure` asserting an addon whose settings module raises partway through is treated as unloadable rather than left half-applied (edge case, FR-022)  
  **Closed (US-6):** `tests/test_conf/test_addons.py::TestAddonPartialFailure` (both methods) · fixture package `tests/test_conf/broken_execution_addon/`, whose setup module writes a setting and then raises. Red before T102 for the right reason: the `RuntimeError` propagated raw.
- [x] T102 [US-6] Implement partial-failure handling so a partway addon exception is caught and routed through the same unloadable-addon path (edge case, FR-022)  
  **Closed (US-6):** `fairdm/conf/setup.py:316` and `:326` · `fairdm/conf/addons.py:47` — layer 3 applies each addon to a private scratch scope and merges only on success, routing a failure through the same production-raise / non-production-warn split as an addon that could not be found. `discover_addon_setup_modules` and `load_addons` now return `(addon_name, path)` pairs so a failure can still name the addon. Mutations: restoring the unguarded `include(*paths, scope=caller_globals)` reds both partial-failure tests; removing the production raise reds the production one.

- [x] T111 [US-6] Scope the addon scratch copy to settings, so applying an addon does not rebind names Django never reads in the portal's own namespace (FR-021)  
  **Closed (US-6, convergence):** `tests/test_conf/test_addons.py::TestAddonScopeIsolation::test_portal_non_setting_objects_keep_their_identity` · `fairdm/conf/setup.py:114` — `_scratch_scope` copied every mutable container in the caller's scope, including lowercase names and `__builtins__` (a dict in an imported module), and the success path merged all of them back. A portal that imports a list or dict shared with another module and appends to it after the `setup()` call was appending to a copy nothing else could see. Red before the fix for that reason.
- [x] T112 [US-6] Restore the second vacuous skipped addon test — an addon defining no `__fdm_setup_module__` is warned about by name and skipped (FR-022)  
  **Closed (US-6, convergence):** `tests/test_conf/test_addons.py::TestAddonDiscovery::test_addon_without_setup_module_logs_warning` · `fairdm/conf/addons.py:75` — skipped for a path-escaping problem in a hand-built settings file and beginning with a bare `pass` before dead code, so it asserted nothing on any platform. The `settings_module` fixture removes the escaping the skip was about. Mutation: dropping the addon name from the warning reds it.
- [x] T113 [US-6] Cover what the scratch copy guards — an addon that mutates a settings container in place and then raises (edge case, FR-022)  
  **Closed (US-6, convergence):** `tests/test_conf/test_addons.py::TestAddonScopeIsolation::test_in_place_mutation_by_a_failing_addon_is_discarded` · `fairdm/conf/setup.py:91` — no test distinguished the deep copy from a shallow one, because `broken_execution_addon` rebinds a name before raising and a shallow copy already isolates that. The new fixture appends to `INSTALLED_APPS` in place. Mutation: making the scratch a shallow `dict(caller_globals)` reds it.

## Documentation

- [x] T103 [P] [US-2] Write `docs/portal-development/configuration.md` covering the entry point, all five layers from FR-008, the environment variable, the environment files, the check behaviour and the interrogation command, using the recommended `config/<environment>.py` project structure in every example and stating that the portal override module is resolved beside the settings module (FR-023, FR-024, SC-007)  
  **Closed (US-2):** rewritten for the five-layer contract. Superseded finding — `docs/portal-development/configuration.md:1` — The page documents the superseded design: three fixed profiles, a 7-step order whose steps 6-7 are **overrides and in-setup() validation, and a section recommending **overrides; it never mentions the five-layer order, the portal override module, or an interrogation command.
- [x] T104 [P] [US-3] Write `docs/portal-administration/configuration-checks.md` covering the production-critical check subset, the production-boot failure behaviour, and how to run the full check set on demand (FR-015, FR-023)  
  **Done (US-3):** `docs/portal-administration/configuration-checks.md:1` — the production-critical subset and its ids, boot-failure behaviour, and the environment-agnostic on-demand run
- [x] T105 [P] [US-1] Update the package README and CHANGELOG for the new `fairdm.setup()` public entry point and the removed `**overrides` argument (Article VI/XVII)  
  **Open (A3, never_built):** Neither README nor CHANGELOG mentions the entry point, and **overrides is still in the signature.

## Found during implementation

- [x] T106 [US-2] Add `tests/test_conf/test_setup.py::TestBundledPortalBoots` asserting the bundled example portal (`config/settings.py`) starts under both shipped environments, and fix `config/production.py` so it does  
  **Why:** wiring `config/production.py` in as a real layer-4 override broke `DJANGO_ENV=production` startup — it narrows `LANGUAGES` to `en, de` while the baseline hardcodes `PARLER_LANGUAGES` with `fr`, and django-parler validates one against the other at import. Every existing test imports `tests/settings.py`, so nothing in the suite exercised the example portal. Test proven against the defect before it was fixed.
- [x] T107 [US-5] Give the `LANGUAGES` / `PARLER_LANGUAGES` coupling a named Django check, so a portal that narrows `LANGUAGES` gets a FairDM error naming both settings rather than an `ImproperlyConfigured` traceback from inside django-parler (FR-012)  
  **Why:** a concrete instance of the FR-012 promise failing on a setting the baseline composes. Reproducer: delete the `PARLER_LANGUAGES` block from `config/production.py` and run `DJANGO_ENV=production DJANGO_SETTINGS_MODULE=config.settings python -c "import django; django.setup()"`. Reproduced red first, then fixed.  
  **Done:** `fairdm.E400`, registered under `Tags.translation` so `manage.py check` reports it, and applied ahead of parler's own validation, which runs at model-import time before any Django check can. Not gated to production: the underlying crash is not environment-dependent, so gating the message to production would leave development with the bare traceback.
- [x] T108 [US-1] Bring the surviving January spec artefacts into line with the settled design or delete them: `specs/001-fairdm-setup/data-model.md` (describes `staging.py` as shipped, and production/staging fail-fast), `specs/001-fairdm-setup/quickstart.md`, `specs/001-fairdm-setup/contracts/settings-sections.md`, and the R1 paragraph at `docs/ROADMAP.md:34`, which still promises three profiles  
  **Why:** S1 rewrote `spec.md` in place and left its siblings describing the design this feature removed.

## Coverage

| ID | Task(s) |
|---|---|
| FR-001 | T001, T027, T052 |
| FR-002 | T031–T048 |
| FR-003 | T031–T048, T053 |
| FR-004 | T006, T007, T054, T055, T056, T057 |
| FR-005 | T049, T050, T051 |
| FR-006 | T007, T028, T029, T030 |
| FR-007 | T008, T009, T010, T011 |
| FR-008 | T012, T013, T025, T094 |
| FR-009 | T018, T019, T056, T057, T058 |
| FR-010 | T010, T011, T014, T015, T016, T017, T025 |
| FR-011 | T021, T022, T023, T024 |
| FR-012 | T026, T027, T091, T092, T093, T107, T110 |
| FR-013 | T071, T072 |
| FR-014 | T073, T074 |
| FR-015 | T075, T076, T104 |
| FR-016 | T062, T064, T066, T068, T070, T076 |
| FR-017 | T061–T070, T077, T078 |
| FR-018 | T079, T080 |
| FR-019 | T081, T082, T083, T085, T086 |
| FR-020 | T081, T084, T088, T089 |
| FR-021 | T094, T095, T096, T111 |
| FR-022 | T097–T102, T112, T113 |
| FR-023 | T103, T104 |
| FR-024 | T103 |
| SC-001 | T052 |
| SC-002 | T020 |
| SC-003 | T071 |
| SC-004 | T073 |
| SC-005 | T090 |
| SC-006 | T054, T065, T067, T069 |
| SC-007 | T103 |

## Reconciliation (A3)

Every task above was walked against the codebase. A task is ticked only where implementing code is cited **and** an existing passing test exercises it — code with no test stays open, and its remaining work is the test. The previous task list's checkboxes were not consulted.

- **104 tasks total** — 9 proven done, 95 open. (A3 first ticked 12 of 105; the S3R reconciliation lens reopened T063, T064 and T076 as partial, and T087 was dropped as a step Django does not have.)

| Why a task is open | Count | Tasks |
|---|---|---|
| never built | 56 | T004, T006, T008, T010, T012, T014, T016, T018, T020, T021, T023, T024, T025, T026, T030, T031, T033, T035, T037, T039, T041, T043, T045, T047, T049, T051, T052, T053, T054, T055, T056, T058, T059, T071, T072, T073, T074, T077, T078, T079, T081, T082, T083, T084, T085, T086, T087, T088, T089, T090, T094, T096, T099, T101, T102, T105 |
| built differently — the code contradicts the spec and must change | 15 | T007, T011, T015, T019, T027, T032, T034, T044, T050, T057, T080, T093, T095, T100, T103 |
| partly built | 18 | T005, T013, T017, T022, T028, T029, T048, T060, T063, T064, T065, T066, T075, T076, T091, T092, T097, T104 |
| built, no test covering it | 7 | T009, T036, T038, T040, T042, T046, T098 |

Proven done: T001, T002, T003, T061, T062, T067, T068, T069, T070.

Evidence baseline: `poetry run pytest tests/test_conf` — 60 passed, 3 skipped.

## Progress since A3

The A3 figures above are that stage's snapshot and are left as recorded. Current state:

| | Tasks | Done | Notes |
|---|---|---|---|
| After A3 | 104 | 9 | T087 dropped as a step Django does not have |
| After US-2 | 107 | 34 | T106 (the bundled portal's boot), T107 (the `LANGUAGES` / `PARLER_LANGUAGES` coupling) and T108 (the January spec artefacts) added at convergence |
| After US-3 | 107 | 51 | T059–T080 and T104 closed |
| After US-1 | 107 | 83 | T004–T007 and T031–T058 closed. T105 (README/CHANGELOG) and T108 (the January spec artefacts) stay with the orchestrator |
| After US-4 | 108 | 93 | T081–T086 and T088–T090 closed. T109 added and closed at convergence — the identity diff missed a layer that appends |
| After US-5 | 109 | 98 | T091–T093 and T107 closed. T110 added and closed at convergence — the check ran Django's whole `translation` tag, and its only call site was too late for a portal's own parler-model apps |
| After US-6 | 112 | 110 | T094–T102 closed. T111–T113 added and closed at convergence — the addon scratch scope copied and merged back names Django never reads, nothing distinguished the deep copy from a shallow one, and a second vacuous skipped test was still in the file |

Evidence at US-3 convergence: `poetry run pytest` — 1326 passed, 70 skipped.

Evidence at US-1 convergence: `poetry run pytest` — 1391 passed, 70 skipped; `poetry run pre-commit run --files <32 touched files>` — every hook passes, mypy included.

Evidence at US-4 convergence: `poetry run pytest` — 1401 passed, 70 skipped; `poetry run pre-commit run --files <7 touched files>` — every hook passes, mypy included. Five mutations red the tests that should catch them: reverting the before-snapshot to an identity diff reds 2, making `producer()` return the first layer rather than the last reds 3, storing values beside names in the record reds 7, omitting absent layers reds 2, and dropping `cleanse_setting()` reds 1.


Evidence at US-6 convergence: `poetry run pytest` — 1423 passed, 68 skipped; `poetry run pre-commit run --files <5 touched files>` — every hook passes, mypy and deptry included; `forge verify --base 446f493` — conformance, lint, typecheck, test and build all green. Six mutations red the tests that should catch them: restoring the unguarded `include(*paths, scope=caller_globals)` reds 2, reverting the non-production log to DEBUG reds 1, removing the production raise reds 1, moving the addon layer ahead of FairDM's override reds 2, moving it after the portal's reds 1, and making the scratch scope a shallow copy reds 1.

## Review remedies (S6)

| | Tasks | Done | Notes |
|---|---|---|---|
| After review | 115 | 115 | T114 (the boot refusal keys on the composed settings, not the string), T115 (`DJANGO_SETUP_TOOLS` scaffold residue), T116 (`THUMBNAIL_DEBUG` moves to the development override) added and closed at the review gate — see D21 |

Evidence at the review gate: `poetry run pytest` — 1429 passed, 68 skipped; `poetry run pre-commit run --all-files` — every hook passes, mypy and deptry included; `forge verify` — conformance, lint, typecheck, test and build all green. Two mutations red the tests that should catch them: restoring `!= "production"` reds all four cases of the unrecognised-environment boot test, and restoring either piece of baseline residue reds its own test.
