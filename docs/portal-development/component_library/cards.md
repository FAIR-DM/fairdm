# Cards

The four overview pages (project, dataset, sample and measurement) are built from a small set of
cards. Each card is one Cotton component under the `card` namespace, drawn the same way on every
page, so you can put the same card in a sample type's own template and it will look and behave as
it does everywhere else. The [overview pages guide](../overview-pages.md) says where each card sits
on a page and which template block holds it.

Every card is a `<c-card.NAME>` tag. Attributes that take a Python value (a list, a dictionary, a
record) are written with a leading colon, the way any Cotton component takes one:
`<c-card.people :people="people" />`. Every card also takes `class`, which adds classes to the
card's outer element.

A page draws every card it has and each says what is missing when it has nothing to show. Each card carries a `data-card` attribute (`details`, `people`, `identifiers`, `funding`, `citation`, `timeline`, `location`, `readiness`, `projects`, `datasets`, `roles`, `links`, `affiliations`, `members`, `hierarchy`) that tests and scripts can find it by.

## The shared cards

### `c-card.details`

The record's metadata in one card: what it belongs to, its licence, its status and dates, and how
a machine reaches it. Every entry is a `c-card.details.entry`, so a card built from rows and one
you add sections to read as one list. The card always ends with a "For machines" entry holding the
REST API link and a disabled "Metadata downloads" button.

| Attribute | What it takes |
| --- | --- |
| `rows` | A list of dictionaries, one per entry. Keys: `label`, `icon`, and one of `record` (a record, shown by name and linked to its own page), `badge` with `badge_variant`, `date` (with `until` for a range), `text` with an optional `url`. Also `note` (a line under the value) and `warning` (draws the value as a warning). |
| `api_url` | The record's REST API address. Left empty, no API link is drawn. |

Dates are written in the active language's short date format.

| Slot | What it holds |
| --- | --- |
| default | Entries after the rows, for example a project's timeline. |

```django
<c-card.details :rows="details" api_url="{{ api_url }}">
  <c-card.details.entry label="Instrument" icon="info">
    Bruker S8 Tiger
  </c-card.details.entry>
</c-card.details>
```

`details` is a list such as
`[{"label": "Licence", "icon": "license", "text": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}]`.

### `c-card.details.entry`

One entry in a Details card: an icon and a title in capitals, then the value. Use it inside
`c-card.details` to add a section of your own.

| Attribute | What it takes |
| --- | --- |
| `label` | The entry's title. |
| `icon` | An icon name. |

```django
<c-card.details.entry label="Instrument" icon="info">Bruker S8 Tiger</c-card.details.entry>
```

### `c-card.people`

Everyone credited on the record, the people named in the page header included, as a grid of faces.
Hovering a face shows the name, and every face is a link to the contributor's page, named for
assistive technology. At most eighteen faces are drawn. The rest are counted, and the count links
to the full list when `all_url` is given. With nobody credited the card says so.

| Attribute | What it takes |
| --- | --- |
| `people` | A dictionary: `shown` (the contributors to draw), `more` (how many were left out) and `total`. `RecordOverviewPlugin.get_people()` builds it. |
| `all_url` | Where the full list of contributors is. |
| `title` | The card's title. Defaults to "People". |
| `empty` | What to say when nobody is credited. Has a default. |

```django
<c-card.people :people="people" all_url="{{ people_url }}" />
```

### `c-card.identifiers`

Every identifier the record carries, the team's own ID and the record's portal ID, which has a
button to copy it. DOIs and IGSNs link to doi.org.

| Attribute | What it takes |
| --- | --- |
| `identifiers` | A list of `{"type", "value", "link"}` dictionaries. `link` is set for a DOI or an IGSN. `RecordOverviewPlugin.get_identifiers()` builds it. |
| `portal_id` | The record's portal ID. |
| `local_id` | The team's own ID for the record. |

```django
<c-card.identifiers :identifiers="identifiers"
                    portal_id="{{ record.uuid }}"
                    local_id="{{ record.local_id|default:'' }}" />
```

### `c-card.funding`

The awards that paid for the record, each with its funder, title and number. The funder links to
its identifier and the number to the award's page where the award records them. An identifier
or award page is linked only when it is an `http://` or `https://` address; anything else, such as a
bare funder ID, is shown as plain text.

| Attribute | What it takes |
| --- | --- |
| `funding` | A list of DataCite funding references: `funderName`, `funderIdentifier`, `awardTitle`, `awardNumber`, `awardURI`. |
| `can_manage` | Whether the viewer is on the record's team. |

With no funding, everyone gets a card that says none is recorded.

```django
<c-card.funding :funding="funding" :can_manage="can_manage" />
```

### `c-card.citation`

How to cite the record, with a button that copies it and a disabled export button. The card's
element id is `cite`, which the Cite button in every page header jumps to.

| Attribute | What it takes |
| --- | --- |
| `title` | The card's title. |
| `text` | The citation, as plain text. `RecordOverviewPlugin.get_citation()` writes it. |

| Slot | What it holds |
| --- | --- |
| default | A note under the citation, for example that it points at the page because the record has no DOI. |

```django
<c-card.citation title="Citation" text="{{ citation.text }}">
  This record has no DOI, so the citation points at this page.
</c-card.citation>
```

### `c-card.descriptions`

The record's descriptions, abstract first. With more than one, each has a tab in the card's header.
With one, its name is the card's title. With none, the card is titled "About" and shows its slot.

| Attribute | What it takes |
| --- | --- |
| `descriptions` | A list of `{"label", "value"}` dictionaries in the order the tabs appear. The value is markdown. |
| `group` | A name for the tab set, unique on the page. |

| Slot | What it holds |
| --- | --- |
| default | What to show when there are no descriptions. |

```django
<c-card.descriptions :descriptions="descriptions" group="project-about">
  <p>No description has been added yet.</p>
</c-card.descriptions>
```

### `c-card.timeline`

What happened to a record, in order: a sample's history, a measurement's procedure. Each step says
when, by whom and how. A date recorded only to the year is written as the year, and one recorded
only to the month as the month.

| Attribute | What it takes |
| --- | --- |
| `title` | The card's title. |
| `steps` | A list of `{"label", "date", "day", "people", "note"}` dictionaries. `day` is set when the date is a full day. `RecordOverviewPlugin.get_timeline()` builds it. |
| `empty` | What to say when there are no steps. |

```django
<c-card.timeline title="History" :steps="history" empty="Nothing is recorded yet." />
```

### `c-card.location`

Where a sample was taken: a map with the point marked and the coordinates written out, so the
position is in the page as text as well. The map is drawn by the script the page loads when it has
a location.

| Attribute | What it takes |
| --- | --- |
| `location` | A location point with `x` (longitude), `y` (latitude) and `crs`. |
| `title` | The card's title. Defaults to "Location". |
| `empty` | What to say when there is no location. Without it, the component draws nothing. |
| `label` | The map's name for assistive technology. Defaults to a name written for a sample. |

```django
<c-card.location :location="sample.location" empty="No location recorded." />
```

### `c-card.readiness`

For the record's team only: what is still missing before the record can be found, trusted or
published. Missing items come first, each linked to the page that fixes it where there is one.

| Attribute | What it takes |
| --- | --- |
| `title` | The card's title. |
| `summary` | One line on the overall state. |
| `about` | One line on why the list matters. |
| `badge` | Who can see the card. Defaults to "Edit access only". |
| `readiness` | A dictionary: `items` (a list of `{"label", "done", "url"}`, plus `required` set to `False` for a recommended item), `done`, `total` and `ready`. |

```django
<c-card.readiness :readiness="readiness"
                  title="Metadata readiness"
                  summary="{{ readiness.done }} of {{ readiness.total }} in place"
                  about="What search engines and repositories look for." />
```

### `c-card.records`

The projects or the datasets a contributor is behind, each linked to its page. A project shows its
status. The card counts every record, lists the ones it is given and links to the full list. Its
`data-card` is `projects` or `datasets`, following `kind`.

| Attribute | What it takes |
| --- | --- |
| `title` | The card's title. |
| `records` | A dictionary: `shown` (a list of `{"record", "owned"}`), `more` (how many do not fit) and `total`. `fill_slots()` builds it. |
| `kind` | `project` or `dataset`. It picks the icon and, for a project, shows the status. |
| `variant` | The theme colour of the record type. |
| `all_url` | Where the full list lives. It is the "View all" button and the link on the count of the rest. |
| `empty` | What to say when there are none. |

```django
<c-card.records title="Projects" :records="projects" kind="project" variant="info"
                all_url="{{ urls.projects }}" empty="Not credited on any public project yet." />
```

`projects` is `fill_slots([{"record": project, "owned": False}, ...], 5)`. An entry with `owned` set shows an owner badge, which an organization's page uses for the projects it owns. Ordering the records
beforehand, for example with `active_then_recent()`, decides which ones are shown.

### `c-card.roles`

The contribution roles a contributor holds, most held first, each with the number of records it is
held on and a bar showing its share of the most held role.

| Attribute | What it takes |
| --- | --- |
| `roles` | A list of `{"label", "count", "percent"}`, the shape `ranked_shares()` returns. |

```django
<c-card.roles :roles="roles" />
```

### `c-card.links`

A contributor's links elsewhere on the web, each named by the site it points at and opened without
passing the page on to the site.

| Attribute | What it takes |
| --- | --- |
| `links` | A list of `{"url", "host"}`, the shape `Contributor.get_links_display()` returns. |

```django
<c-card.links :links="links" />
```

### `c-card.affiliations`

Where a person works and has worked. The current affiliations come first, the primary one marked,
then the earlier ones. Each links to its organization and gives its period as precisely as it was
recorded. `c-card.affiliations.row` draws one affiliation and is used inside the card.

| Attribute | What it takes |
| --- | --- |
| `affiliations` | A dictionary of `current` and `past`, each a list of affiliations. `Person.get_affiliation_history()` returns it. |

```django
<c-card.affiliations :affiliations="affiliations" />
```

### `c-card.hierarchy`

Where an organization sits among the organizations around it: its parent at the top, this
organization among its siblings, and its own direct sub-organizations beneath it. This organization
is highlighted and not a link, and every other one links to its page. With no parent, this
organization is the top of the tree. With neither a parent nor sub-organizations the card says that
none is recorded. `c-card.hierarchy.node` draws one organization and is used inside the card.

| Attribute | What it takes |
| --- | --- |
| `organization` | The organization the page is about. |
| `hierarchy` | A dictionary of `parent` (or `None`), `siblings` (the parent's sub-organizations, this one included) and `children`. `Organization.get_hierarchy()` returns it. |

```django
<c-card.hierarchy :organization="organization" :hierarchy="hierarchy" />
```

### `c-card.placeholder`

A card for something FairDM cannot show yet. It carries a "Coming soon" badge, one line on what
the card will show, and no link or button. Every page uses it for the same things (maps, recent
activity), so a planned feature always looks the same.

| Attribute | What it takes |
| --- | --- |
| `title` | The card's title, as it will read once the feature exists. |
| `icon` | An icon for the empty area. |
| `message` | What the card will show. |
| `wide` | Keeps the empty area at 16:9, for cards that will hold a map or a chart. |

```django
<c-card.placeholder title="Spatial coverage" icon="map" wide
                    message="A map of every sample with a location." />
```

A button for something that is not available yet is the `c-actions.pending` component, described
under the general components.

## General components

The pages also use a few small components that are not cards.

### `c-stats` and `c-stats.item`

A strip of figures read as one group. `cols` sets how many columns the strip has below the `lg`
breakpoint and `lg` how many from it up.

| Attribute of `c-stats.item` | What it takes |
| --- | --- |
| `title` | What is counted. |
| `value` | The figure. |
| `desc` | A line under the figure. |
| `href` | Makes the title a link to where the figure comes from. |
| `variant` | The colour of the figure and its icon. |
| `icon` | An icon drawn in a tinted tile. |

```django
<c-stats cols="2" lg="4" aria-label="Project at a glance">
  <c-stats.item title="Datasets" value="4" icon="dataset" variant="success" />
  <c-stats.item title="Samples" value="1,280" icon="sample" variant="secondary" />
</c-stats>
```

### `c-list` and `c-list.row`

Rows of like records, each laid out the same way. `title` is a small heading above the rows and
`label` names the list for assistive technology when there is no visible title.

```django
<c-list label="Most recently updated datasets">
  <c-list.row>
    <div class="list-col-grow">Core samples</div>
    <div>4 Mar 2026</div>
  </c-list.row>
</c-list>
```

### `c-tabs` and `c-tabs.tab`

Tabs built from radio inputs, so they switch with no JavaScript and every panel stays in the page.
Every tab in one set takes the same `group`. `label` on `c-tabs` names the set for assistive
technology, and `checked` marks the tab shown first.

```django
<c-tabs group="about" label="Descriptions">
  <c-tabs.tab group="about" label="Abstract" checked>An abstract.</c-tabs.tab>
  <c-tabs.tab group="about" label="Methods">The methods.</c-tabs.tab>
</c-tabs>
```

### `c-progress`

A progress bar. `label` is required: it names the bar for assistive technology, so say what is
measured and how far along it is.

```django
<c-progress value="40" max="100" label="Year 2 of 5" />
```

### `c-missing`

What a card says when it has nothing to show, drawn as a notice so it cannot be taken for a short
line somebody wrote. The default slot holds the text, and anything that follows it, such as a
button that fixes the gap.

```django
<c-missing><span>No links have been added.</span></c-missing>
```

### `c-actions.pending`

A button for something that is not available yet. It is disabled, never submits or links, and gives
its reason to a pointer and to a screen reader.

| Attribute | What it takes |
| --- | --- |
| `label` | The button's text. |
| `icon` | An icon before the text. |
| `reason` | What the button will do once it exists. |
| `variant` | `primary` for a filled button. The default is outlined. |
| `size` | `xs` or `sm`. The default is `sm`. |

```django
<c-actions.pending label="Publish" icon="upload" reason="Publishing is not available yet." />
```
