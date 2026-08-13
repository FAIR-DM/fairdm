# Implementation plan — 001 portal configuration

**Spec**: `spec.md` · **Research**: `research.md` · **Decisions**: `decisions.md`
**Epic**: #80 · **Stories**: #130 #131 #132 #135 #133 #134 · **PR**: #136

## Technical context

Django 5.2/6.0 on Python 3.12/3.13, Poetry, pytest with `pytest-django`. The configuration layer is
`fairdm/conf/`, composed with `django-split-settings` and `django-environ`. It is imported by a
portal's settings module, which means every part of it runs before Django's app registry exists —
the single constraint that shapes most of this plan (research R1).

Surface this feature owns:

```
fairdm/conf/
├── __init__.py          public re-export of setup()
├── setup.py             the entry point: environment, env files, layer composition
├── environment.py       the shared Env declaration and its defaults
├── settings/            the production baseline, one module per concern
├── development.py       FairDM's only shipped override module
├── checks.py            configuration checks
├── addons.py            addon discovery and settings contribution
├── orbit.py             observability dashboard access policy
└── urls.py              the shipped URL baseline
fairdm/apps.py           FairDMConfig.ready() — where checks execute
tests/test_conf/         the test package mirroring the above
docs/portal-development/configuration.md
docs/portal-administration/configuration-checks.md
```

## Constitution check

- **Article I (test-first)** — every task pairs a test with its change; the reconciliation rule for
  this feature is stricter still, so a behaviour with no test is unfinished by definition.
- **Article X (test structure)** — `tests/test_conf/` mirrors `fairdm/conf/`, one module per source
  module, `Test<Subject>` classes within. The existing package already follows this; new modules
  extend it rather than introducing a parallel layout.
- **Article II / III (simplicity, anti-abstraction)** — this plan removes two mechanisms (the
  `**overrides` kwarg, the staging profile) and one special case (`SPECTACULAR_SETTINGS` in the
  entry point). Nothing here adds an abstraction layer; the provenance record is a list of
  dictionaries, not a settings-object wrapper (research R2).
- **Article V (security)** — FR-004 and the production-critical subset are this feature's security
  content. Removing shipped fallbacks for secret material is the substantive change.
- **Article VI / XVII (documentation)** — a single configuration page is a first-class deliverable
  (FR-023, FR-024), not a follow-up.
- **Article XIV / XV (configuration over plumbing, production-grade defaults)** — the feature is
  the direct expression of both. Article XV's "container-friendly, 12-factor-style configuration via
  environment variables" is satisfied by the layering; the container stack itself is R26.

No article requires an exemption.

## Approach

Six stories, delivered in three phases. The first phase is foundational and sequential because
everything else composes over it; the rest can proceed independently once it lands.

### Phase 1 — the layering (US-2, then US-1)

US-2 establishes the mechanism and US-1 makes the baseline honest, in that order, because the
baseline audit is expressed as "this value moves to the development layer", which needs the layer to
exist.

1. Replace the profile allowlist and the override map in `setup.py` with an existence probe for
   `fairdm/conf/<environment>.py`, then the same probe for the portal's directory, captured before
   `__file__` is overwritten (research R4).
2. Delete `staging.py` and every reference to staging (research R8).
3. Remove the `**overrides` keyword argument; assignment after the call is the only tail.
4. Move the `SPECTACULAR_SETTINGS` finalisation out of `setup.py` into `settings/api.py`.
5. Audit the baseline: no module branches on the environment, no security-critical value carries a
   working default (research R6), `THUMBNAIL_DEBUG` and the `DJANGO_SETUP_TOOLS` template residue
   go, docstrings stop naming `local.py` and `staging.py`, `settings/logging.py` uses the shared
   `Env`.
6. Recompose `INSTALLED_APPS` so portal apps precede FairDM's (research R3).

### Phase 2 — refusing to start (US-3) and interrogation (US-4)

**Not independent.** US-3, US-4 and US-6 all rewrite the same layer-composition block in
`setup.py` — the resolved-environment record, the snapshot-and-diff around each `include()`, and the
addon layer's position. They run sequentially in that order, or in one worktree, rather than in
parallel branches that collide on the file the whole feature turns on. US-5 is verification-only and
runs last, after item 4 has removed the `SPECTACULAR_SETTINGS` special case it asserts is gone.

7. Record the resolved environment where `FairDMConfig.ready()` can read it; run the
   production-critical subset there and raise on any error, aggregating every failure into one
   message (research R1, R5).
8. Delete `validate_services()`, its 51 test references and its documented migration path
   (research R7).
9. Capture the per-layer provenance record in `setup()` by diffing the scope around each
   `include()`, and add the management command that reports it (research R2).

### Phase 3 — the remaining contracts (US-5, US-6)

10. Prove the override contract across every settings module, and prove that no setting needs
    special-case handling now that item 4 has landed.
11. Fix the addon layer's position in the order and its production/non-production failure split, and
    leave everything else about addons to R27.

### Documentation, throughout

`docs/portal-development/configuration.md` is rewritten to cover the entry point, the five layers,
the environment variable, the environment files, the check behaviour and the interrogation command,
using the recommended project structure in every example.
`docs/portal-administration/configuration-checks.md` loses the migration path and gains the
production-boot behaviour.

## Risks

| Risk | Handling |
|---|---|
| Removing the fallback secret key and site domain stops an existing portal starting | Intended. Release-note item; development values move into `development.py` so the development experience is unchanged |
| Reordering `INSTALLED_APPS` may surface a portal template that was silently inert | Intended, and the point of FR-005. Called out in the PR's risk section |
| Removing `**overrides` breaks any portal passing settings that way | Documented replacement exists and already works |
| Raising from `ready()` blocks every management command on a misconfigured production box | Accepted, documented (research R1). The remedy is always to set the variable |
| The staging removal touches 15 modules, mostly docstrings | Mechanical, and verified by a grep gate in the story's tests |

## Out of scope

The container stack (R26), the addon contract (R27), a staging profile, and the environment-file
naming convention (research R9 — kept as-is deliberately).

## Task generation

`tasks.md` is written against this plan and `spec.md` **as though the repository were empty**, then
reconciled against the code in a separate pass. A task closes only with both a code citation and a
passing test that exercises it; anything satisfied by code alone stays open with the test as its
remaining work.
