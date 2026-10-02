# Decisions: 023-shared-record-list-tabs

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are the points under "Agreed so far" on #403, recorded in
`spec.md` under *Clarifications*, session 2026-10-01.

## For Sam to confirm

These three change what gets built, and the request did not settle them.

1. Comparing a sample's measurements across methods means every method's results on one page, each
   method in its own table. No chart, no side-by-side alignment of fields and no derived figures.
   See "What comparing across methods means" below.
2. A tab stays on the page when its list is empty. See "Empty tabs stay".
3. The feature is prototyped before it is planned, because the sample's Measurements tab and the
   way of moving between types on a dataset are layouts nobody has drawn. See "A prototype comes
   first".

## The reading of the request

The request was read as follows, and the specification is written from this reading.

Six lists become six plugins, each registered on every page it applies to: Projects on a person and
an organization, Datasets on a project, a person and an organization, Samples and Measurements on a
dataset, Measurements on a sample, and Members on an organization. Two of them replace plugins that
exist today in duplicate. Four are new. The project's Export tab goes. Nothing else on any page
changes: no page actions, no Manage menu entries and no overview cards belong to this feature. It
serves G5, because every portal gets these lists with no frontend work, and G9, because each list
can be searched, sorted and filtered.

## Contributor pages keep the public-only rule

The request says every list shows only what the viewer may see. Specification 019 says a
contributor's page names public projects and public datasets only, for every viewer, the person
included, and the glossary repeats it. The two do not conflict: a public record is one every viewer
may see. The stricter rule is the maintainer's earlier ruling for those two pages and it stands. A
profile reads the same to its owner as to the visitor they send the link to.

## A project's Datasets tab filters by viewer

The tab lists every dataset in the project today, whoever is looking. Under the request's rule it
lists the ones the viewer may open. Unlike a contributor's page, a project's page is where private
work is reached from, so a project member sees the private datasets they have access to.

A project with hidden datasets and a project with none give a visitor the same empty state.
Anything else would tell the visitor that private datasets exist.

## What belongs to a dataset

A measurement may belong to a different dataset than its sample. The dataset's two tabs list what
belongs to the dataset, because that is what the dataset distributes and what its team is
responsible for. A measurement that belongs to it is listed even when the sample is someone else's.
The other team's sample is not listed among this dataset's samples. Where the viewer may not open
that sample, the measurement's row does not name it, following FR-023 of specification 018.

## An unpublished public dataset says so

Specification 018 shows a visitor the sample and measurement counts of a public dataset that is not
published, and none of its records. A tab that then says "no samples" would contradict the count on
the overview. The tab says the data is not published. A dataset that holds nothing says that
instead. The specification requires the two states to differ and does not fix the words.

## One type at a time on a dataset

Types have different columns, so they cannot share a table. One table at a time, with the chosen
type in the address, keeps each table able to page, sort and filter on its own and lets a reader
link to it. Only types the dataset holds are offered. A portal may register dozens of types, and a
dataset usually holds one or two.

## What comparing across methods means

The request says the sample's Measurements tab "shows a single sample's results and lets them be
compared across methods". The narrowest reading that delivers this is every measurement type on one
page, each in its own table, so a reader sees all results for one specimen together. That is the
difference from the dataset's tab, which shows one type at a time.

Anything richer was left out: aligning fields across types, charts, or computed differences.
FairDM knows nothing about which fields of two measurement types are comparable, and plotting one
field against another is named in #397 as addon work. If a richer comparison is wanted, it is a
change to FR-024.

## Whose measurements a sample lists

All of them that the viewer may see, whichever dataset they belong to, decided by each
measurement's own dataset. This is the rule the sample's overview already applies to its short
list, so the tab and the overview count the same records.

## Members are current members only

The glossary defines a member as a person with a verified affiliation that has not ended, and the
organization's overview lists and counts exactly those. The tab uses the same definition and the
same order, so the tab's total equals the overview's count. Former members are part of each
person's own affiliation history and are not repeated here.

Managing members is announced on the overview as not available yet and stays that way. The tab
replaces only the notice about the full member list.

## Empty tabs stay

A tab is present whatever it holds. A dataset's team needs to see where its samples will appear
before any exist, addresses stay stable, and whether a tab is shown never depends on a count that
would have to be worked out per viewer on every page load. Hiding the tab strip when a record has a
single tab was left as a separate issue by specification 018 and is not taken up here.

## Old addresses are not kept

The Projects and Datasets tabs have addresses derived from the names of the two plugins being
merged, so they differ between a project's page and a contributor's. One plugin has one address
segment. FairDM has not reached 0.1.0 and promises no stable addresses, so no redirects are added.
Links inside the portal are generated by name and follow the change.

## The own-profile page title is dropped

On a person's own profile the two tabs are titled differently today. One plugin on three pages
carries one title. Nothing in the specification fixes a title either way, and this note records
that the variant was not carried over.

## The Export tab is removed and nothing replaces it here

The maintainer ruled that the tab goes because a dataset is the unit of distribution. What a
dataset offers for download is described in #397 as a page action and is tied to tabular import and
export on the roadmap. This feature removes the tab and adds no export anywhere.

## Creating records from a list

The lists are for reading and finding. Whatever a list already offers for adding a record, such as
adding a dataset from a project's Datasets tab, is kept for the people who may use it. No new way to
create or import a record is added, because importing data into a dataset is a Manage menu entry in
#397 and belongs to another feature.

## Records of a type that is no longer registered

A dataset can hold records whose type a portal has since stopped registering. Leaving them out
would hide data the viewer is entitled to see, and failing would break the tab. They are listed with
the fields every sample or measurement has.

## Tab order

The list tabs come straight after the overview, in the order of the data model: projects, datasets,
samples, measurements, members. The sibling features add other tabs to the same pages (Contributors,
Map, Statistics). This specification assumes they come after the lists and does not set their
positions.

## No dependency on the sibling features

Nothing here needs page actions, overview cards, or removing and replacing a plugin (#401), and
nothing needs the Contributors tab (#402). The tabs use the plugin system as specification 008
delivered it. Once #401 is delivered, each of these six plugins can be removed or replaced like any
other, with no further work in this feature.

## A prototype comes first

Most of this feature puts existing tables and lists into a tab slot that already exists, which
would not need a prototype. Two parts are new layouts: several type tables on one page for a
sample, and the way of moving between types on a dataset. Both are judgements about how a page
reads, so the feature is prototyped and shown before it is planned.
