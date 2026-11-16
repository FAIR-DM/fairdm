# Planning notes: show recent activity on project and dataset pages

Notes for research and planning. The plan answers each one by name.

## The prototype this feature comes from

Branch `prototype-overview-pages`, its hand-over document `PROTOTYPE.md` at the branch's root, and
this feature's part of it: "F3. Recent activity on a project or dataset". The prototype is
https://github.com/FAIR-DM/fairdm/issues/668, and its "Decisions" bind this feature. The branch is
read, never merged and never branched from.

## Build it on django-mvp-community's activity extra

"This will require installing Django-mvp-community." Use the `activity` extra of
https://github.com/django-mvp/django-mvp-community, which is built on django-activity-stream and
supplies the list of activity, `<c-mvp_community.activity.feed :actions="…" />` (its
`docs/developer/activity.md`). FairDM adds the dependency, registers its records, records an action
when something happens to one, chooses the actions a viewer may see, gathers them into lines and
passes them to that component inside its own panel. django-mvp-community is used as published and
is not edited (decisions.md, D5).

## The prototype's activity is replaced, not ported

From the hand-over's shared pieces: Activity, at `overview_proto.py:149` (`activity`), "Replaced by
actions recorded with django-activity-stream", now shown through django-mvp-community's list of
activity, which FairDM hands the lines it chooses (decisions.md, D5). Built by this feature. The
prototype's function is evidence of what the panel shows (additions gathered by dataset and day),
not code to keep.

## The panel is the one the redesigned pages build

From the hand-over's shared pieces: Panel, "heading, count, 'See all', an edit control", at
`cotton/ov/panel.html` and inside `cotton/ov/activity.html:8`. It is built by the first pull
request of https://github.com/FAIR-DM/fairdm/issues/672 (the shared page and the project page), and
this feature reuses it, its "See all" link leading to the full list (decisions.md, D11). That work
is on `main`, as `cotton/overview/panel.html`.

## The look is ported

`fairdm/templates/cotton/ov/activity.html` lands as FairDM's Recent activity panel, on the
overview panel `main` already has, with a template override of django-mvp-community's activity row
where its look differs from the prototype's line. The plan names each file it
ports and where it lands in `main`. A plan that redraws a screen the prototype already has fails the
design review. Every merge is checked side by side against the prototype's screens for this
feature: the project page `/projects/p2u5RQQxsGcHgpnCE6TMcJQ/` and the dataset page
`/datasets/dAKZzsr4nsJSL4WMHeK4zao/` on the prototype's database, at 390 and 1440 pixels wide,
signed out and signed in as `regular.user@example.com` (on the team) and
`regular.user2@example.com` (not on it).

## Design rules the maintainer gave during the prototype

As written on https://github.com/FAIR-DM/fairdm/issues/668:

- Every badge is a pill.
- No central Manage menu. Each part of the record is edited from the panel that shows it.
- Map tile credits start closed, behind their (i) button.
- A change to one element keeps everything else where it was: a swap keeps the old element's
  placement, size and fade.

## What the panels show (the maintainer, 2026-11-16)

Project-level and dataset-level events only, the newest 8 lines, with a link to the full list:
datasets created and published, the project's and its datasets' details edited, people joining the
project or a dataset, and the per-day count of samples and of measurements added to each dataset,
one line per dataset per day. A sample's or measurement's own changes never appear on the project
or dataset panels (decisions.md, D14).
