# Research: show recent activity on project and dataset pages

Investigated on 2026-11-16 against `main` at 89511577, with the redesigned project and dataset
pages (https://github.com/FAIR-DM/fairdm/issues/672) merged.

## Assumptions checked

- **django-activity-stream is installed in FairDM.** False. `fairdm/conf/settings/addons.py:12`
  defines `ACTSTREAM_SETTINGS`, but `actstream` is in neither `pyproject.toml` nor
  `INSTALLED_APPS` (`fairdm/conf/settings/apps.py:17`). Neither is `mvp_community`. The feature adds
  both, through `django-mvp-community[activity]` (0.1.4 on PyPI, requiring `django-mvp>=0.28.1`,
  which FairDM's `django-mvp>=0.33.2,<0.34` meets).
- **django-mvp-community's list of activity draws a list handed to it.** True:
  `cotton/mvp_community/activity/feed.html` takes `actions`, already in order, draws each through
  `cotton/mvp_community/activity/entry.html` and has its own empty state. Both templates are listed
  as override points in the package's `docs/developer/activity.md`. The list wraps its rows in a
  `c-mvp.card` and a `c-list` and does not group them. FairDM hands it one item per day and
  overrides the row to draw a day (decisions.md, D5, D17).
- **The recent-activity component can show a project's activity with its datasets', or keep
  activity from a viewer who may not open it.** False, and no longer needed: FairDM chooses the
  lines itself and hands them to the list (D5).
- **Installing `mvp_community` leaves FairDM's Account Center as it is.** True when it is listed
  after `mvp_accounts`. Both packages override `mvp/account/overview.html`, and the first app listed
  wins. `mvp_accounts`' version is the one FairDM shows today. The package's version only adds a
  Following card when its URLs are included, and FairDM includes none of them (FR-013).
- **Every record carries when it was added.** True. `fairdm/db/models.py:70` gives every
  `fairdm.db.models.Model` an `added` (`auto_now_add`) and a `modified`. Project, dataset, sample
  and measurement all inherit it. `Contribution` does not: it records no time at all
  (`contrib/contributors/models.py:1851`).
- **Every addition, edit and new contributor goes through `save()`.** True for every path that
  exists:
  - Data import runs django-import-export row by row with `use_bulk` unset, so each row is an
    `instance.save()` (`contrib/import_export/views.py:186`). No code bulk-creates samples or
    measurements.
  - Project and dataset details are edited through `core/editing.py:236` (`EditDetails`), the API
    (`api/viewsets.py:100`) and the administration interface, each a `save()`.
  - Contributors are added through `Crediting.add()` (`contrib/contributors/services/crediting.py:121`),
    `Contribution.add_to` (`models.py:1974`) and `Contributor.add_to` (`models.py:747`), each a
    create. `Crediting.move` uses `bulk_update`, which adds no one.
- **Publishing has one path.** `Dataset.published` is set only in the administration interface
  (`dataset/admin.py:118`), with a `save()`. It is read-only in
  the API and absent from `DatasetForm`.
- **Who may open a record.** The pages decide it per object: `project_is_visible`
  (`project/plugins.py:44`) and `dataset_is_visible` (`dataset/plugins.py:51`). As a queryset,
  `Dataset.all_objects.visible_to(user)` (`dataset/models.py:150`) returns the datasets a user may
  open. Projects have no `visible_to`, and the panel needs none: the project page is already open
  to its viewer.
- **A receiver can tell a change from a save that changes nothing.** Not as the code stands. The
  `FieldTracker` declared on the abstract `BaseModel` (`core/abstract.py:56`) is never set up:
  django-model-utils finalizes a tracker on `class_prepared` for the class it is declared on
  (`model_utils/tracker.py:364-382`), and Django sends that for concrete models only. In the
  running settings `hasattr(Project, "tracker")` and `hasattr(Dataset, "tracker")` are both false.
  Declared on the concrete model, a tracker wraps `save_base`, which sends `post_save`, and resets
  only when it returns (`tracker.py:410-425`), so a `post_save` receiver sees what changed. The
  feature declares it on `Project` and `Dataset` (decisions.md, D19).
- **Days in the portal's time zone.** `TIME_ZONE` is the portal's (`DJANGO_TIME_ZONE`, `apps.py:164`)
  with `USE_TZ = True`. No view activates another zone, so `TruncDate` gives the portal's day.

## Planning notes, answered

### The prototype this feature comes from — adopted

Read: `PROTOTYPE.md` part F3, `cotton/ov/activity.html`, the `.ov-activity` rules in
`static/css/overview.css:555-562`, and `overview_proto.py:149` on `prototype-overview-pages`. The
prototype's panel is a list of days, each a date beside the day's lines, each line a coloured square
in its record's colour, then what happened and the record it happened to. On a dataset's own page a
line about the dataset leaves its name out. The empty state is one muted sentence. All of it is
ported (plan, "What is ported").

### Build it on django-mvp-community's activity extra — adopted, as published

The extra is installed and its list of activity draws the lines. The package is not edited (D5).
django-activity-stream records the events that leave no other trace: a dataset published, details
edited, a contributor added. Each is recorded not public (D4).

### The prototype's activity is replaced, not ported — adopted in part

The prototype worked everything out from `added`, which can only show additions. Publishing, edits
and contributors joining are now recorded as actions. **Additions stay worked out from `added`, as
the prototype did** (D16):

- Recording an action per sample would write one more row for each of an import's 10,000 samples
  (SC-003).
- It would keep counting samples since deleted, unless every deletion also removed its action
  (FR-015).
- It would leave an upgraded portal's history empty without a data migration writing an action for
  every record it holds (FR-016, SC-005).

Counting from `added` has none of those costs: the counts are of what exists now, the history is
there on upgrade, and an import writes nothing extra.

### The panel is the one the redesigned pages build — adopted

`cotton/overview/panel.html` on `main` takes `title` and `more_url` ("See all"). The activity panel
uses it, with `more_url` leading to the record's full list (D11).

### The look is ported — adopted

See the plan, "What is ported". The line's look comes through FairDM's overrides of the package's
`entry.html` and `feed.html` (D17).

### Design rules from the prototype — adopted

No badge is drawn. The panel has no edit control, since activity is not edited.

### What the panels show (2026-11-16) — adopted

Project-level and dataset-level events, 8 lines, a link to the full list (D14, D11).

## Unknowns settled

- **Where the work lives.** A new contrib app, `fairdm.contrib.activity`, installed with the other
  contrib apps. It owns the receivers that record actions, the code that gathers lines, the
  full-list pages and the templates. The core models do not import it.
- **What an action names.** django-activity-stream needs an actor. A receiver has no requesting
  user, and the line names the record, not who made the change (D8). So:
  - details edited: actor the project or dataset, verb `edited`;
  - published: actor the dataset, verb `published`;
  - contributor added: actor the contributor, verb `joined`, target the project or dataset.

  Project, Dataset and Contributor (with Person and Organization) are registered with
  django-activity-stream's `registry`.
- **What counts as details edited.** A save of a project or dataset in which a field other than
  `modified`, `visibility` and `published` changed (D1 leaves visibility out, and publishing is its
  own line), and a save or deletion of one of its descriptions, dates or identifiers. Keywords and
  tags are many-to-many and change without a save of the record: they are left out, and the
  documentation says so.
- **Recording never fails the change (FR-003).** Each action is sent inside a savepoint. An error
  is logged and swallowed.
- **Gathering.** Each source returns its newest lines already grouped in the database: samples and
  measurements by dataset and `TruncDate("added")`, edits by record and day. Each source is cut to
  the number of lines wanted, the sources are merged by latest time, and the merged list is cut
  again. A line among the newest 8 overall is among the newest 8 of its own source, so the result
  is exact. The number of queries is constant, while the rows each grouping reads grow with the
  scope's history, so the timing at the browser pass is the evidence for SC-004.
- **Who sees what (FR-012).** The project page is already open to its viewer. Its panel takes its
  datasets from `Dataset.all_objects.visible_to(user).filter(project=project)`, and every
  dataset-level line, sample and measurement counts and contributors joining a dataset included, is
  limited to those. Visibility is read when the page is drawn (D3). A deleted dataset's actions name
  no dataset in that set and fall out (FR-015).
- **The full list.** One plugin per record type, `url_path="activity"`, behind the same check as the
  overview page, drawing the same lines a page at a time through Django's `Paginator`. The merged
  sequence supports `len()` and slicing, which is all `Paginator` asks of an object list.
- **Indexes.** Grouping a project's samples by dataset and day reads `dataset_id` and `added`, and
  both tables are already indexed on `dataset_id`. SC-004 is measured at the browser pass on a
  seeded project of 50 datasets. An index on `(dataset_id, added)` is added only if that
  measurement asks for it.

## What already exists

- record an action as not public · 3, package · `actstream.action` (`actstream/actions.py`)
- registry of models that act · 3, package · `actstream.registry.register`
- list of activity rows and its empty state · 3, package · `cotton/mvp_community/activity/feed.html`
- one activity row · 3, package · `cotton/mvp_community/activity/entry.html`, overridden for the look
- panel with heading and See all · 2, this repo · `cotton/overview/panel.html`
- datasets a viewer may open · 2, this repo · `DatasetQuerySet.visible_to` (`dataset/models.py:150`)
- check for the full list page · 2, this repo · `project_is_visible`, `dataset_is_visible`
- refusing a private record with a 404 · 2, this repo · `PrivateRecordNotFoundMixin`
- changed fields on save · 3, package · django-model-utils `FieldTracker`, `BaseModel.tracker`
- day in the portal's zone · 4, Django · `django.db.models.functions.TruncDate`
- paging the full list · 4, Django · `django.core.paginator.Paginator`
- day label "Today", "Yesterday" · 3, package · `django.contrib.humanize` `naturalday`
- singular and plural counts · 4, Django · `ngettext`
- record colour square · 2, this repo · `.record-*` classes (`static/css/fairdm.css:429-447`)
- the activity icon · 2, this repo · `EASY_ICONS["activity"]` (`addons.py:112`)
- the panel component, `Line`, the two full-list pages and their template · 7, new · searched
  `cotton/overview/` and the record sub-page plugins: none draws activity
- gathering lines from several sources · 7, new · searched django-activity-stream's managers and
  streams (one object, or the public site), django-mvp-community's components (they draw a given
  list), this repo's overview helpers (`core/overview.py`): nothing merges grouped rows across models
- receivers recording edits, publishing and joining · 7, new · searched `project/receivers.py`
  (empty), `contributors/receivers.py` (roles only), django-lifecycle hooks (contributors only)
