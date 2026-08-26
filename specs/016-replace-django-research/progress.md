# Progress — FS-016, controlled vocabularies replace django-research-vocabs

## Spec gate — approved 2026-08-26

Sam approved the specification in session: "The spec looks fine. Proceed with research and planning
but do not implement." Approved surface: `spec.md` at `016-replace-django-research`, epic #195,
stories #305–309, draft PR #310.

Two rulings recorded at the gate:

- **Planning only this session.** Research, plan, task graph and design review run; implementation
  does not start until Sam says so.
- **The live portal's migration state is out of bounds.** Sam declined the diagnosis offered at the
  gate. Nothing in this run inspects, reasons about, or acts on that portal's migrations, and the
  upgrade guide this feature ships is written against the framework rather than against any
  particular deployment.

## Stages

| Stage | State | Note |
|---|---|---|
| S0 INTAKE | done | Grilled in session; seven decisions recorded as D-001 to D-007. |
| S1 SPECIFY | done | `spec.md`: 5 stories, 23 requirements, 6 success criteria, 5 clarifications self-answered. |
| S2 SETUP | done | Epic #195 promoted in place, stories #305–309, draft PR #310, title lint green. |
| GATE_SPEC | approved | 2026-08-26, in session. |
| S3 PLAN | done | `research.md`, `plan.md`, 54 tasks across 5 stories, ledger created. |
| S3R DESIGN_REVIEW | blocked | The subagent spawn mechanism is absent from this session. Not substituted. |

## S3R blocked — 2026-08-26

The pre-dispatch craft-skill gate is green (`craft-review`, `craft-security`, `craft-simplify`, all
three receipts verified) and the reviewer brief is written to
`engineering-org/runs/fairdm/016-replace-django-research/brief-design-review.json`. The dispatch
mechanism itself is not available in this session.

Not worked around. The standing rule is that a failed dispatch is a wait, never a substitution, and
it names the design review specifically: routing it to an in-process subagent works technically and
takes the run out of view while it happens. The review is dispatched when the mechanism returns.

## Open with Sam

- **D-016, the Django 5.1 drop.** The vocabulary package requires Django 5.2 or newer; FairDM
  declares 5.1 and its required checks test both. Narrowing needs an edit to
  `.github/workflows/tests.yml` and a change to the repository's required checks, neither of which
  this run makes on its own. T019 is blocked on it, and with it every story except US-1.
