# Implementation Plan: Find a record from anywhere in the portal

**Branch**: `042-site-search` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

django-mvp's site search already draws the results page, the dialog, the header field and button,
and counts, pages and narrows what registered kinds find. FairDM adds one kind class, `RecordKind`,
seven kinds built on it, the mount of django-mvp's search addresses and the three components in the
header. A kind finds records by running its record type's own list `q` filter over the records the
person may open, so the header and the list cannot disagree on what matches.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-mvp 0.37.0 (`mvp.search`),
  django-cotton, django-filter through `mvp.filters.SearchFilter`.
- **New dependencies**: none.
- **Storage**: none. Nothing is indexed or cached.
- **Testing**: pytest with pytest-django against the shared PostGIS, from the worktree's own
  `.venv` (`. ../fairdm-042-env.sh; .venv/bin/python -m pytest tests/test_search.py -n0`). Tests sit
  in `Test<Subject>` classes in the module that mirrors the source file. No test of wording or
  layout.
- **Standards that bind every task**: no leading-underscore names, line length 88, no
  compatibility aliases, no test of text or design preferences, Cotton components and never
  `{% include %}` partials, a Google-style docstring on every new public name.

## Constitution Check

- **Simplicity**: one module, one base class, seven small subclasses. Nothing new in the database,
  no setting, no template of FairDM's own beyond three component tags in a block that exists.
- **Privacy first**: every kind starts from the records the person may open (`visible_to`,
  `accessible_to`) and only then matches. A record the person may not open is neither listed nor
  counted, because the count is taken over the same queryset.
- **Established packages over custom code**: the page, dialog, counting, paging and shortcut are
  django-mvp's. The matching is the list's own filter.
- **Works without custom JavaScript**: django-mvp's results page is a plain form and links. The
  dialog is its progressive enhancement.

## Modules

### `fairdm/search.py` (new)

- `RecordKind(Kind)`: class attributes `name`, `label`, `icon`, `description` (django-mvp's),
  `filterset_class`, `ordering` (a tuple of field names). Methods:
  - `records(self, user)`: the records the person may open. The subclass defines it.
  - `find(self, query, request)`: `self.filterset_class.base_filters["q"].filter(
    self.records(request.user), query).order_by(*self.ordering)`. Every kind's `ordering` ends
    with `"pk"`, for example `("name", "pk")` and `("title", "pk")`, because the results page pages
    twenty at a time and a single non-unique column is not a total order (D11). Returns a queryset, so django-mvp
    counts it with `count()` and slices it in the database.
  - `describe(self, item)`: the line under the title. The subclass defines it. Returns a
    `(where, passage)` pair.
  - `result(self, item)`: `Result(title=str(item), url=item.get_absolute_url(), where=…,
    passage=…)`, from `describe`.
- `ProjectKind`, `DatasetKind`, `SampleKind`, `MeasurementKind`, `PeopleKind`,
  `OrganizationKind`, `LiteratureKind`. Each sets its four attributes and the two methods:
  - Projects: `Project.objects.get_visible() | Project.objects.accessible_to(user, VIEW)`.
  - Datasets: `Dataset.all_objects.visible_to(user)`, `select_related("project")`.
  - Samples: `Sample.objects.visible_to(user)`, `select_related("dataset")`. The base model, so a
    registered type is found as a sample and links to its own page (D5).
  - Measurements: `Measurement.objects.visible_to(user)`, `select_related("sample")`.
  - People: `Person.objects.real()`. Organizations: `Organization.objects.all()`.
  - Literature: `Item.objects.all()` through `ItemFilterSet`. A query that is only a DOI prefix
    (`doi:`) is read by the list's filter as no words and would return every reference, so
    `find()` normalises the words as the filter does and returns `Item.objects.none()` when none
    are left (D14).
- `register_kinds()`: registers one instance of each, in the order of D4.

### `fairdm/apps.py`

`FairDMConfig.ready()` calls `register_kinds()`. The kinds' models are imported inside methods or
at call time, so importing `fairdm.search` at start-up needs no model loaded.

### `fairdm/conf/urls.py`

`path("search/", include("mvp.search.urls"))`, before the catch-all permanent-link pattern and
beside the other mounts. The two names (`mvp-search`, `mvp-search-panel`) are django-mvp's.

### `fairdm/templates/base.html`

The `app.navbar.end` block keeps `<c-actions.create-new />` and gains, after it,
`<c-mvp.search.field />`, `<c-mvp.search.button />` and `<c-mvp.search.dialog />` (PROTOTYPE.md,
"The look"). The landing page overrides `app.header`, so it carries none (D6).

### Documentation

- `docs/developers/reference/site-search.md` (new), a reference page and nothing more: the seven
  record types in their order, the fields each matches, who sees what, that a type's own
  `search_fields` match only in its own table (D10), and the names of django-mvp's
  `MVP_CONFIG["search"]["kinds"]` setting and `register`, without steps. Linked from the
  reference index.
- `CHANGELOG.md`, `Added`: one entry in the file's style.

## Tests

`tests/test_search.py`:

- `TestRegisteredKinds`: the active kinds' names are projects, datasets, samples, measurements,
  people, organizations, literature, in that order (FR-003).
- `TestFindsEveryRecordType`: one record of each type sharing a word, searched through
  `/search/panel/?q=<word>`: every type appears as a group and each result links to its record
  (US1.3, FR-007, SC-002).
- `TestMatchingFollowsTheList`: a sample by local ID, a project, dataset, sample and measurement
  by portal ID, a project by external identifier, a dataset by description (US1.4, FR-004, D9).
  For SC-004, for each kind that has a list page (projects, datasets, people, organizations,
  literature): the primary keys the list page returns for a shared word, as a visitor, are a
  subset of the primary keys the kind returns for the same word. The expected side comes from the
  list's address, never from the filter the kind reads. A query that is only `doi:` lists no
  literature (D14).
- `TestVisibility`: a private project, its dataset, a sample and a measurement are absent for a
  visitor and for a person with no level, present for a person holding a level, and absent from
  the count (US1.5, US1.6, US1.7, SC-003). A public dataset inside a private project is hidden
  from a person with no level (edge case). A private dataset that sits in no project, and a sample
  of it, are absent for a visitor and for a person with no level, and present, and counted, for a
  person holding a level on that dataset alone. Superusers are not found among the people (US1.12).
- `TestRegisteredTypes`: a `ConcreteSample` is found among the samples and links to its own page
  (US1.11, FR-006).
- `TestResultsPage`: more matches than a page shows are reachable at `/search/?q=<word>&kind=
  samples` and page 2 returns the rest (the records past the first page share one name, so a
  missing tie-break fails the test); a query matching nothing lists no group (US1.8, US1.9,
  US1.10).
- `TestHeader`: `/datasets/` as a visitor and as a signed-in person carries the dialog
  (`id="mvp-search"`) and the form's `data-mvp-search-form`; the landing page does not (US1.1,
  FR-002, D6).
- `TestChecks`: running the system checks reports no `mvp.E004` to `mvp.E009` (FR-008).

Each test that checks a template or a page's output is mutated once at S5: break the behaviour it
names, see it fail.

## What is ported

From `prototype-mobile-dock`, read with `git show origin/prototype-mobile-dock:<path>`: the three
component tags of the `app.navbar.end` block, and the result line each kind shows (`fairdm/search.py`).
The prototype's `.mvp-search-form > i` rule is not ported (D7).

## Risks

- **A kind's queryset that breaks `count()` or slicing**: `visible | held` unions and `.distinct()`
  from the list filter. Each is exercised by a test that searches through the panel.
- **Polymorphic records**: `Sample.objects` returns the concrete instance, so `get_absolute_url`
  is the type's own. `select_related` on a polymorphic queryset is exercised by the registered-type
  test.
