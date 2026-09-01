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
| S3R DESIGN_REVIEW | returned | Changes requested, risk high. 14 findings, all dispositioned; design documents corrected. See `design-review.md`. |

## S3R — dispatched and returned, 2026-08-26

The first attempt was blocked: the dispatch mechanism was absent from the session. It was not worked
around — the standing rule is that a failed dispatch is a wait, never a substitution, and it names
the design review specifically. The mechanism returned and the review ran on the second attempt,
against the branch at `05adcf2`, with all three method receipts verified before and after.

The verdict was changes requested at high risk, and it earned it: one critical finding is a conflict
inside the approved specification itself, and two high findings would each have caused silent data
loss or an unexecutable task. Corrections are recorded as D-019 to D-022 and folded through
`spec.md`, `research.md`, `plan.md` and `tasks.md`. `design-review.md` carries the dispositions.

Two claims the reviewer checked and cleared, recorded so they are not re-litigated: the rich-choices
metaclass research is correct against Django 5.2.16's own source, and the nested transaction in the
upgrade is a savepoint inside the migration's transaction, so FR-017's all-or-nothing guarantee
holds on PostgreSQL.

## Open with Sam

- **D-019, the narrowed retirement.** The approved specification required the retired library gone
  from the migrations as well, which is the squash D-007 refused on Sam's instruction. The two
  cannot both hold. The retirement is narrowed to the running framework and the distribution stays
  declared, with a stated reason, until the squash. This changes FR-019, SC-004 and US-5.
- **D-016, the Django 5.1 drop.** The vocabulary package requires Django 5.2 or newer; FairDM
  declares 5.1 and its required checks test both. Narrowing needs an edit to
  `.github/workflows/tests.yml` and a change to the repository's required checks, neither of which
  this run makes on its own. T019 is blocked on it, and with it every story except US-1.
