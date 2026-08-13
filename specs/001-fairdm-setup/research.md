# Research — 001 portal configuration

Unknowns resolved before planning. Each entry states the question, what was checked, and the
decision the plan is built on.

---

## R1 — Where can production checks run and still stop a boot?

**Question.** FR-013 requires a production portal to refuse to start when its configuration is
unsafe. `fairdm.setup()` executes inside the settings module, which Django imports *before*
`django.setup()` populates the app registry. `django.core.checks.run_checks()` needs that registry,
so the check framework is not available at the moment `setup()` returns.

**Checked.** `django/core/checks/registry.py` resolves checks against `apps.get_app_configs()`;
`django/apps/registry.py` populates them during `django.setup()`, which runs after settings are
imported. Django's own deployment checks are all registered `deploy=True` and only execute under
`manage.py check --deploy` or an explicit `run_checks` call. `AppConfig.ready()` runs inside
`django.setup()`, after the registry is populated and before any request is served or any
management command body executes.

**Decision.** The production-critical subset executes from `FairDMConfig.ready()`, guarded on the
resolved environment, and raises `SystemCheckError` when any check in the subset reports an error.
`setup()` records the resolved environment for `ready()` to read; it does not run the checks itself.

Observable behaviour is what FR-013 and SC-003 describe — a misconfigured production portal does not
start, and the error names every problem. `ready()` is simply the first point in the boot at which
the check framework exists. This also means the guard covers `runserver`, a WSGI or ASGI server and
every management command alike, rather than only the paths that happen to call `setup()` directly.

**Consequence to accept.** A production box with broken configuration cannot run *any* management
command until the configuration is fixed, including `check --deploy` itself. That is the intended
reading of fail-fast, and the remedy is always to set the missing variable. Documented on the
configuration page.

---

## R2 — How is per-setting provenance captured?

**Question.** FR-020 requires reporting which layer produced a setting's final value.

**Checked.** `split_settings.tools.include()` executes each module against a scope dictionary — in
FairDM's case the portal settings module's globals, passed by `setup()`. Every layer therefore
mutates one observable dict, in order.

**Decision.** `setup()` snapshots the scope's uppercase keys before and after each layer and records
the deltas. The result is an ordered list of `(layer name, path, found, settings written)`. Because
each layer is applied in a separate `include()` call, no extra instrumentation is needed — a shallow
copy before and a diff after is sufficient and costs one pass per layer at startup.

**Rejected.** Wrapping the scope in a tracking `dict` subclass. It changes the object every settings
module sees, which is a large behavioural surface for a debugging feature, and `split_settings`
copies out of the scope in places.

**Storage.** The record is written to a module-level structure in `fairdm.conf`, not into settings,
so it never leaks into a settings dump or a serialisation. The reporting command reads it after
`django.setup()`.

---

## R3 — What makes a portal's templates win?

**Question.** FR-005 requires a portal's templates and static files to take precedence over
FairDM's.

**Checked.** `django/template/loaders/app_directories.py` builds its directory list from
`apps.get_app_configs()` in `INSTALLED_APPS` order and returns the first match. `staticfiles`
resolves the same way through `AppDirectoriesFinder`. FairDM currently appends portal apps last
(`fairdm/conf/settings/apps.py:122`), so a portal template at the same path as a FairDM one is never
reached.

**Decision.** Portal apps are inserted ahead of FairDM's own apps and ahead of the third-party set,
while staying behind the Django contrib apps that must load first. The ordering becomes an explicit,
commented composition rather than a single interpolation at the end of a literal list.

**Risk carried into the plan.** A portal that already ships a template shadowing a FairDM path has
been silently inert and will start being served. This is the intended behaviour and a breaking
change; it goes in the PR's risk section.

---

## R4 — How does an override module get found without naming a directory?

**Question.** FR-011 anchors the portal's override module beside its settings module.

**Checked.** `setup()` reads the caller's frame globals (`setup.py:68`) and derives `BASE_DIR` from
`__file__` two levels up. It then overwrites `caller_globals["__file__"]` with FairDM's own path
(`setup.py:110`) before including any settings module, because `split_settings` resolves relative
includes against it.

**Decision.** Capture the portal's settings directory at the same point `BASE_DIR` is derived, before
the overwrite, and hold it in a local. The portal override is that directory joined with
`<environment>.py`.

**Edge case.** A settings module with no usable `__file__` — generated, or imported from an archive
— cannot be anchored. The lookup is skipped with a warning rather than raising, since the portal
override is optional by design.

---

## R5 — Which checks belong to the production-critical subset?

**Question.** FR-017 names a minimum. The subset has to be small enough that it never blocks a boot
for a stylistic reason.

**Checked.** The existing checks in `fairdm/conf/checks.py` cover database, cache, secret key,
allowed hosts, debug and Celery, with ids `fairdm.E001`, `E003`–`E005`, `E100`–`E101`, `E200`,
`E300`–`E301`. Django separately supplies `security.W009` (secret key, catching the
`django-insecure-` prefix), `security.W008`, `W012`, `W016` and `W018`.

**Decision.** The subset is exactly: a production-grade database is configured; a shared cache is
configured; the secret key is neither absent nor insecure; allowed hosts is non-empty and not
wildcarded; debug is off. Celery stays outside it — a portal may legitimately run without a worker,
and blocking a boot on it would make the guard something operators route around.

**Note on severity.** Django reports the secret key as a *Warning*, so a subset built only from
Django's own checks cannot block. FairDM's own error-severity check for the same condition is
therefore kept rather than delegated, and it must test for absence and for the insecure prefix.

---

## R6 — What does removing the fallback secret key break?

**Question.** FR-004 forbids a working default for a security-critical value.

**Checked.** `fairdm/conf/environment.py:15-18` declares `DJANGO_SECRET_KEY` with a literal default,
`:19` declares `DJANGO_SITE_DOMAIN` as `localhost:8000`, and `:9-10` declare superuser credentials.
`security.py:19` reads the key and `:23` composes `ALLOWED_HOSTS` from the domain. Removing a default
from a `django-environ` `Env` declaration makes the read raise `ImproperlyConfigured` when the
variable is absent.

**Decision.** The declarations lose their defaults. The failure this produces is a bare
`ImproperlyConfigured` from `django-environ`, which names the variable but gives no guidance, so the
reads are wrapped to produce FairDM's own message naming the variable and what to set it to. In
development the same variables need values, so FairDM's `development.py` supplies a clearly-marked
development-only key and a `localhost` host list — the value moves from the shipped baseline, where
it silently applies to production, into the development layer, where it cannot.

**Consequence.** A portal that runs in production without setting these stops working on upgrade.
That is the point of the change and it belongs in the release notes, not in a compatibility shim.

---

## R7 — Is a second validation path still needed anywhere?

**Question.** FR-018 forbids one, and D5 deletes `validate_services()`.

**Checked.** `grep -rn validate_services` over `fairdm/` and `tests/` returns 54 hits: the definition
and its own warning string in `checks.py`, one comment in `setup.py`, and 51 references across
`tests/test_conf/test_checks.py` and `tests/test_conf/test_setup.py`. No production code calls it.
`docs/portal-administration/configuration-checks.md:200-206` documents migrating off it.

**Decision.** Delete the function, the comment, the documented migration path, and every test
reference. The test classes involved (`TestDevelopmentSetup`, `TestProductionSetup`,
`TestStagingSetup`) also exercise `setup()` itself, so removal is a surgical edit inside them rather
than deleting the classes — except `TestStagingSetup`, which goes entirely with the staging profile.

---

## R8 — What is in the way of removing staging?

**Checked.** `fairdm/conf/staging.py` (25 lines), the profile allowlist at `setup.py:58`, the
override map at `setup.py:135-138`, nine references in `checks.py`, one apiece in eight
`settings/*.py` modules (all in docstrings), two in `addons.py`, one in `conf/__init__.py`, and 28
in `tests/test_conf/test_checks.py`. `docs/portal-development/configuration.md` describes it.

**Decision.** Remove all of them. The docstring references are part of the same sweep that fixes the
stale `local.py` mentions, since both name modules that will not exist.

---

## R9 — Does the environment-file convention change?

**Question.** FR-006 requires the entry point to document which environment files it reads.

**Checked.** `setup.py:78-101` reads `stack.env`, then `stack.<environment>.env`, then an explicit
`env_file=` argument, the last with `overwrite=True` and the first two respecting variables already
set. `stack.env` is also the file the absent container stack refers to.

**Decision.** Keep the mechanism and the precedence exactly as they are, and document them. Renaming
to `.env` is a portal-visible break that buys only convention, and R26 will decide the container
story's filenames — settling the name here would pre-empt it. Recorded so the question is not
reopened without cause.
