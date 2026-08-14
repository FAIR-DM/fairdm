# Decisions — 001 portal configuration

Adjudications from the retrospective audit of 2026-08-13. Each entry records what the previous
version of the spec said, what the code actually did, which way it was settled, and why. The
previous spec is in git history; this file is the reason it changed.

---

## D1 — Staging is not a supported environment


**Spec said**: three profiles — production, staging, development — with staging named in FR-008,
in the addon failure rule (FR-010), in the check clarifications and throughout the acceptance
criteria.

**Code did**: implemented all three. `fairdm/conf/staging.py` existed, `DJANGO_ENV` accepted
`staging` from a hardcoded allowlist, staging branches ran through 15 modules under `fairdm/conf/`,
and the test suite carried a `TestStagingSetup` class and 28 staging references.

**Settled**: staging is removed. FairDM ships no staging override module, and the word does not
appear in the configuration layer.

**Why**: FairDM is not willing to support a third environment. A profile that exists but is
unsupported is worse than either supporting it or not shipping it, because it ends up in someone's
deployment on the strength of being there. Under D2 the removal costs nothing in flexibility — a
portal that wants staging supplies its own module and gets the same layering as any other
environment.

**ADR:** none — a scope call, recorded in the spec and the changelog. Under ADR 0001 it is a deletion rather than a standing rule, so there is nothing for a future engineer to abide by.

---

## D2 — Override modules are selected by existence, not from an allowlist


**Spec said**: nothing about the selection mechanism, only that each environment has its own
profile module.

**Code did**: `setup.py:58` validated `DJANGO_ENV` against a hardcoded tuple and `setup.py:135-138`
mapped environments to filenames through a hardcoded dict.

**Settled**: `setup()` looks for a module named after the resolved environment. Found, it applies;
absent, nothing happens. Both hardcoded lists are deleted.

**Why**: it is one mechanism instead of two, it deletes more code than it adds, and it makes D1 free
rather than a special case. An unrecognised environment name falls through to the production
baseline, which is the safe direction — the strictest configuration — and a developer notices within
seconds because the portal behaves as if in production.

**ADR:** docs/adr/0001-environment-overrides-are-found-by-existence.md

---

## D3 — The portal's override module is anchored to its settings module


**Spec said**: nothing. No portal-level environment override existed.

**Code did**: `setup.py:68-72` captured the caller's globals and walked two directories up to derive
`BASE_DIR`, using the caller's location for nothing else.

**Settled**: a portal's override module is resolved beside its settings module — `config/production.py`
for the recommended layout — rather than at a hardcoded `config/` directory.

**Why**: both resolve identically for the recommended structure. They differ for a portal made by
`django-admin startproject`, where the settings module sits in a package named after the project.
Under a hardcoded lookup that portal's override module is never found, and because "no module means
no overrides" is legitimate, the failure is silent. The anchored rule states a promise that is true
in both layouts. The documentation still presents the recommended structure everywhere and says
plainly that it is the structure to use.

**ADR:** docs/adr/0001-environment-overrides-are-found-by-existence.md

---

## D4 — Configuration checks belong to this feature, and run in production only


**Spec said**: FR-012 required validation on Django's check framework, non-environment-aware, tagged,
aggregating all issues.

**Code did**: the check framework half was built correctly on 2026-01-20 (`dc39e83`). The same
commit stopped validation running during setup at all — *"Configuration validation no longer runs
automatically during setup"* — and dropped runtime logging to debug *"to reduce development noise"*.
Validation now happens only if someone runs `manage.py check --deploy`.

**Settled**: the checks stay inside this feature. The production-critical subset runs automatically
during setup when the resolved environment is production and prevents startup on failure. No checks
run in any other environment. The full set stays available on demand.

**Why**: the January diagnosis was right and the remedy overshot. The checks were noise in
development, where they have nothing useful to say about a machine nobody is deploying. The answer
is to stop checking where it does not matter, not to stop checking. Two findings show what the
current state costs:

- `database.py:46` falls back to SQLite when no database is configured, at `logger.debug`, with a
  comment reading *"Production will fail validation if this path is taken"*. That validation was
  `validate_services()`, which no longer runs. `cache.py:53` degrades to local-memory cache the same
  way. A production portal missing both variables starts clean on SQLite and an in-process cache.
- `environment.py:15-18` supplies a hardcoded fallback secret key, published in FairDM's source. A
  production portal that omits `DJANGO_SECRET_KEY` boots on a key anyone can read, so its sessions
  and signed cookies can be forged. Django's own `security.W009` does detect the
  `django-insecure-` prefix, but only as a **Warning** and only under `--deploy`, which nothing
  triggers.

Both become a refusal to boot. See D8 for the values themselves.

**ADR:** docs/adr/0002-configuration-checks-run-in-production-only.md

---

## D5 — `validate_services()` is deleted


**Spec said**: FR-012, from the 2026-01-20 clarification — *"The existing `validate_services()`
function MUST be replaced entirely by individual check functions"*, and *"remove the function"*.

**Code did**: deprecated it instead. `fairdm/conf/checks.py:269` is still there behind a
`DeprecationWarning`, called by no production code, kept green by 51 test references across two
files, with a migration path documented at
`docs/portal-administration/configuration-checks.md:200`. The original run's own `tasks.md` records
T026–T029 as SKIPPED.

**Settled**: delete the function, the tests that exercise it, and the documented migration path.

**Why**: the deletion was decided and simply unfinished — the skip reasons recorded against T026–T028
concern `validate_addon_module`, a different function that is genuinely still needed, and the
`validate_services` removal was carried along with them. Under D4 there is no remaining argument for
a second validation path, and a deprecated function nothing calls is a maintenance cost with no
consumer to protect.

**ADR:** none — a direct consequence of ADR 0002. One validation path follows from the checks being the validation path; it constrains nothing on its own.

---

## D6 — Container deployment leaves this feature


**Spec said**: FR-009 — the documentation must include a reference container deployment driven
entirely by environment variables.

**Code did**: nothing that works. `docker-compose.yml` builds from a `compose/` directory and reads
a `stack.env` file, neither of which is in the repository, and
`docs/portal-development/production.md` describes a `production.yml` that does not exist either.

**Settled**: FR-009 is removed. Roadmap R26 owns the deployment story.

**Why**: R26 already describes this gap in the same terms, and it advances G16 rather than G7. This
feature says how configuration reaches a portal; how a portal is shipped is a different question with
its own roadmap item.

**ADR:** none — roadmap routing. R26 owns the deployment story and says so in its own text.

---

## D7 — Addons keep a thin slice


**Spec said**: FR-010 and FR-011 covered addon configuration declaration, discovery and
documentation.

**Code did**: implemented all of it — `conf/addons.py`, the `__fdm_setup_module__` protocol,
fail-fast in production and warn-and-skip in development, with its own tests.

**Settled**: this feature owns only where an addon's settings sit in the precedence order and what a
broken addon does. What an addon may rely on, how it is discovered and how it is packaged move to
R27.

**Why**: an addon is one of the layers, so omitting it entirely would leave the precedence order —
this feature's central claim — untestable. Everything beyond its position in that order is a separate
contract that R27 is going to grow.

**ADR:** none — roadmap routing. R27 owns the addon contract.

---

## D8 — The baseline supplies no working default for a security-critical value


**Spec said**: FR-013 recommended environment variables as the canonical mechanism for secrets.
Nothing forbade a fallback.

**Code did**: `environment.py` supplies defaults for values that must not have them — a published
secret key (`:15-18`), `DJANGO_SITE_DOMAIN` defaulting to `localhost:8000` and so setting
`ALLOWED_HOSTS`, and `DJANGO_SUPERUSER_PASSWORD` defaulting to `admin`. `security.py:5` claims
*"Production/Staging: Requires SECRET_KEY, ALLOWED_HOSTS (fails fast if missing)"*, which has not
been true since `validate_services()` stopped running.

**Settled**: the baseline supplies no usable default for a security-critical value. A portal that
omits one fails.

**Why**: a default that is safe only because a check elsewhere catches it is safe only while that
check runs, and D4 documents the period in which it did not. Removing the value makes the failure
structural rather than conditional.

**ADR:** docs/adr/0003-no-working-default-for-a-security-critical-value.md

---

## D9 — One tail to the precedence order


**Spec said**: FR-007 named assignment after the `setup()` call as the primary supported override
pattern.

**Code did**: supported that, and also accepted arbitrary settings as `**overrides` keyword
arguments (`setup.py:26, 153-156`), applied at a different point in the sequence.

**Settled**: the keyword argument is removed. Assignment after the call is the only mechanism.

**Why**: two ways to do one thing, in the feature whose entire purpose is a predictable precedence
order, and they do not even apply at the same point — so the two paths differ in result for any
setting a later stage touches.

**ADR:** none — a public-interface simplification, recorded as breaking in the changelog. ADR 0001 already states that the precedence order has one tail; a second way to reach it was the defect, not a rule worth preserving.

---

## D10 — No setting needs special-case handling in the entry point


**Spec said**: nothing.

**Code did**: `setup.py:162-170` re-derives `SPECTACULAR_SETTINGS["TITLE"]` and `["DESCRIPTION"]`
from portal-supplied names after all layers have run — a Feature 011 special case living in the
entry point because there was no general way for a portal to override one FairDM-composed setting.

**Settled**: no FairDM-owned setting requires special-case handling in the entry point. This one
moves into the settings module that owns it and uses the ordinary layering.

**Why**: an entry point that grows a branch per feature is how a configuration layer becomes the
thing it was written to replace. If the layering cannot express this case, that is a defect in the
layering, not a reason for an exception.

**ADR:** none — stated as a corollary inside ADR 0001, where it belongs. On its own it is a restatement of the layering contract rather than a separate decision.

---

## D11 — Portal apps take precedence over FairDM's


**Spec said**: nothing about ordering.

**Code did**: appended portal apps to the end of `INSTALLED_APPS` (`settings/apps.py:122`). Django's
app-directories template loader returns the first match, so a portal shipping a template at the same
path as a FairDM one is ignored.

**Settled**: portal apps are registered so that the portal's templates and static files win.

**Why**: a portal overriding a framework template is the ordinary case and the current order makes it
impossible without a separate mechanism. Whatever the answer, it is a contract this specification has
to state and test rather than leave to list order.

**ADR:** docs/adr/0004-portal-apps-precede-framework-apps.md

---

## D12 — The layering is interrogable


**Spec said**: nothing.

**Code did**: `setup()` knows every layer it considered, which it found, and what each one wrote, and
discards all of it apart from a few log lines.

**Settled**: a command reports the layers in application order, each marked found or absent, and for
a named setting the layer that produced its resolved value.

**Why**: D2 makes absence a silent, legitimate outcome, which is right for the mechanism and hostile
to debugging without this. Layered configuration is acceptable when it can be asked what it did.

---

## Findings routed out of this feature

Not this feature's work, recorded so they are not lost:

- **Container deployment** → roadmap R26 (D6).
- **The addon contract** → roadmap R27 (D7).
- **`settings/logging.py:20`** constructs its own `environ.Env()` rather than using the shared
  instance from `environment.py`, contrary to `contracts/settings-sections.md`. Inside this feature's
  scope as part of the baseline audit.
- **`settings/static_media.py:115`** sets `THUMBNAIL_DEBUG = True` unconditionally in the production
  baseline. Inside this feature's scope under FR-003.
- **`settings/apps.py:271-279`** carries template residue in `DJANGO_SETUP_TOOLS` — a `development`
  block running `loaddata myapp` and calling `some_extra_func`. Inside this feature's scope under
  FR-003.
- **Stale docstrings** across `fairdm/conf/settings/*` referring to overrides in `local.py` and
  `staging.py`, neither of which exists. Inside this feature's scope under FR-002.

**ADR:** none — feature content, delivered as `manage.py show_config` and specified by FR-019 and FR-020. It constrains no future work beyond the command continuing to exist.

---

## D13 — FR-013 attributes the checks to the entry point; the entry point cannot run them


**What the spec says.** FR-013: the entry point must run the production-critical configuration
checks and must prevent startup if any fails.

**What the research found.** Django's check framework needs a populated app registry, which does not
exist at the moment `setup()` returns (research R1). `setup()` records the resolved environment and
`FairDMConfig.ready()` runs the subset and aborts the boot.

**Reading adopted.** "The entry point" means the boot path `setup()` initiates, not the function
body. The observable behaviour — a misconfigured production portal refuses to start, a development
portal starts silently — matches US-3 and SC-003 exactly, and running the checks anywhere else is
impossible rather than merely inconvenient.

**Not a licence to rewrite the spec.** FR-013 passed the spec gate, so its wording is carried to Sam
as a one-line delta at the next gate rather than corrected here.

**ADR:** docs/adr/0002-configuration-checks-run-in-production-only.md

---

## D14 — the security-critical variables lose their working defaults, not their readability


**What the audit found.** `fairdm/conf/environment.py` ships a working fallback secret key, a
`localhost:8000` site domain and an `admin` superuser password, so a production portal that sets none
of them boots on a key published in the package source.

**First plan.** Remove the defaults outright, so the read raises and names the variable (research R6,
first draft).

**Why that was wrong.** `settings/security.py` is the second module of the baseline layer and
FairDM's `development.py` is layer 2. A baseline read that raises kills the process before any
override can supply the value — taking development startup and the whole test suite with it, and
contradicting FR-014, SC-004 and US-3's third scenario. The design review caught this before it was
built (DR-001).

**Decision.** The declarations take an explicitly unusable sentinel instead of a working default.
FR-004's "no working default" holds, the environment stays resolvable, and the refusal to boot comes
from the production-critical checks under FR-013 — which is where the spec already puts it.
`ALLOWED_HOSTS` composes from truthy entries only, so an unset domain yields `[]` and the existing
emptiness check can fire.

**ADR:** docs/adr/0003-no-working-default-for-a-security-critical-value.md

---

## D15 — a layer that appends is a producer, so the provenance diff compares by value


**What US-4 built.** The provenance record diffed the settings scope by object identity: a layer
"wrote" a setting if the name was new, or if it now pointed at a different object.

**Why that is wrong.** A layer does not have to rebind a name to change a setting. `INSTALLED_APPS
+= [...]` calls `list.__iadd__`, which mutates the baseline's own list in place, so both sides of an
identity diff see the same object and conclude nothing was written. FairDM's only shipped override
layer does exactly that, for `INSTALLED_APPS` and for `MIDDLEWARE`. Verified live before the fix:
`manage.py show_config INSTALLED_APPS` under `DJANGO_ENV=development` printed a list containing
`django_browser_reload` and named `baseline` as its producer — the wrong answer, on the two settings
a portal is most likely to ask about, from the command that exists to answer exactly that question.

**Decision.** The before-snapshot deep-copies mutable containers (`list`, `dict`, `set`) and those
are compared by value; everything else is kept by reference and compared by identity, which is
correct for immutables and safe for objects whose equality is identity anyway. Copy and comparison
each fall back to identity rather than raising, so an uncopyable setting degrades the record instead
of breaking startup. Recorded as T109.

**A narrowing this makes explicit.** The record now names the layer that last *changed* a value, not
the last one to assign it: a layer that reassigns a setting to the value it already held leaves the
earlier layer named. The resolved value is the same either way, which is the question FR-020 asks.
`Provenance.producer` says so.

**ADR:** none — an implementation detail of the provenance diff, sealed inside `setup()`. Nothing downstream inherits it.

---

## D16 — the US-4 tamper flags, adjudicated


`forge tamper-check --base 272ef40` raised two flags, both cleared:

- **`tests/test_conf/test_setup.py`** — additive only. The range removes zero lines from the file;
  the two T109 tests are new methods on an existing class.
- **`tests/test_conf/conftest.py`** — removed `snapshot_scope`, an unused helper (zero references in
  the tree) whose docstring asserted that a *shallow*-copy diff "is how the provenance command
  attributes a setting to the layer that wrote it". D15 makes that false. It weakened no test
  because it backed none.

**ADR:** none — a tamper-flag adjudication, not a design decision.

---

## D17 — the `PARLER_LANGUAGES` check is applied twice, and to nothing but itself


**The problem T107 set out to fix.** A portal that narrows `LANGUAGES` — the very thing FR-012
invites it to do — is met with `ImproperlyConfigured: PARLER_LANGUAGES[1][1]['code'] does not exist
in LANGUAGES`, raised from inside django-parler, naming no FairDM setting and no remedy. The bundled
example portal hit exactly this at US-2 convergence.

**Why the check framework cannot reach it.** django-parler validates the two settings against each
other in `parler.utils.conf.add_default_language_settings`, which runs when `parler.appsettings` is
imported — that is, when the first app whose models import `parler.models` is imported, during
Phase 2 of `apps.populate()`. Django's check framework needs a populated app registry, so no
registered check can run before that. `ready()` is Phase 3, later still.

**Decision — two call sites, because neither alone covers every portal.**

1. **`setup()`, on the composed settings scope.** This is the only point ahead of *every* app's
   models. It has to be, because a portal's own apps are registered ahead of FairDM's (D11), so a
   portal shipping a translated model of its own reaches parler before `fairdm`'s AppConfig exists.
2. **`FairDMConfig.import_models()`, on the loaded settings.** This is the only point after a
   portal's post-`setup()` assignments — layer 5, the override route FR-012 names — and it still
   precedes `fairdm.contrib.identity`, whose models import parler's.

A portal that does both at once (assigns `LANGUAGES` after the call *and* ships a parler-model app)
still gets parler's own error. Closing that would mean patching parler, which is not this feature's
business.

**A narrowing worth stating.** The enforcement runs only FairDM's own `fairdm.E400`, not the whole
`Tags.translation` set. Running the tag also ran Django's translation checks, which turned
`translation.E004` — `LANGUAGE_CODE` not among `LANGUAGES` — into a refusal to boot in every
environment. That is a `manage.py check` finding about which language a site defaults to, not a
configuration FairDM refuses to start on, and FR-014 confines boot refusals to production.
`tests/test_apps.py::TestParlerLanguagesCheck::test_a_language_settings_disagreement_django_owns_does_not_block_boot`
holds the line.

**Not gated to production**, unlike the FR-013 checks. The underlying crash is not
environment-dependent — parler raises identically under `development` — so gating the *message* to
production would leave a developer with the bare traceback and nothing else. Replacing a crash with
a named error changes no environment's outcome, only what it says. Recorded as T107 and T110.

**ADR:** none — a defect fix. The check was wrong and is now right.


## D18 — an addon's settings are applied to a private copy of the scope, and that copy holds only settings


**FR-021, FR-022. Recorded at the US-6 convergence, 2026-08-14.**

`split_settings`' `include()` executes a settings module directly against whatever dictionary it is
given, so an addon that raises partway through its own setup module leaves everything it wrote up to
that point in the composed scope. FR-022 says such an addon is treated as unloadable — failing the
boot in production, warned about and skipped elsewhere — and "skipped" is not true of a scope that
kept half its writes. Layer 3 therefore applies each addon to a private scratch copy and merges it
into the caller's scope only when the module returns.

**The copy is a deep one, and only of settings.** Two separate corrections, both made at convergence:

1. **Deep, because a shallow copy shares the object `INSTALLED_APPS += [...]` mutates.** The
   implementer argued this in its report but shipped no test that distinguished the two: the fixture
   addon rebinds a name before raising, which a shallow copy already isolates. `T113` adds a fixture
   that appends to `INSTALLED_APPS` in place, and a shallow scratch scope reds it.
2. **Only settings, because merging the copy back rebinds whatever it copied.** As delivered,
   `_scratch_scope` copied every mutable container in the caller's scope — the portal's own imports
   and helpers, and `__builtins__`, which is a dict rather than a module in an imported module — and
   the success path merged all of them back over the originals. A portal that imports a list or dict
   shared with one of its own modules and appends to it after the `setup()` call would have been
   appending to a copy nothing else could see: precisely the surprise this feature exists to remove.
   Django reads uppercase names and nothing else, so the copy is confined to those and everything
   lowercase stays in the scratch scope by reference, which makes merging it back a no-op. `T111`.

**An internal signature changed to keep the error message useful.** `discover_addon_setup_modules`
and `load_addons` return `(addon_name, path)` pairs rather than bare paths, so a failure applying a
module can still name the addon it came from. This is internal to `fairdm.conf` with one consumer
and does not touch the `__fdm_setup_module__` protocol, which R27 owns.

**ADR:** none — the isolation an addon's settings get is part of the addon contract, which R27 owns. Recorded here so R27 inherits the reasoning rather than rediscovering it.


## D19 — the two vacuous skipped addon tests are replaced, not re-skipped


**Recorded at the US-6 convergence, 2026-08-14. `forge tamper-check` flag on `tests/test_conf/test_addons.py`.**

Three pre-existing tests in `test_addons.py` were changed, and all three are strengthenings:

- `test_broken_addon_fails_fast_in_production` asserted `pytest.raises(Exception)` around executing a
  generated settings module, which any unrelated failure satisfies. It now requires
  `ImproperlyConfigured` and that the message names the addon (T097).
- `test_addon_with_invalid_module_fails_gracefully_in_development` and
  `test_addon_without_setup_module_logs_warning` were both `@pytest.mark.skip`, reason "Windows path
  escaping issue in dynamically generated settings file", and both bodies began with a bare `pass`
  before unreachable code — so each asserted nothing on any platform, including the one CI runs on.
  Both are rewritten against the `settings_module` fixture, which builds the module for them and
  removes the escaping the skip was about (T099, T112).

The warnings are observed by patching the logger call rather than through `caplog`:
`tests/settings.py` sets `disable_existing_loggers`, which silently defeats `caplog` for any logger
created before Django's settings load. That convention was already established in
`test_setup.py::TestPortalOverride`.

**ADR:** none — a tamper-flag adjudication, not a design decision.



---

## D20 — the feature-level tamper flags, adjudicated

**Recorded at convergence, 2026-08-14.** `forge tamper-check --base 4bae1d7` flags five
pre-existing test files: `tests/settings.py`, `tests/test_conf/conftest.py`, and the `test_addons.py`,
`test_checks.py` and `test_setup.py` modules. D16 and D19 cleared two of these per story; this entry
covers the feature diff as a whole.

**No test was weakened.** Across all five files the diff adds 139 assertions and removes 13, adds
zero `@pytest.mark.skip` decorators, and removes two — the vacuous skipped addon tests restored under
D19. `tests/settings.py` and `conftest.py` are pure additions with no assertion change.

**The one deletion that needed checking** is `test_checks.py`, which loses 418 lines against 263
added. Three whole classes go: `TestDevelopmentSetup`, `TestProductionSetup` and `TestStagingSetup`.
`TestStagingSetup` goes with the staging profile under D1. The other two were the tests of
`validate_services()`, deleted under D5 — but several of them asserted behaviour that outlives the
function they were written against, and deleting those without replacement would have dropped real
guarantees while the gate stayed green.

They were not dropped. The coverage moved into modules that mirror the source tree per Article X, and
grew doing so: `tests/test_conf/test_environment.py` for the security-critical variables,
`test_development.py` for the development override, and `tests/test_conf/test_settings/` with a module
per baseline concern. `test_production_requires_secret_key` is now four tests across
`test_environment.py` and `test_checks.py`, and the production boot refusal itself is tested directly
against `SystemCheckError` rather than through the deleted function.

**ADR:** none — a tamper-flag adjudication, not a design decision.


---

## D21 — the boot refusal keys on the composed settings, not on the name "production"

**Recorded at S6 review, 2026-08-14.** The review found that `FairDMConfig._check_production_configuration()`
gated on `resolved_environment() != "production"` — an exact string match. Reproduced against the
bundled portal: `DJANGO_ENV=Production`, `DJANGO_ENV=prod` and `DJANGO_ENV=""` each booted cleanly
with an empty `SECRET_KEY`, `ALLOWED_HOSTS = ["*"]` and no database configured. `DJANGO_ENV=production`
refused, naming four failures. The layering was right in every one of those runs — no override file
exists for any of those names, so the strict baseline stood. Only the refusal was bypassed.

**What went wrong is that two mechanisms disagreed about what production means.** Layer selection
decides it by file existence (D1, ADR 0001); the boot refusal decided it by string equality. The
combination is the worst available: a typo gets production's settings and development's leniency, and
nothing says so. ADR 0001's own prose — "a developer notices within seconds because the portal
behaves as if in production" — was false for exactly this path.

**The refusal now stands down only for an environment FairDM ships a non-production override module
for**, which today means `development` alone, expressed as `apps.NON_PRODUCTION_ENVIRONMENTS`. Every
other name is a production deployment and is checked as one. A portal supplying its own `staging.py`
is included: layer 1 is still the production baseline underneath it, and a staging box is a
deployment.

The spec's own wording caused this. FR-013 and FR-014 were written as "when the resolved environment
is production" and "in any other environment", which assumes `DJANGO_ENV` holds one of two values —
the assumption the existence-probe design explicitly abandoned. Both are amended to name the composed
settings rather than the string, along with SC-003. The behaviour Sam gated is unchanged in the two
environments the spec discussed, and now holds for the ones it did not.

**Two in-scope residue items found in the same review, both under FR-003** (baseline modules state
what they own and carry no environment branch or scaffold):

- `settings/apps.py` — `DJANGO_SETUP_TOOLS` carried a `development` block running `loaddata myapp`
  and `django_setup_tools.scripts.some_extra_func`, neither of which exists. Copied from the template
  FairDM was scaffolded from. Removed.
- `settings/static_media.py` — `THUMBNAIL_DEBUG = True` unconditionally in the baseline. easy-thumbnails
  re-raises rather than degrading to a blank image when this is on, which turns a missing source file
  into a 500 in production. Off in the baseline, on in `conf/development.py`.

**ADR:** docs/adr/0002-configuration-checks-run-in-production-only.md — amended rather than added to.
The exemption is now stated in terms of the shipped override modules, and the corrected mistake is
recorded in its Why section so it is not reintroduced.
