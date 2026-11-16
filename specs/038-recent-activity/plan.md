# Implementation Plan: show recent activity on project and dataset pages

**Branch**: `038-recent-activity` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

A new contrib app, `fairdm.contrib.activity`, records the three events that leave no other trace
(a dataset published, a project's or dataset's details edited, a contributor added to a project or
dataset) as not-public django-activity-stream actions. When a project or dataset page is drawn, it
gathers the record's lines from those actions and from the `added` times of its datasets, samples
and measurements, limited to what the viewer may open, grouped by record and day in the database,
and hands the newest 8, one item per day, to django-mvp-community's list of activity inside the
overview panel. FairDM's override of the package's row draws the prototype's day. A full list of each record's
activity, a page at a time, sits at `activity/` under the record. django-mvp-community is used as
published.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-cotton components.
- **New dependencies**: `django-mvp-community[activity] (>=0.1.4,<0.2.0)` and
  `django-activity-stream (>=2.0,<3.0)`, declared directly since FairDM imports it.
- **Storage**: django-activity-stream's own tables and migrations. No FairDM model changes and no
  FairDM migration.
- **Testing**: pytest with pytest-django, against PostGIS. Tests are grouped in `Test<Subject>`
  classes in the module that mirrors the source file. No test of text content or layout.

## Constitution Check

- **Simplicity**: one app, three receivers, one gathering class, one panel component, one template
  override, two list pages. No setting and no hook: a portal changes the panel by overriding the
  `overview.activity` block or the templates.
- **Privacy first**: every line is limited to the datasets the viewer may open, and the sample and
  measurement counts to the records the viewer may see, as the page's own figures are. Actions are
  recorded not public, so no feed the package offers can show them, and FairDM mounts none.
  django-activity-stream registers its actions in the administration interface, where only
  superusers reach them: no role FairDM ships holds its permissions.
- **Established packages over custom code**: recording is django-activity-stream's, the list is
  django-mvp-community's. FairDM writes only what neither does: merging grouped lines across models.
- **Works without custom JavaScript**: the panel and the list are plain HTML.

## What is ported

From `prototype-overview-pages`, read with `git show origin/prototype-overview-pages:<path>`:

| Prototype | Lands on `main` as |
|---|---|
| `fairdm/templates/cotton/ov/activity.html` | `fairdm/contrib/activity/templates/cotton/overview/activity.html`, the panel around the package's list |
| its day `<li>`: `ov-activity__day` and the `ov-activity__events` lines | `fairdm/contrib/activity/templates/cotton/mvp_community/activity/entry.html`, the package's row overridden to draw one day |
| `.ov-activity` rules, `static/css/overview.css:555-562` | `fairdm/static/css/fairdm.css`, beside `.ov-history`, applied to the package's list inside the panel with the card's frame taken off; values unchanged but for the variable names `main` uses |
| the `overview.activity` block in both detail templates | the same block, at the same place, after `overview.map` |

The day's markup, its class names and the day label (`naturalday:"j M Y"|capfirst`) are copied.
Two deviations from the prototype, both shown at the walkthrough:

- The empty state is the package's own, with "Nothing has happened yet." as its heading, not the
  prototype's muted sentence: the package's list draws it (D17).
- The dataset page shows the panel always, not only when the dataset has records the viewer may
  see, since publishing, edits and people joining are activity too (FR-004).

## Dependency and settings

- `pyproject.toml`: `django-mvp-community[activity] (>=0.1.4,<0.2.0)` beside the other mvp packages,
  and `django-activity-stream (>=2.0,<3.0)`. `uv lock`, `uv sync`. deptry: `mvp_community` is used
  from settings and templates only, so `django-mvp-community` goes in the `DEP002` ignore list;
  `django-mvp-community` → `mvp_community` and `django-activity-stream` → `actstream` in
  `package_module_name_map`.
- `fairdm/core/project/models.py` and `fairdm/core/dataset/models.py`: `tracker = FieldTracker()`
  on `Project` and `Dataset`, and the declaration removed from `BaseModel` in
  `fairdm/core/abstract.py` (D19). No migration.
- `fairdm/conf/settings/apps.py`, `INSTALLED_APPS`:
  - `fairdm.contrib.activity` with the other contrib apps;
  - `mvp_community` after `mvp_accounts`, so the Account Center keeps `mvp_accounts`' page
    (research.md), and after `fairdm.contrib.activity`, so FairDM's row wins;
  - `actstream`.
  A test pins both orders by what renders, not by the list.
- `ACTSTREAM_SETTINGS` (`addons.py:12`) stays as it is. No URLs of either package are included.

## Recording (`fairdm/contrib/activity/receivers.py`, connected in `apps.py`)

`ActivityConfig.ready()` registers `Project`, `Dataset`, `Contributor`, `Person` and `Organization`
with `actstream.registry` and imports the receivers.

- `record(actor, verb, target=None)`: `actstream.action.send(actor, verb=verb, target=target,
  public=False)` inside `transaction.atomic()`. Any exception is logged with `logger.exception` and
  swallowed (FR-003). The verbs are module constants `EDITED`, `PUBLISHED`, `JOINED`.
- `post_save` on `Project` and `Dataset`, not created: when
  `instance.tracker.changed()` has a field other than `modified`, `visibility` and `published`,
  `record(instance, EDITED)`.
- `post_save` on `Dataset`: when `instance.published` is true and either the dataset was just
  created or `published` is in `tracker.changed()`, `record(instance, PUBLISHED)`.
- `post_save` and `post_delete` on `ProjectDescription`, `ProjectDate`, `ProjectIdentifier`,
  `DatasetDescription`, `DatasetDate`, `DatasetIdentifier`: `record(instance.related, EDITED)`.
  A deletion cascading from the record itself records nothing: skip when `origin` is not the row.
- `post_save` on `Contribution`, created, with a contributor, whose `content_type_id` is
  `Project`'s or `Dataset`'s (compared before `content_object` is read, so a credit on a sample
  costs no query): `record(instance.contributor, JOINED, target=instance.content_object)`. Samples and
  measurements record nothing.

## Gathering (`fairdm/contrib/activity/lines.py`)

`Line`, a frozen dataclass: `timestamp` (the newest event it covers), `day` (a `date`), `kind`
(`project`, `dataset`, `sample` or `measurement`, the record colour), `html` (the sentence, a
`SafeString`).

`ActivityLines(record, user)`, a sequence:

- The scope. For a project: the project, and its datasets
  `Dataset.all_objects.visible_to(user).filter(project=record)`. For a dataset: the dataset alone,
  no project. The page has already decided the viewer may open `record`.
- `__getitem__(slice)` with a `stop` of n: each source below returns its newest n rows, already
  grouped and ordered by their newest time. The rows become `Line`s, are merged by `timestamp`
  descending and cut to the slice. Records named by the lines are fetched once each with
  `in_bulk`. A plain index is refused: the panel and `Paginator` only slice.
- `__len__`: the sum of each source's grouped row count. Only the full list asks for it.
- The sources:
  1. Samples added: `Sample.objects.visible_to(user)` in the scope's datasets, grouped by
     `dataset_id` and `TruncDate("added")`, `Count("pk")` and `Max("added")`. The viewer's
     visibility of samples is the page's own rule for its Samples figure, so a public dataset
     whose records are not yet published shows no counts to a visitor (D18).
  2. Measurements added: the same on `Measurement`, by the measurement's own `dataset_id` (D7).
  3. Datasets created: the scope's datasets by `added`.
  4. The project created: on a project's page only, one line at `project.added`.
  5. Details edited: actions with verb `EDITED` whose actor is the project or one of the scope's
     datasets, grouped by actor and `TruncDate("timestamp")`.
  6. Datasets published: actions with verb `PUBLISHED` whose actor is one of the scope's datasets.
  7. Contributors joining: actions with verb `JOINED` whose target is the project or one of the
     scope's datasets. Registering a model with django-activity-stream gives it generic relations
     to its actions (`actstream/registry.py:13-43`), so deleting a contributor or a dataset deletes
     its actions.

  Actions are matched on content type and on `*_object_id` against the scope's keys cast to text
  (`object_id` is a `CharField`), as `core/managers.py:97-103` does, and only `public=False`
  actions are read.
- The sentences, `format_html` over `gettext`/`ngettext` with named placeholders, the record's name
  linked to its page. On the record's own page, the line about it leaves the name out, as the
  prototype's `here` did:

  | Source | Elsewhere | On its own page |
  |---|---|---|
  | samples | `{count} samples added to {dataset}` | `{count} samples added` |
  | measurements | `{count} measurements added to {dataset}` | `{count} measurements added` |
  | dataset created | `Dataset created: {dataset}` | `Dataset created` |
  | project created | | `Project created` |
  | edited | `Details edited: {dataset}` | `Details edited` |
  | published | `Dataset published: {dataset}` | `Dataset published` |
  | joined | `{contributor} joined {record}` | `{contributor} joined` |

  Counts use `ngettext`, with `intcomma`'s grouping.
- `group_days(lines)`: the lines grouped into `Day` items, `day` and `lines`, in order. A `Day` is
  what the package's list is handed, one row each.
- `recent_activity(record, request)`: the panel's context, `{"days": …, "more_url": …}`, reading 9
  lines, grouping the newest 8 into days, and giving the full list's address only when there is a
  ninth.

Constant query count: the scope's dataset keys are a subquery, never a list in Python, and the
named records are two `in_bulk` calls (datasets, contributors), so a page asks the same number of
queries for one dataset as for fifty (SC-004).

## The panel and the overrides

- `cotton/overview/activity.html`: `<c-vars days more_url />`, a `c-overview.panel` titled
  "Recent activity" with `more_url`, `data-card="activity"` and the class `ov-activity`, holding the
  package's list unchanged: `<c-mvp_community.activity.feed :actions="days" only />`.
- `cotton/mvp_community/activity/entry.html`, the only override: it is handed one `Day` as
  `action` and draws `<li class="list-row ov-activity__row">` with the prototype's
  `ov-activity__day` label and its `ov-activity__events` list, one
  `<li class="record-{{ line.kind }}"><span>{{ line.html }}</span></li>` per line. Its
  `@description` says it draws a FairDM day.
- `project_detail.html` and `dataset_detail.html`: `{% block overview.activity %}` after
  `overview.map`, `<c-overview.activity :days="activity.days" more_url="{{ activity.more_url }}" />`.
- `Overview.get_context_data` on the project and dataset plugins adds
  `activity = recent_activity(record, request)`.

## The full list (`fairdm/contrib/activity/plugins.py`)

`ProjectActivity` and `DatasetActivity`, each `PrivateRecordNotFoundMixin, Plugin,
FairDMTemplateView`, registered on their model with `url_path="activity"` and `name="activity"`,
passing `menu=False` to `plugins.register(...)` (the keyword, `registration.py:182`, not the class
attribute; the prototype has no Activity tab), and the overview page's own check
(`project_is_visible`, `dataset_is_visible`). The template `activity/activity_list.html` extends the
record page shell the other record sub-pages use and draws `ActivityLines` a page of 25 lines at a
time through `Paginator` and the pagination component the record lists already use, each page's
lines grouped into days and drawn through the same panel and list. Addresses: `project:activity`, `dataset:activity`.

## Specifications edited

- `specs/018-overview-pages/spec.md`: FR-016 no longer lists recent activity for project and dataset
  pages, and keeps it for person and organization pages (D13).

## Documentation

- `docs/users/`: the page describing a project's and a dataset's page gains a section on Recent
  activity: the events it shows, one line per dataset and day for additions, who sees what, the
  full list, what an upgraded portal shows of its past, and that keyword and tag changes are not
  shown.
- `docs/developers/reference/overview-page-blocks.md`: `overview.activity` in the project and
  dataset rows, and `activity` in the context table.
- `docs/developers/reference/components.md`: `c-overview.activity`, and that FairDM overrides
  django-mvp-community's activity list and row.
- `CHANGELOG.md`: under `[Unreleased]`, Added.

## Tests

`tests/test_contrib/test_activity/test_receivers.py`:

- `TestRecordEdits`: editing a project's or dataset's name records one `edited` action, not public,
  with the record as actor; a record fetched with `objects.get()` and saved with a new name records
  one, and saved again unchanged records none (this fails while the tracker is missing); a save that
  changes nothing records none; a visibility-only change
  records none; saving and deleting a description, date or identifier records `edited` on its
  record; deleting the record records nothing new.
- `TestRecordPublished`: setting `published` records `published` and not `edited`; a dataset
  created published records `published`; saving an already published dataset records nothing.
- `TestRecordJoined`: crediting a person on a project and on a dataset records `joined` with the
  contributor as actor and the record as target; crediting one on a sample records nothing.
- `TestRecordingNeverFails`: with `action.send` patched to raise, the save succeeds and the error
  is logged.

`tests/test_contrib/test_activity/test_lines.py`, `TestActivityLines`, each pinning kinds, counts
and order, never wording:

- Scenarios 1-9: a line per source; samples on two days give two lines; samples on two datasets
  give two lines; measurements apart from samples; a measurement counted in its own dataset and not
  its sample's. Each line's html carries the named record's `get_absolute_url()`, and a joined
  line the contributor's.
- Scenario 11: one sample-count case is seeded with `ConcreteSampleFactory`, a portal-defined type.
- Escaping: a dataset and a person named `<b>x</b>` give lines whose html holds the escaped form
  and not the tag.
- Scenario 10 and FR-014: sample edits and a contributor on a sample give no line.
- Scenario 12: lines newest first, days contiguous.
- Scenario 13: with `TIME_ZONE` set to a zone east of UTC, a sample added at 23:30 local falls on
  the local day.
- Scenario 14: nine lines seeded, `recent_activity` gives eight and a `more_url`; eight seeded, no
  `more_url`.
- Scenarios 18-22: a private dataset's lines absent for a visitor and for a signed-in stranger,
  present for its team member; made public later, its earlier lines appear; made private, they go.
  A public, unpublished dataset shows a visitor no sample count.
- Scenarios 24-25: a deleted sample leaves the count; all deleted, no line; a deleted dataset's
  edits, publishing and contributors give no line.
- Scenarios 26-27: records created with recording switched off still give their additions.
- Edge case: a dataset moved to another project gives its lines on the new project only.
- `len()` equals the number of lines a full slice returns.
- `django_assert_num_queries` gives the same count for a project with one dataset and with five,
  each with samples, measurements and actions. The timing in "Proof of scale" is SC-004's evidence.

`tests/test_contrib/test_activity/test_plugins.py`, `TestActivityPage`: both addresses answer for a
public record; a private record answers 404 to a visitor and a stranger and 200 to its team; 30
lines give two pages, the second holding five.

`tests/test_templates/test_activity.py`:

- `TestActivityPanel`: two days render two `ov-activity__row` items, each with its lines and
  `record-<kind>` classes; no days renders the package's empty state and no row; `more_url` renders
  the panel's See all link, none renders none.
- `TestOverrides`: the package's list draws FairDM's row (an `ov-activity__row`, no avatar), and the
  Account Center renders `mvp_accounts`' page.
- The project and dataset pages each render `data-card="activity"`.

`tests/test_contrib/test_activity/test_apps.py`, `TestNoOtherFeed` (scenario 23, FR-013): no address of
`mvp_community_activity` or `actstream` resolves, and every action recorded is not public.

## Proof of scale (SC-003, SC-004)

At the browser pass: seed one project with 50 datasets, 20,000 samples spread over a year and their
actions, and time the project page against a project with one dataset. Record both in the ledger.
This is the evidence for SC-004, and the `(dataset_id, added)` index is added only if it asks.
SC-003 needs no measurement: an addition records nothing.

## What is not built

- No change to django-mvp-community (D5).
- No action per sample or measurement, and no data migration (D16).
- No line for keyword or tag changes, visibility changes, deletions, or a contributor removed.
- No Activity tab, no site-wide feed, no following.
- No test of wording, translation or layout.
