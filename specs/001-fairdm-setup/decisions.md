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

---

## D16 — the US-4 tamper flags, adjudicated

`forge tamper-check --base 272ef40` raised two flags, both cleared:

- **`tests/test_conf/test_setup.py`** — additive only. The range removes zero lines from the file;
  the two T109 tests are new methods on an existing class.
- **`tests/test_conf/conftest.py`** — removed `snapshot_scope`, an unused helper (zero references in
  the tree) whose docstring asserted that a *shallow*-copy diff "is how the provenance command
  attributes a setting to the layer that wrote it". D15 makes that false. It weakened no test
  because it backed none.
