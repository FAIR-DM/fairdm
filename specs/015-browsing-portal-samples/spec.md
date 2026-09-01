# Feature Specification: Browsing a portal's samples and measurements by type

**Feature Branch**: `015-browsing-portal-samples`

**Created**: 2026-09-01

**Status**: Draft

**Goals**: G2 — registering a model is enough to get a working portal surface. G9 — records in the
core model can be searched, sorted and filtered. G12 — private and public data sit side by side,
controlled per object.

**Roadmap**: R16 — every core record type can be created and edited in the portal. This feature is
the listing half of it. It also delivers part of R17, namely the searchable fields a listing
declares and the indexes behind them.

**Input**: A portal registers any number of sample and measurement types, and a visitor has no
dependable way to browse what it holds. Every registered type should have a page of its own listing
every published record of that type, which a reader can page through, filter and search, with the
columns, the filters and the fields search covers all taken from the model author's registration so
that a type gets a listing shaped for its own data. Those listings show public data only. Every
registered type is placed in the portal's navigation, and every listing offers a way to reach any
other listing in the portal without going back to a landing page.

This feature owns `fairdm/contrib/collections` outright and may rewrite or delete any part of it.
Much of what is specified here exists in that app already, in an untested and partly broken form.
None of it is treated as delivered, and where this specification and the current code disagree, this
specification decides.

## Clarifications

### Session 2026-09-01

- Q: The collections app already generates a page per registered type, pulls its table and
  filter set from the registry, and fills the navigation. Does this feature only add what is
  missing? → A: No. It owns the app and is judged on the behaviour a reader gets, not on
  preserving what is there. The existing code is a starting point with no standing: it has no
  tests, no page template of its own, a redirect view that points at addresses which do not
  exist, a plugin registered nowhere, and a README describing a configuration style the registry
  no longer uses.
- Q: Search, sorting and indexes belong to R17. Does this feature stop at the page and wire up
  whatever the framework already generates? → A: No, it takes part of R17. Each type declares the
  fields its search covers, a sensible default applies where the author declares nothing, and the
  fields searched are indexed. What it does not take is ranking, tolerance of partial words, or
  search across record types. Those stay with R17 and will upgrade every listing at once.
- Q: A collection could be portal-wide or scoped to a dataset. Which? → A: Portal-wide only, one
  per registered type. A dataset's own samples and measurements are a plugin on the dataset's
  page, which is R18's work. The plugin this app carries for that purpose is registered nowhere
  and is deleted rather than finished.
- Q: `DataTableView` overrides no queryset, and the polymorphic manager it reads through has its
  visibility filter commented out, so a collection page serves records from private datasets to
  anonymous visitors today. What should a collection show? → A: Public data exclusively. Not "what
  the viewer is entitled to see" — a signed-in researcher does not see their own unpublished
  records mixed into a collection. The rule is the same for every viewer, which makes the page
  cacheable in principle and removes a whole class of leak.
- Q: What decides that a record is public? FS-014 settled that a dataset's visibility governs its
  metadata alone, and FR-066 of that specification forbids introducing a published state. → A: A
  new `published` boolean on `Dataset`, added by this feature. This deliberately supersedes
  FS-014's FR-066, which is annotated in place in that specification rather than deleted. The
  checked process that decides when a dataset is fit to publish remains R22's work: this feature
  adds no transitions, no completeness rules and no review step.
- Q: If no workflow sets the flag, what does? → A: The Django admin, and nothing else. No portal
  page exposes it. A fresh portal's collections are therefore empty until an administrator
  publishes a dataset, which is accepted: the alternative puts a one-click publish control in
  front of researchers, and R22 exists precisely because publishing should not be one click.
- Q: A measurement may belong to a different dataset than the sample it was made on, so a
  published measurement can reference an unpublished sample, and the measurement table links to
  its sample. Which dataset decides, and what happens to the link? → A: A record's own dataset
  decides whether the record appears. A row in a measurement collection whose sample belongs to an
  unpublished dataset shows no sample name and no link to it. Membership of a collection must
  never become a route to a record that is not itself published.
- Q: R17 also asks for sorting, which was not discussed. Is it in? → A: Yes, in the form a table
  gives for free. Each collection has a stable default order and sorts on the columns its
  registration produces. Ordering is declared on the table class, because the shell's table view
  refuses a view that declares `order_by` itself.
- Q: The current page offers eight export formats, in the request, untested. Do they stay? → A:
  No. They are removed. Downloading data belongs to R21, which describes export as dataset-scoped
  and names in-request execution as one of the faults it exists to fix.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mark a dataset published (Priority: P1)

A portal administrator opens a dataset in the Django admin and marks it published. Nothing else in
the portal changes: the dataset's own pages, its visibility and everything a researcher can reach
behave exactly as before. The flag records that the data beneath the dataset may be shown to the
public, and the collections built in the rest of this feature are the first thing to read it.

**Why this priority**: every other story that shows a record depends on this flag existing and
being readable. It is also the story that can ship on its own without exposing anything, because
until a collection page reads it, the flag changes no visible behaviour.

**Independent Test**: mark a dataset published in the admin, confirm the value persists, confirm no
portal page's behaviour changes, and confirm existing datasets are unpublished after the migration.

**Acceptance Scenarios**:

1. **Given** a portal upgraded from a version before this feature, **When** the migration runs,
   **Then** every existing dataset is unpublished.
2. **Given** an administrator in the Django admin, **When** they mark a dataset published and save,
   **Then** the value persists and is readable from the dataset record.
3. **Given** a dataset that is published, **When** any portal page other than a collection is
   opened, **Then** it behaves exactly as it did before the flag existed.
4. **Given** a signed-in researcher who owns a dataset, **When** they open every portal page that
   edits it, **Then** none of them offers to publish or unpublish it.
5. **Given** a dataset whose metadata visibility is private, **When** an administrator marks it
   published, **Then** the two states are recorded independently and neither overwrites the other.

---

### User Story 2 - Browse a type's records (Priority: P1)

Anyone, signed in or not, opens the listing for a registered sample or measurement type and sees a
table of the published records of that type held anywhere in the portal. The columns are the ones
the model author's registration produces, so a listing of ice cores and a listing of heat-flow
measurements do not look alike. The reader pages through the results and selects a row to open that
record.

**Why this priority**: it is the feature. Every remaining story either narrows this table, leads a
reader to it, or clears away what preceded it.

**Independent Test**: register two sample types and one measurement type in the demo application,
publish one dataset and leave another unpublished, then open each listing while signed out and
confirm the columns differ per type, that only published records appear, and that paging works.

**Acceptance Scenarios**:

1. **Given** a registered sample type, **When** its listing is opened, **Then** the published
   records of that type appear and records of other types do not.
2. **Given** two registered types whose registrations declare different fields, **When** each
   listing is opened, **Then** each shows the columns its own registration produces.
3. **Given** a type registered with no field declarations at all, **When** its listing is opened,
   **Then** it renders with the framework's default columns rather than failing.
4. **Given** records in both published and unpublished datasets, **When** the listing is opened by
   an anonymous visitor, **Then** only records from published datasets appear.
5. **Given** a signed-in researcher who owns records in an unpublished dataset, **When** they open
   the listing, **Then** their own unpublished records are absent.
6. **Given** more records than fit one page, **When** the listing is opened, **Then** it pages, and
   every page is reachable.
7. **Given** a measurement whose sample belongs to an unpublished dataset, **When** the measurement
   listing is opened, **Then** the row appears without the sample's name and without a link to it.
8. **Given** a registered type with no published records, **When** its listing is opened, **Then**
   it says so rather than rendering an empty table.
9. **Given** a listing row, **When** it is selected, **Then** that record's page opens.
10. **Given** a listing of any size, **When** it renders, **Then** the number of database queries
    does not grow with the number of rows.

---

### User Story 3 - Narrow a listing to what is wanted (Priority: P1)

A reader looking at a type's listing types a word into the search box at the top of the table and
narrows the rows to those that match. They also apply the filters the type's registration produces,
and sort by any column that carries an order. The fields the search covers are the model author's
choice, and where the author has said nothing the record's name is searched.

**Why this priority**: a listing that cannot be narrowed is unusable the moment a portal holds real
data, which is the whole reason R17 exists. It is separated from the story above because the table
is worth having before it is searchable, and because the indexes belong with the search rather than
with the page.

**Independent Test**: load a type with enough records to page, search for a word held by one of
them, apply each generated filter, sort each sortable column both ways, and confirm each of the
searched fields carries a database index.

**Acceptance Scenarios**:

1. **Given** a type whose registration declares no searchable fields, **When** a word from a
   record's name is searched, **Then** that record appears and unrelated records do not.
2. **Given** a type whose registration declares searchable fields, **When** a word held only by one
   of those fields is searched, **Then** the matching records appear.
3. **Given** a type whose registration declares searchable fields, **When** a word held only by a
   field outside that declaration is searched, **Then** no records are returned on the strength of
   it.
4. **Given** a search that matches nothing, **When** the listing renders, **Then** it says so.
5. **Given** a search that would match a record in an unpublished dataset, **When** it is run,
   **Then** that record does not appear.
6. **Given** the filters a type's registration produces, **When** each is applied in turn, **Then**
   only the records satisfying it remain, and no filter raises an error.
7. **Given** a filter whose choices are drawn from related records, **When** the filter is opened,
   **Then** no unpublished record's values appear among the choices.
8. **Given** a sortable column, **When** the reader sorts by it, **Then** the rows order by that
   column, and reversing the sort reverses the order.
9. **Given** a listing opened with no sort chosen, **When** it renders, **Then** the rows are in a
   stable, repeatable order.
10. **Given** the fields the framework searches by default, **When** the database schema is
    inspected, **Then** each of them carries an index.

---

### User Story 4 - Find the listings from the navigation (Priority: P2)

A visitor who has not been given a link opens the portal's navigation and finds every registered
sample type under Samples and every registered measurement type under Measurements, each named as
its registration names it. Selecting one opens that listing. A portal author who registers a type
does nothing further to make it appear.

**Why this priority**: without it the listings exist at addresses nobody can discover, but a reader
holding a link still gets the full value of the three stories above.

**Independent Test**: register a new type in the demo application, restart, and confirm it appears
in the navigation under the correct heading with its declared plural name, and that the entry leads
to its listing.

**Acceptance Scenarios**:

1. **Given** registered sample types, **When** any page is opened, **Then** each appears in the
   navigation under Samples, named by its registration's plural display name.
2. **Given** registered measurement types, **When** any page is opened, **Then** each appears under
   Measurements.
3. **Given** a newly registered type, **When** the portal starts, **Then** its entry is present
   without any navigation declaration having been written for it.
4. **Given** a navigation entry, **When** it is selected, **Then** that type's listing opens.
5. **Given** a portal with no registered types of one kind, **When** the navigation renders, **Then**
   no empty heading is shown for that kind.
6. **Given** a portal that has not installed the collections application, **When** any page is
   opened, **Then** the navigation still renders.

---

### User Story 5 - Move between listings (Priority: P2)

A reader looking at one type's listing uses a control on the page to jump straight to any other
listing the portal offers, samples and measurements alike, grouped under those two headings. They
do not have to return to the navigation or to a landing page to cross from a sample type to a
measurement type.

**Why this priority**: it is the difference between a set of listings and a way of exploring a
portal, and the reader who has just narrowed a sample listing usually wants the measurements next.
It sits below the stories above because the navigation already offers the same journeys in more
steps.

**Independent Test**: with several types of each kind registered, open one listing, confirm the
control lists every other listing grouped by kind and marks the current one, and follow it to a
listing of the other kind.

**Acceptance Scenarios**:

1. **Given** a listing, **When** it renders, **Then** it offers a control listing every other
   registered type's listing in the portal.
2. **Given** that control, **When** it renders, **Then** its entries are grouped under Samples and
   Measurements.
3. **Given** that control, **When** it renders, **Then** the listing currently being viewed is
   marked as current.
4. **Given** a sample listing, **When** a measurement type is chosen from the control, **Then** that
   measurement listing opens.
5. **Given** a portal with exactly one registered type, **When** its listing renders, **Then** the
   control does not offer a journey to nowhere.
6. **Given** a listing that has been searched and filtered, **When** another listing is chosen,
   **Then** that listing opens unfiltered rather than carrying terms that mean nothing to it.

---

### User Story 6 - Clear away what the app no longer needs (Priority: P3)

A developer reading `fairdm/contrib/collections` finds only code that runs, and documentation that
describes what is there. The redirect view that points at addresses which do not exist, the plugin
registered nowhere, the orphaned template, the export machinery and the README's account of a
configuration style the registry no longer uses are all gone.

**Why this priority**: it changes nothing a reader of the portal can see, and it is the story most
safely dropped if the run runs short. It is specified rather than left implicit because the
alternative is a rewritten app with its predecessor's corpse still in it.

**Independent Test**: confirm each named item is absent, that the application's own documentation
describes the code as it now stands, and that the test suite and the demo application still pass.

**Acceptance Scenarios**:

1. **Given** the collections application, **When** it is inspected, **Then** it contains no view,
   plugin or template that no route or registration reaches.
2. **Given** a listing, **When** it renders, **Then** it offers no download of any format.
3. **Given** the application's README, **When** it is read against the code, **Then** every
   component it names exists and every example it gives works.
4. **Given** the full test suite, **When** it runs, **Then** it passes, and no test was deleted
   without a recorded decision.

### Edge Cases

- **A portal registers a type but installs no data.** The listing renders its empty state and its
  navigation entry is still present, because a reader learning that a portal holds no ice cores yet
  has been told something true.
- **A dataset is unpublished after its records have been browsed.** The records leave every listing
  at the next request. Nothing caches membership across the change.
- **A measurement's own dataset is published but its sample's is not.** The measurement appears.
  The sample is not named and not linked. The reverse case needs no rule, because a sample's
  presence in a sample listing says nothing about measurements made on it.
- **A model author declares a searchable field that spans a relation.** It is honoured. The
  application shell already searches related field paths, and a related path is often the useful
  one — the dataset a sample came from, or the sample a measurement was made on.
- **A model author declares a searchable field that does not exist.** The registration is refused
  at import naming the type and the field, rather than the listing silently searching less than
  the author asked for.
- **A model author declares a searchable field on an unindexed column.** The listing works. The
  index requirement in this feature binds the fields the framework itself searches by default. What
  an author adds is the author's to index, and the documentation says so.
- **Two registered types resolve to the same address.** The registration is refused at import with a
  message naming both, rather than one listing shadowing the other.
- **A portal overrides a type's table class entirely.** The listing uses it. Nothing in this feature
  requires a table to inherit from the framework's own base to be shown.

## Requirements *(mandatory)*

Requirements state what a person can do and what the portal guarantees. Where the application shell
already provides a facility, the requirement is to use it rather than to build an equivalent, per
Article XIV.

### The published flag

- **FR-001**: `Dataset` MUST carry a boolean recording whether its data is published, separate from
  and independent of its metadata visibility.
- **FR-002**: The flag MUST default to unpublished, and the migration that adds it MUST leave every
  existing dataset unpublished.
- **FR-003**: The flag MUST be settable through the Django admin.
- **FR-004**: No page a researcher can reach MUST offer to set, clear or display the flag.
- **FR-005**: Setting the flag MUST NOT run any check on the dataset's completeness, require a
  review, or record a transition. The process that decides when a dataset may be published is
  roadmap item R22 and is not built here.
- **FR-006**: Nothing outside the listings specified below MUST read the flag. In particular it
  MUST NOT alter the dataset listing, any dataset page, the API, or any permission check.
- **FR-007**: This requirement supersedes FR-066 of `014-dataset-crud-views`, which forbade
  introducing a published state. That requirement MUST be annotated in place in its own
  specification, marked superseded and pointing here, and MUST NOT be deleted.

### The listings

- **FR-008**: Every registered sample type and every registered measurement type MUST have a
  listing of its own, at an address of its own, generated from its registration with no per-type
  declaration required.
- **FR-009**: A listing MUST show records of its own type only.
- **FR-010**: A listing MUST show every record of its type held anywhere in the portal, subject to
  the publication rule below, and MUST NOT be scoped to a project, a dataset or a sample.
- **FR-011**: A listing MUST show a record if and only if the dataset that owns it is published.
  This rule MUST hold identically for every viewer, signed in or not, and MUST NOT be widened for
  a record's owner, its contributors or portal staff.
- **FR-012**: A measurement's presence in a listing MUST be decided by the dataset that owns the
  measurement, not by the dataset that owns its sample.
- **FR-013**: Where a listing would name or link a record whose own dataset is not published, it
  MUST show neither the name nor the link.
- **FR-014**: A listing's columns MUST come from the registered configuration for its type, so that
  two types with different declarations produce different columns.
- **FR-015**: A type whose registration declares nothing MUST still produce a working listing from
  the framework's default fields.
- **FR-016**: A portal that declares its own table class for a type MUST have it used unchanged.
- **FR-017**: A listing MUST page its results.
- **FR-018**: A listing with no records to show MUST say so.
- **FR-019**: A listing row MUST lead to that record's page.
- **FR-020**: The number of database queries a listing issues MUST NOT grow with the number of rows
  it shows.
- **FR-021**: Every user-visible string a listing renders — column headers, filter labels, empty
  state, and the switching control — MUST be translatable.

### Narrowing a listing

- **FR-022**: A listing MUST offer a search box that narrows its rows.
- **FR-023**: A registered configuration MUST be able to declare which fields its type's search
  covers.
- **FR-024**: Where a configuration declares no searchable fields, search MUST cover the record's
  name.
- **FR-025**: Search MUST NOT match against any field outside the fields declared or defaulted for
  that type.
- **FR-026**: A declared searchable field that the framework cannot search MUST cause the
  registration to be refused at import, with a message naming the type and the field, rather than
  being dropped silently.
- **FR-027**: Every field the framework searches by default MUST carry a database index.
- **FR-028**: A listing MUST offer the filters its type's registered configuration produces.
- **FR-029**: Applying any generated filter MUST narrow the rows and MUST NOT raise an error.
- **FR-030**: A filter whose choices are drawn from related records MUST NOT offer a value that
  exists only on an unpublished record.
- **FR-031**: Search and filtering MUST be applied before the publication rule is relaxed in any
  way, so that no combination of terms returns a record the reader could not otherwise see.
- **FR-032**: A listing MUST sort on the columns its registration produces as sortable, in both
  directions.
- **FR-033**: A listing opened with no sort chosen MUST return rows in a stable, repeatable order.
- **FR-034**: Ranking of results, tolerance of misspelled or partial words, and search spanning more
  than one record type MUST NOT be built here. They belong to roadmap item R17.

### Navigation

- **FR-035**: Every registered sample type MUST appear in the portal's navigation under Samples, and
  every registered measurement type under Measurements.
- **FR-036**: A navigation entry MUST be created from the registration alone, with no navigation
  declaration written per type.
- **FR-037**: A navigation entry MUST be labelled with the type's plural display name from its
  registration.
- **FR-038**: A navigation entry MUST lead to that type's listing.
- **FR-039**: A registered type MUST NOT be able to decline its navigation entry. Every registered
  type appears.
- **FR-040**: Where a portal has registered no types of one kind, the navigation MUST NOT show an
  empty heading for that kind.
- **FR-041**: The portal's navigation MUST render whether or not the collections application is
  installed. Loading the navigation MUST NOT depend on that application's start-up.

### Switching between listings

- **FR-042**: Every listing MUST carry a control offering every other type's listing in the portal.
- **FR-043**: That control MUST offer sample types and measurement types alike, grouped under those
  two headings.
- **FR-044**: That control MUST mark the listing currently being viewed.
- **FR-045**: Choosing another listing from the control MUST open it.
- **FR-046**: A listing opened from the control MUST open unnarrowed. Search terms and filter values
  MUST NOT be carried across, because they are chosen from a different type's fields.
- **FR-047**: Where a portal has registered only one type, the control MUST NOT offer a journey to
  nowhere.

### Addresses

- **FR-048**: Each listing MUST have a stable address derived from its registered type.
- **FR-049**: Each listing's address MUST be reversible by name, and those names MUST follow the
  convention the portal's other listings already use.
- **FR-050**: Two registered types resolving to the same address MUST be refused at import, with a
  message naming both, rather than one shadowing the other.
- **FR-051**: Every address this feature registers MUST have at least one test asserting the status
  code it returns, per Article I.

### Deliberate omissions

- **FR-052**: A listing MUST NOT offer to download its results in any format. Export belongs to
  roadmap item R21, which specifies it as dataset-scoped and run outside the request.
- **FR-053**: This feature MUST NOT build a listing scoped to a dataset, a project or a sample.
  Those are plugins on the owning record's page and belong to roadmap item R18.
- **FR-054**: This feature MUST NOT build create, edit or delete pages for sample or measurement
  types. They are the remainder of roadmap item R16.
- **FR-055**: This feature MUST NOT introduce a publication workflow, a review step or any state
  beyond the single flag in FR-001.
- **FR-056**: The redirect view that resolves to addresses which do not exist MUST be removed rather
  than repaired.
- **FR-057**: The data-table plugin, which no registration reaches, MUST be removed rather than
  wired up.
- **FR-058**: Any template the application carries that no view renders MUST be removed.
- **FR-059**: The application's README MUST describe the code as it stands after this feature. Every
  component it names MUST exist and every example it gives MUST work.
- **FR-060**: Documentation MUST state what registering a type produces — a listing, its columns,
  its filters, its search and its navigation entry — and how a portal overrides one of them without
  taking over the rest. It MUST state that a searchable field an author adds is the author's to
  index.

### Key Entities

- **Published**: whether the data held beneath a dataset may be shown to anyone using the portal.
  A boolean on the dataset, set by an administrator, independent of the dataset's metadata
  visibility. It is the sole test for a record's presence in a listing.
- **Listing**: the page for one registered sample or measurement type, showing the published
  records of that type held anywhere in the portal, with the columns, filters and searchable fields
  its registration produces.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A portal author who registers a sample or measurement type and writes nothing else
  gets a working listing for it, reachable from the navigation, without editing a URL
  configuration, a template or a menu.
- **SC-002**: No record whose dataset is unpublished appears in any listing, in any column, or among
  any filter's choices, for any viewer, signed in or not.
- **SC-003**: Two types registered with different field declarations produce visibly different
  listings.
- **SC-004**: A reader can narrow a listing to a known record by typing a word from its name, and
  can order the listing by any column it presents as sortable.
- **SC-005**: A reader viewing any listing can reach any other listing in the portal in one step.
- **SC-006**: The number of queries a listing issues is the same for one row as for a full page.
- **SC-007**: Every field the framework searches by default is indexed in the database schema.
- **SC-008**: Every address this feature registers is covered by a test asserting its status code,
  and the collections application, which had no tests before this feature, meets the project's
  coverage floor.
- **SC-009**: The collections application contains no view, plugin or template that nothing reaches,
  and its README describes only what is there.
- **SC-010**: Marking a dataset published changes what appears in the listings and changes nothing
  else in the portal.

## Assumptions

- The registry generates a table class and a filter set class for every registered sample and
  measurement type, and does so without database access, as specified in `002-fairdm-registry`.
- The application shell provides the table, paging, search box, filter and empty-state facilities
  that the project and dataset listings already use, so this feature configures them rather than
  building equivalents.
- A dataset's metadata visibility, its two values and its existing behaviour are as
  `014-dataset-crud-views` left them, and are untouched here.
- The demo application is where registered types are exercised, and it is updated in the same pull
  request, per Article XVIII.
- Sample and measurement records already have pages of their own to link a row to. Where a
  measurement's page is a placeholder, linking to it is still correct and completing it is the
  remainder of R16.
