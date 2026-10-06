# Decisions: 026-statistics-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The request in issue #406 gave the four pages, what each reports in outline, the rule
that figures are taken only over records the viewer may see, and the two things left to addons.
Everything below fills a gap the request left open.

## For Sam to confirm

These four change what gets built, and the request does not settle them.

### An unpublished public dataset shows a visitor no field summaries

Specification 018 lets a visitor see the sample and measurement counts and the two charts of a
public dataset that is not published, and none of its records. The request for this feature says
figures are taken only over records the viewer may see. A range, a mean or a list of values tells a
reader what the records hold in a way a count does not, so the stricter reading was taken: the
visitor's Statistics page for such a dataset has nothing to summarise. The alternative is to treat
field summaries like the overview's counts and show them before publication.

### An organization's member output counts everything its current members are credited on

The request asks for "the output of its members over time". Specification 019 ruled that an
organization's overview counts only its own work, so the Statistics page reports both and keeps
them apart. A record counts toward member output when a current member is credited on it, whenever
that was. This credits an organization with work a member did before joining, and drops the work of
people who have left. The alternative is to count a record only when the credit itself names the
organization as the affiliation, which is more accurate where that field is filled in and empty
where it is not.

### Organizations work together through shared records, including affiliations on credits

Organizations are seldom credited on a record directly. If only direct credits counted, the list of
organizations an organization works with would be empty in most portals. The specification also
counts an organization named as the affiliation on a person's credit on a counted record. The
alternative is the glossary's collaborator rule alone, restricted to organizations.

### Credits are placed in time by when the record was added to the portal

A contribution has no date. The only date every project and dataset is certain to carry is when it
was added, so "over time" means by that date. A portal that imports ten years of work in one week
will show all of it in one year. The alternative is a date from the record's own key dates, such as
a dataset's collection or publication date, falling back to the date added where none is recorded.

## Settled without needing confirmation

### No dependency on the other features in issue #397

A Statistics page is a tab, which a plugin can already contribute. It needs neither the page
actions and cards of #401 nor the shared list tabs of #403. The epic carries no "Depends on" line.

### The fields summarised default to the type's registered fields

The request says "per-field summaries" without saying which fields. G2 asks that registering a
model is enough, so the default is the field list the registration already carries, and a portal
developer can name a different list where the default is wrong. This is the fifth user story.

### The summary depends on the kind of field

"Count, range, mean, share missing and distribution" only makes sense in full for numbers. Dates
get a range and a distribution over time, categories get a count per value, and free text and
identifiers get the count and the share missing. The median was added beside the mean because a
mean alone misleads on skewed measurements, which are common in the sciences these portals serve.

### Summaries are grouped by sample and measurement type

Samples and measurements are polymorphic, and each registered type has its own fields. A summary
across types would mix fields that do not mean the same thing.

### The project page adds a per-dataset breakdown and four running totals

"How the project has grown" was read as the running totals of datasets, samples, measurements and
contributors. The overview already charts samples and measurements by month; this page adds
datasets and contributors and shows which dataset contributes what.

### Contributor pages keep the rule from specification 019

Projects and datasets are counted only when public, for every viewer. Role counts and collaborators
come from credits on records the viewer may open, so they match the overview. The collaborator list
uses the overview's ranking, so the overview's card is always the top of this page's list.

### The tab is always present, and an empty page says so

Specification 019 removed the old Statistics tab because it rendered blank. Hiding the tab whenever
there is nothing to count would make it come and go between viewers, which reveals something about
what a viewer cannot see. The tab stays, and a page with nothing to count says so.

### Samples and measurements get no Statistics tab

The request and the plan in #397 name four record types. One sample or one measurement has nothing
to aggregate.

### No export, no API and no filters on the pages

None is in the request. Narrowing the figures by a filter is a step toward the data explorer the
request leaves to an addon.

### A speed target is stated as a success criterion

Field summaries are worked out over every record of a dataset, so the page can be slow on a large
one. The specification sets a target of three seconds for 100,000 measurements and leaves the means
to planning. Whether figures are prepared ahead of time is a planning decision, bounded by the rule
that every figure is right for the viewer who asks.
