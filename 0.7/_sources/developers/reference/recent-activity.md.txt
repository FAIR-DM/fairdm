# Recent activity

The Recent activity panel on the project and dataset pages, and each record's full list of activity, come from `fairdm.contrib.activity`. This page lists what that app records, the classes and functions that gather the lines, and the pages that draw the full list. The panel's component is described on [Components](components.md#c-overviewactivity) and its block on [Overview page blocks](overview-page-blocks.md).

## What is recorded

`fairdm.contrib.activity.receivers` records three kinds of event as django-activity-stream actions, each with `public=False`:

| Verb | Constant | Recorded when | Actor | Target |
|---|---|---|---|---|
| `edited` | `EDITED` | A project or dataset is saved with a field changed other than `modified`, `visibility` and `published`, or one of its descriptions, dates or identifiers is saved or deleted on its own | The project or dataset | None |
| `published` | `PUBLISHED` | A dataset is created published, or its `published` flag is set | The dataset | None |
| `joined` | `JOINED` | A contributor is credited on a project or dataset | The contributor | The project or dataset |

`record(actor, verb, target=None)` sends one action inside a savepoint. A failure is logged and never reaches the save that caused it.

Additions are not recorded. A project or dataset created, and the samples and measurements added to a dataset, are worked out from each record's own `added` time when the page is drawn. ADR 0045 gives the reasons.

Do not include `actstream.urls` in a portal's URLs: some of django-activity-stream's views show actions that are not public, to anyone.

## Gathering the lines

`fairdm.contrib.activity.lines`:

| Name | What it is |
|---|---|
| `ActivityLines(record, user)` | The lines of a project or dataset for one viewer, newest first. A project covers itself and the datasets the viewer may see. A dataset covers itself. It is sliced, never indexed, and `len()` counts its lines in the database, so a `Paginator` can page it. |
| `Line` | One line: `timestamp`, `day` (the portal's day), `kind` (`project`, `dataset`, `sample` or `measurement`, the record colour), `html` (the sentence, escaped and linked) and `count`. |
| `Day` | One day's lines: `day` and `lines`. |
| `Row` | What one source found before the records it names are fetched: `timestamp`, `day`, `source`, `model`, `record_id`, `count` and `contributor_id`. Used inside `ActivityLines`. |
| `group_days(lines)` | Lines in order, grouped into `Day` items. |
| `recent_activity(record, request)` | The panel's context: `days`, the newest 8 lines grouped by day, and `more_url`, the full list's address when there are more, or an empty string. |
| `PANEL_LINES` | How many lines the panel shows: 8. |

Samples and measurements count only when the viewer may see them, by their managers' `visible_to()`, as the page's own figures do. A measurement counts in the dataset it belongs to.

## The full list

`fairdm.contrib.activity.plugins`:

| Class | Registered on | Address | Name |
|---|---|---|---|
| `ActivityList` | Base class | | |
| `ProjectActivity` | `Project` | The project's address followed by `activity/` | `project:activity` |
| `DatasetActivity` | `Dataset` | The dataset's address followed by `activity/` | `dataset:activity` |

Each is registered with `menu=False`, so it adds no tab, and applies the record page's own check, so a private record answers "not found" wherever its page does. It draws 25 lines a page, `paginate_by`, through `activity/activity_list.html`, and answers "not found" for a page number that does not exist.
