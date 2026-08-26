# Tasks — FS-016: Controlled vocabularies replace django-research-vocabs

**Plan**: `plan.md` · **Research**: `research.md` · **Decisions**: `decisions.md`

Article I applies to every task that changes behaviour: the failing test comes first. Tasks marked
**[P]** may run in parallel with their siblings; everything else is sequential within its phase.

**T009 is blocked on Sam's ruling on D-016** (dropping Django 5.1). Phase 1 and every US-1 task run
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
| T010 | Convert the five vocabulary classes to rich-choices classes, carrying every label and definition across verbatim | `fairdm/core/vocabularies.py` |
| T011 | Point `Sample.status` at `SampleStatus` as a plain `CharField` with `choices`, keeping the `unknown` default and the column unchanged | `fairdm/core/sample/models.py` |
| T012 | Repoint the generic description, date and identifier models at the new subsets | `fairdm/core/project/models.py`, `dataset/models.py`, `sample/models.py`, `measurement/models.py`, `contrib/contributors/models.py` |
| T013 | Repoint the sample status filter, which already reads `choices` rather than concept rows | `fairdm/core/sample/filters.py` |
| T014 | Repoint the DataCite contributor-type export mapping and its name-agreement test | `fairdm/core/project/transforms.py` |
| T015 | Delete `DatasetDescriptions`, which nothing outside its own definition refers to | `fairdm/core/choices.py` |
| T016 | Confirm `makemigrations --check` across all apps is clean — the columns and their values are unchanged, so this change must produce no migration | — |
| T017 | Surface definitions in the templates that render these fields, so a reader sees what a term means | `fairdm/**/templates/` |
| T018 | Document the rich-choices mechanism as a public surface, with a working example (Article VI) | `docs/portal-development/` |

---

## Phase 2 — US-2: Vocabularies ship and load (P1, #306)

Blocks US-3 and US-4.

| id | task | files |
|---|---|---|
| T019 | **Blocked on D-016.** Narrow the Django constraint to `>=5.2`, add `django-controlled-vocabularies` and `django-tomselect`, remove `django-research-vocabs`; `deptry` green | `pyproject.toml`, `poetry.lock` |
| T020 | Test that a portal missing the autocomplete route, the middleware or a loaded vocabulary reports the expected warning and still starts | `tests/test_conf/test_settings/` |
| T021 | Add the settings the package requires: both apps installed, the middleware, the mounted route, and the base address | `fairdm/conf/settings/apps.py`, `urls.py` |
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
| T032 | Convert `Contribution.roles` to a concepts field over the roles vocabulary | `fairdm/contrib/contributors/models.py` |
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
| T040 | Convert `keywords` on the shared base and on the identity model | `fairdm/core/abstract.py`, `fairdm/contrib/identity/models.py` |
| T041 | Repoint the keyword form and the project keyword filters | `fairdm/contrib/generic/forms.py`, `fairdm/core/project/filters.py` |
| T042 | Delete the concept autocomplete view and widgets, which the package now supplies | `fairdm/contrib/autocomplete/` |

---

## Phase 5 — The upgrade (US-3 and US-4, sequential)

| id | task | files |
|---|---|---|
| T043 | Test the conversion against a database populated in the old shape: every role and keyword survives and resolves to the same term | `tests/test_migrations/` |
| T044 | Test that an unresolvable term makes the migration report **every** failure and convert nothing, leaving the old data intact | `tests/test_migrations/` |
| T045 | Write the data migration: load the shipped vocabularies, resolve every recorded term scoped per source vocabulary, collect all failures, then either raise with the complete list or write every membership row | `fairdm/core/migrations/` |
| T046 | Test that migrating from zero on an empty database reaches the same final state | `tests/test_migrations/` |

---

## Phase 6 — US-5: The retired library is gone (P2, #309)

| id | task | files |
|---|---|---|
| T047 | Edit the three migrations that name the retired library's field classes and the retired stub, replacing them with the plain field the column has always been (D-017) | `core/sample/migrations/0001_initial.py`, `0007_...py`, `contrib/contributors/migrations/0001_initial.py` |
| T048 | Delete the retired `SampleStatus` stub | `fairdm/core/choices.py` |
| T049 | Delete the template override the retired library required | `fairdm/utils/templates/research_vocabs/` |
| T050 | Test that no module imports the retired library and that it is absent from the installed applications | `tests/test_conf/` |
| T051 | Remove the dedicated vocabulary cache alias if the package does not use it, or repoint it if it does | `fairdm/conf/settings/cache.py` |
| T052 | Rewrite the six documentation pages naming the retired library, running every example against the branch | `docs/portal-development/` |
| T053 | Write the upgrade guide, with concrete steps (FR-023) | `docs/upgrading/016-controlled-vocabularies.md` |
| T054 | Confirm migrating from zero succeeds with the retired library uninstalled | — |

---

## Exit

Full suite green, `deptry` green, `makemigrations --check` clean across all apps, migrate-from-zero
reaching the same state, documentation examples run, and the branch's schema migrations consolidated
with the data migration left standalone (Article IX).
