# Tasks: open any record from its portal ID at a short, permanent link

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [sketch.md](sketch.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail before the code
that makes it pass is written. Wording and appearance get no tests.

**How tests run**: through the shared development container,
`~/.openclaw/devserver/fairdm-shared-test.sh <worktree> <command>`, which queues runs one at a time.

**Format**: `[ID] [Story] Description`.

**Order**: US1, then US2 from US1's verified commit. In US2, T011 comes before T009, and T007's
Copy link assertion passes only once T011 is in.

## Phase 1: User Story 1, a visitor opens a record from its portal ID (P1)

### Group 1

- [x] T001 [US1] `tests/test_views/test_permalink.py`: for a project, a dataset, a sample and a
  measurement of a registered subtype each, and a person (including one who has not claimed their
  profile and one whose account is deactivated) and an organization, `GET /<uuid>/` answers a
  temporary redirect (302) to the record's `get_absolute_url()`, and following it renders the page of
  the record as its own type (AS 1, AS 2, FR-001, FR-002). A well-formed ID that belongs to no
  record, the ID of a deleted record and an ID that differs from a real one only in case all end, once
  followed, at the not-found page (AS 3, FR-003). For an anonymous visitor, a private project's and a
  private dataset's links answer exactly as a well-formed ID of the same kind that belongs to no
  record does, step for step, and someone holding a level reaches the page (AS 4, FR-005). A query
  string is carried to the target. `/<uuid>` with no slash reaches the record (AS 6). The redirect
  is never permanent (AS 5, FR-006).
- [x] T002 [US1] `tests/test_conf/test_urls.py`: an address at the root with a portal ID's length but
  a letter no record uses, and the existing root pages (`/projects/`, `/legal/`, the home page),
  answer as they do without the permalink pattern. Add one portal-ID-shaped path to
  `tests/test_conf/routed_addon/urls.py`, and with `TestAddonUrlMounting`'s reload-and-restore
  fixture in `tests/test_conf/test_addons.py`, show that address is served by the addon (AS 7,
  FR-004). Reloading `fairdm.conf.urls` twice raises nothing.
- [x] T003 [US1] `tests/test_views/test_permalink.py`: the `uuid` a factory makes for each of the five
  models resolves to the `permalink` route. `get_permalink(record)` returns `/<uuid>/`, and with a
  request the absolute link.
- [x] T004 [US1] `fairdm/views/permalink.py` (replacing the sketch's `fairdm/views/links.py`):
  `PORTAL_ID_PATTERN`, `OVERVIEW_URL_NAMES`, `get_permalink` and `PermalinkView`, per the plan. No
  converter and no record lookup. Append the `re_path` `permalink` pattern in `fairdm/conf/urls.py`
  and remove the sketch's `register_converter`. Update the sketch's imports of `record_link` to
  `get_permalink`.
- [x] T005 [US1] Docs: one sentence on the permalink in "How to reach it" of the project, dataset,
  sample, measurement, person and organization pages under `docs/users/`. Developer reference for the
  `permalink` URL name, `get_permalink`, and the rule that a declared root page wins. `CONTEXT.md`:
  **Portal ID** and **Permalink** entries. A changelog entry.

## Phase 2: User Story 2, a visitor shares or cites a record by its permanent link (P2)

### Group 1

- [x] T006 [US2] `tests/test_templates/test_cards.py`: the identifiers card given a `permalink` lists
  it as a link whose address is that permalink, beside a button that copies it, and still lists the
  Portal ID with its own copy button. Given no permalink, no Permalink row (AS 1, AS 2, FR-007).
  `tests/test_templatetags/`: `{% permalink record %}` gives the absolute link for the request.
- [x] T007 [US2] `tests/test_templates/test_overview_page.py` and the contributor overview tests:
  on the overview page of each of the six kinds of record, the identifiers card's permalink and every
  choice in the Share menu carry the record's absolute permalink (AS 1, AS 3, FR-007).
- [x] T008 [US2] Plugin tests: the citation of a dataset with no DOI, a sample with no IGSN and a
  measurement with no DOI ends with the record's absolute permalink. With a DOI or IGSN the
  citation is unchanged (AS 4, AS 5, FR-008). `tests/test_contrib/test_import_export/test_utils.py`:
  the DataCite export's `IsVariantFormOf` URL is the dataset's absolute permalink (AS 6, FR-009).
- [x] T011 [US2] Raise django-mvp in `pyproject.toml` to the release whose Share menu's Copy link
  copies the `url` it is given, and relock. Every other choice already shares `url`.
- [x] T009 [US2] The `permalink` template tag in `fairdm/templatetags/fairdm.py`. The `permalink`
  attribute and row on `<c-card.identifiers>`, keeping the approved sketch's markup, with the copy
  button copying the given link. The three overview templates use the tag for the card and the Share
  menu, replacing the sketch's hand-built address. The three plugins and `datacite_xml` use
  `get_permalink(record, request)`.
- [x] T010 [US2] Docs: `docs/users/editing-a-record/identifiers.md`, "Where the identifiers appear",
  covers the Permalink row, and the record page docs say the citation and the Share menu use the
  permalink where they describe them. The developer reference names the `permalink` tag and the
  card's `permalink` attribute.
- [x] T012 [US2] `tests/test_core/test_project/test_plugins.py`: a project with no DOI is cited by its
  absolute permalink (AS 4, FR-008). `fairdm/core/project/plugins.py` uses
  `get_permalink(project, request)`, and the project page docs say so. Found at story acceptance:
  the plan named the dataset, sample and measurement citations and missed the project's.
