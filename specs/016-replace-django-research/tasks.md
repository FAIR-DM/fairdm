# Tasks — FS-016: Controlled vocabularies replace django-research-vocabs

**Plan**: `plan.md` · **Research**: `research.md` · **Decisions**: `decisions.md`

Article I applies to every task that changes behaviour: the failing test comes first. Tasks marked
**[P]** may run in parallel with their siblings; everything else is sequential within its phase.

**T019 is blocked on Sam's ruling on D-016** (dropping Django 5.1). Phase 1 and every US-1 task run
without it.

---

## Phase 0 — Foundations (sequential, before any story)

| id | task | files |
|---|---|---|
| T001 | Test the rich-choices metaclass against Django's contract: `.choices` emits two-tuples, `.labels`/`.values`/`.names` unchanged, a member exposes `value`, `label` and `definition`, and `gettext_lazy` survives on both text fields | `tests/test_utils/test_choices.py` |
| T002 | Implement the metaclass and the `TextChoices` base alongside the existing `Visibility` | `fairdm/utils/choices.py` |
| T003 | Test that a member renders all three parts from a template, and that a definition is reachable from a stored value alone | `tests/test_utils/test_choices.py` |
| T004 | Implement the `definitions()` mapping and the template filter that resolves a stored value to its definition | `fairdm/utils/choices.py`, `fairdm/utils/templatetags/` |
| T005 | Test that a set declared with a per-record-type subset returns only that subset's choices | `tests/test_utils/test_choices.py` |
| T006 | Implement subset declaration and the choices accessor the generic models consume | `fairdm/utils/choices.py` |

---

## Phase 1 — US-1: Closed metadata terms explain themselves (P1, #305)

Independent of every other story. No data migration.

| id | task | files |
|---|---|---|
| T007 [P] | Test `SampleStatus`: five members, values unchanged (`available`, `in_use`, `stored`, `destroyed`, `unknown`), each with the definition it carries today | `tests/test_core/test_sample/test_models.py` |
| T008 [P] | Test `DescriptionTypes`, `DateTypes` and `IdentifierTypes`: member counts of 17, 17 and 10, stored values unchanged, definitions present, and each per-record-type subset matching the collection it replaces | `tests/test_core/test_choices.py` |
| T009 [P] | Test `DataciteContributorTypes`: 14 members, and the two groupings resolving to real members — the collections they replace are dangling today | `tests/test_core/test_choices.py` |
| T010 | Convert the five vocabulary classes to rich-choices classes, carrying every label and definition across verbatim. `DataciteContributorRoles` lives in `choices.py`, not with the other four | `fairdm/core/vocabularies.py`, `fairdm/core/choices.py` |
| T011 | Point `Sample.status` at `SampleStatus` as a plain `CharField(choices=SampleStatus.choices, max_length=9, default="unknown")`, matching the width the frozen state already carries so the column is unchanged | `fairdm/core/sample/models.py` |
| T012 | Repoint the generic description, date and identifier models at the new subsets | `fairdm/core/project/models.py`, `dataset/models.py`, `sample/models.py`, `measurement/models.py`, `contrib/contributors/models.py` |
| T013 | Repoint the sample status filter, which already reads `choices` rather than concept rows | `fairdm/core/sample/filters.py` |
| T014 | Repoint the DataCite contributor-type export mapping and its name-agreement test | `fairdm/core/project/transforms.py` |
| T015 | Delete `DatasetDescriptions`, which nothing outside its own definition refers to | `fairdm/core/choices.py` |
| T016 | The description, date and identifier `type` columns produce no migration — their `choices` pairs are unchanged. `Sample.status` produces exactly one `AlterField`, swapping the retired library's field class for a plain `CharField`: the class path and its deconstructed arguments both change even though the column and its values do not. Generate that one and confirm `makemigrations --check` is then clean across all apps | `fairdm/core/sample/migrations/` |
| T017 | Surface definitions in the templates that render these fields, so a reader sees what a term means | `fairdm/**/templates/` |
| T018 | Document the rich-choices mechanism as a public surface, with a working example (Article VI), and record the closed-set rule as an architectural decision (D-005) | `docs/portal-development/`, `docs/adr/` |

---

## Phase 2 — US-2: Vocabularies ship and load (P1, #306)

Blocks US-3 and US-4.

| id | task | files |
|---|---|---|
| T019 | **Blocked on D-016.** Narrow the Django constraint to `>=5.2` and add `django-controlled-vocabularies` and `django-tomselect`. Keep `django-research-vocabs` with a comment naming D-019, and move it to `[tool.deptry.per_rule_ignores].DEP002` once nothing imports it. Add `django-tomselect` to that same list — it is a settings-string dependency FairDM never imports — add `django-controlled-vocabularies = "controlled_vocabularies"` to `package_module_name_map` and drop the stale `django-research-vocabs` entry there. `deptry` green | `pyproject.toml`, `poetry.lock` |
| T019a | With the pinned version installed, re-check the six claims `research.md` §4 makes about the package against `site-packages`, since they were read from an unreleased sibling checkout. Correct §4 or the plan before Phase 2 proceeds | `specs/016-replace-django-research/research.md` |
| T020 | Test that a portal missing the autocomplete route, the middleware or a loaded vocabulary reports the expected warning and still starts | `tests/test_conf/test_settings/` |
| T021 | Add the settings the package requires: both apps installed, the middleware, the base address, and the autocomplete route mounted behind a login requirement (D-022), with the one route smoke test Article XVI requires | `fairdm/conf/settings/apps.py`, `urls.py`, `tests/test_conf/` |
| T021a | Register FairDM's own system check: name the missing vocabularies **and** the `load_vocabularies` command (FR-010), warn when the portal-wide keyword setting is empty (FR-014), and warn when `CONTROLLED_VOCABULARIES_BASE_URI` is unset or still the package's localhost default. The package's own check covers none of the three | `fairdm/conf/checks.py` |
| T022 | Test the loader against a fresh database: the roles vocabulary arrives with all 29 concepts, their labels, definitions and four collections | `tests/test_management/test_load_vocabularies.py` |
| T023 | Author `fairdm-roles.ttl` from the current `FairDMRoles`, carrying every definition and grouping | `fairdm/vocabularies/fairdm-roles.ttl` |
| T024 | Implement `load_vocabularies`, defaulting to every shipped file, passing `--dry-run` through | `fairdm/management/commands/load_vocabularies.py` |
| T025 | Test that a second run creates no duplicates and that an edited definition updates in place | `tests/test_management/test_load_vocabularies.py` |
| T026 | Test the read-only admin: schemes and concepts are listable and not editable | `tests/test_admin.py` |
| T027 | Register the read-only admin, replacing what the retired library provided | `fairdm/admin.py` |
| T028 | Remove the retired library's `preload` step from the always-run setup tooling | `fairdm/conf/settings/apps.py` |
| T029 | Ensure the package's vocabulary files are included in the built distribution, and assert it | `pyproject.toml`, `tests/` |
| T030 | Document loading vocabularies as a setup step, with the command and its dry run | `docs/` |

---

## Phase 3 — US-3: Contribution roles are concepts (P1, #307)

| id | task | files |
|---|---|---|
| T031 | Test that roles assigned to a contribution are concepts, expose a definition, and that a concept a contribution refers to cannot be deleted | `tests/test_contrib/test_contributors/test_models.py` |
| T032 | Add the concepts field over the roles vocabulary as `roles_concepts` alongside the existing `roles`, and generate the migration that creates its through table. The old field is dropped and this one renamed in Phase 5 — an in-place conversion would re-point the existing join table at the new concept table while keeping the old table's key values (D-020) | `fairdm/contrib/contributors/models.py`, `contributors/migrations/` |
| T033 | Delete FairDM's own membership-enforcing signal receiver, now duplicated by the field's own | `fairdm/contrib/contributors/receivers.py` |
| T034 | Test that the receiver's rejection behaviour still holds after deletion, through the field | `tests/test_contrib/test_contributors/test_receivers.py` |
| T035 | Repoint the contribution form, the role narrowing in two admin classes, and the role lookups in helpers and the fake-data command | `contrib/contributors/forms/contribution.py`, `core/sample/admin.py`, `core/measurement/admin.py`, `contrib/contributors/utils/helpers.py`, `management/commands/generate_fake_data.py` |
| T036 | Repoint the concepts table renderer, which dispatches on the old field class | `fairdm/contrib/collections/tables.py` |

---

## Phase 4 — US-4: Keywords are concepts, scoped (P2, #308)

| id | task | files |
|---|---|---|
| T037 | Test the keyword setting: named vocabularies scope what is offered, and naming none warns while still starting | `tests/test_conf/test_settings/` |
| T038 | Add the portal-wide keyword setting; delete `FAIRDM_DATASET["keyword_vocabularies"]` and `FAIRDM_PROJECT["keywords"]` | `fairdm/conf/settings/addons.py` |
| T039 | Test keywords on all five models: concepts with labels and definitions, and a referenced concept refusing deletion | `tests/test_core/`, `tests/test_contrib/test_identity/` |
| T040 | Add the concepts field as `keywords_concepts` on the shared base and on the identity model, alongside the existing `keywords`, and generate the five migrations that create the new through tables. Dropped and renamed in Phase 5, for the reason in D-020 | `fairdm/core/abstract.py`, `fairdm/contrib/identity/models.py`, the five owning apps' `migrations/` |
| T041 | Repoint the keyword form and the project keyword filters | `fairdm/contrib/generic/forms.py`, `fairdm/core/project/filters.py` |
| T042 | Delete the concept autocomplete view and widgets, which the package now supplies | `fairdm/contrib/autocomplete/` |

---

## Phase 5 — The upgrade (owned by US-4, #308)

One story owns these tasks, or two stories author the same migration in separate worktrees and
collide at convergence. US-4 owns them because it is the later of the two the migration needs: US-3
lands the roles field, US-4 lands the keyword fields and then this shared upgrade.

| id | task | files |
|---|---|---|
| T043 | Test the conversion against a database populated in the old shape: every role and keyword survives and resolves to the same term | `tests/test_migrations/` |
| T044 | Test that an unresolvable term makes the migration report **every** failure and convert nothing, leaving the old data intact | `tests/test_migrations/` |
| T045 | Write the data migration in `fairdm/contrib/contributors/migrations/` (D-021), depending on the latest migration of each of the six owning apps and on `controlled_vocabularies`, and `run_before` each of T046a's migrations. It loads the shipped vocabularies only when the roles vocabulary is absent, resolves every recorded term scoped per source vocabulary, collects all failures, then either raises with the complete list or writes every membership row into the new through tables | `fairdm/contrib/contributors/migrations/` |
| T046 | Test that migrating from zero on an empty database reaches the same final state | `tests/test_migrations/` |
| T046a | Drop the old `roles` and `keywords` fields and rename the temporary ones onto those names, one migration per owning app, and repoint anything still naming the temporary fields | the six owning apps' `migrations/`, `fairdm/core/abstract.py`, `contrib/contributors/models.py`, `contrib/identity/models.py` |

---

## Phase 6 — US-5: The retired library is gone (P2, #309)

| id | task | files |
|---|---|---|
| T047 | Edit the three migrations that name the retired library's **field classes** and the retired stub, replacing them with the plain field the column has always been (D-017). Leave every `dependencies` entry and every `to="research_vocabs.concept"` reference alone, in these and in the other ten files — those are the graph edges D-019 defers to the squash | `core/sample/migrations/0001_initial.py`, `0007_...py`, `contrib/contributors/migrations/0001_initial.py` |
| T048 | Delete the retired `SampleStatus` stub | `fairdm/core/choices.py` |
| T049 | Delete the template override the retired library required | `fairdm/utils/templates/research_vocabs/` |
| T050 | Test that no module outside the migration history imports the retired library, and that nothing but the `INSTALLED_APPS` entry names it in the settings. Assert the entry carries its D-019 comment, so it is removed deliberately rather than forgotten | `tests/test_conf/` |
| T051 | Remove the dedicated vocabulary cache alias if neither package uses it, or repoint it if the new one does | `fairdm/conf/settings/cache.py` |
| T052 | Rewrite the six documentation pages naming the retired library, running every example against the branch | `docs/portal-development/` |
| T053 | Write the upgrade guide, with concrete steps (FR-023), including why the retired library is still installed and what the deferred squash will remove | `docs/upgrading/016-controlled-vocabularies.md` |
| T054 | Confirm migrating from zero succeeds and that nothing outside the migration history resolves to the retired library afterwards | — |

---

## Exit

Full suite green, `deptry` green, `makemigrations --check` clean across all apps, migrate-from-zero
reaching the same state, documentation examples run, and the branch's schema migrations consolidated
with the data migration left standalone (Article IX).
