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
