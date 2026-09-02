# Progress — FS-015, browsing a portal's samples and measurements by type

## Spec gate — approved 2026-09-01

Sam approved in session, with no amendments. Approved surface: `spec.md` and `decisions.md` at
`015-browsing-portal-samples`, epic #315, stories #316–321, draft pull request #322.

All four decisions put to him at the gate stand as written:

- A listing shows published data only, identically for every viewer.
- A record's own dataset decides its presence, and an unpublished referent loses its name as well
  as its link.
- Listing URL names move to the `<name>-list` convention, away from `<slug>-collection`.
- Retiring the dead code in `fairdm/contrib/collections` is US-6, not an implicit tidy.

The accepted consequence was stated at the gate and accepted: portals upgrading to this version see
empty listings until an administrator publishes a dataset.

## Stages

| Stage | State | Note |
|---|---|---|
| S0 INTAKE | done | Eight questions. The feature statement was confirmed verbatim on 2026-09-01. |
| S1 SPECIFY | done | `spec.md`: 6 stories, 60 requirements, 10 success criteria, 9 clarifications. `decisions.md`: D1–D8. FR-066 of `014-dataset-crud-views` annotated in place as superseded. |
| S2 SETUP | done | Epic #315, stories #316–321, draft PR #322. Branch `015-browsing-portal-samples`. |
| Spec gate | approved | 2026-09-01, in session, no amendments. |
| S3 PLAN | done | `plan.md`, `research.md` (13 items), `data-model.md`, `quickstart.md`, `tasks.md` (66 tasks across 6 stories). `feature-state.json` generated, all tasks `todo`. Baseline `tests/test_registry/` (243 tests) confirmed green before any change. |
| S3R DESIGN_REVIEW | next | |

## Where the boundaries were drawn

Three of the eight intake answers moved the boundary and are worth finding here rather than in the
clarification list:

- The feature owns `fairdm/contrib/collections` outright. Nothing in that app counts as delivered.
- It takes part of R17: each type declares the fields its search covers, the record's name is
  searched where nothing is declared, and every field searched by default is indexed. Ranking,
  typo tolerance and cross-type search stay with R17.
- The published flag is set in the Django admin and nowhere else, which supersedes FR-066 of
  `014-dataset-crud-views`. The recommendation at intake was a control on the dataset's own
  attributes page; it was declined, and D2 records why the more awkward placement is the right one
  until R22 designs the workflow.
