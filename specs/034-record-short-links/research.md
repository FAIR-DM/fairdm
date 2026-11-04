# Research: open any record from its portal ID

Done against main at `89385154`, after the sketch was approved.

## Planning notes

### N1. Look samples and measurements up on the base table

**Adopted, in the record's page rather than the link.** The link itself looks nothing up: a lookup
there would answer a private record differently from an ID that belongs to no record, and reveal that
the private record exists (design review). The link goes to the overview address for the ID's
letter, and the overview page does the lookup on the base table. `Sample.objects` and `Measurement.objects` are `PolymorphicManager`s, and
`Contributor.objects` is one too, so `Sample.objects.get(uuid=...)` returns a `SoilSample` or a
`WaterSample` and `get_absolute_url()` gives that subtype's page. The sketch confirmed it on the
development data: a water sample and an ICP-MS measurement each reached their own type's page, and
a person and an organization reached theirs. One query per link, on the base table's unique `uuid`
index.

## What the screens need, and what the sketch faked

| From `sketch.md` | Met by |
|---|---|
| The identifiers card shows the permalink beneath the portal ID, and copies the whole link | A `permalink` attribute on `<c-card.identifiers>`, the absolute link, given by the page. The card stays a pure renderer: it reverses nothing, so its existing tests, which pass made-up IDs, keep working |
| The copy button copies the absolute link | The anchor's `href` is the absolute link itself, so the button copies the string it was given, as the Portal ID button already does |
| Every citation with no DOI or IGSN uses the absolute permalink | `get_permalink(record, request)` in the dataset, sample and measurement plugins |
| The Share menu shares the absolute permalink | The same template tag gives `url` to `<c-mvp.addons.share-dropdown>` on the three overview templates |
| The DataCite export gives the permalink | `get_permalink(dataset, request)` in `datacite_xml` |
| The redirect, converter and citation changes have no tests | Rebuilt test-first in the stories below |
| The absolute link is put together from `request.scheme` and `request.get_host` in three templates | One `permalink` simple tag that calls `request.build_absolute_uri`, which also honours `SECURE_PROXY_SSL_HEADER` and `USE_X_FORWARDED_HOST`, which the hand-built string did not |
| No documentation | User docs on each record page and identifiers, developer reference for the URL, and the glossary |

## Findings that shape the plan

- **The letters and the alphabet come from the fields, never a second copy.** Each model's `uuid`
  field carries its `prefix` and `length`, and `alphabet=None` means shortuuid's default alphabet,
  `shortuuid.get_alphabet()`. The converter's regular expression is built from those at import,
  so a portal ID's shape is defined in exactly one place.
- **Ordering decides precedence.** Django resolves patterns in order, so the permalink pattern
  appended after every other root pattern, addon routes included, can never shadow a declared page.
  `tests/test_conf/routed_addon` is an addon with a root route that the test can reuse.
- **No closing slash.** `APPEND_SLASH` with `CommonMiddleware` already turns `/<id>` into a
  permanent redirect to `/<id>/`. That 301 points at the permalink itself, which never moves, so it
  does not conflict with FR-006.
- **Private records.** The overview pages answer not-found both for a record the viewer may not open
  and for one that does not exist (`fairdm/contrib/plugins/mixins.py`). The link does no lookup, so
  it inherits that and reveals nothing (FR-005).
- **`register_converter` raises on a second registration** in Django 6.0, and three test modules
  reload `fairdm.conf.urls`. The pattern is a `re_path` with a named group.
- **The Share menu's Copy link** in django-mvp 0.33.0 copies `window.location.href` and ignores
  `url`. It is fixed in django-mvp and the dependency is raised.
- **The schema.org description on a dataset page keeps its page address as `url`.** It describes the
  page, and the spec does not cover it.

## What already exists

- The redirect: Django's `RedirectView`, with `permanent = False` and `query_string = True`.
- The pattern: Django's `re_path`.
- The absolute address: `HttpRequest.build_absolute_uri`.
- The Share menu's address: django-mvp's `share-dropdown` already takes `url`.
- The copy button: the identifiers card's existing inline `navigator.clipboard.writeText` pattern.
- New code: the view and its URL-name map, the pattern constant, `get_permalink`, and the `permalink`
  template tag. Each one is small, and nothing in the repository or its packages does the same job.
