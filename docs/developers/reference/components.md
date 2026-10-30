# Components

FairDM ships Cotton components that a portal's templates can use. This page lists each one with its attributes, its slots and what it renders. It does not say where a component sits on a page. The pages that use them are described in [Overview page blocks](overview-page-blocks.md), [Home page](home-page.md) and [Entrance pages](entrance-pages.md).

Every component is written as a tag named after its template path, with `/` turned into `.` and `_` turned into `-`. `card/details/entry.html` is `<c-card.details.entry>`. An attribute that takes a Python value, such as a list, a dictionary or a record, is written with a leading colon: `<c-card.people :people="people" />`. Most components also take `class`, which adds classes to the outer element, and pass any other attribute to it.

The tables give each attribute's type, its default and what it accepts. A blank default means the attribute is not set.

## Actions

### `c-actions.create-new`

A dropdown button labelled "Create new" with a link to the project create page and one to the dataset create page. It renders only for a signed-in user and reads `user` from the template context, so it takes no attributes.

### `c-actions.manage`

The Manage menu of a record's page: a dropdown of the editing pages the viewer may use. It draws nothing when there are no entries and the slot is empty.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `entries` | list | | The `manage_menu` context entry. Each entry has `label`, `icon` and `url`, and `destructive` on the entry that deletes the record, which is drawn last after a divider in the error colour. |

| Slot | Holds |
|---|---|
| default | Further `<c-menu.item>` entries, drawn after the shared ones. |

```django
<c-actions.manage :entries="manage_menu">
  <c-menu.item text="Import data" icon="upload" href="{{ import_url }}" />
</c-actions.manage>
```

### `c-actions.pending`

A disabled button for something a portal does not offer yet. It never submits or links. Its `title` and a screen-reader-only line carry the reason.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `label` | string | | The button's text. |
| `icon` | string | | An icon name, drawn before the text. |
| `reason` | string | | What the button will do once it exists. |
| `variant` | string | outlined | `primary` for a filled button. |
| `size` | string | `sm` | `xs` or `sm`. |

```django
<c-actions.pending label="Publish" icon="upload" reason="Publishing is not available yet." />
```

## Cards for record pages

Every card is a `<c-card.NAME>` tag. Each carries a `data-card` attribute that tests and scripts can find it by. The attributes below are the data the overview plugins build, listed in [Overview plugins](overview-plugins.md).

### `c-card.citation`

How to cite the record, with a button that copies the text and a disabled export button. The card's element id is `cite`, which the Cite button in every page header jumps to. `data-card` is `citation`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | The card's title. |
| `text` | string | | The citation as plain text. |
| `class` | string | | Extra classes on the card. |

| Slot | Holds |
|---|---|
| default | A note under the citation. |

### `c-card.descriptions`

The record's descriptions. With more than one, each has a tab. With one, its label is the card's title. With none, the card is titled "About" and shows the slot. Values are rendered as markdown.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `descriptions` | list | | Dictionaries with `label` and `value`, in the order the tabs appear. |
| `group` | string | | A name for the tab set, unique on the page. |
| `class` | string | | Extra classes on the card. |

| Slot | Holds |
|---|---|
| default | What to show when there are no descriptions. |

### `c-card.details`

The record's metadata in one card, as a list of entries followed by a "For machines" entry that holds the REST API link and a disabled "Metadata downloads" button. `data-card` is `details`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `rows` | list | | Dictionaries with `label` and `icon`, and one of `record` (a record, shown by name and linked to its page), `badge` with `badge_variant`, `date` with an optional `until` for a range, or `text` with an optional `url`. A row may also carry `note` (a line under the value) and `warning` (draws the value as a warning). |
| `api_url` | string | | The record's REST API address. With none, no API link is drawn. |
| `class` | string | | Extra classes on the card. |

| Slot | Holds |
|---|---|
| default | Entries after the rows. |

```django
<c-card.details :rows="details" api_url="{{ api_url }}">
  <c-card.details.entry label="Instrument" icon="info">Bruker S8 Tiger</c-card.details.entry>
</c-card.details>
```

### `c-card.details.entry`

One entry in a Details card: an icon and a title in capitals, then the value.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `label` | string | | The entry's title. |
| `icon` | string | | An icon name. |
| `class` | string | | Extra classes on the entry. |

| Slot | Holds |
|---|---|
| default | The value. |

### `c-card.funding`

The awards that paid for the record, each with its funder, title and number. A funder identifier or award address is linked only when it starts with `http://` or `https://`. With no funding the card says so. `data-card` is `funding`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `funding` | list | | DataCite funding references with `funderName`, `funderIdentifier`, `awardTitle`, `awardNumber` and `awardURI`. |
| `can_manage` | boolean | `False` | Whether the viewer is on the record's team. With no funding, the team is told why funding matters. |
| `class` | string | | Extra classes on the card. |

### `c-card.identifiers`

Every identifier the record carries as a small table, then the team's own ID and the portal ID with a button that copies it. `data-card` is `identifiers`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `identifiers` | list | | Dictionaries with `type`, `value` and `link`. A `link` makes the value a link. |
| `portal_id` | string | | The record's portal ID. |
| `local_id` | string | | The team's own ID for the record. |
| `class` | string | | Extra classes on the card. |

### `c-card.location`

Where a sample was taken: a map with the point marked, and the coordinates written out as decimal degrees in WGS 84 to five places. The map is drawn by the script in `overview/includes/map_library.html`, which the page includes in its `extra_js` block when it has a location. `data-card` is `location`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `location` | point | | A point with `x` (longitude) and `y` (latitude). |
| `elevation` | number | | Metres above sea level. Left out of the card when not given. |
| `uncertainty` | number | | Metres. Left out of the card when not given. |
| `title` | string | `Location` | The card's title. |
| `label` | string | | The map's accessible name. Defaults to a sentence about where the sample was taken, with the coordinates. |
| `empty` | string | | What to say when there is no location. Without it and without a location, nothing is drawn. |
| `class` | string | | Extra classes on the card. |

### `c-card.people`

Everyone credited on the record, as a grid of faces. Hovering a face shows the name, and each face links to the contributor's page. With nobody to show, the card says so. `data-card` is `people`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `people` | dict | | `shown` (the contributors to draw), `more` (how many were left out) and `total`. |
| `all_url` | string | | Where the full list is. It becomes a "See all" button and the link on the count of the rest. |
| `title` | string | `People` | The card's title. |
| `empty` | string | `No one is credited yet.` | What to say when nobody is shown. |
| `class` | string | | Extra classes on the card. |

### `c-card.placeholder`

A card for something a portal does not show yet. It carries a badge that marks it as not available, one line saying what the card will show and no link or button. `data-card` is not set.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | The card's title. |
| `icon` | string | | An icon for the empty area. |
| `message` | string | | What the card will show. |
| `wide` | boolean | `False` | Keeps the empty area at 16:9, for cards that will hold a map or a chart. |
| `class` | string | | Extra classes on the card. |

### `c-card.readiness`

For the record's team only: what is still missing before the record can be found, trusted or published. Missing items come first, each with a Fix link where one exists. `data-card` is `readiness`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | The card's title. |
| `summary` | string | | One line on the overall state. |
| `about` | string | | One line on why the list matters. |
| `badge` | string | `Edit access only` | Who can see the card. |
| `readiness` | dict | | `items` (dictionaries with `label`, `done`, `url` and `required`, where `required` set to `False` marks a recommended item), `done`, `total` and `ready`. |
| `class` | string | | Extra classes on the card. |

### `c-card.timeline`

What happened to a record, in order. Each step shows its label, its date, the people who did it and a note. A date recorded only to the month is shown as the month, and one recorded only to the year as the year. `data-card` is `timeline`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | The card's title. |
| `steps` | list | | Dictionaries with `label`, `date`, `day`, `people` and `note`. `day` is set when the date is a full day. `note` is rendered as markdown. |
| `empty` | string | | What to say when there are no steps. |
| `class` | string | | Extra classes on the card. |

## Cards for contributor pages

### `c-card.affiliations`

Where a person works and has worked. The current affiliations come first, the primary one marked, then the earlier ones. `data-card` is `affiliations`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `affiliations` | dict | | `current` and `past`, each a list of affiliations. `Person.get_affiliation_history()` returns it. |
| `class` | string | | Extra classes on the card. |

`<c-card.affiliations.row>` draws one affiliation and takes `affiliation`.

### `c-card.hierarchy`

Where an organization sits among the organizations around it: its parent, its siblings and its own sub-organizations. The organization the page is about is highlighted and not a link. With neither a parent nor sub-organizations, the card says none is recorded. `data-card` is `hierarchy`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `organization` | organization | | The organization the page is about. |
| `hierarchy` | dict | | `parent` (or `None`), `siblings` (the parent's sub-organizations, this one included) and `children`. `Organization.get_hierarchy()` returns it. |
| `class` | string | | Extra classes on the card. |

`<c-card.hierarchy.node>` draws one organization and takes `node` and `current` (boolean, `False`).

### `c-card.links`

A contributor's links elsewhere on the web, each named by its site. `data-card` is `links`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `links` | list | | Dictionaries with `url` and `host`, the shape `Contributor.get_links_display()` returns. |
| `class` | string | | Extra classes on the card. |

### `c-card.records`

The projects or the datasets a contributor is behind, each linked to its page. A project shows its status. `data-card` is `projects` or `datasets`, following `kind`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | The card's title. |
| `records` | dict | | `shown` (dictionaries with `record` and `owned`), `more` and `total`. `fill_slots()` in `fairdm.contrib.contributors.profiles` builds it. |
| `kind` | string | | `project` or `dataset`. It picks the icon and shows the status for a project. |
| `variant` | string | | The theme colour of the record type. |
| `all_url` | string | | Where the full list is, used for the "View all" button and the count of the rest. |
| `empty` | string | | What to say when there are none. |
| `class` | string | | Extra classes on the card. |

An entry with `owned` set shows an Owner badge. `active_then_recent()` in the same module orders records before they are cut to fit.

```django
<c-card.records title="Projects" :records="projects" kind="project" variant="info"
                all_url="{{ urls.projects }}" empty="Not credited on any public project yet." />
```

### `c-card.roles`

The contribution roles a contributor holds, most held first, each with the number of records it is held on and a bar showing its share of the most held role. `data-card` is `roles`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `roles` | list | | Dictionaries with `label`, `count` and `percent`, the shape `ranked_shares()` in `fairdm.contrib.contributors.profiles` returns. |
| `class` | string | | Extra classes on the card. |

## Contributors

These components draw the people and organizations credited on a record. Each accepts a `Person`, an `Organization` or a `Contribution`. Given a contribution, it draws the contributor behind it, the roles held on the credit and the organization named on the credit. The components that take several contributors accept a list or queryset of any of these.

Each image comes from the avatar resolver set in `MVP_CONFIG["brand"]["avatar_resolver"]`, described in [Settings](settings.md).

### `c-contributor.affiliation`

The organization a person is shown with: the organization icon, then its name linked to its page. Nothing is drawn without an organization, and nothing is written outside the root element.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `organization` | organization | | The organization to show. |
| `class` | string | | Extra classes on the root element. |

### `c-contributor.avatar`

The contributor's photo or logo. A person is round and an organization is a rounded box. Without an image it shows initials. The avatar is decorative unless `link` or `label` is given.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributor` | contributor | | A person, an organization or a contribution. |
| `size` | string | `md` | `xs`, `sm`, `md`, `lg`, `xl` or `xxl`. |
| `link` | boolean | | Wraps the avatar in a link to the contributor's page, named for them. |
| `label` | boolean | | Names the avatar for assistive technology without linking it. |
| `class` | string | | Extra classes on the avatar. |

```django
<c-contributor.avatar :contributor="person" size="lg" link />
```

### `c-contributor.byline`

Contributors in a row, each with an avatar and a name. Past `max`, the rest are counted.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributors` | list | | Contributions or contributors. |
| `max` | number | `6` | People shown before the count. `0` shows everyone. |
| `total` | number | | The real total, when `contributors` was already cut short. |
| `size` | string | `xs` | `xs` or `sm`. |
| `identifier` | boolean | `False` | Follows each name with its ORCID iD or ROR icon. |
| `more_url` | string | | Where the full list is. |
| `label` | string | `Contributors` | The list's accessible name. |
| `class` | string | | Extra classes on the list. |

### `c-contributor.card`

The card for the people and organization listings. It draws `c-contributor.card.person` for a person and `c-contributor.card.organization` for an organization, and both can be used directly.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributor` | contributor | | A person, an organization or a contribution. |
| `class` | string | | Extra classes on the card. |

The person card shows the photo, the name with the ORCID iD, the affiliation and place, the roles on a credit when given one, and a badge for each portal role the person holds. The organization card shows the logo, the name with the ROR ID, the type and place, the roles on a credit when given one, and the number of members and credits. Fetch people for a listing with `Person.objects.real().for_cards()` so the card's relations are loaded in bulk.

### `c-contributor.item`

An avatar, the name and one short line beneath. For a person the line is their affiliation. For an organization it is its type and place. Given a contribution, the affiliation on that credit replaces the person's primary one and the roles on the credit follow as badges. Inside a `c-list`, use `c-contributor.row`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributor` | contributor | | A person, an organization or a contribution. |
| `size` | string | `sm` | `sm` or `md`, for the avatar. |
| `secondary` | string | | Text for the second line. `none` leaves the line out. |
| `link` | boolean | `True` | `False` for a plain-text name. |
| `class` | string | | Extra classes on the root element. |

### `c-contributor.name`

The contributor's name linked to their page, followed by their ORCID iD icon (a person) or ROR icon (an organization) when they have one. The ORCID icon differs when the iD is not authenticated. Nothing is written outside the root element, so the name can sit mid-sentence.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributor` | contributor | | A person, an organization or a contribution. |
| `format` | string | the preferred name | `family_given` ("Lovelace, Ada"), `family_initial` ("Lovelace, A.") or `initials_family` ("A. Lovelace"). |
| `link` | boolean | `True` | `False` for plain text. |
| `identifier` | boolean | `True` | `False` to leave out the ORCID iD or ROR icon. |
| `class` | string | | Extra classes on the root element. |

```django
Data collected by <c-contributor.name :contributor="person" format="family_initial" />.
```

### `c-contributor.names`

Names in a row: "Ana Silva, Ben Wu and Chen Li". Past `max`, the rest are counted. A list one longer than `max` is shown in full.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributors` | list | | Contributions or contributors. |
| `max` | number | `3` | Names shown before the count. `0` shows everyone. |
| `total` | number | | The real total, when `contributors` was already cut short. |
| `format` | string | | A name format, as for `c-contributor.name`. |
| `identifier` | boolean | `False` | Follows each name with its ORCID iD or ROR icon. |
| `link` | boolean | `True` | `False` for plain-text names. |
| `more_url` | string | | Where the full list is. |
| `empty` | string | | Text shown when nobody is credited. Without it nothing is drawn. |
| `class` | string | | Extra classes on the root element. |

To list only the contributors holding a role, filter first with `by_role` from `contributor_tags`:

```django
{% load contributor_tags %}
{% with creators=dataset.contributors.all|by_role:"https://w3id.org/fairdm/vocabularies/contributor-roles/creator" %}
  <c-contributor.names :contributors="creators" />
{% endwith %}
```

### `c-contributor.row`

`c-contributor.item` as a daisyUI list row, for use inside a `c-list`.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributor` | contributor | | A person, an organization or a contribution. |
| `class` | string | | Extra classes on the row. |

| Slot | Holds |
|---|---|
| `actions` | Buttons at the end of the row. |

```django
<c-list>
  {% for credit in record.contributors.all %}
    <c-contributor.row :contributor="credit">
      <c-slot name="actions">
        <button type="button" class="btn btn-ghost btn-sm">Change</button>
      </c-slot>
    </c-contributor.row>
  {% endfor %}
</c-list>
```

### `c-contributor.stack`

A daisyUI avatar group of overlapping faces, then a "+N" placeholder for the rest.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributors` | list | | Contributions or contributors. |
| `max` | number | `5` | Faces shown before the count. |
| `total` | number | | The real total, when `contributors` was already cut short. |
| `size` | string | `sm` | `xs`, `sm`, `md` or `lg`. |
| `more_url` | string | | Where the full list is. |
| `link` | boolean | `True` | Links each face to its contributor. Use `False` inside another link. |

### `c-contributor.summary`

An avatar group followed by the first names: the contributor line of a listing card.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `contributors` | list | | Contributions or contributors. |
| `faces` | number | `4` | Faces in the group. |
| `names` | number | `2` | Names written out. |
| `total` | number | | The real total, when `contributors` was already cut short. |
| `more_url` | string | | Where the full list is. |
| `link` | boolean | `True` | Links the names. Use `False` inside a card that is a link as a whole. |
| `class` | string | | Extra classes on the root element. |

## Listing cards

Each card is one link to its record. Load the record with the queryset methods named below, or every card costs extra queries.

### `c-dataset.card`

A dataset in a listing: banner, type and counts, name, contributors, abstract, keywords, identifier, licence and the date it was last updated. Counts are shown only for a published dataset.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `object` | dataset | | A dataset loaded with `Dataset.objects.get_visible().with_list_data()`. |

### `c-project.card`

A project in a listing: banner, type, status, number of datasets, name, contributors, abstract, keywords and identifier.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `object` | project | | A project loaded with `Project.objects.get_visible().with_list_data().with_contributors()`. |

### `c-sample.card`

A sample of any type in a listing: image or icon, its type, name, the dataset it belongs to, portal identifier and local ID.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `object` | sample | | A sample loaded with `select_related("dataset")`. |

## Landing page sections

Each section of the home page for a visitor is a component that takes its data as attributes. A section with nothing to show draws nothing. [Home page](home-page.md) says which view context entry feeds each one.

### `c-landing.about`

The portal in its own words, beside four lines on what a visitor can count on from any FairDM portal.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `name` | string | | The portal's name. |
| `description` | string | | The portal's description. Left out, the heading stands alone. |
| `keywords` | list | | Concepts, each shown as a badge from its `label`. |
| `authority` | string | | Who runs the portal. |
| `authority_url` | string | | The authority's website. |

### `c-landing.api`

One example request to the API and a link to its documentation.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `api_url` | string | | The dataset endpoint's address, shown in the example request. |

### `c-landing.community`

The most-credited people and organizations. It draws nothing when there are neither.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `people` | list | | People, most credited first. |
| `people_count` | number | | How many people the portal lists in all, for the count after the faces. |
| `organizations` | list | | Organizations, most credited first. |

### `c-landing.datasets`

The public datasets changed most recently, as `c-dataset.card` cards.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `datasets` | list | | Datasets loaded with `with_list_data()`. |

### `c-landing.footer`

The footer: logo, tagline, links to the places a visitor can go and a copyright line.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `name` | string | | The portal's name, used in the copyright line when there is no authority. |
| `authority` | string | | Who runs the portal, named in the copyright line. |
| `allow_registration` | boolean | | Lists account creation among the links. |

### `c-landing.hero`

The opener, as tall as the window. With a picture it is dimmed and the text turns light. Without one it draws a background in the theme's colours.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `eyebrow` | string | | The short line above the title. |
| `title` | string | | The page's heading. |
| `lead` | string | | The sentence under the title. |
| `image` | string | | The address of a background picture. |
| `logo` | boolean | | Shows the portal's logo above the title. Drawn only without a picture. |
| `allow_registration` | boolean | | Offers account creation under the buttons. |

| Slot | Holds |
|---|---|
| `actions` | Replaces the two buttons, "Browse datasets" and "Explore projects". |

### `c-landing.join`

The closing invitation to contribute. With registration closed it asks members to sign in.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `name` | string | | The portal's name. |
| `allow_registration` | boolean | | Offers account creation. |

### `c-landing.projects`

The public projects added most recently, as `c-project.card` cards.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `projects` | list | | Projects loaded with `with_list_data()` and `with_contributors()`. |

### `c-landing.stats`

The portal in figures, one count for each kind of public record.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `counts` | list | | Dictionaries with `title`, `value` (a whole number) and `icon`. |

### `c-landing.type-list`

One list of record types, a row for each linking to its table. `c-landing.types` uses it for samples and for measurements.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | What the list holds. |
| `icon` | string | | The icon drawn on each row. |
| `types` | list | | Dictionaries with `name`, `description`, `count` and `url`. |
| `more` | number | | How many types were left off, named in a last row. |

### `c-landing.types`

Every sample type and measurement type registered with the portal, with how many public records each has.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `sample_types` | dict | | `shown` (the types to list, in the shape `c-landing.type-list` takes) and `more`. |
| `measurement_types` | dict | | The same shape for measurement types. |

## Entrance pages

### `c-entrance.aside`

What the entrance pages say beside the form: the portal's name, what it holds and who runs it. Decoration only.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `name` | string | | The portal's name, drawn as a paragraph and not as a heading. |
| `description` | string | | What the portal says about itself. Left out when empty. |
| `authority` | string | | Who runs the portal. Left out when empty. |
| `authority_url` | string | | Where the authority can be read about. |

## General components

### `c-date`

A date shown at the precision the record holds.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `date` | date | | The date to show. |
| `precision` | number | `0` | `0` for the year, `1` for the month and year, `2` for the full date. |

### `c-list`

A daisyUI list of like rows. Put `c-list.row` children inside.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | A small heading row above the items. |
| `label` | string | | The list's accessible name, for a list with no visible title. |
| `class` | string | | Extra classes on the list. |

`<c-list.row>` is one row. Its children sit side by side, and the child with `list-col-grow` takes the remaining width. It takes `class`.

### `c-missing`

What a card says when it has nothing to show, drawn as an informational alert so it cannot be taken for a short line somebody wrote.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `class` | string | | Extra classes on the alert. |

| Slot | Holds |
|---|---|
| default | The text, and anything after it such as a button that fixes the gap. |

### `c-progress`

A daisyUI progress bar.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `value` | number | | The current amount. |
| `max` | number | `100` | The total. |
| `label` | string | | The bar's accessible name. Required: say what is measured and how far along it is. |
| `variant` | string | | `primary`, `secondary`, `accent`, `info`, `success`, `warning` or `error`. |
| `class` | string | | Extra classes on the bar. |

```django
<c-progress value="40" max="100" label="Year 2 of 5" />
```

### `c-stats`

A daisyUI strip of figures read as one group. Put `c-stats.item` children inside.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `cols` | string | | Grid columns below the `lg` breakpoint, `1` to `4`. Unset keeps daisyUI's single scrolling row. |
| `lg` | string | | Grid columns from `lg` up, `2` to `6`. |
| `class` | string | | Extra classes on the strip. |

`<c-stats.item>` is one figure.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `title` | string | | What is counted. |
| `value` | string | | The figure. |
| `desc` | string | | A line under the figure. |
| `href` | string | | Makes the title a link to where the figure comes from. |
| `variant` | string | | The colour of the figure and its icon, such as `success` or `secondary`. Without one both stay neutral. |
| `icon` | string | | An icon drawn in a tinted tile at the end of the stat. |
| `class` | string | | Extra classes on the item. |

| Slot | Holds |
|---|---|
| `figure` | A trailing element that replaces the icon tile. |

```django
<c-stats cols="2" lg="4">
  <c-stats.item title="Datasets" value="4" icon="dataset" variant="success" />
  <c-stats.item title="Samples" value="1,280" icon="sample" variant="secondary" />
</c-stats>
```

### `c-tabs`

Tabs built from radio inputs, so they switch with no JavaScript and every panel stays in the page. Put `c-tabs.tab` children inside.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `variant` | string | `border` | `border`, `lift` or `box`. |
| `size` | string | | `sm` for a compact set. |
| `label` | string | | The set's accessible name. |
| `class` | string | | Extra classes on the tab list. |

`<c-tabs.tab>` is one tab and its panel.

| Attribute | Type | Default | Accepts |
|---|---|---|---|
| `group` | string | | A name shared by every tab in the set. Required. |
| `label` | string | | The tab's text. |
| `checked` | boolean | | Marks the tab shown first. |
| `flush` | boolean | `False` | Removes the leading padding. |
| `class` | string | | Extra classes on the panel. |

```django
<c-tabs group="about" label="About">
  <c-tabs.tab group="about" label="Abstract" checked>An abstract.</c-tabs.tab>
  <c-tabs.tab group="about" label="Methods">The methods.</c-tabs.tab>
</c-tabs>
```
