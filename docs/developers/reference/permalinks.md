# Permalinks

A record's permalink is its portal ID at the portal's root: `/` followed by the portal ID. It opens the record whatever the address of the record's pages is today. This page describes the URL name, the helper that builds the link, the pattern that matches it and the rule for a page that shares its shape. To see how a visitor uses the link, read [The project page](../../users/projects/project.md).

## The route

| Name | Pattern | View |
|---|---|---|
| `permalink` | `^(?P<portal_id>PORTAL_ID_PATTERN)/$` | `fairdm.views.permalink.PermalinkView` |

The route is appended at the end of `fairdm/conf/urls.py`, after every page the portal and its addons declare. It is a regular-expression route, not a path converter, because a converter can be registered once and the configuration is reloaded in tests.

## `PORTAL_ID_PATTERN`

A letter followed by 22 characters of the alphabet the `uuid` fields generate from. The letters and the length are read from the `uuid` fields of `Project`, `Dataset`, `Sample`, `Measurement` and `Contributor`, so the pattern follows the fields.

## `OVERVIEW_URL_NAMES`

Maps the letter of a portal ID to the overview URL name of that kind of record.

| Letter | URL name |
|---|---|
| `p` | `project:overview` |
| `d` | `dataset:overview` |
| `s` | `sample:overview` |
| `m` | `measurement:overview` |
| `c` | `contributor:overview` |

## `PermalinkView`

A `RedirectView` that answers with a temporary redirect (302) and carries the query string to the target. It looks nothing up. The overview page finds the record and answers not-found for a record the visitor may not open and for one that does not exist alike, so the link reveals nothing a page does not.

## `get_permalink(record, request=None)`

Returns the record's permalink as a path. With a request, it returns the absolute link for that request's host.

```python
from fairdm.views.permalink import get_permalink

get_permalink(dataset)  # "/d3xK...Wq/"
get_permalink(dataset, request)  # "https://portal.example.org/d3xK...Wq/"
```

## The `permalink` template tag

`{% permalink record as permalink %}`, loaded with `{% load fairdm %}`, returns `get_permalink(record, request)` for the request in the template context. The overview pages call it once for the identifiers card and once for the Share menu.

```django
{% load fairdm %}
{% permalink record as permalink %}
<c-card.identifiers :identifiers="identifiers" portal_id="{{ record.uuid }}" permalink="{{ permalink }}" />
<c-mvp.addons.share-dropdown url="{{ permalink }}" />
```

## The identifiers card's `permalink` attribute

`<c-card.identifiers>` takes the absolute link as its `permalink` attribute. When it is set, a **Permalink** row beneath the Portal ID row shows the link, with a button that copies it. The card builds no address itself, and without the attribute it shows no Permalink row. The Share menu needs django-mvp 0.33.2 or later, whose **Copy link** copies the `url` it is given.

## A page shaped like a portal ID

A page that a portal or an addon declares at the root always wins over the permalink, because the permalink route comes last. A declared root page whose path has the shape of a portal ID hides the link of any record with that ID. None of the words the framework or its addons use for pages has that shape.
