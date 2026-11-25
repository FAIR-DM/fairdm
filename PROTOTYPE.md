# Prototype: the mobile dock

The prototype branch `prototype-mobile-dock`. It is a reference and is never merged. The record
of decisions is the GitHub issue labelled `prototype` that links to this file.

## What a person can now do

On a phone or a tablet in portrait (below the sidebar's `lg` breakpoint), a dock along the
bottom of every page holds five items, in this order:

| Item | Goes to | Shown as current on |
|---|---|---|
| Home | `home` | the home page |
| Projects | `project-list` | the project list, `project-create`, every view in the `project` namespace |
| Datasets | `dataset-list` | the dataset list, `dataset-create`, every view in the `dataset` namespace |
| Profile (signed in) | `request.user.get_absolute_url` | every view in the `contributor` namespace whose `uuid` is the signed-in person's |
| Log in (signed out) | `account_login`, with `?next=` back to the current page | never: the log-in page has no dock |
| Menu | toggles the sidebar drawer (`mvp-app-toggle`) | every other page, the search results and other people's profiles included |

The header has no "Create new" button at any width. Its right-hand end holds the site search:
django-mvp's search button on a phone or tablet, its search field on a wide screen (Ctrl K
opens it too). Both open the same dialog with the field focused. The header draws no sidebar
toggle on a phone. On a wide screen the dock is hidden.

Below the sidebar's breakpoint, where the header shows the site's icon, the site's name sits
beside it, the same name the sidebar header shows (`MVP_CONFIG["layout"]["sidebar"]["title"]`).
On a wide screen the sidebar header already shows both, and the app header shows neither.

Behind the header's search, django-mvp's site search is mounted at `/search/` with seven kinds:
projects, datasets, samples (name, local ID or UUID), measurements, people, organizations and
literature.

## The features

1. **Find a record from anywhere** (a new way to work with the site, so feature-request work).
   Anyone can search the portal's records from the header, and see the results grouped by
   kind. Owns no models. Depends on django-mvp's `mvp.search`.
2. **The FairDM dock** (changes a way that exists, the dock, so resolve work). Declare the dock in
   the template with the five items above, mark the current section, drop the header's toggle on
   a phone, and leave room at the bottom of the page. Needs nothing from feature 1.

## The shared pieces

- **Which section a page belongs to.** `fairdm/templatetags/fairdm_dock.py` maps URL namespaces
  and view names to dock items. The sidebar's own current-item logic in flex_menu matches view
  names exactly, so a dataset's tabs don't mark "Datasets" in the sidebar either. The rebuild
  could use the same mapping for both, or give django-mvp's `c-dock.item` a way to be current
  on a whole namespace.
- **Filled icons for the current item.** `home-current`, `project-current`, `dataset-current`
  and `person-current` aliases in `EASY_ICONS` (`fairdm/conf/settings/addons.py`).
- **Search kinds.** `fairdm/search.py` repeats the same shape seven times (model, fields to
  match, visibility, result line). The rebuild writes one base kind that takes those four.

## Duplication to remove

- The seven kinds in `fairdm/search.py`, as above.
- `fairdm/templates/cotton/app/navbar.html` is a whole copy of django-mvp's navbar for one
  added line. The fix belongs in django-mvp: a setting or slot for a title beside the icon.
- The `.mvp-search-form > i` rule in `fairdm/static/css/fairdm.css` repeats django-mvp's rule,
  which only matches an `<svg>` icon. The fix belongs in django-mvp: place the icon whatever its
  element.

## The look

| File | What it holds | Ported by | Lands in `main` at |
|---|---|---|---|
| `fairdm/templates/cotton/app/dock.html` | The dock, declared with `c-dock` and `c-dock.item` | Feature 2 | same path |
| `fairdm/templatetags/fairdm_dock.py` | The current-section tag | Feature 2 | same path |
| `fairdm/static/css/fairdm.css`, the "Mobile dock" and "room for the dock" blocks at the end | Current item colour and weight, the overline, icon size, page bottom padding | Feature 2 | same file |
| `fairdm/static/css/fairdm.css`, the `.mvp-search-form > i` block | Search page icon | Feature 1, or a django-mvp fix | django-mvp |
| `fairdm/templates/base.html`, `app.navbar.end` | Header search button and field, the search dialog, no "Create new" | Feature 1 | same path |
| `fairdm/conf/settings/addons.py` | `navbar.mobile.sidebar_toggle: False`, the `*-current` icon aliases | Feature 2 | same file |
| `fairdm/templates/cotton/app/navbar.html` | django-mvp's navbar copied to add the site name beside the icon | Feature 2, or a django-mvp option for a header title | django-mvp |

Screens to compare, each signed out, as `regular.user` and as `regular.user2`:

| Screen | Address | Widths |
|---|---|---|
| Dock on the home page | `/` | 390, 820 |
| Dock on a list | `/projects/`, `/datasets/` | 320, 390, 820 |
| Dock inside a record | `/datasets/dCj6LdQpbohniJC4Tp34V7v/samples/` | 390 |
| Dock on a sidebar-only page | `/samples/skxPx9uaRbJwyeRgFKaiXCJ/` | 390 |
| Search dialog from the header | any page, tap the search icon, type `sample` | 390 |
| Dock on the person's own profile | Profile in the dock, signed in | 390 |
| Log in from the dock | `/datasets/`, signed out, tap Log in | 390 |
| Search results | `/search/?q=alp` | 390, 1280 |
| Header search field | `/datasets/` | 1280 |
| Header search button | `/datasets/`, tap the search icon at the top right | 390, 820 |
| Site name beside the logo | `/datasets/`, a dataset's samples tab | 320, 390, 820 |
| Page bottom clears the dock | `/datasets/` scrolled to the end | 390 |

Seeded with the portal's own `create_dev_accounts` and `generate_fake_data`.

## The data model

No models. The search reads Project, Dataset, Sample, Measurement, Person, Organization and
literature's Item.

## Sam's decisions and design rules

- The sidebar toggle goes in the dock, in the last place, and the header has none on a phone.
- The dock is declared in the template, not built from `MobileFooterMenu`.
- The current item's bar is an overline above the icon, not daisyUI's underline.
- The header has no "Create new" button. Its right-hand end holds the search toggle.
- The dock's fourth place is the signed-in person's profile.
- The header shows the site's name next to its icon.

## Faked or skipped

- Search matches with a plain `icontains` on names and identifiers. Feature 1 decides whether to
  index with modelsearch.
- Projects in search are only the public ones, as on the project list. Feature 1 decides whether
  members find their private projects.
- The visitor's landing page has no app header, so a wide screen shows no search field there.
- The desktop search field reads "Search example.com" on the dev server because the dev
  database's Site is still `example.com`.

## What it replaces

- django-mvp's menu-driven dock (`MobileFooterMenu`, the `dock` renderer). FairDM's
  `FLEX_MENUS["renderers"]["dock"]` entry becomes unused and can go.
