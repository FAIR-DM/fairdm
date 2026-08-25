# Tasks — FS-014, managing a dataset through the portal

**Written greenfield.** This list describes building the feature from nothing, to the standard the
constitution sets, from `spec.md` and `plan.md` alone. It does not describe the code that exists.
What the codebase already satisfies is settled afterwards, in `reconciliation.json`, against a code
citation and a passing test — never against this list's own judgement of what is likely already
there.

Article I: every behavioural task writes its test first, and the test fails for the stated reason
before the change. Article X: tests mirror the source tree, one factory per model, shared fixtures
in `conftest.py`, related assertions grouped in classes.

Test locations, throughout: `tests/test_core/test_dataset/` for the record's own surface,
`tests/test_contrib/test_plugins/` for registration and addressing.

---

## Phase F — Foundations

Shared machinery the feature needs before any page can be built. Every one of these is used by more
than one story.

| Id | Task | Serves |
|---|---|---|
| T001 | A `Dataset` factory producing a valid record, with traits for public and private visibility and for belonging to a project or not. | all |
| T002 | Factories for `DatasetDescription`, `DatasetDate` and `DatasetIdentifier`, each taking its type from its own vocabulary. | US-3, US-4 |
| T003 | Fixtures in `conftest.py` for the four actors every page is checked against: an anonymous visitor, a signed-in user with no rights over the record, one holding `change_dataset` on it, one holding `delete_dataset` on it. | all |
| T004 | A row-set declaration base for related records carrying a type and a value, rendering one row per stored pair and no blank rows beyond them. | US-3 |
| T005 | A dataset dates row set built on T004. | US-3 |
| T006 | A dataset identifiers row set built on T004. | US-3 |
| T007 | A precision-aware comparison for two dates that may be recorded to different precisions, so a rule about ordering does not read a year as a January. | US-3 |
| T008 | A row-set validation rule refusing an end date earlier than a start date, parameterised on which two types are the pair and on the message, so a record type supplies its own. | US-3, FR-029 |
| T009 | A form generating one text area per concept in a related model's description vocabulary, labelled with the concept's name and helped by its definition, which writes, updates and removes one row per area on save. | US-4, FR-037–FR-040 |
| T010 | Tests for T004–T009 covering: rows render for stored values only; an end before a start is refused naming the field; an equal start and end is accepted; a whitespace-only description area is treated as empty; a cleared area removes its row. | |

## Phase 1 — US-1, Find a dataset

| Id | Task | Serves |
|---|---|---|
| T011 | A listing page for datasets at a stable address named `dataset-list`, open to visitors who are not signed in. | FR-001 |
| T012 | The listing shows only public datasets, whoever is looking. Test with both visibilities present, signed in and signed out, including a user holding rights over a private dataset. | FR-002 |
| T013 | One search, across the dataset's name, its uuid, its external identifiers, its descriptions and its keywords. Test each of the five finds a record the others would not, and that no second search control is offered. | FR-003, FR-006 |
| T014 | Ordering by name and by date added, both directions. Test that reversing reverses. | FR-004 |
| T015 | Filters by licence, by project, and by the types of description and date a dataset carries. | FR-005 |
| T016 | Every offered filter runs a query without error. The test enumerates the filters the rendered filterset form actually offers — never a hand-written list — and applies each in turn, asserting on the returned records rather than on the filter form. | FR-006 |
| T017 | No filter is offered that cannot change the result set. | FR-006 |
| T018 | The project filter offers only projects the visitor may see. Test that a private project's name is absent for a visitor with no rights over it. | FR-007 |
| T019 | An empty state when nothing matches. | FR-008 |
| T020 | Each listing entry links to its dataset's page. Test asserts the rendered address. | FR-009 |
| T021 | The listing entry's existing design is otherwise unchanged. | FR-010 |

## Phase 2 — US-2, Register a dataset

| Id | Task | Serves |
|---|---|---|
| T022 | A creation page at a stable address named `dataset-create`, requiring the visitor to be signed in and sending them to sign in otherwise. | FR-011 |
| T023 | The page asks for a name, a visibility, a licence and a project, and for nothing else. Test asserts the exact field set, so a field added later fails here. | FR-012 |
| T024 | Visibility is presented as a visible choice between its options, pre-selecting public. Test asserts the rendered control and the pre-selection, not just the form's initial value. | FR-013 |
| T025 | The portal's configured default licence is pre-selected. Test under an overridden setting, so the test does not pin one licence name. | FR-014 |
| T026 | The project field is optional and starts empty; a dataset can be created without one. | FR-015 |
| T027 | The project field offers only projects the signed-in researcher may use, and none at all to a visitor who is not signed in. | FR-016 |
| T028 | A dataset cannot be created without a name. | FR-017 |
| T029 | On creation the creator is granted view, change, delete, change-metadata and change-settings on the record. | FR-018 |
| T030 | On creation the creator is recorded among the contributors as Creator, ProjectMember and ContactPerson. | FR-019 |
| T031 | On creation the dataset records who created it, written server-side and not through the form. | FR-020 |
| T032 | A successful creation arrives at the new dataset's page. | FR-021 |
| T033 | The creation page uses the update page's declared form narrowed to those four fields, rather than a field list of its own. Test asserts the form class in use and that a label declared once reaches both pages. | FR-022 |

## Phase 3 — US-3, Correct a dataset's own attributes

| Id | Task | Serves |
|---|---|---|
| T034 | An update page at a stable address identifying the dataset by its identifier, requiring the visitor to be signed in. | FR-023 |
| T035 | The page refuses a user who does not hold permission to change that dataset. | FR-024 |
| T036 | The page covers image, name, project, licence, visibility and the publication that describes the dataset. Test asserts the exact field set. | FR-025 |
| T037 | Each of those attributes persists when changed. | FR-025 |
| T038 | The project field offers only projects the researcher may use, on the same terms as the creation page. | FR-026 |
| T039 | External identifiers can be added, changed and removed, any number, each typed from the dataset identifier vocabulary. | FR-027 |
| T040 | Collection start and collection end can be set, changed and removed. | FR-028 |
| T041 | A collection end earlier than the collection start is refused, reporting which field is at fault. | FR-029 |
| T042 | An identifier value already recorded against another record is refused, and nothing in the submission is saved. Test asserts the other rows are also unsaved. | FR-030 |
| T043 | The page offers no descriptions, keywords, tags or contributors. Test asserts absence by field set, so a field reintroduced later fails. | FR-031 |
| T044 | A dataset cannot be saved without a name. | FR-032 |
| T045 | A successful submission arrives at the dataset's page. | FR-033 |
| T046 | Identifiers and dates are edited through the shared facility for editing related records, not a hand-written equivalent. | FR-034 |
| T047 | The form declares its layout so it does not emit a form element inside the one the page has already opened. Test asserts the rendered page has one form element. | FR-025 |

## Phase 4 — US-4, Describe a dataset

| Id | Task | Serves |
|---|---|---|
| T048 | A descriptions page at a stable address of its own, identifying the dataset by its identifier, requiring the visitor to be signed in. | FR-035 |
| T049 | The page refuses a user who does not hold permission to change that dataset. | FR-036 |
| T050 | One editable area per description type in the dataset description vocabulary, labelled with the type's name and explained by its definition. Test asserts one area per vocabulary member, by reading the vocabulary rather than by counting a fixed number. | FR-037 |
| T051 | Saving text into an area records a description of that type; a dataset holds at most one of any type. | FR-038 |
| T052 | Clearing an area removes that description. | FR-039 |
| T053 | An empty area creates nothing. | FR-040 |
| T054 | A successful submission arrives at the dataset's page. | FR-041 |
| T055 | The page uses the vocabulary-driven form from T009, not a row-based editor. | FR-042 |

## Phase 5 — US-5, Move between a dataset's pages

| Id | Task | Serves |
|---|---|---|
| T056 | The dataset's own page, its update page, its descriptions page and its deletion page are all registered against the dataset record, so the portal's own navigation can construct every address. | FR-059 |
| T057 | Every address names the record type in the plural, and every page belonging to a dataset sits below the dataset's own address. | FR-057, FR-058 |
| T058 | The singular form no longer answers. Test asserts a request to it fails, not merely that the plural one succeeds. | FR-057 |
| T059 | A dataset's address resolves to its registered page wherever the record is asked for its address. Sweep every reversal, template link, redirect target and test that names one of the retired routes. | FR-058 |
| T060 | Each of the four pages states the permission it requires for itself. Test that a page stating none is not treated as inheriting one. | FR-060 |
| T061 | Each of the four pages states its own visibility rule, so a private dataset is refused at every one of its addresses. Test the case that motivates it: a user holding the model-level right but no record-level grant. | FR-061 |
| T061a | The refusal at all four addresses does not disclose that a private dataset exists. Test each address for an anonymous visitor and for a signed-in user with no rights: both get the not-found response, never a permission refusal and never a redirect to sign in. Test separately that a *public* dataset the user may not change still refuses with a permission response, so the two cases are not collapsed. | FR-061 |
| T062 | The dataset's pages contribute exactly one entry to the per-record navigation. Test asserts the entry count, not the entry names. | FR-062 |
| T063 | The dataset's page draws a link to its update page and its descriptions page for a user who may change it, and to its deletion page for a user who may delete it. | FR-050 |
| T064 | No page offers a link to a page that would refuse the user looking at it. Test each of the three actions against a user who lacks exactly that right. | FR-051 |
| T065 | Every link drawn resolves to a real address, and a link that cannot be resolved is not drawn as an empty one. | FR-052 |
| T066 | The update, descriptions and deletion pages each offer a way back to the dataset. | FR-053 |
| T067 | The update page offers the deletion page to a user who may delete the dataset. | FR-054 |
| T068 | Links are declared through the shell's current mechanism; the deprecated one is not used. Test asserts no deprecation warning is raised while rendering each page. | FR-055 |
| T069 | The dataset's own page keeps its content and layout, gaining only the links. | FR-056 |

## Phase 6 — US-6, Remove a dataset

| Id | Task | Serves |
|---|---|---|
| T070 | A deletion page at a stable address identifying the dataset by its identifier, requiring the visitor to be signed in. | FR-043 |
| T071 | The page refuses a user who does not hold permission to delete that dataset. | FR-044 |
| T072 | The deletion proceeds only when the dataset's name is typed exactly, disregarding leading and trailing spaces. | FR-045 |
| T073 | The rendered page carries exactly one control named for the confirmation. Fails against the pinned shared package, so it is marked expected-to-fail **strictly**, with the issue in the reason — an unexpected pass fails the suite, which is how the upstream fix landing is noticed. | FR-045 |
| T074 | The page states what will be deleted with the dataset — the number of samples and the number of measurements beneath it, and that its descriptions, dates and identifiers go too — prominently and before the confirmation is offered. Test asserts rendered content, not context. | FR-046 |
| T075 | A dataset holding no samples and no measurements is not warned about data it does not hold. | FR-047 |
| T076 | A public dataset is deleted like any other; visibility alone never prevents a deletion. | FR-048 |
| T077 | A successful deletion arrives at the dataset listing, and the samples and measurements beneath the dataset are gone. | FR-049 |

## Phase 7 — Deliberate omissions, and closing out

| Id | Task | Serves |
|---|---|---|
| T078 | Keywords are not editable anywhere in this feature, and the portal offers no keywords page for a dataset. Test asserts the address does not answer. | FR-063 |
| T079 | Tags are not editable through this feature. | FR-064 |
| T080 | Contributors are not managed through this feature beyond recording the creator. | FR-065 |
| T081 | Nothing in this feature publishes a dataset's data, gates access to it, or introduces a published state. | FR-066 |
| T082 | The project's deletion refusal is unchanged by this feature. Test asserts its current behaviour still holds. | FR-067 |
| T083 | Documentation: every page this feature adds or moves is described where a portal author would look for it, and any page describing the retired addresses is corrected. | Article VI |
| T084 | The full suite, lint, type checks and the build pass, and `makemigrations --check` is clean across all apps. | |

---

## Reconciliation

Each task above is settled against the codebase before any implementation begins, and the result is
written to `reconciliation.json` and then to `feature-state.json`. A task starts `done` only with a
code citation **and** a passing test that covers it. Code with no test leaves the task open, and the
remaining work is the test.
