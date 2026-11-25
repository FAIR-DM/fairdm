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
   kind. Owns no models. Built on what django-mvp's `mvp.search` already provides: its
   results page, dialog, button and field are used as they ship, and the results need not
   match this prototype exactly.
2. **django-mvp's dock, header and search page** (changes to ways that exist in django-mvp, so
   resolve work there, one session and one pull request):
   - `c-dock.item` can be marked current for a whole section of the site (URL namespaces and
     view names), and can take a second icon to draw while it is current.
   - django-mvp's stylesheet draws the current dock item in the primary colour with a heavier
     label and a bar above the icon, sizes the dock's icons up from the body text, and leaves
     room at the bottom of the page for the dock below the sidebar's breakpoint.
   - The menu-driven dock (`MobileFooterMenu`, `MobileFooterNavRenderer` and the menu path of
     `app/dock.html`) is deprecated in favour of declaring the dock in a template.
   - The header can show the site's name beside its icon below the sidebar's breakpoint.
   - The search results page places its icon over the field whatever element the icon is.
3. **The FairDM dock** (changes a way that exists, the dock, so resolve work). Declare the dock in
   the template with the five items above using item 2's options, drop the header's toggle on a
   phone, show the site name beside the icon through item 2's header option, remove "Create new"
   everywhere it lives, and drop FairDM's `dock` renderer entry. Depends on a django-mvp release
   carrying item 2, and needs nothing from feature 1.

## The shared pieces

- **Which section a page belongs to.** `fairdm/templatetags/fairdm_dock.py` maps URL namespaces
  and view names to dock items. In `main` this becomes django-mvp's: `c-dock.item` is current
  on a whole section (item 2). FairDM keeps only what is its own, the signed-in person's
  profile and the Menu item holding every other page.
- **Filled icons for the current item.** `home-current`, `project-current`, `dataset-current`
  and `person-current` aliases in `EASY_ICONS` (`fairdm/conf/settings/addons.py`), passed as
  the item's current icon (item 2).
- **The dock's look.** The current item's colour, weight and overline, the icon size and the
  room at the page bottom move from `fairdm.css` into django-mvp's stylesheet (item 2).
- **Search kinds.** `fairdm/search.py` repeats the same shape seven times (model, fields to
  match, visibility, result line). The rebuild writes one base kind that takes those four.

## Duplication to remove

- The seven kinds in `fairdm/search.py`, as above.
- `fairdm/templates/cotton/app/navbar.html` is a whole copy of django-mvp's navbar for one
  added line. Item 2 adds the option to django-mvp, and the copy never reaches `main`.
- The `.mvp-search-form > i` rule in `fairdm/static/css/fairdm.css` repeats django-mvp's rule,
  which only matches an `<svg>` icon. Item 2 fixes it in django-mvp, and the rule never reaches
  `main`.

## The look

| File | What it holds | Ported by | Lands in `main` at |
|---|---|---|---|
| `fairdm/templates/cotton/app/dock.html` | The dock, declared with `c-dock` and `c-dock.item` | Item 3 | same path |
| `fairdm/templatetags/fairdm_dock.py` | The current-section tag | Items 2 and 3 | django-mvp's `c-dock.item`, with FairDM's profile and Menu rules in FairDM |
| `fairdm/static/css/fairdm.css`, the "Mobile dock" and "room for the dock" blocks at the end | Current item colour and weight, the overline, icon size, page bottom padding | Item 2 | django-mvp's stylesheet |
| `fairdm/static/css/fairdm.css`, the `.mvp-search-form > i` block | Search page icon | Item 2 | django-mvp |
| `fairdm/templates/base.html`, `app.navbar.end` | Header search button and field, the search dialog | Feature 1 | same path |
| `fairdm/templates/base.html`, `app.navbar.end` | No "Create new" | Item 3 | same path |
| `fairdm/conf/settings/addons.py` | `navbar.mobile.sidebar_toggle: False`, the `*-current` icon aliases | Item 3 | same file |
| `fairdm/templates/cotton/app/navbar.html` | django-mvp's navbar copied to add the site name beside the icon | Item 2 | a django-mvp header option, set by FairDM in item 3 |

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
- The changes the dock, header and search page need are made in django-mvp, not carried in
  FairDM: the dock component and its styles, a header option for the site name, and the search
  page's icon.
- django-mvp's menu-driven dock is deprecated.
- "Create new" goes, and nothing replaces it here. It will come back somewhere else, later.
- Search is built on what django-mvp's search already provides, and need not match this
  prototype exactly.

## Faked or skipped

- Search matches with a plain `icontains` on names and identifiers. Feature 1 decides whether to
  index with modelsearch.
- Projects in search are only the public ones, as on the project list. Feature 1 decides whether
  members find their private projects.
- The visitor's landing page has no app header, so a wide screen shows no search field there.
- At 320 px wide, the project, dataset and people lists scroll sideways by 16 px. That comes from
  the list pages' filter panel, which this branch doesn't touch.
- The header's search button is about 32 px square, below the 44 px touch target. It is
  django-mvp's button as it ships.
- The "Claim this profile" notice is squashed on narrow phones. That predates this branch.
- The desktop search field reads "Search example.com" on the dev server because the dev
  database's Site is still `example.com`.

## What it replaces

- django-mvp's menu-driven dock (`MobileFooterMenu`, the `dock` renderer). FairDM's
  `FLEX_MENUS["renderers"]["dock"]` entry becomes unused and can go.
