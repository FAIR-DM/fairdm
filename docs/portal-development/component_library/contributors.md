# Contributors

The people and organizations credited on a record are drawn with a set of Cotton components under
the `contributor` namespace. They are built on django-mvp's avatar, card and list components, so
they follow the portal's theme like everything else.

Every component that takes one contributor accepts a `Person`, an `Organization` or a
`Contribution`. Given a contribution, it draws the contributor behind it and adds what belongs to
that credit: the roles held on it, and the organization the contributor was affiliated with for
it. Every component that takes several accepts a list or queryset of either.

Attributes that take a Python value are written with a leading colon:
`<c-contributor.item :contributor="person" />`.

## One contributor

### `c-contributor.name`

The contributor's name linked to their page, followed by their ORCID iD icon (a person) or ROR
icon (an organization) when they have one. The ORCID icon shows whether the iD is authenticated,
which means the person has signed in with ORCID. Nothing is written outside the root element, so
the name can sit mid-sentence and be followed directly by a comma. A long name wraps like text,
and the icon stays on the line of its last word.

| Attribute | What it takes |
| --- | --- |
| `contributor` | A person, an organization or a contribution. |
| `format` | A citation-style name for a person: `family_given` ("Lovelace, Ada"), `family_initial` ("Lovelace, A.") or `initials_family` ("A. Lovelace"). Left empty, the preferred name is shown. |
| `:link` | `False` for plain text. Linked by default. |
| `:identifier` | `False` to leave out the ORCID iD or ROR icon. Shown by default. |

```django
Data collected by <c-contributor.name :contributor="person" format="family_initial" />.
```

### `c-contributor.avatar`

The contributor's photo or logo. A person is round, and an organization is a rounded box. Without
an image it shows the contributor's initials: a person's given and family initials, or an
organization's leading acronym ("GFZ Helmholtz Centre" gives "GFZ").

The avatar is decorative by default, because it normally sits beside the name. When it stands on
its own, pass `link` to make it a link to the contributor named for them, or `label` to name it
for assistive technology without linking it.

| Attribute | What it takes |
| --- | --- |
| `contributor` | A person, an organization or a contribution. |
| `size` | `xs`, `sm`, `md` (default), `lg`, `xl` or `xxl`. |
| `link` | Wrap the avatar in a link to the contributor's page. |
| `label` | Name the avatar for assistive technology. |

```django
<c-contributor.avatar :contributor="person" size="lg" link />
```

The image comes from the contributor's `image` field, through the avatar resolver described
[below](#avatar-images).

### `c-contributor.item`

The avatar, the name and one short line beneath. For a person the line is their affiliation,
linked to the organization's page behind the organization icon. For an organization it is its type
and place. Given a contribution, the affiliation on that credit is shown in place of the person's
primary one, and the roles held on the credit follow as badges.

Use it anywhere a contributor is named on their own, such as a "Contact person" line on a record
page. Inside a `c-list`, use `c-contributor.row`.

| Attribute | What it takes |
| --- | --- |
| `contributor` | A person, an organization or a contribution. |
| `size` | `sm` (default) or `md`, for the avatar. |
| `secondary` | Text for the second line instead. `none` leaves the line out. |
| `:link` | `False` for a plain-text name. |

```django
<c-contributor.item :contributor="contact" size="md" />
```

### `c-contributor.row`

`c-contributor.item` as a DaisyUI list row, for use inside a `c-list`, with an `actions` slot for
buttons at the end of the row.

| Slot | What it holds |
| --- | --- |
| `actions` | Buttons at the end of the row, such as edit and remove. |

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

### `c-contributor.affiliation`

The organization a person is shown with: the organization icon, then the organization's name
linked to its page. `c-contributor.item` and the person card use it. Nothing is written outside the
root element.

```django
<c-contributor.affiliation :organization="person.primary_organization" />
```

### `c-contributor.card`

The card for the people and organization listings. It draws `c-contributor.card.person` for a
person and `c-contributor.card.organization` for an organization, which can also be used directly.

- **The person card** shows the photo, the name with the ORCID iD, the affiliation and place, the
  roles on a credit when given one, and a badge for each [portal role](../portal_roles.md) the
  person holds.
- **The organization card** shows the logo, the name with the ROR ID, the type and place, the roles
  on a credit when given one, and how many members and credits the organization has.

```django
<c-contributor.card :contributor="person" />
```

## Several contributors

`c-contributor.names`, `c-contributor.byline`, `c-contributor.stack` and
`c-contributor.summary` all take `contributors` and share how they cut a long list short. Past
`max`, the rest are counted, and the count links to `more_url` when given. A list one longer than
`max` is shown in full, because counting one person takes as much room as naming them. When the
list was already cut short by the caller, pass the real number as `total` so the count is right.

### `c-contributor.names`

Names in a row: "Ana Silva, Ben Wu and Chen Li".

| Attribute | What it takes |
| --- | --- |
| `contributors` | Contributions or contributors. |
| `max` | Names shown before the count. `3` by default. `0` shows everyone. |
| `total` | The real total, when `contributors` was already cut short. |
| `more_url` | Where the full list lives. |
| `format` | Name format, as for `c-contributor.name`. |
| `:identifier` | `True` to follow each name with its ORCID iD or ROR icon. |
| `:link` | `False` for plain-text names. |
| `empty` | Text shown when nobody is credited. Nothing is drawn without it. |

```django
<c-contributor.names :contributors="dataset.contributors.all" max="3"
                     more_url="{{ dataset.get_absolute_url }}#contributors" />
```

To list only the contributors holding a role, filter the list first with the `by_role` filter
from `contributor_tags`:

```django
{% load contributor_tags %}
{% with creators=dataset.contributors.all|by_role:"Creator" %}
  <c-contributor.names :contributors="creators" />
{% endwith %}
```

### `c-contributor.byline`

Contributors in a row, each with their avatar and name: the header of a record page. It takes the
same `contributors`, `max` (`6` by default), `total`, `more_url` and `:identifier` as
`c-contributor.names`, plus `size` (`xs` by default, or `sm`) for the avatars and `label` for the
list's accessible name.

```django
<c-contributor.byline :contributors="project.contributors.all" />
```

### `c-contributor.stack`

A DaisyUI avatar group of overlapping faces, then a "+N" placeholder for the rest. It takes
`contributors`, `max` (`5` by default), `total`, `more_url` and `size` (`sm` by default). Each face
links to its contributor. Pass `:link="False"` when the stack sits inside another link.

```django
<c-contributor.stack :contributors="sample.contributors.all" max="4" />
```

### `c-contributor.summary`

An avatar group followed by the first names: the contributor line of a listing card, where the
record is the subject rather than its people. It takes `contributors`, `faces` (`4` by default),
`names` (`2` by default), `total` and `more_url`. Pass `:link="False"` inside a card that is a link
as a whole.

```django
<c-contributor.summary :contributors="dataset.contributors.all" more_url="{{ dataset.get_absolute_url }}" />
```

## Avatar images

Every `<c-mvp.avatar :for="...">` in the portal asks the function set as
`MVP_CONFIG["brand"]["avatar_resolver"]` for its image. FairDM sets it to
`fairdm.contrib.contributors.utils.helpers.avatar_url`, which returns the thumbnail of a
contributor's `image`: the 150×150 thumbnail for sizes up to `md`, and the 600×600 one for `lg`
and larger. It returns `None` when there is no image, or when the file is missing, and the avatar
then shows its placeholder. The signed-in user's avatar in the menu is drawn the same way, because
a portal user is a `Person`.

## Listing many contributors

The person card reads each person's identifiers, sign-in accounts, affiliations and portal roles.
In a listing, fetch people with `Person.objects.for_cards()` so those are loaded for the whole page
at once rather than once per card:

```python
from fairdm.contrib.contributors.models import Person

people = Person.objects.real().for_cards()
```

The people listing and the portal team page both do this.
