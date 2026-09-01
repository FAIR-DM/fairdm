# Progress — FS-015, browsing a portal's samples and measurements by type

## Stages

| Stage | State | Note |
|---|---|---|
| S0 INTAKE | done | Eight questions. The feature statement was confirmed verbatim on 2026-09-01. |
| S1 SPECIFY | done | `spec.md`: 6 stories, 60 requirements, 10 success criteria, 9 clarifications. `decisions.md`: D1–D8. FR-066 of `014-dataset-crud-views` annotated in place as superseded. |
| S2 SETUP | done | Epic #315, stories #316–321, draft PR #322. Branch `015-browsing-portal-samples`. |
| Spec gate | pending | Summoned 2026-09-01. |

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
