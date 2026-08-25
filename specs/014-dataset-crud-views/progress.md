# Progress — FS-014, managing a dataset through the portal

## Spec gate — approved 2026-08-25

Sam approved the rewritten specification in session. Approved surface: `spec.md` at
`014-dataset-crud-views`, epic #288, stories #289–294, draft PR #295.

Two rulings recorded at the gate:

- **PR #287 is superseded by this feature and closes when this pull request lands.** It repaired the
  descriptions and key-dates pages for datasets and samples; this feature replaces the dataset half
  outright. Sam's words: it "should never have been done". #280 stays open for the sample pages,
  which this feature does not reach.
- Three findings routed out rather than absorbed: #296 (takedown requests for published data), #297
  (the project deletion guard keyed on visibility rather than publication), #298 (the keyword
  rebuild).

## Stages

| Stage | State | Note |
|---|---|---|
| A1 ASSESS | done | Four standalone views, built and tested, under two address prefixes, linked from nothing. |
| A2 GRILL | done | Seven adjudications, recorded in `decisions.md`. |
| S1 SPECIFY | done | `spec.md` rewritten in place: 67 requirements, 6 stories, 10 success criteria. |
| S2 SETUP | done | Epic #288, stories #289–294, draft PR #295. |
| Spec gate | approved | 2026-08-25, in session. |
| S3 PLAN | done | Research, plan, greenfield task list, reconciliation: 85 tasks, 19 satisfied, 66 open. |
| S3R DESIGN REVIEW | done | One round, nine findings, all verified and applied; six reconciliation ticks withdrawn. |
| Plan gate | filed | Recorded on the pull request for veto; approved in session 2026-08-25. |
| S4 IMPLEMENT | in progress | Foundations `ecad5f9`. US-3 update page: 13 tasks closed on evidence. Ledger now 32 satisfied, 53 open. |

## Carried forward into US-6

The update page does not yet declare that the record's pages offer a listing and a deletion, and
does not name the deletion page's permission, because the deletion page does not exist. Naming it
now would fail at import. The deletion story adds both, and the project's equivalent page is the
shape to copy.
