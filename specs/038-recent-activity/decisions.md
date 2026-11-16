# Decisions: show recent activity on project and dataset pages

Each decision below was made without putting it to the maintainer, from the request, the
prototype he has seen and liked, and his decisions on
https://github.com/FAIR-DM/fairdm/issues/668. Each can be overturned before the build starts.

## D1 — The events shown

Shown: a project created, a dataset created, samples added to a dataset, measurements added to a
dataset, a dataset published, a project's or dataset's details edited, and a contributor added to
a project or dataset.

Not shown: edits to samples and measurements, contributors added to samples and measurements,
deletions and visibility changes.

The request names additions, publishing, edits and people joining. On a project or dataset page,
the reader wants to know what happened to that project or dataset. A portal edits samples and
measurements in bulk, and an entry per sample edit would bury everything else. A sample's own
history is its timeline on the sample page. A deletion leaves nothing to link to, and the reader of
a deleted record's page is not on it. Publishing already covers the visibility change a reader
cares about.

## D2 — Additions and edits are gathered by record and day

The samples added to one dataset on one day are one entry with a count, and so are the
measurements. Edits to one record's details on one day are one entry.

This is what the prototype shows, and it is what keeps an import of thousands of samples from
filling the panel. Whether each addition is recorded on its own and gathered when shown, or
recorded once per batch, is for the plan. The reader sees the same either way.

## D3 — Visibility is judged when the page is viewed

An entry is shown only to a viewer who may open the record it is about, judged when the page is
viewed. Judging it when the activity was recorded would be simpler, and wrong twice over: a
dataset made public later would hide its own history from everyone, and a dataset made private
later would keep showing its history to people who may no longer open it. Specification 018's rule
for who may open a record is used unchanged.

## D4 — Activity is recorded as not public in the activity package

django-activity-stream marks each action public or not, and django-mvp-community's feeds,
following page and recent-activity component show public actions to everyone, with no regard to
who may open the records they name. FairDM's records have their own visibility, which those feeds
cannot see. So every action FairDM records is marked not public, and FairDM chooses which actions a
viewer sees itself (D3). Any feed the activity package offers, whether mounted by FairDM or by a
portal later, then shows none of them (FR-013).

## D5 — FairDM chooses the lines and hands them to django-mvp-community's list of activity

The maintainer's decision (2026-11-16): django-mvp-community is not changed. Its recent-activity
component shows the public actions around one object, and changing it to take a chosen list is
outside that package's bounds.

FairDM chooses the actions for a project or dataset itself, keeps those about records the viewer
may open (D3, D4), gathers them into lines (D2) and passes them to the package's existing
`<c-mvp_community.activity.feed :actions="…" />` component, which already draws whatever list it is
given and its empty state. The heading, the "See all" link and the grouping by day come from
FairDM's own overview panel. Where the package's row does not look like the prototype's line,
FairDM overrides the row's template, as the package's documentation allows. The package itself is
not edited.

## D6 — The project page includes its datasets' activity

The prototype's project panel lists samples and measurements added to each dataset, and datasets
created. A project's own events alone would leave a project page nearly empty, since a project
changes little once its datasets exist.

## D7 — A measurement counts in the dataset it belongs to

A measurement can belong to one dataset while its sample is in another (CONTEXT.md, Measurement).
It is added to the dataset it belongs to, and the team of that dataset made it, so that is where it
counts. Its visibility follows that dataset too.

## D8 — Entries name the record, not who made the change

As in the prototype. One entry can gather the additions of several people on one day, so naming
one of them would be wrong, and naming them all would make the panel a list of people. The entry
for a contributor added names the contributor, since that is the event. Who made a change belongs
to revision history (https://github.com/FAIR-DM/fairdm/issues/170).

## D9 — Days are the portal's own

Entries fall on the day in the portal's configured time zone. FairDM sets no per-viewer time zone
anywhere else, and a research group's portal serves one community, usually in one region.

## D10 — An upgraded portal shows its past additions

The prototype works activity out from when records were added, so the pages it showed the
maintainer already have history. An upgrade that left every existing project's panel empty until
the next change would be a step back from what he approved. Every record already carries when it
was added, so the creation of projects and datasets and the additions of samples and measurements
are shown from that date. Publishing, edits and contributors added before the upgrade were never
recorded, and nothing pretends they were.

## D11 — The newest 8 lines, with a link to the full list

The maintainer's decision (2026-11-16). The panel shows the newest 8 lines and links to a page
listing all of the record's activity, one for each project and each dataset, newest first, grouped
by day and paged. The page applies the same rule for who sees what as the panel (D3), so it is
FairDM's own page, not the activity package's feed view, which shows public actions only.

## D12 — Sample, measurement, person and organization pages are left out

The prototype puts the panel on project and dataset pages only. The sample page shows its history
as a timeline (https://github.com/FAIR-DM/fairdm/issues/672). Person and organization pages keep
their "not yet available" card from specification 018.

## D13 — Specification 018 is amended, not replaced

Specification 018 lists recent activity as not yet available (FR-016, FR-017). For project and
dataset pages that statement stops being true. The pull request that delivers this feature edits
018 so FR-016 no longer lists recent activity for project and dataset pages, and it keeps the item
for person and organization pages. The placeholder card on the project page is removed by
https://github.com/FAIR-DM/fairdm/issues/672.

## D14 — The project and dataset pages show project-level and dataset-level events only

The maintainer's decision (2026-11-16). The project panel shows datasets created and published,
the project's and its datasets' details edited, people joining the project or one of its datasets,
and per day one line per dataset counting the samples added to it, and one counting the
measurements. A sample's or measurement's own changes never appear on either page. The dataset
panel follows the same rule for the dataset alone.

## D15 — A project's own creation stays on its panel

The maintainer's list for the project panel names its datasets' creation and not the project's own.
His rule is "only project-level and dataset-level events", and a project being created is one, so it
stays, as the first line of a project's history. It is one line, at most, in a project's life.

## D16 — Additions are counted from when each record was added

Samples and measurements added, and projects and datasets created, are worked out from each
record's own `added` time, as the prototype does. Only the events that leave no other trace are
recorded as actions: a dataset published, details edited, a contributor added.

Counting from `added` counts only what still exists (FR-015), shows an upgraded portal's past with
no migration (FR-016, SC-005), and adds nothing to an import (SC-003). Recording an action for each
sample would need all three solved again.

## D17 — The package's list draws the days, and FairDM's row draws one day

django-mvp-community's list, `<c-mvp_community.activity.feed :actions="…" />`, is used as
published: a card holding a list, one row per item it is handed, or its own empty state. FairDM
hands it one item per day, newest day first, each holding that day's lines. FairDM overrides only
the row, `cotton/mvp_community/activity/entry.html`, which the package documents as a template a
project may override, so that a row draws the prototype's day: the date beside its lines, each line
a square in its record's colour. The card's frame is taken off inside FairDM's panel by FairDM's
stylesheet, so the panel reads as the prototype's. When there is nothing to show, the package's own
empty state is drawn. FairDM includes none of the package's pages, so nothing else draws through the
overridden row.

**ADR:** none — local to this feature's templates, and the package's documentation already names
the row as an override point.

## D18 — Sample and measurement counts follow who may see the records

A line counting samples or measurements added to a dataset counts only the records the viewer may
see, by the same rule as the page's own Samples and Measurements figures. A visitor reading a
public dataset whose data is not yet published sees the dataset's other lines and no counts, as
the page shows them no samples.

## D19 — Projects and datasets declare their own change tracker

The design review found that `tracker = FieldTracker()` on the abstract `BaseModel` never takes
effect: django-model-utils sets the tracker up when a model's class is prepared, which Django does
for concrete models only, so `Project`, `Dataset`, `Sample` and `Measurement` have no `tracker` at
all. Recording an edit needs to know what changed, so `Project` and `Dataset` each declare their own
tracker, and the dead declaration on `BaseModel` is removed. A tracker is not a field and needs no
migration. django-lifecycle's `has_changed()` is not used: it resets on commit, and the portal runs
each request in one transaction.
