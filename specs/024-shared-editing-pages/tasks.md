# Tasks: One set of editing pages for projects, datasets, samples and measurements

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests first**: in every story the test task comes first and is seen to fail before the code that
makes it pass is written. Page tests request and submit the real page through the Django test
client, for each record type and each kind of account the scenario names, and assert on the
response and on what is stored afterwards. Layout, wording and appearance get no tests.

**Accounts**: a visitor, a signed-in person with no level, and people at the view, edit and manage
levels given with `ContributionFactory`. People are made with `is_active=True`.

**Record types**: a project, a dataset, a demo sample type and a demo measurement type, so that
registered types are what is tested (SC-006).

**Existing tests of a removed page**: a test that requests a page this feature removes, or reverses
its old URL name, describes behaviour the feature replaces. It is rewritten against the shared page
where it asserts something the new tests do not, and removed where they do. Each task that removes
a page lists the test classes it changed or removed in the story's progress entry. No other
existing test is changed.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, US2, US3, US4, one after another, each from the previous story's accepted
commit.

## Phase 1: US-1, a record's team edits its details and descriptions from the Manage menu (P1)

This story also lays what the others stand on: the module, the access rule and the menu.

- [ ] T001 [US1] `tests/test_core/test_editing.py`, new.
  - `TestRegistration`: `edit` and `descriptions` resolve on all four record types at the record's
    address followed by the segment, and neither is among the record's tabs (scenario 2, FR-005,
    FR-007).
  - `TestAccess`, parametrised over the four record types and both pages: an edit-level person
    opens the page; a view-level person on a private record is refused with 403 and nothing
    changes on POST (9, FR-013); a signed-in person with no level on a public record gets 403; a
    visitor on a public record is redirected to sign in (10); anyone who may not see the record
    gets 404 on GET and POST (11, FR-014); a person whose level is removed after the page was
    opened is refused on POST (FR-015).
  - `TestManageMenu`, over the four record types: an edit-level person's overview offers the two
    entries with the shared addresses (1); a view-level person's overview has no Manage menu
    (FR-008); a measurement's overview has the menu; the project's menu has no contributors entry.
  - `TestEditDetails`: a valid save returns to the record's page, sets a success message and
    stores the value, on all four (3); an invalid save stores nothing, reports the error on the
    field and keeps the other values (4, FR-018); a demo sample type's page offers its type's
    fields with their current values and no `dataset` field, and a demo measurement type's offers
    neither `dataset` nor `sample` (5, FR-017); the page of a registry-built form draws one Save
    control; an edit-level person is not offered visibility on a project or a dataset and a
    manage-level person is.
  - `TestEditDescriptions`: one area per type in the record's vocabulary, filled with what is
    recorded, on all four (7, FR-020); filling an area records it and emptying one removes it (8,
    FR-021).
  - `TestOverviewPrompts`: the prompt for a missing description and the prompt to change
    visibility on a project and a dataset lead to the shared pages (12, FR-010).
- [ ] T002 [US1] Implement to make T001 pass (plan D1 to D5, D9 row US-1, D10):
  - `fairdm/core/editing.py`: `RecordEditingPage`, `EditDetails`, `EditDescriptions`,
    `manage_menu`, registered on the four models and imported where plugin discovery reaches it
  - `<c-actions.manage>`, used on all four overview pages. `RecordOverviewPlugin` adds
    `manage_menu` to the context
  - remove `Update` and `Descriptions` from the project and dataset overviews, `Edit` and
    `Descriptions` from the sample, `UpdatePlugin`, `DescriptionsPlugin` and the templates only
    they used. `EditDetails` keeps the identifier and date row sets on a project and a dataset
    until US-2
  - repoint the overview prompts and the readiness checklists of the project and dataset overviews
  - bring the existing tests of the removed pages up to date, as the heading of this file says
- [ ] T003 [US1] Documentation: `docs/portal-development/record-editing-pages.md`, new and linked
  from its index, covering the pages this story adds, their addresses, the Manage menu, which right
  opens each and that a registered type gets them with no work (FR-034). Bring the user guide
  pages for updating and describing a project and a dataset up to date, and
  `docs/portal-development/overview-pages.md`, `create_a_plugin.md` and
  `docs/contributing/record-page-building-blocks.md` where they name a removed page. A decision
  record superseding 0008 (plan D9), with 0008 marked superseded. `CHANGELOG.md`.

## Phase 2: US-2, key dates and identifiers each have a page of their own (P2)

- [ ] T004 [US2] `tests/test_core/test_editing.py`:
  - `TestRegistration` and `TestAccess` and `TestManageMenu` extended to `key-dates` and
    `identifiers` (scenarios 1 and 10).
  - `TestEditKeyDates`, over the four record types: the page offers the date types of the record's
    vocabulary and shows the dates recorded (2); adding, changing and removing a date is stored
    (3); on a project and a dataset an end before the start stores nothing and reports which date
    is wrong (4, FR-026); a year-only date is stored and read back as year-only (5, FR-027); a row
    the model refuses comes back as an error on the page and not as a server error.
  - `TestEditIdentifiers`, over the four record types: the page offers the identifier types of the
    record's vocabulary and shows those recorded (6); adding, changing and removing is stored (7);
    the record's portal ID is not among the rows and cannot be changed through the page (8,
    FR-029).
  - `TestEditDetails`: the details page of a project and a dataset carries no date and no
    identifier rows (9, FR-016).
  - `tests/test_core/test_related_records.py`: the four new row-set classes are capped at one row
    per type.
- [ ] T005 [US2] Implement to make T004 pass (plan D6, D9 row US-2, D10): the four row-set classes
  and the two date-ordering subclasses in `fairdm/core/related_records.py`; `EditKeyDates` and
  `EditIdentifiers`; the row sets leave `EditDetails`; remove the sample `KeyDates` page,
  `KeyDatesPlugin` and its template; the readiness items for dates and identifiers lead to the new
  pages; existing tests of the row sets on the old details page move to the new pages.
- [ ] T006 [US2] Documentation: the two pages in `record-editing-pages.md`; the user guide pages
  for a project and a dataset say where dates and identifiers are edited; `CHANGELOG.md`.

## Phase 3: US-3, a record's team deletes it from the Manage menu (P2)

- [ ] T007 [US3] `tests/test_core/test_editing.py`:
  - `TestRegistration` and `TestManageMenu` extended to `delete`: a manage-level person is offered
    the entry on all four (scenario 1); an edit-level person is offered the editing entries and
    not delete (2).
  - `TestAccess` for delete: an edit-level person gets 403 on GET and POST and nothing is deleted
    (2); the visitor, no-level and cannot-see cases as for the editing pages.
  - `TestDeleteRecord`: GET deletes nothing and lists what goes with the record (3, 4, FR-030); a
    POST without the right confirmation deletes nothing; confirming a sample or a measurement
    deletes it, lands on its dataset and sets a message (5); confirming a dataset or a project
    lands on its list page with a message (6); a sample with measurements shows them and has no
    confirmation form (7); a project with a public dataset shows those datasets and has no
    confirmation form (8); a POST for a record that became protected deletes nothing and answers
    with the page in its protected state (9, FR-032); a measurement without a name is confirmed by
    its portal ID.
- [ ] T008 [US3] Implement to make T007 pass (plan D8, D9 row US-3): `DeleteRecord`; remove
  `Delete` from the project and dataset overviews, `DeletePlugin`, and the `crud_views` entries
  that name removed pages; existing tests of the old delete pages are brought up to date.
- [ ] T009 [US3] Documentation: the delete page in `record-editing-pages.md`; the user guide pages
  for deleting a project and a dataset; `CHANGELOG.md`.

## Phase 4: US-4, keywords are edited the same way on every record type (P3)

- [ ] T010 [US4] `tests/test_core/test_editing.py`:
  - `TestRegistration`, `TestAccess` and `TestManageMenu` extended to `keywords` (scenarios 1
    and 5). `TestManageMenu` asserts the order of all six entries, the same on every record type
    (FR-006), and that all 24 combinations are offered to a manage-level person (SC-001).
  - `TestEditKeywords`, over the four record types: the keywords a record carries are shown as
    chosen (2); adding and removing is stored and shown on the record's page (3); the page opens
    and saves on a record type with no keyword vocabulary configured (4, FR-023).
  - `tests/test_contrib/test_generic/test_forms.py`: building `KeywordForm` for two different
    models leaves each bound to its own.
- [ ] T011 [US4] Implement to make T010 pass (plan D7, D9 row US-4, D10): `EditKeywords`; the
  `KeywordForm` repair; remove the sample `Keywords` page, `KeywordsPlugin` and its template; the
  readiness keywords item leads to the page.
- [ ] T012 [US4] Documentation: the keywords page in `record-editing-pages.md`, saying it is
  replaced by #298; `CHANGELOG.md`.
