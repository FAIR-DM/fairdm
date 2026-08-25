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
| S3 PLAN | in progress | |
