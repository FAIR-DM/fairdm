# Tasks: Record list tabs are shared across the pages that need them

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [sketch.md](sketch.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code that
makes them pass is written. View tests send requests through the test client to the real routes and
assert on the response and its context. Wording, layout and CSS classes get no tests.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, then US2, then US3, each from the previous story's accepted commit.

## Phase 1: User Story 1, a dataset's samples and measurements can be browsed from its page (P1)

### Group 1

The plugin, its home, the dataset registration, which records it lists and the tab mark.

- [ ] T001 [US1] `tests/test_contrib/test_collections/test_plugins.py`, `TestDatasetRecords`: on a
  published dataset holding two sample types and two measurement types, the Samples and
  Measurements tabs answer 200 for a visitor, list only that dataset's records of the most numerous
  type, offer exactly the types the dataset holds with their counts, and a type's own address shows
  that type. A type the dataset holds none of, and an unregistered slug, answer 404. A
  measurement on another dataset's sample is listed on its own dataset's Measurements tab and that
  sample is not on its Samples tab. A private dataset's tabs answer 404 to a visitor and 200 to its
  team. Each row's name links to the record's page. A sample's page has no Samples or Measurements tab.
- [ ] T002 [US1] same file, `TestRecordState`: a public unpublished dataset offers a visitor no
  Samples or Measurements tab in its tab strip and both addresses answer 404; its team gets both tabs
  and the rows. A dataset holding nothing gives
  `empty` to everyone. The tab is present in the tab strip in both states. With no measurement type registered, a dataset's Measurements tab answers 200 with `empty`.
- [ ] T003 [US1] `tests/test_contrib/test_plugins/test_menus.py`: a plugin's tab is marked as the
  current page on its own address, on each of its `extra_views` addresses and on an extra pattern
  its `get_urls` mounts, and is not marked on another plugin's address. Asserted through a rendered tab strip, so the per-request copy is exercised.
- [ ] T004 [US1] `fairdm/contrib/collections/plugins.py`: move the sketch's module here and
  register `Samples` and `Measurements` on `Dataset`; scope, viewer, `type_counts`, `resolve_type`
  and the not-published check per plan D1 to D3. Remove the import from
  `fairdm/contrib/contributors/plugins/__init__.py` and the view-name rewrite.
- [ ] T005 [US1] `fairdm/contrib/plugins/menus.py` and `registration.py`: `PluginTabItem` per plan
  D7.

### Group 2

The table: columns, links, choices, order and query count.

- [ ] T006 [US1] `tests/test_contrib/test_collections/test_plugins.py`, `TestRecordTable`: the
  first columns are name then, on measurements, sample; there is no dataset column on a dataset's
  tab. A measurement whose sample the viewer may open links it; one whose sample they may not see
  shows `—` and the sample's name is nowhere in the response. Search, a filter and a sort narrow and
  reorder rows within the dataset and never include another dataset's record; sorting by sample
  puts the hidden samples' rows in one block after the named ones. The table's resolved ordering
  ends in a unique key, for a generated table and for a declared table with no `order_by`. Fifty rows per page.
- [ ] T007 [US1] same file, `TestRecordChoices`: a measurement tab's sample filter offers only
  samples of the listed measurements the viewer may see; a team member's choices include their
  unpublished samples and a visitor's do not. A dataset's own tab has no dataset filter.
- [ ] T008 [US1] same file, `TestRecordQueries`: a type table with ten rows and with sixty issues
  the same number of queries, for samples and for measurements.
- [ ] T009 [US1] `tests/test_registry/test_factories.py`, `TestScopedChoicesMixin`: it narrows a related filter to the rows given and leaves a filter on
  an unrelated model alone.
- [ ] T010 [US1] `fairdm/contrib/collections/plugins.py` and `fairdm/registry/factories.py`: the
  annotations, `DatasetColumn`, `SampleColumn`, the sequence, `ScopedChoicesMixin` and the dataset
  filter removal per plan D5 and D6.

### Group 3

The page around the table, the overview links, records of an unregistered type, data and docs.

- [ ] T011 [US1] `tests/test_contrib/test_collections/test_plugins.py`, `TestRecordPage`: the
  response carries the breadcrumb trail ending in the dataset and the kind. Where more than one type
  is listed the switcher's entries link to each type's address; where one is listed there is no
  switcher. The filter panel is absent on an empty tab.
- [ ] T012 [US1] `tests/test_contrib/test_collections/test_views.py`: the portal-wide listing's
  `page.title` is still the type's verbose name after plan D8.
- [ ] T013 [US1] `tests/test_core/test_dataset/` overview test: the Samples and Measurements figures
  link to the two tabs and equal the tabs' totals for a visitor and for the team. On a public
  unpublished dataset a visitor gets no Samples or Measurements figure, no composition or growth
  chart and no spatial coverage drawn from its records; its team gets all of them. Every existing
  overview test that expected a visitor to see those counts is changed to this rule.
- [ ] T014 [US1] `tests/test_contrib/test_collections/test_plugins.py`, `TestUnregisteredType`:
  records of a sample subclass with no registration are listed under the fallback entry with the
  base table, and the tab does not fail.
- [ ] T015 [US1] `tests/test_demo/test_management/test_commands/test_seed_record_lists.py`: the
  command refuses outside development, and run twice creates the same records once. And one test per FR-032 state: each seeded record reaches the state the requirement names.
- [ ] T016 [US1] `fairdm/contrib/collections/views.py`, `fairdm/contrib/collections/plugins.py`,
  `fairdm/core/dataset/plugins.py`, the overview plugins and templates: plan D3a, D4, D8, D9 and D10.
  The template's not-published panel is removed.
- [ ] T017 [US1] `docs/developers/reference/plugins.md` and a new `docs/users/` page per plan D11,
  covering the dataset tabs, written so the later stories extend them. Plus the `CHANGELOG.md` entry and the `seed_record_lists` row in `management-commands.md`.

## Phase 2: User Story 2, a project's samples and measurements can be browsed from its page (P2)

- [ ] T018 [US2] `tests/test_contrib/test_collections/test_plugins.py`, `TestProjectRecords`: a
  project's tabs list the records of its datasets the viewer may see; a visitor sees nothing from a
  private dataset in rows, totals, types or choices, and a member of that dataset's team does. Each
  row names its dataset and links it where the viewer may open it. A project whose only records are
  unpublished, and one whose records are all in private datasets, give a visitor the same `empty` as
  one with none. A measurement on another project's sample is listed and that sample
  is not. A private project's tabs answer 404 to a visitor. The dataset filter offers only the
  project's datasets with visible rows.
- [ ] T019 [US2] same file: the project overview's figures link to the tabs and equal the tabs'
  totals for a visitor, a member of a private dataset and the project's team, on a project holding a
  published, an unpublished and a private dataset. Ten and sixty rows issue the same
  number of queries. A member of a private dataset in a public project gets the same figure and tab total.
- [ ] T020 [US2] `fairdm/contrib/collections/plugins.py`: register on `Project`; scope and
  `DatasetColumn` per plan D2 and D5. Docs from T017 extended to the project.

## Phase 3: User Story 3, a contributor's samples and measurements can be browsed from their page (P2)

- [ ] T021 [US3] `tests/test_contrib/test_collections/test_plugins.py`, `TestContributorRecords`: a
  person credited on a project lists its datasets' released records; on a dataset in another
  project, that dataset's and not its siblings'; on one sample, that sample and not its siblings.
  Credit on a sample does not bring in other people's measurements of it. An organization lists the
  records of a project it owns and not those its members are credited on. A record credited in
  several ways is listed once. Each row's dataset links to it; a measurement whose own dataset is released and whose sample's dataset is not is listed.
- [ ] T022 [US3] same file, `TestContributorViewer`: a person credited on a private dataset, an
  unpublished public dataset and a public dataset in a private project: anyone else sees none of
  their records in rows, totals, types or choices; the person sees them and their choices include
  them. An organization credited on a private dataset shows none of it, to a member of its team
  too. A contributor with nothing the viewer may see gives `empty`. Ten and
  sixty records issue the same number of queries.
- [ ] T023 [US3] `fairdm/contrib/collections/plugins.py`: register on `Contributor`; scope and
  viewer per plan D2. Docs from T017 extended to contributors.
