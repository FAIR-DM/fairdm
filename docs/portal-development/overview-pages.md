# Overview pages

Every project, dataset, sample and measurement opens on an **overview page**, the first tab of the
record's tabbed detail view. A person's page and an organization's page follow the same anatomy, described under
[the person page](#the-person-page) and [the organization page](#the-organization-page). It is written for three readers: someone deciding whether the data is
usable to them, someone who has to cite it, and the team keeping the record complete. All four
pages share one anatomy, one set of [cards](component_library/cards.md) and one list of template
blocks, so a portal changes one piece of a page by overriding one block or one method, not by
rewriting the page.

## The anatomy

Each page has, in order:

1. a **header** with the record's image or icon, badges, name, the people behind it, keywords and
   actions
2. **notices**, alerts about the record's state
3. a strip of **figures**
4. a wide **content column** beside a narrow **side column**. Below the `lg` breakpoint the two
   stack, content first.

The side column presents its cards in this order, leaving out any that do not apply to the record:
the readiness checklist (the team only), Details, the record's timeline of key dates, People,
Identifiers, Funding, the citation, and then cards particular to the record.

Two rules hold on every page. A card the page has is always drawn, and says what is missing when it
has nothing to show. Only the readiness checklist is left out, for anyone who cannot change the
record. And anything FairDM cannot do yet (a map of a project's samples, recent
activity, publishing a dataset, exporting a citation, metadata downloads) is announced the same
way: a card or a button that says "Coming soon", and a button is disabled and says why.

## The blocks

`overview/page.html` defines every block, in page order. Each record's own template extends it and
fills blocks. The blocks carry the `overview.` prefix:

| Block | What it holds |
| --- | --- |
| `overview.notices` | Alerts above the header, so they are read first. |
| `overview.image` | Header: the record's image, or its icon. |
| `overview.badges` | Header: status badges. |
| `overview.name` | Header: the name inside the heading. A contributor's page follows the name with a link to its ORCID record. |
| `overview.byline` | Header: the people behind the record (a project's leaders, a dataset's creators), each linked to their page. |
| `overview.keywords` | Header: keywords. |
| `overview.actions` | Header: buttons. Cite and Share by default. |
| `overview.figures` | The figures strip. |
| `overview.main` | The wide column. Each record fills it with its own blocks. |
| `overview.side` | The side column, which holds the blocks below. |
| `overview.readiness` | What the team still has to add. The team only. |
| `overview.details` | What the record belongs to, its licence, status, dates and how machines reach it. |
| `overview.details_extra` | Inside Details: sections a record adds, such as a project's timeline. |
| `overview.timeline` | Key dates in the record's life, on records that have their own card for them. |
| `overview.people` | Everyone credited, the people named in the header included. |
| `overview.identifiers` | DOI, IGSN and the rest, the team's own ID and the portal ID. |
| `overview.funding` | Funding awards, on records that carry them. |
| `overview.cite` | How to cite the record. |
| `overview.record_facts` | Cards particular to the record. |
| `overview.chart_library` | The ECharts script. Replace it to serve ECharts yourself. |

The blocks that wrap other blocks (`overview.main`, `overview.side`, `overview.details`) keep their
content when you add to them with `{{ block.super }}`, and replace it when you do not.

## The project page

A project's page is the landing page people reach from a grant report, a group website or a paper.
Its template is `project/project_detail.html`.

**Header.** The project's status, and a Private badge when it is private. The project's leaders
are named, each linked to their page. Cite and Share are offered to everyone. The team also gets
Add dataset and a Manage menu holding Edit details, Edit descriptions, Manage contributors and,
for a user who may delete the project, Delete. A user who may delete a project but not change it
sees a Manage menu holding only Delete.

**Notices.** Someone who may change a private project is told the project is private. A project whose status
is "Searching for collaborators" says so and names who to contact, the contact person or else the
first leader.

**Figures.** Datasets, samples, measurements and contributors.

**Content column** (`overview.about`, `overview.datasets`, `overview.charts`, `overview.map` and
`overview.activity`). The descriptions card, with a tab for each description type. The five most
recently updated datasets, each saying whether it is published, its licence, its record counts and
when it was last updated. A chart of records by type and a chart of the running total of samples
and measurements by month, each with a text description of what it shows. The map and recent
activity, announced as not available yet. A project with no datasets shows its team the first-run
state, with a way to add a dataset and no empty chart.

**Side column.** The readiness checklist for the team, Details (organisation, status, the
licences of its public datasets, when it was added and last updated, and its timeline with how far
through it the project is), People, Identifiers, Funding and the citation. The timeline sits in
`overview.details_extra`.

**Who sees what.** A visitor's figures, charts and licence summary count only the project's public
datasets, and the samples and measurements beneath them. The team's count every dataset. The
readiness checklist has ten items taken from DataCite's required and recommended properties, and
each missing item links to the page that fixes it where such a page exists.

**The page head.** The project's schema.org description is in a `<script type="application/ld+json">`
element. It carries nothing the viewer could not read on the page.

## Extending a project page

Override the template. Put a template named `project/project_detail.html` in your portal's
templates, ahead of FairDM's, and extend the one it replaces. This adds a card to the end of the
side column and keeps every card FairDM draws there:

```django
{% extends "project/project_detail.html" %}

{% block overview.side %}
  {{ block.super }}
  <c-card title="Our funder's reporting" class="bg-base-100">
    Reports are filed under grant {{ record.funding.0.awardNumber }}.
  </c-card>
{% endblock overview.side %}
```

To change what one card says, override the block that draws it. `overview.byline` replaces the
people row in the header:

```django
{% extends "project/project_detail.html" %}

{% block overview.byline %}
  <p class="text-sm">Led by {{ header_people|join:", " }}</p>
{% endblock overview.byline %}
```

The context the blocks read comes from the plugin, so a block can use everything the page has:
`counts`, `descriptions`, `team`, `people`, `identifiers`, `citation`, `details`, `licenses`,
`datasets_preview`, `composition_chart`, `growth_chart`, `timeline`, `urls` and, for the team,
`readiness`.

## The dataset page

A dataset is the unit a portal cites and distributes, so its page answers a reuser's questions in
the order they ask them: what it is, whether its data is published, under which licence, what it
holds and how it grew, when each step of its life happened, how to cite it and who made it. Its
template is `dataset/dataset_detail.html`.

**Header.** Whether the dataset is published, public but unpublished, or private, and its licence,
as badges. The creators are named, each linked to their page. The team also gets a Publish button,
announced as not available yet while the dataset is unpublished, and a Manage menu holding Edit
details, Edit descriptions and, for a user who may delete the dataset, Delete. A user who may
delete a dataset but not change it sees a Manage menu holding only Delete.

**Notices.** A private dataset tells anyone who may change it that only people with access can
open the page. A public dataset that is not published yet tells a visitor that its data is not
published, and tells people who may change it that its records stay hidden until it is. A dataset with a Withdrawn date says it has been withdrawn
and that the page stays so existing citations still resolve.

**Figures.** Samples, measurements, contributors and related publications.

**Content column** (`overview.about`, `overview.data`, `overview.charts` and `overview.map`). The
descriptions card, with a tab for each description type. A chart of records by type, and once the
dataset's records span more than one month, a chart of the running total of samples and
measurements by month, each with a text description of what it shows. The map, announced as not
available yet. A dataset that holds no samples or measurements shows its team the first-run state
in `overview.data`, with a way to add data announced as not available yet and no empty chart. The
page lists no record. A type the registry no longer holds is left out.

**Side column.** The readiness checklist for the team, Details (its project, with how many other
datasets the project has, its licence and when it was last updated), the timeline, People,
Identifiers, the citation and the related publications.

**The timeline.** A card in `overview.timeline` lists the dataset's key dates in the order they
happened: collected (with its end date, or "ongoing"), added to the portal, submitted, published,
available from and withdrawn. A step with no date recorded is left out. Each date is shown as
precisely as it was recorded, as a day, a month and year, or a year alone, and days follow the
active language's short date format. The withdrawal notice at the top of the page words its date
the same way.

**The readiness checklist.** The team sees "Ready to publish?" until the dataset is published, and
a visitor never sees it. It has seven required items and three recommended ones, taken from
DataCite's required and recommended properties:

| Item | Required |
| --- | --- |
| An abstract describes the data | yes |
| The methods are described | yes |
| At least one creator is credited | yes |
| Someone is named as the contact | yes |
| A licence is chosen | yes |
| It holds samples or measurements | yes |
| The collection period is recorded | yes |
| The dataset is public | no |
| Keywords make it findable | no |
| A related publication is linked | no |

Publishing a dataset makes it public, so a private dataset with every required item in place is
ready to publish.

Each missing item links to the page that fixes it where such a page exists.

**The citation.** A dataset with a data publication is cited by that publication, and the card
says to cite it rather than the page. Otherwise the citation is written as `Creators (Year).
Title. Publisher. Identifier.`, with the year taken from the Published date, else the Available
date, else the year the record was added. It ends with the DOI link, or the address of the page
when the dataset has no DOI yet, and the card says so.

**Related publications.** Each relation is worded from the publication's side, such as "Describes
this dataset", and the relations a reuser cares about most come first: describes, documents,
supplements, cites, refers to, then the relations the dataset makes to other work.

**What a visitor sees before publication.** Visibility governs the page and `published` governs the
records. A public dataset that is not published shows everyone its description, its figures
(including the counts of samples and measurements) and its charts. The page never lists a record,
published or not. The project is named and linked only when the viewer may see it, because a
public dataset can sit in a private project.

**The page head.** The dataset's schema.org description is in a `<script type="application/ld+json">`
element. It names the variables its record types measure and never a value, and it carries nothing
the viewer could not read on the page.

## Extending a dataset page

Override the template the same way as for a project. Put a template named
`dataset/dataset_detail.html` in your portal's templates, ahead of FairDM's, and extend the one it
replaces. This adds a card under the related publications and keeps everything else:

```django
{% extends "dataset/dataset_detail.html" %}

{% block overview.record_facts %}
  {{ block.super }}
  <c-card title="Our repository" class="bg-base-100">
    Deposited under {{ record.name }}.
  </c-card>
{% endblock overview.record_facts %}
```

The blocks read `access`, `dates`, `team`, `descriptions`, `literature`, `counts`, `data_types`,
`composition_chart`, `growth_chart`, `lifecycle`, `citation`, `details`, `urls` and, for the team,
`readiness`.

## The sample page

A sample is a physical specimen, so its page is organised around what happened to it and what was
learned from it: its type and status, a timeline of its life, the measurements made on it, where
it sits, how to cite it and what it is related to. It reads only the base `Sample` model and what
the registry says about the sample's type, never a field a particular type adds. Its template is
`sample/sample_overview.html`.

**Header.** The type and the status as badges. Where the registry describes the type, the type
badge opens that description in a dialog, with the type's keywords, the authority that maintains
its schema and how to cite it. A type the registry does not describe opens nothing. The status
badge is green for available, blue for in use, grey for stored and red for destroyed; a sample
with no recorded status reads "Status unknown". A user who may change the sample also gets a
Manage menu that links to the pages for editing its details, descriptions, keywords and key dates.
Those pages are not tabs. They keep their addresses (`/samples/<uuid>/edit/`,
`/basic-information/`, `/keywords/` and `/key-dates/`), and a portal's own content tabs stay in the
tab strip.

**Notices.** A destroyed specimen says it no longer exists and that its record and measurements
are kept. A sample whose dataset is not public and published says that only people with access to
the dataset can see it.

**Figures.** Measurements, related samples and people credited.

**Content column** (`overview.properties`, `overview.notes`, `overview.history` and
`overview.measurements`). `overview.properties` is empty on the shared page: it is the block a
sample type fills with its own fields. Then the notes, the history and the measurements.

- *The history* joins three things the sample vocabularies record for each step in a specimen's
  life: its date, the contributor role that performed it and the description that explains it. The
  steps are created, collected, prepared, archived, returned, restored and destroyed. Dated steps
  come first, in date order, each date shown as precisely as it was recorded (a year, a month or a
  day). A step with no date follows them.
- *The measurements* are listed most recent first, ten at a time, each naming its type. The rest
  are counted ("and 2 more"). A measurement recorded in another dataset than the sample's is
  marked with that dataset.

**Side column.** Details (its project, dataset, licence, status with what it means for
re-examining the specimen, and when it was added and last updated), People, Identifiers, the
citation, the location and the related samples.

- *The citation* follows DataCite's form for a physical object and points at the IGSN when the
  sample has one. Without an IGSN it points at the page and says an IGSN would outlive the portal.
- *The location* is a map of the point with its longitude and latitude listed. A sample without
  one says so.
- *The related samples* are the sample's parents and subsamples in one list, each saying how it
  relates to this sample.

**Who can open it.** A sample follows its own dataset. Its page opens for everyone once that
dataset is public and published. Before then it opens only for a user who holds `view_dataset` or
`change_dataset` on the dataset, and anyone else gets a "not found" response, so the address never
confirms the sample exists.

The same rule applies to each record the page lists. A measurement or a related sample in another
dataset is shown only when the viewer may see that dataset. One they may not see is counted and
never named, linked or mapped: the related samples card says how many belong to datasets that are
not published yet, and the measurement list leaves them out of its count.

## The measurement page

A reuser opens a measurement to judge whether its value is comparable with theirs, so the page
answers four questions in order: what the result was, what it was measured on, how it was
measured, and whether they can cite and reuse it. It reads only the base `Measurement` model and
what the registry says about the measurement's type, never a field a particular type adds. Its
template is `measurement/measurement_overview.html`, and the page stays at
`/measurement/<uuid>/`.

A measurement with no name is called by its portal ID in the breadcrumbs, the heading and the
browser title.

**Header.** The type as a badge. Where the registry describes the type, the badge opens that
description in a dialog, with the type's keywords, the authority that maintains its schema and how
to cite it. A type the registry does not describe opens nothing. A measurement whose dataset is not
public and published says that only people with access to the dataset can see it.

**Figures.** The result. A type that declares a `value` (and optionally an `uncertainty`) gets it
shown as "value ± uncertainty unit" with no template of its own. A type that records its result
another way leaves the result to its own template, which fills `overview.result`.

**Content column** (`overview.properties`, `overview.procedure`, `overview.notes`,
`overview.sample` and `overview.siblings`). `overview.properties` is empty on the shared page: it
is the block a measurement type fills with its own fields.

- *How it was measured* is a timeline of three steps, set up, measured and taken down. Each joins
  the date, the contributor role that performed it and the description that explains it.
- *Measured on* shows the sample as a small version of its own header: its image or icon, type and
  status, name, local ID, dataset and keywords. A measurement recorded in a different dataset from
  its sample says so, since that is how one group measures specimens another group collected.
- *Other measurements on this sample* lists up to eight, most recent first, and counts the rest.

**Side column.** Details (its project, dataset, licence, and when it was added and last updated),
People, Identifiers, the citation and the location of the sample.

- *The citation* names the contributors credited with the measurement role, and points at the
  measurement's DOI when it has one. Most measurements have none, so the page points at itself and
  suggests citing the dataset instead.
- *The location* is a map of the sample's location when the sample has one and the viewer may see
  the sample. Otherwise the card says that no location is recorded, or that the sample's dataset has
  not been published, and shows no coordinates.

**Who can open it.** A measurement follows its own dataset, not its sample's. Its page opens for
everyone once the measurement's dataset is public and published, whatever the state of the sample's
dataset. Before then it opens only for a user who holds `view_dataset` or `change_dataset` on that
dataset, and anyone else gets a "not found" response.

The sample's dataset is checked separately. A sample in a dataset that is not published is
described as "an unpublished sample" on the page, in the citation and in the card. It is never
named, linked or mapped. The list of other measurements leaves out those in datasets the viewer
may not see, and its count leaves them out too.

## The person page

A person's page is where a credit on a dataset leads. It tells a visitor who the person is, where
they work, whether their ORCID iD is authenticated, what they are credited on in this portal and who
they work with. Its template is `contributors/overview/person.html`, and the `Overview` plugin in
`fairdm.contrib.contributors.plugins` works out what it draws. Every contributor's page is open to
everyone, including the page of an unclaimed profile and of an inactive account.

The header has the person's photo or initials, whether the profile is claimed, unclaimed or belongs
to an inactive account, each portal role the person holds, and their name followed by a link to
their ORCID record. The link says, to sighted readers and to assistive technology, whether the iD
is authenticated, meaning the person has signed in with that ORCID account. Beneath the name come
the primary organization, linked to its page, that organization's location and the person's
languages in the active language. Each is left out when it is not recorded. A person has no
location of their own.

An unclaimed profile and an inactive account each get a notice. The figures are the number of
projects and of datasets the person is credited on, each linking to the matching tab, and when the
account was created. A profile with no account says so in place of a date.

The content column holds the biography, a Projects card and a Datasets card side by side, the
contribution roles and two cards announced as not available yet, the person's publications and a
map. Each record card lists at most five records, with projects in progress first and then the most
recently updated, and links to the full list. The side column holds the readiness checklist for the
person themselves, identifiers, links, affiliations, frequent collaborators and recent activity as
not available yet. The collaborators card shows at most eighteen people and counts the rest. A
person has no Details, funding or citation card.

The blocks only the contributor pages have, in page order:

| Block | What it holds |
| --- | --- |
| `overview.about` | The biography, or what an empty one is for. |
| `overview.records` | The Projects and Datasets cards. |
| `overview.roles` | The contribution roles card. |
| `overview.future` | The publications and map cards, announced as not available yet. |
| `overview.readiness` | The person's own checklist. |
| `overview.identifiers` | The person's identifiers and portal ID. |
| `overview.links` | The links card. |
| `overview.affiliations` | The affiliations card. |
| `overview.people` | The frequent collaborators card. |
| `overview.activity` | Recent activity, announced as not available yet. |

The blocks that mean the same on a record page keep their name. The Projects and Datasets tabs sit
beside the overview.

### Who sees what

A project or dataset appears on a contributor's page, in a list or in a count, only when it is
public. That holds for every viewer, including the person and the members of a private project.
A public dataset inside a private project is left out as well. The Projects and Datasets tabs
follow the same rule, so a figure always equals the number of entries behind its link.

The role counts and the collaborators come from the credits on records the viewer may open. Someone
who shares only a private record with the person is not named, and a role held only on private
records is not counted. Neither the page nor its schema.org description in the head contains an
email address, and the description names an affiliation only when it is the verified, current
primary affiliation the header shows. [What a profile may show](contributors.md#what-a-profile-may-show)
lists the methods behind this.

### Extending a contributor page

Override the template, as for a record page. A template named `contributors/overview/person.html`
in your portal's templates, ahead of FairDM's, extends the one it replaces. This adds a card to the
end of the side column and keeps every card FairDM draws there:

```django
{% extends "contributors/overview/person.html" %}

{% block overview.side %}
  {{ block.super }}
  <c-card title="Our research group" class="bg-base-100">
    {{ person.name }} is a member of the group.
  </c-card>
{% endblock overview.side %}
```

The blocks read `record`, `person`, `is_self`, `is_unclaimed`, `is_inactive`, `affiliations`,
`primary_organization`, `location_text`, `languages`, `portal_roles`, `identifier`,
`identifier_url`, `orcid_verified`, `member_since`, `counts`, `projects`, `datasets`, `roles`,
`identifiers`, `links`, `people`, `urls`, `api_url` and `json_ld`. The plugin's `records_shown`
(five) and `collaborators_shown` (eighteen) say how many records each record card lists and how
many faces the collaborators card draws.

## The organization page

An organization's page is where an owner or an affiliation leads. It tells a visitor what the
organization is, where it sits among the organizations around it, who belongs to it and what
research in this portal it is behind. It reuses the person page's template skeleton and cards. Its
template is `contributors/overview/organization.html`, drawn by the same `Overview` plugin, and
like every contributor's page it is open to everyone.

The header has the organization's logo or its initials, its type, and its name followed by a link
to its ROR record when it has a ROR ID. Beneath the name come the organization it is part of,
linked to its page, its city and country, and its languages. Each is left out when it is not
recorded. The actions are sharing the page and the organization's address in the API. A signed-in
person who is not a current member is also offered asking to join, shown as not available yet. The
people who keep the record are offered a menu of management actions instead, also not available
yet.

The figures are the organization's projects, its datasets and its current members. The first two
link to the matching tabs.

The content column holds the description, the members, a Projects card and a Datasets card, and a
map of where its members work, announced as not available yet. The side column holds the
readiness checklist for the people who keep the record, identifiers, links, a map of where the
organization is based, the hierarchy and recent activity as not available yet. An organization has
no Details, funding or citation card. The map of where it is based is left out when no location is
recorded, because the header already names the city and country. Every other card is drawn and
says what is missing.

The blocks only the organization page has are `overview.members`, which holds the Members card,
and `overview.hierarchy`, which holds the Hierarchy card. It also fills the blocks the person page
defines (`overview.about`, `overview.records`, `overview.future`, `overview.readiness`,
`overview.identifiers`, `overview.links`, `overview.activity`) and adds `overview.location` for the
map of where the organization is based.

### Members and hierarchy

A member is a person with a verified affiliation to the organization that has not ended. A pending
request and a former member are neither listed nor counted. The Members card lists the owner first,
then the administrators, then the other members, each group by name, and marks the owner and the
administrators. It has ten places. When there are more members than that, the tenth place counts
the members not shown. `Organization.get_current_memberships()` returns the list and the plugin's
`member_slots` sets the number of places.

The Hierarchy card places the organization among its neighbours: its parent, the parent's
sub-organizations with this one marked among them, and this organization's own direct
sub-organizations, each group by name. Every organization in it other than this one links to its
page. An organization with no parent starts the tree itself, and one with neither a parent nor
sub-organizations shows a notice that none is recorded. `Organization.get_hierarchy()` returns the
three groups, and [`c-card.hierarchy`](component_library/cards.md#c-cardhierarchy) draws them.

### Whose work an organization's page counts

An organization's projects are the public projects it owns and the public projects it is credited
on. Its datasets are the public datasets it is credited on and the public datasets inside the
projects it owns, whether or not it is credited on them. Nothing is counted twice, a record in a
private project is left out, and what its members did under their own names is not counted as the
organization's. A project the organization owns is marked as owned in the Projects card.

`Organization.get_public_projects()` and `get_public_datasets()` return these two lists. The
overview's figures and cards and the Projects and Datasets tabs all read them, so a figure always
equals the number of entries behind its link.

### Who keeps the record

The checklist and the management menu are shown to the organization's owner and administrators,
meaning the people whose current affiliation to it is of that kind. A portal role such as
Community Manager does not count, because portal staff manage organizations from the administration
interface. `Organization.is_managed_by(user)` answers it. Asking to join is offered to a signed-in
user for whom neither `has_member(user)` nor `is_managed_by(user)` holds.

### Extending an organization page

Override the template as for the person page. This adds a card to the end of the side column and
keeps every card FairDM draws there:

```django
{% extends "contributors/overview/organization.html" %}

{% block overview.side %}
  {{ block.super }}
  <c-card title="Our partners" class="bg-base-100">
    {{ organization.name }} works with several partners.
  </c-card>
{% endblock overview.side %}
```

The blocks read `record`, `organization`, `can_manage`, `is_member`, `members`, `projects`,
`datasets`, `org_counts`, `hierarchy`, `location_text`, `has_map`, `languages`, `identifier`,
`identifier_url`, `identifiers`, `links`, `urls`, `api_url` and `json_ld`, and `readiness` for the
people who keep the record. `records_shown` (five) and `member_slots` (ten) on the plugin say how
many records each record card lists and how many places the Members card has.

## Giving a sample or measurement type its own page

A portal that defines a sample type adds the type's fields to its page by providing one template.
There is nothing to register. For each type from the sample's own up to `Sample`, the page looks for
`<app_label>/<model_name>_overview.html`, then falls back to `sample/sample_overview.html`. So:

- A type with a template of its own uses it.
- A subtype without one uses its parent type's template.
- A type with no template anywhere in its ancestry uses the shared page.

Measurements work the same way, with `measurement/measurement_overview.html` as the shared page.

The demo's XRF measurement is the worked example. `XRFMeasurement` records an element and a
concentration instead of a single `value`, so the shared result area has nothing to show. Its
template, `demo/xrfmeasurement_overview.html`, extends the shared page and fills three blocks:

```django
{% extends "measurement/measurement_overview.html" %}
{% load i18n humanize %}

{# Add the element beside the type badge; block.super keeps it. #}
{% block overview.badges %}
  {{ block.super }}
  <span class="badge badge-outline badge-sm font-mono">{{ measurement.element }}</span>
{% endblock overview.badges %}

{# The result, in place of the single value the shared page would show. #}
{% block overview.result %}
  <c-card.wrapper class="bg-base-100">
    <div class="card-body gap-3">
      <p class="text-4xl font-semibold tabular-nums">{{ measurement.concentration_ppm|floatformat:"-2"|intcomma }}</p>
    </div>
  </c-card.wrapper>
{% endblock overview.result %}

{# The block the shared page leaves empty for exactly this: the type's own fields. #}
{% block overview.properties %}
  <c-card title="{% translate 'Analytical conditions' %}" class="bg-base-100">
    <c-data-field label="{% translate 'Element' %}" value="{{ measurement.element }}" />
  </c-card>
{% endblock overview.properties %}
```

The demo's template goes further, with the detection limit and a warning when the concentration is
at or below it. Every block it does not fill shows the shared content: how it was measured, the
sample it was made on, the other measurements and the side column. In the template, `measurement`
is the measurement as its own type, so `measurement.element` reads the XRF field. An
`ICP_MS_Measurement` declares a `value` and has no template of its own, so it shows the shared page
with its result drawn for it.

The demo's rock sample is the worked example. `RockSample` is in the `demo` app, so its template is
`demo/rocksample_overview.html`. It extends the shared page and fills two blocks:

```django
{% extends "sample/sample_overview.html" %}
{% load i18n %}

{# Add the rock type beside the generic type and status badges; block.super keeps those. #}
{% block overview.badges %}
  {{ block.super }}
  {% if sample.rock_type %}
    <span class="badge badge-outline badge-sm">{{ sample.rock_type|capfirst }}</span>
  {% endif %}
{% endblock overview.badges %}

{# The block the shared page leaves empty for exactly this: the type's own fields. #}
{% block overview.properties %}
  <c-card title="{% translate 'Rock properties' %}" class="bg-base-100">
    <c-data-field label="{% translate 'Rock type' %}" value="{{ sample.rock_type|capfirst }}" />
    <c-data-field label="{% translate 'Hardness (Mohs)' %}" value="{{ sample.hardness_mohs|default_if_none:'' }}" />
  </c-card>
{% endblock overview.properties %}
```

Every block the template does not fill shows the shared content: the history, the measurements,
the side column and the citation all stay. In the template, `sample` is the sample as its own type,
so `sample.rock_type` reads the rock's field. The shared page still reads only `Sample`. A
`WaterSample` in the same app has no `demo/watersample_overview.html`, so it shows the shared page.

A subtype of `RockSample` needs nothing to inherit this page. To give it a page of its own, add
`demo/<subtype>_overview.html` and extend `demo/rocksample_overview.html` to keep the rock card.

**A custom manager is fine.** The page decides who may open a sample by asking `Sample.objects`
(and `Measurement.objects` for a measurement), never the type's own manager. A type can declare a
plain `QuerySet` manager with no `visible_to` and its page still opens for the dataset's team and
answers "not found" to a visitor.

**The visibility rules are queryset methods.** `published()` keeps the records whose own dataset is
published. `visible_to(user)` keeps the records a user may see: those in a dataset that is public
and published, and those in a dataset on which the user holds `view_dataset` or `change_dataset`.
Both are decided against each record's own dataset, so being on one dataset's team never opens
another dataset's records. `SampleQuerySet` and `MeasurementQuerySet` get them from
`fairdm.core.managers.RecordVisibilityMixin`. A queryset of your own for a record that has a
`dataset` foreign key can use the mixin too:

```python
from django.db.models import QuerySet

from fairdm.core.managers import RecordVisibilityMixin


class CoreQuerySet(RecordVisibilityMixin, QuerySet):
    pass
```

The sample's own steps are methods on its `Overview` plugin in `fairdm.core.sample.plugins`:

| Method | What it returns |
| --- | --- |
| `get_status()` | The custody status: its stored `value`, its `label`, the badge colour `variant` and what it `meaning`s for re-examining the specimen. `status_variants` and `status_meanings` hold the colours and the meanings. |
| `get_measurements()` | The measurements made on the sample the viewer may see: `items` (the most recent, up to `measurements_shown`, ten by default), the `total` and how many are `more`. |
| `get_related_samples()` | The parents and subsamples the viewer may see, as `items`, `parents` and `children`, each saying how it relates. `hidden` counts those the viewer may not see. |
| `get_relations_summary(relations)` | The figure's caption, such as "1 parent · 2 subsamples", or "None recorded". |
| `get_citation_details(entries, dates, identifiers)` | The citation's title and text, with a note when the sample has no IGSN. |
| `get_details(project, status)` | The rows of the Details card. `project` is `None` when the viewer may not see it. |

The steps of the history are in the plugin's `lifecycle` list, each as a date type, the contributor
role that performs it, the description type that explains it and the label the page shows. A portal
can subclass `Overview` and replace the list.

The blocks read `record`, `sample`, `sample_type`, `type_info`, `status`, `lifecycle`, `notes`,
`measurements`, `relations`, `location`, `project`, `counts`, `people`, `identifiers`, `citation`
and `details`.

The measurement's own steps are methods on its `Overview` plugin in
`fairdm.core.measurement.plugins`:

| Method | What it returns |
| --- | --- |
| `get_result()` | The result's `text` when the measurement's type declares a `value`, otherwise `None`. |
| `get_sample_status()` | The sample's status `label` and badge colour `variant`, as the sample's own page shows them, or `None` when it has no status. |
| `get_siblings()` | The other measurements on the same sample the viewer may see: `rows` (up to `siblings_shown`, eight by default), the `total` and how many are `more`. |
| `get_citation_details(entries, dates, identifiers, sample)` | The citation's title and text, with a note pointing at the dataset when the measurement has no DOI. `sample` is `None` when the viewer may not see it. |
| `get_details(project)` | The rows of the Details card. `project` is `None` when the viewer may not see it. |

The steps of "How it was measured" are in the plugin's `procedure_steps` list, each as a date type,
the contributor role that performs it, the description type that explains it and the label the page
shows. A portal can subclass `Overview` and replace the list.

The blocks read `record`, `measurement`, `measurement_type`, `type_info`, `result`, `procedure`,
`notes`, `sample`, `sample_type`, `sample_status`, `sample_visible`, `other_dataset`, `siblings`,
`project`, `citation`, `identifiers`, `people` and `details`.

## What the plugins work out

The page's numbers and lists come from two plugin classes in `fairdm.core.plugins`.

`RecordOverviewPlugin` holds what every overview page works out the same way. The four `Overview`
plugins subclass it. A portal building its own page for a record can subclass it too.

| Method | What it returns |
| --- | --- |
| `get_contributions()` | The record's credits with each contributor as its own type, person or organisation. Ask a credit `is_person()` to tell them apart. |
| `get_role_names(contribution)` | The names of the roles held on one credit. |
| `get_contributors_with_role(entries, role)` | The contributors in `get_credits()` entries who hold a role. |
| `get_credits()` | Everyone credited on the record, each contributor as its own type (person or organisation), with role labels and affiliation. |
| `get_people(entries=None)` | What the People card shows: `shown` (up to `people_shown`, eighteen by default), `more` and `total`. |
| `get_identifiers()` | The record's identifiers with a doi.org link on a DOI or an IGSN. `resolvable_identifier_types` lists the types that link. |
| `get_citation(authors=, year=, title=, link=)` | The citation as text: `Creators (Year). Title. Publisher. Identifier.` |
| `get_timeline(steps, dates, descriptions, entries)` | One entry per step in a record's life, joining the date, the contributor role and the description of that step. Dated steps come first. |
| `get_license_entry(licence, note=None)` | The Details card's licence entry, or a warning when none is chosen. |
| `get_composition_chart(samples, measurements)` | The chart of records by type. A type the registry does not hold is left out. |
| `get_growth_chart(samples, measurements)` | The chart of the running total by month. |

`TypedOverviewPlugin` subclasses `RecordOverviewPlugin` for the record types portals subclass, the
sample and the measurement. It adds the template lookup by type and `get_type_info()`, which reads
what the registry says about the record's type. A subclass names its `base_model`, and the plugin
then opens a record only for a user the base model's `visible_to` lets see it. A subclass with no
`base_model` opens no record.

Override one method to change one piece of a page. This subclass lists eight people in the People
card instead of eighteen:

```python
from fairdm.core.plugins import RecordOverviewPlugin


class Summary(RecordOverviewPlugin):
    people_shown = 8
```

The project's own steps are methods on its `Overview` plugin in `fairdm.core.project.plugins`:
`get_descriptions()`, `get_progress()`, `get_team()`, `get_counts()`, `get_datasets_preview()`,
`get_licenses()`, `get_citation_details()`, `get_readiness()` and `get_details()`.

The dataset's own steps are methods on its `Overview` plugin in `fairdm.core.dataset.plugins`:

| Method | What it returns |
| --- | --- |
| `get_access()` | The dataset's state, `private`, `public` (not published) or `published`, with its label. |
| `get_descriptions()` | The descriptions the dataset has text for, in the vocabulary's order. |
| `get_dates()` | The collection start and end and the available, submitted, published and withdrawn dates, each `None` when not recorded and otherwise a partial date with the precision it was recorded at, plus the withdrawal written out as `withdrawn_text`. |
| `get_lifecycle(dates)` | The timeline's steps, in the order they happened. |
| `get_team()` | The creators, whether a contact person is credited, and how many contributions the dataset has. |
| `get_literature()` | The related publications, each with its relation worded from the publication's side, its DOI and its year. |
| `get_record_types(samples, measurements)` | The registered sample and measurement types the dataset holds, each with its `kind`, `label` and the labels of its `fields`. `bookkeeping_fields` lists the fields left out. |
| `get_counts(samples, measurements, data_types)` | The sample and measurement counts, each with how many types it spans. |
| `get_project_info()` | The project and how many other datasets in it the viewer may see, or `None` when the viewer may not see the project. |
| `get_citation_details(page)` | The citation's text and link, and whether it comes from a data publication or has a DOI. |
| `get_schema_org(page)` | The schema.org `Dataset` description for the page head. |
| `get_readiness(page)` | The checklist's items, how many are done and whether every required one is. |
| `get_details(project_info)` | The rows of the Details card. |
| `get_shared_context(page)` | The keys every overview page provides. |

Each `page` argument is the context the plugin has gathered so far.

### Helper functions

What no class owns is a plain function in `fairdm.core.overview`:

| Function | What it does |
| --- | --- |
| `format_authors(contributors)` | Writes creators in citation style: `Keller, A., Oliveira, T. & Brandt, L.` |
| `author_name(contributor)` | One creator: surname and initial, or the contributor's name when they have no first name. |
| `json_ld(data)` | Serialises data for an inline script element, with `<`, `>` and `&` escaped so a name can never end the element. |
| `as_date(partial)` | A date from a partial date of any precision, or `None`. It pads a year or month to a day, so use it to sort and compare, not to show. |
| `format_partial_date(partial)` | Writes a partial date as a day, a month and year, or a year, as it was recorded. |
| `sentence_case(text)` | Capitalises the first letter only, so `XRF measurements` keeps its acronym. |
| `safe_reverse(name, **kwargs)` | A URL, or `None` when the name does not resolve. |

## Development data

`manage.py seed_overviews` loads records that reach every state the pages describe, so you can
open each one as a visitor and as a member of a team. It refuses to run outside development. It
creates three accounts when they are missing and leaves ones that exist as they are, and running
it again replaces only the projects it created. See
[development accounts](development_accounts.md) for the accounts.

The command runs three seeds in `demo/seed/`: `ProjectSeed`, `SampleSeed` and `MeasurementSeed`.
They share three helpers in `demo/seed/common.py`: `example_accounts()` returns the accounts,
creating the missing ones, `remove_own_projects()` deletes the projects an earlier run created, and
`grant_team_rights(user, *records)` gives an account view, change and delete rights on the projects
and datasets it is given. `staff.user` holds those rights on every seeded project and dataset, so
its pages show the readiness checklist. `regular.user` holds none.
