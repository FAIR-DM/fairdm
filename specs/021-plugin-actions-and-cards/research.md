# Research: Plugins contribute page actions and overview cards, and can be removed or replaced

Read against `main` on 2026-10-06, after specification 022 merged. There are no planning notes for
this feature and it had no prototype, so everything here comes from the specification and the code.

## What exists

### The registry

`fairdm/contrib/plugins/registration.py` keeps, per record type, a list of
`(plugin class, registration options)` in the order registrations arrive. The options are `label`,
`icon`, `order` and `menu`. `menu=False` declines the navigation entry and the page is still
served. Validation runs inside the decorator (`checks.py`) and raises `PluginRegistrationError`,
which stops Django from starting, because system checks do not run on a production boot.

`get_urls_for_model(model)` is called from each record type's URL configuration. It walks the list,
asks each plugin class for its URL patterns, and builds the record type's navigation menu with
`flex_menu`. Entries are sorted by `order`. Two entries with the same `order` keep the order they
were registered in, which follows the order applications load.

### Names and addresses

A plugin's name and path segment are read from the class (`get_name`, `get_url_path`).
`Plugin.get_urls` builds one pattern named after the plugin and one per further view, named
`<plugin>-<view>`. Nothing lets a registration serve a class under a different name or segment,
which is what a replacement needs.

### The access decision

`access.can_open(view_class, request, obj)` is the one decision. The navigation calls it through
`menu_check`, which hides the entry and logs when the predicate raises. A page calls it from
`has_permission`. For a further view the predicate is read from the owning plugin, and the
permission from the further view itself. A card's further views need the card's whole decision in
front of them (FR-018), including its permission, and that is not what happens today.

### When plugins are loaded

`FairDMConfig.ready()` runs `autodiscover_modules("plugins")`, which imports the `plugins` module
of every installed application in one pass, whatever position the application has in
`INSTALLED_APPS`. Every documented registration is made in such a module. After that call returns,
every declaration made the documented way is known. This is the earliest point at which a removal
or a replacement can be judged, and it runs on every way of starting the portal, a WSGI server
included.

Tests register plugins after startup and then call `get_urls_for_model`, so the registry cannot be
frozen at startup. The effective set has to be worked out again whenever it is read.

### The overview pages

All six overviews descend from `OverviewPlugin` in `fairdm/core/plugins.py`: project and dataset
through `RecordOverviewPlugin`, sample and measurement through `TypedOverviewPlugin`, and
contributors (people and organizations) directly. Each is registered with `url_path = None`, which
serves it at the record's own address. All six templates extend `fairdm/templates/overview/page.html`.

That template has a header block, `overview.actions`, which each record's template overrides, and
two columns. The person template overrides `overview.actions` without calling the parent block. A
dropdown placed inside the block would therefore be lost on some pages. It has to sit beside the
block, in the same row of buttons.

The Manage menu is written by each record's own template with `c-dropdown`, `c-menu` and
`c-menu.item`. The page actions dropdown can use the same three components.

A location's overview (`PointOverview`) is a plain plugin that does not extend `OverviewPlugin`
and does not use `overview/page.html`. It is the example of a record type whose page offers
neither place.

`base.html` already writes `plugin_media.css` and `plugin_media.js`, which `Plugin.get_context_data`
fills from the plugin's `Media` class. A card's assets can be added to the same object.

### Links from shipped pages to plugins

Found by searching for `plugin_reverse`, `plugins.reverse`, `{% plugin_url %}`, `safe_reverse` and
plain `reverse` with a record namespace:

| Where | Links to | Fails today if the target is removed |
|---|---|---|
| `RecordOverviewPlugin.get_context_data` | `contribution-list` (the People card) | yes, `NoReverseMatch` |
| `{% plugin_url %}` in `project/plugins/overview.html` and the contribution card | `datasets` and others | yes |
| project and dataset overview `urls` | `dataset-list`, `overview-update`, `overview-delete` | no, already `safe_reverse` |
| `get_absolute_url` on every record | `overview` | cannot be removed (FR-030) |
| the navigation menu | every navigation entry | built from the effective set, so a removed entry is not there |

The work for FR-032 is the first two rows, plus a test that removes each removable plugin FairDM
ships from each record type and opens that record type's overview.

## Decisions for the plan

### One place to work out what is served

The registry keeps what was declared and never edits it. A single method works out, for one record
type, what is actually served: declarations in, a list of mounts out. Removals and replacements are
steps in that method. Because it reads the whole set every time, its result cannot depend on the
order the declarations arrived in (FR-028, FR-039).

### Refusals happen in two places

The method above raises when a removal or a replacement cannot work. It is called for every record
type at the end of `FairDMConfig.ready()`, straight after the `plugins` modules are imported, so the
portal does not start (FR-043, SC-008). It is called again when a record type's URLs are built,
which covers a declaration made later than the documented place.

A Django system check was considered and not used, for the reason `checks.py` already gives: checks
do not run when a WSGI server starts.

An application appended to the end of `INSTALLED_APPS` to run the validation last was considered
and not used. A portal can add applications after `fairdm.setup()` returns, so "last" is not
something FairDM controls, and the `plugins` modules are all imported by then anyway.

### What a registration names

- `place`: `"navigation"` (the default), `"action"` or `"card"`.
- `column`: `"side"` (the default) or `"wide"`, for a card only.
- `replaces`: the plugin this one stands in for, given as the plugin class or its name.

The existing keyword for position is `order` and it is kept. The specification's "position" is that
keyword.

A removal is its own declaration, `plugins.remove(Model, plugin)`, taking the class or the name.

### How a plugin is identified

By the name it has in its own right, which is what `get_name()` returns and what already has to be
unique per record type. A removal and a `replaces` both refer to that name. A replacement has its
own name for this purpose, so a second replacement can name the first (the "replacement is itself
replaced" case) and a removal can name one of two competing replacements (FR-040). The name and
address a replacement is served under are those of the plugin at the bottom of the chain.

### Which record types offer the two places

A record type offers page actions and cards when the plugin served at its own address draws them.
That is true when the class is built on a small mixin, `OverviewPlaces`, which supplies the actions
and the drawn cards to the template. `OverviewPlugin` carries it, so the six pages have it and a
location does not. A replacement overview built on the shipped one keeps it (US4 scenario 13).

A separate declaration per record type, in the manner of `declare_addressing`, was considered. It
would be a second thing to keep in step with the class that actually draws the places.

### What a card is

A card has no address, so it is not dispatched as a view. It needs a way to be drawn with a record
and a request. A small base class, `Card`, gives a card a template, a context and optional `Media`,
and one method that returns its HTML. A registration with `place="card"` is refused unless the
class can be drawn that way. Its further views are ordinary plugin views mounted beneath the card's
name.

### Order

Actions and cards are sorted by `order` and then by name. Names are unique per record type, so the
result is the same on every start (FR-011, FR-020). The navigation keeps its present behaviour for
equal positions, because SC-009 requires existing plugins to be listed exactly as they were.

### Packages considered

None is added. `flex_menu` builds the navigation and is not needed for a flat list of actions. The
dropdown, the menu items and the cards are `django-mvp` components the pages already use.
