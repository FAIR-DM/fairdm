# Sketch: 023-shared-record-list-tabs

## What exists

- Every registered sample and measurement type has a generated table, filter set and search, used
  by the portal-wide listings under `/collections/`. Those listings show published records outside
  private projects only, and their filter choices are scoped the same way.
- `visible_to(user)` on sample and measurement querysets returns what a viewer may see, decided by
  each record's own dataset. `visible_to(None)` is the released set: public, published and not in a
  private project.
- A contributor's credits on samples and measurements are read with `credited_object_ids`. Its
  credits on datasets and projects are contributions on those records. An organization owns
  projects through `Project.owner`.
- The dataset and project overviews already count samples and measurements in their figures.
- The portal-wide listing switches between types with a dropdown at the trailing edge of the table
  toolbar. The sketch uses the same control.

## What the screens need from the code

- One list of the types present on the page, with a count each, for the viewer, before the table is
  built.
- On a contributor's page, the records credited directly, through a dataset and through a project,
  and for an organization through the projects it owns, private records included in the scope so
  the person's own page can show them.
- Whether every hidden record sits in a public dataset that is not published, to tell the "not
  published yet" state from "no records".
- The set of datasets the viewer may open, once per page, so each row's dataset is linked only
  where it opens.
- Filter choices drawn from the records the viewer may see on this page.
- The dataset and project overviews' sample and measurement counts, for the same viewer, equal to
  what the tabs list.

## What the sketch faked

- Filter choices use the portal-wide listings' published-only scoping. A team member or a person on
  their own page is offered choices that leave out their unpublished records.
- A measurement's sample is named and linked when the viewer may see samples in its dataset, and
  shown as a dash otherwise. A sample opened only by a credit on the sample itself is missed.
- The tab stays marked in the tab strip on a type's own address by rewriting the request's resolved
  view name. The tab strip needs a real way to count a tab's sub-addresses as the tab.
- The table view replaces the page metadata, so the breadcrumb trail is put back by hand.
- The project overview's sample and measurement counts are not checked against what the tabs list.
- The query count is not measured.
- The tabs are loaded from `fairdm/contrib/contributors/plugins/__init__.py`, because that app is
  discovered after the core record apps.
- The development data is a new command, `seed_record_lists`, beside the overview seeds.

## What was ruled by eye

- The heading names the type shown. Where several types are listed, the heading is the switcher:
  the type's name with a caret, opening a menu of each type with its count. Where one type is
  listed, the heading is the type's name with no caret. The menu sits outside the heading, so the
  heading's accessible name is the type alone.
- Choosing a type is boosted: the page's `<main>` is swapped in place and the type's address is
  pushed, so the back button returns to the previous type. Nothing on the server knows about it.
- On a project, a person and an organization, the dataset is a column of its own, by name, right
  after the record's name. The dataset icon column is dropped on every tab.
- A row starts with the record's name, then the dataset where rows span several, then a
  measurement's sample, then the type's own columns.
- A dataset's own tab has no Dataset filter.
- The two tabs come after the Projects and Datasets tabs, samples first.
- An empty tab shows the list's empty-state panel with the kind's icon. A person on their own page
  is addressed as "you".
- Ruled after the sketch (maintainer, 2026-11-03): there is no "not published yet" panel. A viewer
  who may not see a dataset's records is not offered its tabs at all, and its overview shows them no
  sample or measurement counts.
