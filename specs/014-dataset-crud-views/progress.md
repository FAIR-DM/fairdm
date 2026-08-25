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
| S4 IMPLEMENT | in progress | Foundations `ecad5f9`. US-3 update page: 13 tasks closed on evidence. US-4 descriptions page `dfe0d70`: 8 tasks closed on evidence. US-6 deletion page `a724a5e` and follow-up: 9 tasks closed on evidence. The audit ledger had also drifted from the task ledger — five tasks closed at foundations were never moved out of its open list — so both now read 54 satisfied, 31 open — the update page's own deletion link (T067) closed here too. US-5 links `cc9bc2b` and follow-up: 10 tasks closed on evidence, 64 satisfied, 21 open. |

## Notes from US-5

The deletion page's own cancel control resolved to nothing. `MVPDeleteView`'s fallback reverses
the listing address, which that page never shows, so the shell drew the control with an empty
`href` — the exact case FR-052 forbids. `fairdm.core.project.plugins.Delete` carries a
`get_back_url` for this and the dataset's did not. Added, mirroring it, and the deletion page's
link sweep is now the same whole-page sweep the other three pages get rather than a narrowed one.

## Notes from US-6

`Measurement.sample` was `on_delete=PROTECT`. Django's collector raises against a protected row
even when that row is itself being deleted in the same operation, so a dataset holding samples
with measurements recorded on them — the ordinary shape of a dataset carrying data — could not be
deleted at all, by this page or by any other route. FR-049 requires that it can. Changed to
`RESTRICT`, which refuses the same thing at the level intended (a sample cannot be deleted out
from under a measurement that needs it) and permits the whole-record cascade.

The shell catches `ProtectedError` and turns it into the refusal its template already draws, but
not `RestrictedError`, which is a sibling under `IntegrityError` rather than a subclass. Without
handling, a dataset whose samples are measured by another dataset raised out of the deletion page
instead of refusing. Caught in `FairDMDeleteView` so the project's page is covered by the same
path; raised upstream as django-mvp#308 and to be removed when that lands.
