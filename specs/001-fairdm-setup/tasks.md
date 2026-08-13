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
- [ ] T004 [P] [US-1] Create `tests/test_conf/test_settings/__init__.py` mirroring `fairdm/conf/settings/` (Article X)  
  **Open (A3, never_built):** tests/test_conf/test_settings/ does not exist.
- [ ] T005 [US-1] Write `tests/test_conf/conftest.py`: an env-var isolation fixture (saves/restores `DJANGO_ENV` and related variables per test), a fixture that builds a throwaway portal settings module on `tmp_path` with a real `__file__`, and a scope-snapshot helper reused by the provenance tests in Phase 2 (Article X)  
  **Open (A3, partial):** `tests/test_conf/conftest.py:14` — conftest holds only production_env; no tmp_path portal-settings fixture, no scope-snapshot helper, and the env fixtures that exist are duplicated inside individual test modules.
- [ ] T006 [US-1] Write `tests/test_conf/test_environment.py::TestEnv` asserting the shared `Env` declares `DJANGO_SECRET_KEY`, `DJANGO_SITE_DOMAIN`, the database, cache and admin-credential variables with no default value (FR-004, FR-006)  
  **Open (A3, never_built):** tests/test_conf/test_environment.py does not exist.
- [ ] T007 [US-1] Implement `fairdm/conf/environment.py`: the shared `django-environ` `Env()` declaration for every deployment-varying value, with no default for any security-critical variable (FR-004, FR-006)  
  **Open (A3, built_differently):** `fairdm/conf/environment.py:3` — The shared Env supplies working defaults for the security-critical values FR-004 forbids: DJANGO_SECRET_KEY (:15), DJANGO_SITE_DOMAIN (:19), DJANGO_SUPERUSER_PASSWORD (:10), DJANGO_ALLOWED_HOSTS=[] (:11).

## Phase 1: US-2 — vary configuration by environment through layered overrides (P1)

Establishes the layering mechanism the rest of the feature composes over (plan.md: US-2 before US-1).

- [ ] T008 [US-2] Write `tests/test_conf/test_setup.py::TestResolvedEnvironment` asserting `DJANGO_ENV` unset resolves to `production` (FR-007)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T009 [US-2] Implement environment resolution in `fairdm/conf/setup.py`: read `DJANGO_ENV`, default to `production` (FR-007)  
  **Open (A3, no_test):** `fairdm/conf/setup.py:57` — Default-to-production is implemented, but every test sets DJANGO_ENV explicitly, so the unset path is never exercised.
- [ ] T010 [US-2] Extend `TestResolvedEnvironment` with cases for `DJANGO_ENV` set to an empty string and to a name differing only in case from a shipped one, asserting each is looked up literally with no normalisation (edge case, FR-007, FR-010)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T011 [US-2] Implement literal, non-normalising environment-name handling in `setup.py` (edge case, FR-007)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:58` — DJANGO_ENV is validated against a fixed allowlist (production, staging, development); anything else is warned about and rewritten to production, so the name is normalised and staging is first-class.
- [ ] T012 [US-2] Write `tests/test_conf/test_setup.py::TestLayerOrder` asserting the five layers apply in FR-008's order: baseline, FairDM's environment override, addon settings, the portal's environment override, then post-call assignment (FR-008)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T013 [US-2] Implement layer composition in `setup.py` using `django-split-settings` `include()` calls in FR-008's order (FR-008)  
  **Open (A3, partial):** `fairdm/conf/setup.py:132` — Four layers compose (baseline :132, FairDM env override :145, addons :151, post-call assignment); the portal env override layer is absent and an extra **overrides layer (:156) that FR-012 forbids is applied.
- [ ] T014 [US-2] Extend `TestLayerOrder` with a case asserting an override module is selected by existence, not from a fixed allowlist of permitted environment names (FR-010)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T015 [US-2] Implement the existence probe for `fairdm/conf/<environment>.py`, replacing any fixed profile list (FR-010)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:135` — Selection is a hard-coded dict {development, staging}; the .exists() call at :143 is a secondary guard on an already-allowlisted name, not an existence probe.
- [ ] T016 [US-2] Extend `TestLayerOrder` with a case asserting an environment for which neither FairDM nor the portal ships a module resolves to the baseline unchanged and raises nothing (FR-010, scenario 3)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T017 [US-2] Implement the skip-without-error path when a layer's module does not exist (FR-010)  
  **Open (A3, partial):** `fairdm/conf/setup.py:143` — The exists guard protects only the two allowlisted FairDM modules; an unknown environment never reaches it because :58 has already coerced the name.
- [ ] T018 [US-2] Write `tests/test_conf/test_setup.py::TestShippedOverrides` asserting FairDM ships exactly one override module, `development`, and none for any other environment name (FR-009)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T019 [US-2] Create `fairdm/conf/development.py` as FairDM's sole shipped override module, empty pending the baseline-audit values added in T057 (FR-009)  
  **Open (A3, built_differently):** `fairdm/conf/development.py:1` — development.py exists but is not the sole shipped override: fairdm/conf/staging.py is still shipped and wired in at setup.py:137.
- [ ] T020 [US-2] Write `tests/test_conf/test_setup.py::TestProductionVsDevelopmentDiff` asserting settings resolved for production and for development differ only in the keys `development.py` names, by diffing the two resolutions (SC-002)  
  **Open (A3, never_built):** SC-002 unverified.
- [ ] T021 [US-2] Write `tests/test_conf/test_setup.py::TestPortalOverride` asserting the portal's override module is resolved beside its settings module regardless of directory name, using the `tmp_path` settings-module fixture (FR-011, scenario 5)  
  **Open (A3, never_built):** No portal override mechanism exists to test.
- [ ] T022 [US-2] Implement capture of the caller's settings-module directory in `setup.py`, taken before `__file__` is overwritten for `split_settings`'s relative-include resolution, and derive the portal override path from it (FR-011)  
  **Open (A3, partial):** `fairdm/conf/setup.py:68` — caller_globals is captured before __file__ is overwritten, but only base_dir (.parent.parent) is derived and it is used solely to locate stack.env files; the settings-module directory is not retained.
- [ ] T023 [US-2] Extend `TestPortalOverride` with a case where the portal's settings module has no usable `__file__` — the portal-override lookup is skipped with a warning, not an exception (edge case, FR-011)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T024 [US-2] Implement the no-`__file__` fallback: skip the portal-override lookup and emit a warning (edge case, FR-011)  
  **Open (A3, never_built):** With no base_dir argument, a missing __file__ raises KeyError at setup.py:72 rather than warning.
- [ ] T025 [US-2] Extend `TestLayerOrder` with a case where FairDM and the portal both ship a module for the same resolved environment, asserting both apply in the declared order (edge case, FR-008, FR-010)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T026 [US-2] Write `tests/test_conf/test_setup.py::TestEntryPointSignature` asserting `setup()` accepts no settings keyword arguments and raises `TypeError` if any are passed (FR-012)  
  **Open (A3, never_built):** The existing TestSetupOverrides asserts the opposite — that keyword overrides are accepted.
- [ ] T027 [US-2] Implement `setup()`'s public signature in `fairdm/conf/setup.py`, re-exported from `fairdm/conf/__init__.py`, with no `**overrides`-style parameter (FR-001, FR-012)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:21` — setup() is re-exported but still carries **overrides (:26), applied at :156; five tests in TestSetupOverrides assert this forbidden behaviour and must be rewritten.
- [ ] T028 [US-2] Write `tests/test_conf/test_setup.py::TestEnvFiles` asserting env files are read in order — `stack.env`, then `stack.<environment>.env`, then an explicit `env_file=` argument with `overwrite=True` — and that the first two respect variables already set in the process environment (FR-006)  
  **Open (A3, partial):** `tests/test_conf/test_setup.py::TestEnvFileParameter::test_custom_env_file_is_loaded` — Covers only the explicit env_file leg; stack.env ordering and process-env precedence are unasserted, and test_env_file_takes_precedence is skipped.
- [ ] T029 [US-2] Implement env-file loading in `setup.py` in that order and with that precedence (FR-006)  
  **Open (A3, partial):** `fairdm/conf/setup.py:78` — Order and overwrite flag are implemented (:80-101) but the stack.env and stack.<env>.env legs have no test.
- [ ] T030 [P] [US-2] Document the env-file precedence and the five-layer order in `setup.py`'s module docstring (FR-006)  
  **Open (A3, never_built):** `fairdm/conf/setup.py:1` — The module docstring documents neither the env-file precedence nor the layer order.

## Phase 1: US-1 — obtain a complete settings baseline from one call (P1)

One task pair per named concern (US-1's acceptance scenario names: database, cache, background
tasks, static/media, authentication, email, logging, security headers, REST API), plus the app
ordering and the baseline-wide audits.

- [ ] T031 [P] [US-1] Write `tests/test_conf/test_settings/test_database.py::TestDatabase` asserting the baseline configures a production-grade database from the environment with no environment branching (FR-002, FR-003)  
  **Open (A3, never_built):** Such a test would fail today: settings/database.py:45 branches to SQLite.
- [ ] T032 [P] [US-1] Implement `fairdm/conf/settings/database.py`, with a docstring stating what it owns and what it leaves to a portal (FR-002, FR-003)  
  **Open (A3, built_differently):** `fairdm/conf/settings/database.py:26` — Branches three ways on env-var presence (DATABASE_URL, POSTGRES_*, SQLite fallback at :45-54), so the baseline is not unconditionally production-grade.
- [ ] T033 [P] [US-1] Write `tests/test_conf/test_settings/test_cache.py::TestCache` asserting the baseline configures a shared cache from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T034 [P] [US-1] Implement `fairdm/conf/settings/cache.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, built_differently):** `fairdm/conf/settings/cache.py:22` — Redis only when DJANGO_CACHE and REDIS_URL are both set; falls back to LocMem (:52) then Dummy (:71).
- [ ] T035 [P] [US-1] Write `tests/test_conf/test_settings/test_celery.py::TestCelery` asserting the baseline configures background-task (Celery) settings from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T036 [P] [US-1] Implement `fairdm/conf/settings/celery.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/celery.py:58` — Implemented with an ownership docstring and no environment branching; untested.
- [ ] T037 [P] [US-1] Write `tests/test_conf/test_settings/test_storage.py::TestStorage` asserting the baseline configures static and media handling from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T038 [P] [US-1] Implement `fairdm/conf/settings/storage.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/static_media.py:71` — Implemented as static_media.py rather than storage.py (name difference only); switches to S3 when the S3_* vars are set.
- [ ] T039 [P] [US-1] Write `tests/test_conf/test_settings/test_auth.py::TestAuth` asserting the baseline configures authentication (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T040 [P] [US-1] Implement `fairdm/conf/settings/auth.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/auth.py:29` — Argon2, validators, allauth and guardian backends configured; untested.
- [ ] T041 [P] [US-1] Write `tests/test_conf/test_settings/test_email.py::TestEmail` asserting the baseline configures email from the environment (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T042 [P] [US-1] Implement `fairdm/conf/settings/email.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/email.py:37` — Reads EMAIL_* from the shared env; untested.
- [ ] T043 [P] [US-1] Write `tests/test_conf/test_settings/test_logging.py::TestLogging` asserting the baseline configures logging using the shared `Env`, with no environment branching (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T044 [P] [US-1] Implement `fairdm/conf/settings/logging.py` using the shared `Env` declaration, with an ownership docstring (FR-002, FR-003)  
  **Open (A3, built_differently):** `fairdm/conf/settings/logging.py:20` — Builds its own environ.Env('localenv') for SENTRY_* rather than using the shared Env, and gates Sentry on `if SENTRY_DSN and not DEBUG` (:30).
- [ ] T045 [P] [US-1] Write `tests/test_conf/test_settings/test_security.py::TestSecurity` asserting the baseline sets production-grade security headers (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T046 [P] [US-1] Implement `fairdm/conf/settings/security.py` with an ownership docstring (FR-002, FR-003)  
  **Open (A3, no_test):** `fairdm/conf/settings/security.py:40` — SSL redirect, secure cookies, HSTS and nosniff sit behind `if env('DJANGO_SECURE')` (:49), so one flag strips the production headers.
- [ ] T047 [P] [US-1] Write `tests/test_conf/test_settings/test_api.py::TestApi` asserting the baseline configures the REST API, including the API-schema finalisation, entirely within this module rather than in the entry point (FR-002, FR-003)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T048 [P] [US-1] Implement `fairdm/conf/settings/api.py`, including the API-schema finalisation moved out of `setup.py`, with an ownership docstring (FR-002, FR-003)  
  **Open (A3, partial):** `fairdm/conf/settings/api.py:17` — api.py is a re-export shim over fairdm.api.settings; the API-schema finalisation is still performed in setup.py:162-170.
- [ ] T049 [US-1] Write `tests/test_conf/test_settings/test_apps.py::TestInstalledApps` asserting portal apps are composed ahead of FairDM's own apps and the third-party set, while staying behind the Django contrib apps that must load first (FR-005)  
  **Open (A3, never_built):** The only INSTALLED_APPS assertions in the suite are membership checks, never ordering.
- [ ] T050 [US-1] Implement `fairdm/conf/settings/apps.py`: an explicit, commented `INSTALLED_APPS` composition in that order, accepting the portal's `apps=[...]` (FR-005)  
  **Open (A3, built_differently):** `fairdm/conf/settings/apps.py:122` — Portal apps are spliced LAST, after every FairDM and third-party app, so portal templates and static files lose — the inverse of FR-005.
- [ ] T051 [US-1] Extend `test_apps.py` with `TestTemplateAndStaticPrecedence` asserting that when a portal and FairDM both define a template or static file at the same path, the portal's earlier app position makes its file win (FR-005, scenario 3)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T052 [US-1] Write `tests/test_conf/test_setup.py::TestBaselineCompleteness` asserting a settings module whose entire content is `fairdm.setup()` produces a configuration where every FairDM-owned setting is present and `manage.py check` raises nothing (FR-001, SC-001)  
  **Open (A3, never_built):** SC-001 unverified.
- [ ] T053 [US-1] Write `tests/test_conf/test_setup.py::TestNoEnvironmentBranching`, a static audit test asserting no module under `fairdm/conf/settings/` contains a conditional on the resolved environment (FR-003)  
  **Open (A3, never_built):** No module branches on DJANGO_ENV by name, but several branch on environment-derived state (logging.py:30, security.py:49, database.py:26, cache.py:22).
- [ ] T054 [US-1] Write `tests/test_conf/test_environment.py::TestNoSecurityDefaults` asserting reading `DJANGO_SECRET_KEY`, `DJANGO_SITE_DOMAIN`, `ALLOWED_HOSTS` or an administrative password with the variable unset raises FairDM's own error naming the variable and what to set it to, not a bare `ImproperlyConfigured` (FR-004, SC-006)  
  **Open (A3, never_built):** environment.py ships defaults for every variable this would assert on, so unset values resolve silently instead of raising.
- [ ] T055 [US-1] Implement wrapped reads in `environment.py`/`settings/security.py` that catch `django-environ`'s `ImproperlyConfigured` and re-raise with FairDM's own message (FR-004, SC-006)  
  **Open (A3, never_built):** security.py:19 and :23 call env() bare; the defaults mean django-environ never raises for these variables.
- [ ] T056 [US-1] Write `tests/test_conf/test_development.py::TestDevelopmentDefaults` asserting `development.py` supplies a clearly-marked development-only secret key and a `localhost` allowed-hosts list, and that neither value exists in the production baseline (FR-004, FR-009)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T057 [US-1] Implement `development.py`'s development-only secret key and host list (FR-004, FR-009)  
  **Open (A3, built_differently):** `fairdm/conf/development.py:30` — Supplies a marked dev key but sets ALLOWED_HOSTS = ['*'] (:36); the 'not in the production baseline' half fails because environment.py already ships an insecure default key.
- [ ] T058 [US-1] Write `tests/test_conf/test_setup.py::TestDevelopmentLayerApplies` asserting `DJANGO_ENV=development` applies `development.py` on top of the baseline and leaves every setting neither module names unchanged (scenario 2, FR-009)  
  **Open (A3, never_built):** nothing implements it and no test covers it.

## Phase 2: US-3 — a misconfigured production portal refuses to start (P1)

- [ ] T059 [US-3] Write `tests/test_apps.py::TestFairDMConfigReady` asserting `setup()` records the resolved environment somewhere `FairDMConfig.ready()` can read once `django.setup()` has populated the app registry (R1)  
  **Open (A3, never_built):** tests/test_apps.py does not exist.
- [ ] T060 [US-3] Implement the resolved-environment record in `setup.py`, read by `fairdm/apps.py::FairDMConfig.ready()`  
  **Open (A3, partial):** `fairdm/conf/setup.py:109` — setup() injects DJANGO_ENV into the caller's settings globals, but fairdm/apps.py:8-25 never reads it.
- [x] T061 [US-3] Write `tests/test_conf/test_checks.py::TestDatabaseCheck` asserting a production-critical error when no production-grade database is configured (FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:29` · `tests/test_conf/test_checks.py::TestDatabaseChecks::test_check_database_configured_missing` — Not-production-grade half covered by TestDatabaseChecks::test_check_database_production_ready_sqlite.
- [x] T062 [US-3] Implement the database production-critical check in `fairdm/conf/checks.py`, tagged for the deployment check run (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:28` · `tests/test_conf/test_checks.py::TestDatabaseChecks::test_check_database_production_ready_sqlite` — Registered @register(Tags.database, DeployTags.deploy, deploy=True); nothing yet marks it as a production-critical subset distinct from the rest.
- [x] T063 [US-3] Write `TestCacheCheck` asserting a production-critical error when no shared cache is configured (FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:80` · `tests/test_conf/test_checks.py::TestCacheChecks::test_check_cache_backend_locmem` — An explicitly empty CACHES dict produces no error, but Django's own default is locmem, which is caught.
- [x] T064 [US-3] Implement the cache production-critical check (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:79` · `tests/test_conf/test_checks.py::TestCacheChecks::test_check_cache_backend_dummy`
- [ ] T065 [US-3] Write `TestSecretKeyCheck` asserting a production-critical error both when the secret key is absent and when it carries an insecure or published value (FR-017, SC-006)  
  **Open (A3, partial):** `tests/test_conf/test_checks.py::TestSecretKeyChecks::test_check_secret_key_exists_empty` — Only the absent/empty case is tested; the insecure-or-published-value case is covered only by TestValidationLogic, which exercises the deprecated validate_services().
- [ ] T066 [US-3] Implement the secret-key production-critical check as FairDM's own error-severity check, not delegated to Django's warning-severity one (FR-017)  
  **Open (A3, partial):** `fairdm/conf/checks.py:114` — FairDM's own Error-severity check exists but tests only for absence; the insecure-prefix branch research R5 requires does not exist.
- [x] T067 [US-3] Write `TestAllowedHostsCheck` asserting a production-critical error when allowed hosts is empty or wildcarded (FR-017, SC-006)  
  **Done (A3):** `fairdm/conf/checks.py:145` · `tests/test_conf/test_checks.py::TestAllowedHostsChecks::test_check_allowed_hosts_configured_empty` — Wildcard half covered by TestAllowedHostsChecks::test_check_allowed_hosts_secure_wildcard.
- [x] T068 [US-3] Implement the allowed-hosts production-critical check (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:144` · `tests/test_conf/test_checks.py::TestAllowedHostsChecks::test_check_allowed_hosts_secure_wildcard` — Two checks: fairdm.E003 (empty) at :145 and fairdm.E004 (wildcard) at :167, both deploy-tagged.
- [x] T069 [US-3] Write `TestDebugCheck` asserting a production-critical error when `DEBUG` is on (FR-017, SC-006)  
  **Done (A3):** `fairdm/conf/checks.py:194` · `tests/test_conf/test_checks.py::TestDebugChecks::test_check_debug_false_enabled`
- [x] T070 [US-3] Implement the debug-off production-critical check (FR-016, FR-017)  
  **Done (A3):** `fairdm/conf/checks.py:193` · `tests/test_conf/test_checks.py::TestDebugChecks::test_check_debug_false_disabled`
- [ ] T071 [US-3] Write `tests/test_apps.py::TestProductionBoot` asserting that with `DJANGO_ENV=production` and several production-critical values missing at once, `FairDMConfig.ready()` raises an error naming every failure, not the first (FR-013, SC-003)  
  **Open (A3, never_built):** The 'production fails' tests all call the deprecated validate_services() with a hand-built settings dict; none boots an app registry or proves startup aborts.
- [ ] T072 [US-3] Implement aggregation of every production-critical check failure into a single raised error in `FairDMConfig.ready()` (FR-013)  
  **Open (A3, never_built):** FairDMConfig.ready() imports the checks module to register it and returns; it never runs or aggregates anything, so nothing in the boot path can stop a misconfigured production portal.
- [ ] T073 [US-3] Write `TestNonProductionBoot` asserting the same missing values under `development` start successfully with no configuration-check output emitted (FR-014, SC-004)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T074 [US-3] Implement the environment guard in `FairDMConfig.ready()` so checks run only when the resolved environment is production (FR-014)  
  **Open (A3, never_built):** No guard exists because no checks run at boot in any environment.
- [ ] T075 [US-3] Write `tests/test_conf/test_checks.py::TestDeployCommand` asserting `manage.py check --deploy` reports the full check set against production standards regardless of the current resolved environment (FR-015)  
  **Open (A3, partial):** `tests/test_conf/test_checks.py::TestCheckCommandIntegration::test_check_deploy_fails_with_errors` — Proves check --deploy surfaces one error id and passes on a valid config, but never varies DJANGO_ENV, so FR-015's 'regardless of environment' clause is unasserted.
- [x] T076 [US-3] Implement check registration so the full set participates in Django's deployment check command independent of `FairDMConfig.ready()`'s guard (FR-015, FR-016)  
  **Done (A3):** `fairdm/conf/checks.py:28` · `tests/test_conf/test_checks.py::TestCheckCommandIntegration::test_check_deploy_fails_with_errors` — Registration happens at module import time via @register(deploy=True), triggered by fairdm/apps.py:20, so it is structurally independent of any ready() guard.
- [ ] T077 [US-3] Write `TestSyntacticallyUnusableValue` asserting a production-critical value that is present but syntactically unusable (e.g. a malformed database URL) fails its check distinctly from an absent value (edge case, FR-017)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T078 [US-3] Implement the syntactic-validity branch of the affected production-critical check(s) (edge case, FR-017)  
  **Open (A3, never_built):** No check parses or validates the syntax of any value; they test presence and known-bad literals only.
- [ ] T079 [US-3] Write `tests/test_conf/test_conf_init.py::TestNoSecondValidationPath` asserting `fairdm.conf`'s public API exposes no second configuration-validation entry point beyond the check framework (FR-018)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T080 [US-3] Confirm no second validation path is implemented anywhere in `fairdm/conf/` — a design constraint verified by T079 rather than new code (FR-018)  
  **Open (A3, built_differently):** `fairdm/conf/checks.py:269` — validate_services() (:269) and validate_addon_module() (:452) still raise ImproperlyConfigured on their own and are still the subject under test in four test classes; unreachable from setup(), but FR-018 forbids it existing.

## Phase 2: US-4 — see which layer produced a setting (P2)

- [ ] T081 [US-4] Write `tests/test_conf/test_setup.py::TestProvenance` asserting `setup()` records, per layer, an ordered `(layer name, path, found, settings written)` structure captured by diffing the scope's uppercase keys before and after each layer's `include()` call (FR-019, FR-020)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T082 [US-4] Implement the provenance record as a module-level structure in `fairdm.conf`, populated by a shallow-copy-and-diff around each layer (FR-019, FR-020)  
  **Open (A3, never_built):** setup() applies layers with plain include() calls and takes no before/after snapshot.
- [ ] T083 [US-4] Extend `TestProvenance` with a case asserting a layer with no module for the resolved environment is recorded as absent, not omitted (FR-019, scenario 3)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T084 [US-4] Extend `TestProvenance` with a case asserting that for a setting written by more than one layer, the record names the layer that produced the final value (FR-020, scenario 2)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T085 [US-4] Write `tests/test_conf/test_management/test_show_config.py::TestShowConfigCommand` asserting a management command lists every layer in application order, each marked found or absent (FR-019)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T086 [US-4] Implement `fairdm/conf/management/commands/show_config.py`, reading the provenance record after `django.setup()` and reporting the layer list (FR-019)  
  **Open (A3, never_built):** There is no fairdm/conf/management/ directory.
- [ ] T087 [US-4] Register `show_config` under `fairdm`'s app config so `manage.py show_config` is discoverable (FR-019)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T088 [US-4] Extend `TestShowConfigCommand` with a case: given a setting-name argument, the command reports its resolved value and the layer that produced it (FR-020)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T089 [US-4] Implement the named-setting lookup mode of `show_config` (FR-020)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T090 [US-4] Write `tests/test_conf/test_setup.py::TestProvenanceCoversEverySetting` asserting that for every setting any baseline module sets, the provenance record names a producing layer (SC-005)  
  **Open (A3, never_built):** nothing implements it and no test covers it.

## Phase 3: US-5 — override any FairDM default without editing FairDM (P2)

- [ ] T091 [US-5] Write `tests/test_conf/test_setup.py::TestPortalOverridesSurvive` asserting a portal that assigns one representative setting from each of the nine baseline modules after the `setup()` call sees its own value, regardless of which module originally set it (FR-012, scenario 1)  
  **Open (A3, partial):** `fairdm/conf/setup.py:68` · `tests/test_conf/test_setup.py::TestSetupOverrides::test_post_setup_assignments_work` — The only test asserts two invented names no baseline module sets; setup.py:162-170 re-derives SPECTACULAR_SETTINGS at call time, so that post-call assignment is ignored.
- [ ] T092 [US-5] Write `TestComposedSettingOverride` asserting a setting FairDM composes from several inputs (e.g. `INSTALLED_APPS` or the logging dict) can be overridden by name after `setup()` with no special-case handling in the entry point (FR-012, scenario 2)  
  **Open (A3, partial):** `fairdm/conf/setup.py:132` · `tests/test_conf/test_setup.py::TestSetupOverrides::test_overrides_can_modify_lists` — Shows INSTALLED_APPS and LOGGING can be rebound post-call, but nothing asserts the 'no special-case handling in the entry point' half, which is false.
- [ ] T093 [US-5] Confirm `setup.py` contains no per-setting special-casing for post-call overrides — a design constraint verified by T092 rather than new code (FR-012)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:162` — setup.py rewrites SPECTACULAR_SETTINGS TITLE/DESCRIPTION after all layers and still applies a **overrides layer (:26, :154-156).

## Phase 3: US-6 — an addon contributes settings at a defined point (P3)

- [ ] T094 [US-6] Write `tests/test_conf/test_addons.py::TestAddonPosition` asserting an addon named in `setup()` applies its settings after FairDM's environment override and before the portal's environment override (FR-008, FR-021, scenario 1)  
  **Open (A3, never_built):** `fairdm/conf/setup.py:148` — test_addons.py asserts that addon settings land, never their position relative to another layer.
- [ ] T095 [US-6] Implement addon settings application at that position in `fairdm/conf/addons.py`, wired into `setup.py`'s layer composition (FR-021)  
  **Open (A3, built_differently):** `fairdm/conf/setup.py:148` — Addons apply after FairDM's env override, which is half of FR-008, but there is no portal env override layer; what follows addons is the **overrides update and the SPECTACULAR fixup.
- [ ] T096 [US-6] Extend `TestAddonPosition` with a case asserting a portal's override of a setting the addon also set wins (FR-021, scenario 1 tail)  
  **Open (A3, never_built):** Not testable until the portal override layer exists.
- [ ] T097 [US-6] Write `TestAddonFailureProduction` asserting an addon that cannot be loaded prevents startup in production and names the addon in the error (FR-022, scenario 2)  
  **Open (A3, partial):** `fairdm/conf/checks.py:487` · `tests/test_conf/test_addons.py::TestAddonValidation::test_broken_addon_fails_fast_in_production` — The test asserts only pytest.raises(Exception) around executing a generated settings module, so any unrelated failure satisfies it; it also calls os.environ.clear() with no restore fixture.
- [ ] T098 [US-6] Implement the production failure path for an unloadable addon (FR-022)  
  **Open (A3, no_test):** `fairdm/conf/checks.py:487` — validate_addon_module raises ImproperlyConfigured naming the addon, but the only covering test does not prove the raise came from the addon path.
- [ ] T099 [US-6] Write `TestAddonFailureNonProduction` asserting the same failure in a non-production environment emits a warning, skips the addon, and lets the portal start (FR-022, scenario 3)  
  **Open (A3, never_built):** test_addon_with_invalid_module_fails_gracefully_in_development is one of the 3 skips, and its body begins with a bare pass before dead code.
- [ ] T100 [US-6] Implement the non-production warn-and-skip path for an unloadable addon (FR-022)  
  **Open (A3, built_differently):** `fairdm/conf/checks.py:490` — The non-production path skips the addon but logs at DEBUG, not the warning FR-022 requires, so a skipped addon is invisible at default log level.
- [ ] T101 [US-6] Write `TestAddonPartialFailure` asserting an addon whose settings module raises partway through is treated as unloadable rather than left half-applied (edge case, FR-022)  
  **Open (A3, never_built):** nothing implements it and no test covers it.
- [ ] T102 [US-6] Implement partial-failure handling so a partway addon exception is caught and routed through the same unloadable-addon path (edge case, FR-022)  
  **Open (A3, never_built):** validate_addon_module only calls find_spec and never imports; include(*addon_setup_modules) at setup.py:151 is unguarded, so a partway exception leaves the settings scope half-mutated.

## Documentation

- [ ] T103 [P] [US-2] Write `docs/portal-development/configuration.md` covering the entry point, all five layers from FR-008, the environment variable, the environment files, the check behaviour and the interrogation command, using the recommended `config/<environment>.py` project structure in every example and stating that the portal override module is resolved beside the settings module (FR-023, FR-024, SC-007)  
  **Open (A3, built_differently):** `docs/portal-development/configuration.md:1` — The page documents the superseded design: three fixed profiles, a 7-step order whose steps 6-7 are **overrides and in-setup() validation, and a section recommending **overrides; it never mentions the five-layer order, the portal override module, or an interrogation command.
- [ ] T104 [P] [US-3] Write `docs/portal-administration/configuration-checks.md` covering the production-critical check subset, the production-boot failure behaviour, and how to run the full check set on demand (FR-015, FR-023)  
  **Open (A3, partial):** `docs/portal-administration/configuration-checks.md:1` — Covers the check subset and how to run the full set on demand, but says nothing about production-boot failure behaviour, and still carries a migration section referencing validate_services().
- [ ] T105 [P] [US-1] Update the package README and CHANGELOG for the new `fairdm.setup()` public entry point and the removed `**overrides` argument (Article VI/XVII)  
  **Open (A3, never_built):** Neither README nor CHANGELOG mentions the entry point, and **overrides is still in the signature.

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
| FR-012 | T026, T027, T091, T092, T093 |
| FR-013 | T071, T072 |
| FR-014 | T073, T074 |
| FR-015 | T075, T076, T104 |
| FR-016 | T062, T064, T066, T068, T070, T076 |
| FR-017 | T061–T070, T077, T078 |
| FR-018 | T079, T080 |
| FR-019 | T081, T082, T083, T085, T086, T087 |
| FR-020 | T081, T084, T087, T088, T089 |
| FR-021 | T094, T095, T096 |
| FR-022 | T097–T102 |
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

- **105 tasks total** — 12 proven done, 93 open.

| Why a task is open | Count | Tasks |
|---|---|---|
| never built | 56 | T004, T006, T008, T010, T012, T014, T016, T018, T020, T021, T023, T024, T025, T026, T030, T031, T033, T035, T037, T039, T041, T043, T045, T047, T049, T051, T052, T053, T054, T055, T056, T058, T059, T071, T072, T073, T074, T077, T078, T079, T081, T082, T083, T084, T085, T086, T087, T088, T089, T090, T094, T096, T099, T101, T102, T105 |
| built differently — the code contradicts the spec and must change | 15 | T007, T011, T015, T019, T027, T032, T034, T044, T050, T057, T080, T093, T095, T100, T103 |
| partly built | 15 | T005, T013, T017, T022, T028, T029, T048, T060, T065, T066, T075, T091, T092, T097, T104 |
| built, no test covering it | 7 | T009, T036, T038, T040, T042, T046, T098 |

Proven done: T001, T002, T003, T061, T062, T063, T064, T067, T068, T069, T070, T076.

Evidence baseline: `poetry run pytest tests/test_conf` — 60 passed, 3 skipped.

