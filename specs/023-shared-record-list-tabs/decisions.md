# Decisions: 023-shared-record-list-tabs

Questions settled while writing the specification, with the reasoning behind each. The
maintainer's own rulings are recorded in `spec.md` under *Clarifications*.

## The scope

The specification covers the Samples and Measurements tabs on a dataset, a project, a person and an
organization. An earlier draft also merged the duplicate Projects and Datasets tabs, removed the
project's Export tab, and added a sample's Measurements tab and an organization's Members tab. Those
are independent of these tabs and move to their own issue, so this feature is not held up by them.

An earlier draft also left these tabs off a project, a person and an organization. No reason was
recorded for leaving them off a person or an organization, and a project's records were said to be
reached through its datasets. The maintainer has since asked for all four pages, and nothing
technical stands in the way: a contributor's credits on samples and measurements can already be
looked up, and the Map tab already reaches a contributor's samples through their datasets.

## Credit flows down, and nowhere else

A credit on a project or a dataset counts for every record beneath it. This is how access already
works (`with_level` on every record's queryset), so a person's tab lists the same tree of records
that their credits give them rights over. Someone credited on a large dataset therefore lists all
of it, which is what being credited on the dataset means.

Credit does not flow sideways or upward:

- Credit on a sample does not bring in the measurements others made of it. Those measurements
  belong to their own datasets and teams.
- An organization does not collect the records its members are credited on. A member's work is
  credited to the member, and an organization is credited only where it is named.

An organization also lists the records in the projects it owns, because its Datasets tab already
lists the datasets in those projects (specification 019).

## Whose records a contributor's page shows, to whom

Specification 032 ruled that a list of one person's records shows that person their private
records and their public ones, and everyone else the public ones only, and that its filters offer
the same. The tabs follow it. A person on their own page sees every record of theirs they may see,
unpublished and private included. Every other viewer sees released records: those whose own
dataset is public, published and not in a private project.

An organization has no one who views its page as itself, so its tabs show released records to
everyone, a member of a dataset's team included. That team member reaches the private records from
the dataset or the project.

## What the viewer may see on a dataset or a project

A dataset's and a project's pages are where private work is reached from, so their tabs list what
the viewer may see. A visitor sees records in public, published datasets. The team sees the rest.

A project with hidden records and a project with none give a visitor the same empty state, so the
page does not reveal that private datasets exist.

## What belongs to a dataset

A measurement may belong to a different dataset than its sample. A dataset's tabs list what belongs
to the dataset, because that is what the dataset distributes and what its team is responsible for.
A measurement that belongs to it is listed even when the sample is someone else's. The other team's
sample is not listed among this dataset's samples. Where the viewer may not open that sample, the
measurement's row does not name it, following FR-023 of specification 018. The same rule applies to
a project's records and a contributor's.

## One type at a time

Types have different columns, so they cannot share a table. One table at a time, with the chosen
type in the address, keeps each table able to page, sort and filter on its own, and lets a reader
link to it. Only types present on the page are offered. A portal may register dozens of types, and
a dataset usually holds one or two.

## Each row names its dataset where rows come from several

On a project or a contributor, a sample's name alone does not say whose it is. The dataset is what
a reader cites, so each row names and links it. A dataset's own tabs leave it out, as every row
there belongs to the same dataset.

## Overview counts lead to the tabs

A dataset's and a project's overviews count their samples and measurements. With the tabs in
place, each count leads to the matching tab and the two agree for the same viewer.

## Empty tabs stay

A tab is present whatever it holds. A dataset's team needs to see where its samples will appear
before any exist, addresses stay stable, and whether a tab is shown never depends on a count worked
out per viewer on every page load.

## Filter choices on a team member's table

The portal-wide listings only ever show published records, so their filters draw choices from
published records alone. A team member on a dataset or project tab sees unpublished records too,
and the filter choices must follow the records they may see rather than all records or published
ones only. FR-007 states the requirement and the plan decides the mechanism.

## Records of a type that is no longer registered

A page can hold records whose type a portal has since stopped registering. Leaving them out would
hide data the viewer is entitled to see, and failing would break the tab. They are listed with the
fields every sample or measurement has.

## Tab order

The two tabs follow any Projects or Datasets tab already on the page, in the order of the data
model. Sibling features add other tabs to the same pages (Contributors, Map, Statistics). This
specification assumes those come after and does not set their positions.

## A sketch comes first

The type tables already exist on the portal-wide listings. Two pieces of layout are new: the way of
moving between types inside a tab, and the dataset column on rows drawn from several datasets. Both
are judgements about how a page reads, so the tabs are sketched on the four pages and shown before
the build is planned.

## D1. The sketch's code is rebuilt, its screens kept

The approved sketch fixed the templates, the markup and the copy. Everything behind them is rebuilt
test-first, and every item the sketch listed as faked is a task in `tasks.md`.

**ADR:** none — local to this feature, nothing downstream inherits it.

## D2. No access means no access

The maintainer's ruling, 2026-11-03: a viewer who may not see a public, unpublished dataset's
records is not offered its Samples and Measurements tabs, their addresses answer "not found", and
the dataset's overview shows them no sample or measurement counts and nothing drawn from its
records. Both overviews count only what the viewer may see, so the figures and the tabs always
agree. This replaces specification 018's rule that a visitor sees those counts and charts, and the
not-published state the sketch drew.

**ADR:** none — recorded in spec.md's clarifications and assumptions, which supersede 018 here.

## D3. A plugin's tab is marked on every address it mounts

The tab strip marked a tab only on its plugin's own view name, so a type's address and a plugin's
extra pages left no tab marked. The tab item now holds every view name its plugin mounts. This also
marks the Contributors tab on its add and edit pages, which it did not do before.

**ADR:** none — a fix to existing behaviour, recorded in the plugin reference documentation.

## D4. A contributor's associated records live on the contributor model

The rule for which records a contributor's tabs list is `Contributor.get_associated_records`, with
`Organization` adding the projects it owns, beside the existing `get_public_*` methods, so a
portal's contributor subclass extends it in one place.

**ADR:** none — follows the existing pattern of `get_public_datasets`.
