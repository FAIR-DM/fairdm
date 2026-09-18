# Design review — FS-016

One reviewer, three lenses (specification compliance, architecture, security), one round, against
the branch at `05adcf2`. **Verdict: changes requested**, risk high — 14 findings, 1 critical, 2 high,
7 medium, 4 low. Every finding is dispositioned below; the design documents carry the corrections.

## What changed as a result

Four corrections are structural, and each has a decision record.

**D-019 — the retirement is narrowed to the running framework.** As approved, the spec required the
retired library gone from the migrations, which is the squash D-007 refused; the two were mutually
exclusive and neither the reviewer nor the plan could satisfy both. Thirteen migration files across
six applications name the library, twelve through a graph dependency. A graph dependency needs the
application *installed*, not merely importable, so uninstalling it fails a migrate from empty at
graph-load time and takes the test suite with it. The library therefore stops being imported,
referenced or drawn on by anything, and its distribution and installed-application entry stay —
each carrying a comment saying why — until the deferred squash removes them. FR-019, SC-004 and
US-5 are reworded to match.

The alternative, editing the graph edges and lazy references in all thirteen files, was rejected on
two counts: the historical state would then claim the keyword join tables point at the new concept
table while the live portal's tables still point at the old one, and the upgrade could no longer
read the old concept rows through historical models. Both land on the riskiest migration in the
change, against a live database, for a cleanup the squash performs safely later.

**D-020 — the concept fields are added under temporary names and renamed.** `research.md` §6
assumed the new field would generate a through table under a different name, so old and new could
coexist. It generates it on Django's standard `<owner_table>_<field>` — the same table the current
field uses. Converting in place would alter the existing join table's concept column to point at the
new concept table while keeping key values belonging to the old one, silently re-crediting
contributions against unrelated concepts. SC-003 could not have held.

**D-021 — the upgrade migration lives in the contributors application.** The plan placed it in
`fairdm.core`, which is not an installed application and has no migrations directory. Its
dependencies and `run_before` are now stated rather than left implicit.

**D-022 — the mounted autocomplete route requires a signed-in user.** It is a new trust boundary in
every portal, over a search the research already found to be effectively unindexed.

## Dispositions

| Finding | Severity | Disposition |
|---|---|---|
| SPEC-001 — the retirement story cannot complete | critical | Accepted. Spec, plan and research amended; D-019. |
| ARCH-001 — the in-place many-to-many conversion loses data | high | Accepted. `research.md` §6 corrected; D-020; T032, T040, T045 and a new T046a. |
| SPEC-002 — the data migration's host application does not exist | high | Accepted. D-021; plan §5, T045, project structure. |
| SPEC-003 — `Sample.status` does produce a migration | medium | Accepted. T016 reworded, T011 carries the column width. |
| SPEC-004 — two required warnings had tests but no implementation | medium | Accepted. New T021a registers FairDM's own system check. |
| SPEC-005 — `research.md` §4 was read from an unreleased sibling checkout | medium | Accepted. §4 states its source and its limit; new T019a re-checks against the pinned version. |
| SEC-001 — the mounted autocomplete route had no access decision | medium | Accepted. D-022; T021 carries the requirement and the route smoke test. |
| SEC-002 — the base address default mints localhost concept identities | medium | Accepted. Folded into T021a's check rather than a separate mechanism. |
| ARCH-002 — the migration loads vocabularies through live models | medium | Accepted in part. The nested transaction is fine and FR-017 holds; the other two consequences are recorded in `research.md` §6 and the migration now loads only when the vocabulary is absent. |
| ARCH-003 — the upgrade belonged to no dispatchable story | medium | Accepted. US-4 owns Phase 5; plan sequencing updated. |
| SPEC-006 — the dependency check needs two configuration edits | low | Accepted into T019, along with the retained dependency's ignore entry. |
| SPEC-007 — the preamble blocked T009 instead of T019 | low | Accepted. |
| SPEC-008 — D-005 promised an architectural decision no task produced | low | Accepted. Added to T018. |
| SPEC-009 — US-1 acceptance scenario 5 had no test seam | low | Accepted as written: satisfied by construction, stated in plan §2 rather than tested. |

## Editorial

`DataciteContributorRoles` lives in `core/choices.py`, not with the other four — T010's file list
corrected. D-012's clause about writing missing definitions had no subject and is struck: all 98
terms already carry one.
