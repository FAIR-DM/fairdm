# Overview pages

Every project, dataset, sample and measurement opens on an **overview page**, the first tab of the
record's tabbed detail view. It is written for three readers: someone deciding whether the data is
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

Two rules hold on every page. A card with nothing to show is either left out or says what is
missing, never left blank. And anything FairDM cannot do yet (a map of a project's samples, recent
activity, publishing a dataset, exporting a citation, metadata downloads) is announced the same
way: a card or a button that says "Coming soon", and a button is disabled and says why.

## The blocks

`overview/page.html` defines every block, in page order. Each record's own template extends it and
fills blocks. The blocks carry the `overview.` prefix:

| Block | What it holds |
| --- | --- |
| `overview.image` | Header: the record's image, or its icon. |
| `overview.badges` | Header: status badges. |
| `overview.byline` | Header: the people behind the record (a project's leaders, a dataset's creators), each linked to their page. |
| `overview.keywords` | Header: keywords. |
| `overview.actions` | Header: buttons. Cite and Share by default. |
| `overview.notices` | Alerts above the figures. |
| `overview.figures` | The figures strip. |
| `overview.main` | The wide column. Each record fills it with its own blocks. |
| `overview.side` | The side column, which holds the blocks below. |
| `overview.readiness` | What the team still has to add. The team only. |
| `overview.details` | What the record belongs to, its licence, status, dates and how machines reach it. |
| `overview.details_extra` | Inside Details: sections a record adds, such as a project's timeline. |
| `overview.timeline` | Key dates in the record's life, on records that have their own card for them. |
| `overview.people` | Everyone credited who is not already named in the header. |
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

**Notices.** The team of a private project is told the project is private. A project whose status
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

**Notices.** A private dataset tells its team that only they can open the page. A public dataset
that is not published yet tells a visitor that its data is not published, and tells the team that
its records stay hidden until it is. A dataset with a Withdrawn date says it has been withdrawn
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
available from and withdrawn. A step with no date recorded is left out. Days follow the active
language's short date format.

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
with no recorded status reads "Status unknown".

**Notices.** A destroyed specimen says it no longer exists and that its record and measurements
are kept. A sample whose dataset is not public and published tells the dataset's team that only
they can see it.

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

## Giving a sample or measurement type its own page

A portal that defines a sample type adds the type's fields to its page by providing one template.
There is nothing to register. For each type from the sample's own up to `Sample`, the page looks for
`<app_label>/<model_name>_overview.html`, then falls back to `sample/sample_overview.html`. So:

- A type with a template of its own uses it.
- A subtype without one uses its parent type's template.
- A type with no template anywhere in its ancestry uses the shared page.

Measurements work the same way, with `measurement/measurement_overview.html` as the shared page.

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

## What the plugins work out

The page's numbers and lists come from two plugin classes in `fairdm.core.plugins`.

`RecordOverviewPlugin` holds what every overview page works out the same way. The four `Overview`
plugins subclass it. A portal building its own page for a record can subclass it too.

| Method | What it returns |
| --- | --- |
| `get_credits()` | Everyone credited on the record, each contributor as its own type (person or organisation), with role labels and affiliation. |
| `get_people(entries=None, exclude=())` | What the People card shows: `shown` (up to `people_shown`, eighteen by default), `more` and `total`. `exclude` names contributors already in the header. |
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
| `get_dates()` | The collection start and end and the available, submitted, published and withdrawn dates as plain dates, each `None` when not recorded. |
| `get_lifecycle(dates)` | The timeline's steps, in the order they happened. |
| `get_team()` | The creators, the contact person, everyone else and how many people and organisations are credited. `lead_roles` names the roles listed first. |
| `get_literature()` | The related publications, each with its relation worded from the publication's side, its DOI and its year. |
| `get_record_types(samples, measurements)` | The registered sample and measurement types the dataset holds, each with its `kind`, `label` and the labels of its `fields`. `bookkeeping_fields` lists the fields left out. |
| `get_counts(samples, measurements, data_types)` | The sample and measurement counts, each with how many types it spans. |
| `get_project_info(can_manage)` | The project and how many other datasets it has, or `None` when the viewer may not see it. |
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
| `as_date(partial)` | A date from a partial date of any precision, or `None`. |
| `sentence_case(text)` | Capitalises the first letter only, so `XRF measurements` keeps its acronym. |
| `safe_reverse(name, **kwargs)` | A URL, or `None` when the name does not resolve. |
| `contributions_of(record)` | A record's credits with each contributor as its own type. |
| `roles_of(contribution)` | The names of the roles held on one credit. |
| `is_person(contributor)` | Whether a contributor is a person rather than an organisation. |
| `with_role(entries, role)` | The contributors in `get_credits()` entries who hold a role. |

## Development data

`manage.py seed_overviews` loads records that reach every state the pages describe, so you can
open each one as a visitor and as a member of a team. It refuses to run outside development. It
creates three accounts when they are missing and leaves ones that exist as they are, and running
it again replaces only the projects it created. See
[development accounts](development_accounts.md) for the accounts.

The command runs three seeds in `demo/seed/`: `ProjectSeed`, `SampleSeed` and `MeasurementSeed`.
They share two helpers in `demo/seed/common.py`: `example_accounts()` returns the accounts,
creating the missing ones, and `remove_own_projects()` deletes the projects an earlier run created.
