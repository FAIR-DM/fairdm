# ADR 0045: Recent activity is recorded hidden and read through the records' rules

**Status:** accepted

## Decision

`fairdm.contrib.activity` records with django-activity-stream only the events that leave no other
trace: a dataset published, a project's or dataset's details edited, and a contributor added to a
project or dataset. Every action is recorded with `public=False`.

Additions are never recorded as actions. A project or dataset created, and the samples and
measurements added to a dataset, are worked out when a page is drawn from each record's own `added`
time.

What a viewer sees is decided when the page is drawn, from the records' visibility and the viewer's
levels as they stand then. `ActivityLines` limits every line to the datasets the viewer may see
(`DatasetQuerySet.visible_to`), and the sample and measurement counts to the records the viewer may
see (`visible_to` on their managers). No other page FairDM ships shows the actions. FairDM
includes neither `actstream.urls` nor django-mvp-community's activity URLs, and a portal must not
include `actstream.urls` either: some of django-activity-stream's own views show actions that are
not public, with no regard to who may open the records they name. The administration interface
lists the actions to staff who hold django-activity-stream's view permission, which no role FairDM
ships grants.

## Why

FairDM's records carry their own visibility, which a portal changes after the fact: a private
dataset is made public, or a public one private. django-activity-stream's only rule is the action's
`public` flag, fixed when the action is recorded, so its feeds cannot follow a change of visibility
and would show a private dataset's activity to everyone, or hide a dataset's past once it went
public. Recording every action hidden and reading it through FairDM's own rules keeps the two in
step.

Counting additions from `added` counts only the records that still exist, gives an upgraded portal
its history with no data migration, and adds nothing to an import of thousands of samples. Recording
an action per sample would need each of those solved again.

## Revisit if

A page outside a record's own pages needs this activity, such as a site-wide feed or a person's
page. It must then apply the same rules, or the actions must start carrying what such a page needs
to decide.
