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
portal later, then shows none of them (FR-012).

## D5 — A dependency on django-mvp-community: the recent-activity component takes the actions to show

As published (0.1.4), `<c-mvp_community.activity.recent :object="…" />` shows the public actions
that name the object itself as actor, target or action object. That falls short of this feature in
two ways:

- A project's panel must show its datasets' activity too (FR-005). An action names at most three
  objects, and a sample added to a dataset does not name the project.
- What a viewer sees depends on who may open each record (D3, D4). The component shows every public
  action to everyone, and FairDM's actions are not public.

The component needs a way for a project to hand it the actions to show, already chosen and in
order, with its limit, its empty state and its "more" link working as they do now. That is a change
to django-mvp-community, the maintainer's own package, and this feature depends on it. It is not
worked round in FairDM by drawing the actions some other way.

Gathering entries by record and day (D2) and grouping them by day is FairDM's look on these pages,
and comes through FairDM's override of the component's template.

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

## D11 — The newest few entries, with no page of all activity

The panel shows a fixed number of the newest entries, as the prototype does. The request asks for
recent activity, not a history browser, and the prototype has no page for it. A page listing a
record's whole history is a separate idea, and the activity package's feed view would make it
cheap to add later.

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
