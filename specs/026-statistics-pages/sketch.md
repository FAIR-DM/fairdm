# Sketch: 026-statistics-pages

A prototype of the four Statistics pages, built to be looked at. It has no tests, and the code
behind the screens is there only to put real figures on them.

To load the data the screens need:

    DJANGO_ENV=development python manage.py seed_overviews
    DJANGO_ENV=development python manage.py seed_profiles
    DJANGO_ENV=development python manage.py seed_statistics

`seed_statistics` prints the address of each dataset and project state it creates.

## What exists

- A tab is a plugin registered against a model. Projects, datasets and contributors each have an
  overview plugin, and a person and an organization share one registration on `Contributor` that
  picks a template by type. The Statistics tabs are registered the same way.
- The overview pages draw two charts with `c-chart` (pyecharts through django-mvp-charts), each
  with a caption and a text alternative. They take their colours from the active theme.
- `c-stats` and `c-stats.item` draw a strip of figures. `c-card.roles` lists contribution roles
  with a bar each. `c-progress`, `c-missing`, `c-alert` and `c-avatar` are used as they are.
- Samples and measurements have `visible_to(user)`, which returns the records of published public
  datasets plus those of datasets the user has rights on.
- A contributor has `get_public_projects()`, `get_public_datasets()`,
  `get_visible_contributions(user)`, `get_role_counts()` and `get_collaborators()`. An
  organization has `get_current_memberships()`.
- A registered type's configuration resolves a field list per component (`table`, `form` and so
  on). There is no list for statistics yet.
- A contribution has no date. Projects, datasets, samples and measurements carry `added`.

## What the screens need from the code

- Dataset page: for each sample and measurement type with records the viewer may see, the number
  of records and, per statistics field, how many have a value. A number also needs smallest,
  largest, mean, median and a twelve-bar distribution. A date needs earliest, latest and counts
  per year (per month when all dates fall in one year). A category needs a count per value.
- Dataset page: whether the dataset holds any records at all, separately from whether the viewer
  may see them, so the empty page can say which of the two it is.
- Project page: the same summaries over every dataset the viewer may see, decided dataset by
  dataset. A viewer on the team of one private dataset sees that dataset counted.
- Project page: samples and measurements per dataset, and the dates datasets, samples,
  measurements and contributors were added, for the running totals.
- Person page: counts of credits by kind of record, public projects and datasets by year added,
  role counts that match the overview, and every collaborator with the number of shared records.
- Organization page: its own public projects and datasets, the public projects and datasets of
  its current members with each record counted once, the number of members with a counted record
  in each year, and the other organizations on the counted records.
- Every chart needs its figures as text. The yearly charts carry a table the reader can open.

## What the sketch faked

- Every figure is worked out in Python on each request by loading the values. It is correct on
  the seeded data and far too slow for a large dataset. The speed target in the specification is
  not met or measured.
- The statistics fields of a type are read from an optional `statistics_fields` attribute on its
  configuration, falling back to its table fields. The attribute is not declared on
  `ModelConfiguration`, not validated at start-up and not documented.
- A fixed list of bookkeeping fields (`id`, `uuid`, `name`, `dataset`, `sample`, `added`,
  `modified`, `image`, `options`) is left out by name.
- A field counts as a category only when it has choices, is a yes/no field or points at another
  record. A field holding a quantity with a unit is recognised by its value, and no seeded type
  has one, so the unit is never seen on screen.
- A project's running total of contributors counts the people credited on the project and its
  datasets, each from the date the first of those records was added.
- The person and organization pages apply no access rule of their own beyond the model methods
  they call.
- The four pages load the charting library from the same public address the overview pages use.
- Nothing is cached, and nothing is translated beyond marking the strings.

## What was ruled by eye

Nothing yet. These are the choices made without a rule to settle them, for review:

- Field summaries are rows inside one card per record type, in four columns: the field, how
  complete it is, its figures, its distribution. Below the `md` breakpoint the columns stack.
- The small distributions are drawn in plain markup, not with the charting library, so a type
  with thirty fields costs thirty short rows and no scripts. Each bar shows its range and count
  on hover, and the whole distribution is read out as text.
- A dataset or project with more than one record type gets a row of links to each type's card.
- The project page puts growth first, then the breakdown by dataset, then the field summaries.
- Growth is two charts, not one: samples and measurements on one, datasets and contributors on
  the other. The two pairs differ by orders of magnitude and would flatten each other on a
  shared axis.
- The organization page shows its own records and its members' records as two labelled groups
  of figures side by side.
- Collaborators and partner organizations are tables, in the order the overview's card uses.

## Where the open choices in decisions.md show on screen

- No summaries for a visitor on an unpublished dataset: the dataset page of "Second drilling
  season (not yet published)" shows a notice and nothing else to a visitor, and the full page to
  `regular.user`. With the other answer the visitor would see the same page as the team.
- Member output counts everything a current member is credited on: the right-hand figures and
  both charts on the organization page. With the other answer they would count only credits that
  name the organization as the affiliation, and most seeded bars would shrink or vanish.
- Organizations linked through affiliations on credits: the table at the foot of the
  organization page. With the other answer it would list only organizations credited directly.
- Credits placed by the date the record was added: the horizontal axis of both yearly charts and
  of the project's growth charts.

One more question came up while building. Short text fields that behave like categories (rock
type, element, isotope) are free text in the model, so the specification gives them a count and
nothing else. On screen that is the least informative row of each card.
