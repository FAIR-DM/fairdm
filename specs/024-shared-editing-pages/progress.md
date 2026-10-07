
## 2026-10-07T19:10:43Z · Planner · plan

Did: wrote research.md, plan.md, tasks.md (12 tasks over 4 stories) and the ledger, on the branch brought up to date with origin/main at 9abbd75a. Corrected one assumption in spec.md that named #401, which has since been closed.
Verified: lint, types, tests, build, conformance and docs all green on c6b27d7a before planning.
Next: design review, one reviewer with three lenses.
Watch: #383 is open and touches the overview template and two user guide pages.

## 2026-10-07T19:26:54Z · Implementer US1 · T001

Did: wrote tests/test_core/test_editing.py: TestRegistration, TestAccess, TestManageMenu, TestEditDetails, TestEditDescriptions and TestOverviewPrompts, each parametrised over a project, a dataset, a demo sample type (RockSample) and a demo measurement type (ExampleMeasurement).
Verified: `uv run pytest tests/test_core/test_editing.py -q -n0` fails where it should, since project:edit, dataset:edit and the shared descriptions pages do not exist and the old project, dataset and sample pages still do. `uv run pre-commit run --all-files` passes.
Next: T002, the shared module, the Manage menu and the removals.
Watch: the sample's old `edit` page already sits at the new address, so the sample edit cases that pass today pass against the old page.
