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
