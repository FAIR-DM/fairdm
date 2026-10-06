# Implementation Plan: Plugins contribute page actions and overview cards, and can be removed or replaced

**Branch**: `021-plugin-actions-and-cards` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The registry keeps every declaration as it was made: registrations, which now may name a place and
a plugin they replace, and removals. One method works out from those what a record type actually
serves. URL patterns, the navigation, the page actions and the cards are all built from its result,
so a removed plugin is absent from all four and a replacement stands where its target stood. The
same method refuses what cannot work, and it runs when the portal starts.

The six overview plugins gain a mixin that hands the visitor's page actions and the drawn cards to
the shared overview template, which draws a dropdown beside the header buttons and the cards at the
end of each column.

## Technical context

**Language/version**: Python 3.13, Django 5.2
**Primary dependencies**: django-mvp (`c-dropdown`, `c-menu`, `c-menu.item`), django-cotton,
django-flex-menus for the navigation as today. No new dependency
**Storage**: none. No model and no migration
**Testing**: pytest and pytest-django, per `docs/contributing/standards/testing.md`. Tests mirror
the source tree. Page behaviour is asserted through the test client against the real overview
pages, with plugins registered by the test and the registry restored afterwards by the existing
fixtures in `tests/test_contrib/test_plugins/conftest.py`. A record type's URL patterns are built
once, when its URL module is imported, so the page tests use one new fixture in `tests/conftest.py`
that saves the registry, lets the test declare, rebuilds the record types' URL patterns and clears
the URL caches, and puts both back afterwards
**Target**: the `fairdm` package. The demo application gains nothing, because the feature ships no
action or card (SC-004)
**Constraints**: every plugin registered before this feature is served, listed and refused exactly
as it was (SC-009). Every string is translatable. Wording, layout and styling get no tests

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Each story starts with tests of its acceptance scenarios, seen to fail first. Pages are requested through the test client as each kind of visitor the scenario names |
| II Simplicity / III Anti-Abstraction | One resolving method, one mixin, one small card base class. No plugin-type hierarchy, no settings, no second registry |
| IV Integration-First | Acceptance tests register a plugin the way an addon would and open the real overview of each record type |
| V Security | One access decision for showing and opening in all three places (FR-004). A hidden card contributes nothing to the response, its assets included. A card's further views are refused to anyone the card is hidden from. A removed address answers as an unknown one |
| VI / XVI Documentation | `docs/portal-development/create_a_plugin.md` gains a section per story, each with a working example, written in the story that introduces the names. `CONTEXT.md` gains the three glossary entries |
| VII Dependencies | None added |
| VIII i18n | The dropdown's label and every refusal a person may read are translatable |
| IX Data-model conventions | No model changes |
| X Cohesion | Resolution lives on `PluginRegistry`. What a served plugin is lives on one dataclass. The two places are supplied by one mixin |
| XVII Demo | Unchanged by design. The developer documentation carries the working examples |

## Complexity tracking

| Addition | Why it is needed | Simpler alternative, and why not |
|---|---|---|
| `Mount` dataclass and `PluginRegistry.resolve()` | Removal and replacement must not depend on declaration order, and four consumers need the same answer | Edit the registry list when a removal is declared: the result then depends on whether the plugin was registered yet (FR-028) |
| `OverviewPlaces` mixin | Six overview classes need the same two context values, and the registry needs to know which record types draw the places (FR-005) | A template tag that looks the plugins up: it would have no view to refuse a record type from, and FR-005 would need a separate list of record types |
| `Card` base class | A card has no address, so something other than dispatch has to draw it | Require every card to be a full view and render it by calling `dispatch`: a hidden card would then run its own permission handling and could redirect the whole page |
| A second call to `resolve()` at startup | Refusals must stop the portal from starting on every server | Rely on the URL configuration being imported: under a WSGI server that happens on the first request |

## Design

### D1. Declarations are kept as made

`PluginRegistry` keeps two things per record type:

- registrations, as today: `(plugin class, options)` in arrival order. `options` may now carry
  `place`, `column` and `replaces`.
- removals: the names declared with `registry.remove(model, plugin)`.

`get_plugins_for_model` keeps returning the registrations unchanged, so code and tests that read it
see what they saw before.

`plugins.remove` is exported beside `plugins.register`. Both accept a plugin class or a name where
they refer to another plugin.

### D2. `Place`

`fairdm/contrib/plugins/places.py` holds `Place`, a `TextChoices` with `NAVIGATION`, `ACTION` and
`CARD`, and `Column` with `SIDE` and `WIDE`. A registration passes the value or its string. No
`place` means `NAVIGATION` (FR-002).

Checked when the registration is made (the edge cases):

- `place` is not one of the three, or `column` is not one of the two
- `column` given for anything that is not a card
- `place="card"` on a class that cannot be drawn as a card (D6)
- `place="card"` together with `menu=False`, which means nothing for a card

`menu=False` with `place="action"` is allowed: the plugin is served and not offered, as a page that
declines its entry is today.

### D3. `resolve(model)`: what a record type serves

Returns a list of `Mount`, a frozen dataclass:

| Field | Meaning |
|---|---|
| `plugin_class` | the class that is served or drawn |
| `name` | the name it is served under, which URL names and lookups use |
| `url_path` | the segment it is served at; `None` for the record's own address |
| `place`, `column` | where it appears |
| `label`, `icon`, `order` | its entry |
| `listed` | false when the registration declined its entry |

Steps, each a pure function of the declarations:

1. Every registration becomes a candidate, identified by its plugin's own name.
2. Each removal must name a candidate, or the portal is refused (FR-029). A removal of the record
   type's overview is refused with a message saying it can be replaced (FR-030). The overview is
   the candidate that states no `replaces` and either is built on `OverviewPlaces` or has a
   `url_path` of `None`. A sample's overview is served at `overview/` and not at the sample's own
   address, which is why the address alone does not identify it. A replacement of the overview can
   be removed like any other replacement (FR-040, FR-042). Named candidates are dropped.
3. Each remaining candidate with `replaces` must name a remaining candidate. If its target was
   removed, the refusal names both the replacement and the removal (FR-041). If it never existed,
   the refusal names the replacement and the record type.
4. Two remaining candidates naming one target are refused, both named (FR-040). A cycle is refused.
5. Each chain is collapsed to one mount. The class is the last replacement's. `name` and `url_path`
   are the first plugin's. `label`, `icon`, `order`, `column` and a declined entry (`menu=False`)
   are taken link by link: what a replacement states, otherwise what it replaced had (FR-036). A replacement whose `place` differs
   from its target's is refused, both named (FR-035). A replacement that states no `place` takes
   its target's.
6. Among the mounts, generated URL names and segments must not clash. This applies exactly the
   rules of `validate_against_existing` to the final set, including that a segment of `None` is
   never compared, because a replacement's further views are now named under the target's name.
7. If any mount is an action or a card, some mount of the record type must be built on
   `OverviewPlaces`, or the portal is refused, naming the plugin and the record type (FR-005).

Every refusal is a `PluginRegistrationError` built by the existing `_fail`, which names the plugin,
the record type and the problem (FR-043).

The registration-time checks in `checks.py` stay. When `validate_against_existing` compares
segments and URL names it skips any registration that states `replaces`, whether it is the one
arriving or one already there, since a replacement is not served under its own. This is what lets a
replacement that keeps its target's segment be registered before or after the target (FR-039). Its
own name must still be unique.

### D4. Consumers of `resolve()`

- `get_urls_for_model` builds patterns from the mounts. `Plugin.get_urls` gains `name` and
  `url_path` arguments that default to the class's own, so a replacement is served under its
  target's. A card contributes patterns for its further views only, beneath `<name>/`.
- The navigation menu gets an entry for each mount with `place == NAVIGATION` and `listed`. Sorting
  is unchanged.
- `get_page_actions(model)` returns the listed action mounts sorted by `(order, name)`.
- `get_cards(model)` returns the card mounts sorted by `(order, name)`.
- `validate_all()` calls `resolve()` for every record type that has a declaration.
  `FairDMConfig.ready()` calls it after `autodiscover_modules("plugins")`.

### D5. Page actions on the overview

`OverviewPlaces` (in `fairdm/contrib/plugins/places.py`, mixed into `OverviewPlugin`) adds to the
context:

- `page_actions`: for each action mount the visitor may open, its label, icon and address. The
  decision is `can_open(mount.plugin_class, request, record)`, wrapped the way `menu_check` wraps
  it: a predicate that raises hides the action and is logged.

`overview/page.html` draws `<c-plugins.actions :actions="page_actions" />` in the header's button
row, after the `overview.actions` block and outside it, inside a new block `overview.page_actions`.
The component draws nothing when the list is empty (FR-012). It is a `c-dropdown` holding a `c-menu`
of `c-menu.item`, the same three components the Manage menu uses. Manage menus are not touched
(FR-013), and neither are the buttons already there (FR-014).

A page action is an ordinary plugin page. `has_permission` already refuses it at its address by the
same decision.

### D6. Cards on the overview

`Card` (in `fairdm/contrib/plugins/cards.py`) is `Plugin` with a template and a context and no HTTP
handler:

- `template_name`, `get_context_data(**kwargs)`, optional `Media`
- `render_card(request, record) -> SafeString`: binds the request and the record, then renders the
  template with the context plus `record` and `request`

`OverviewPlaces` adds `overview_cards`, a mapping with `wide` and `side`, each a list of drawn HTML.
For each card mount, in order:

1. `can_open(mount.plugin_class, request, record)`. False, or raising, means the card is skipped.
   Raising is logged.
2. `render_card` inside a `try`. A card that raises is skipped and logged with
   `logger.exception`, naming the card and the record (FR-022).
3. The card's `Media` is added to `plugin_media` only when it was drawn (FR-023). The overview's own
   `plugin_media` is `None` when it declares no `Media`, so the merge starts from an empty one.

`overview/page.html` loops over `overview_cards.wide` after the `overview.main` block and over
`overview_cards.side` after the `overview.side` block, each inside its column and inside a new
block (`overview.contributed_main`, `overview.contributed_side`). With no cards the loops write
nothing (FR-021).

A card's further views are mounted beneath `<name>/<segment>/` with `plugin_class` set to the card.
`as_view` puts `plugin_class` on the view instance, not on the class, so the owner is read from
`self.plugin_class`. When that owner is a card, `Plugin.has_permission` requires three things in
turn: `can_open` for the record type's overview, `can_open` for the card, and then the view's own
decision. The first is what "a card is never drawn on a page that was refused" means for a view
the card owns: a card with no predicate on a private project does not serve its further view to a
stranger. The second applies the card's permission as well as its predicate (FR-018).

A further view of a page is governed today by its own predicate and permission only, because
`has_permission` passes the class and the owner is not on the class. That stays as it is (SC-009).

A card has no page: nothing is mounted at `<name>/` itself.

### D7. Removal

`registry.remove(model, plugin)` records the name. Everything else is `resolve()` (D3, step 2).
A removed plugin contributes no mount, so it has no patterns, no entry, no action and no card, and
its URL names do not exist (FR-026). Nothing is deleted from storage, because nothing in the
registry touches storage (FR-031).

Shipped links (FR-032):

- `plugins.reverse` gains `default=`. When given, a `NoReverseMatch` returns it.
- `{% plugin_url %}` returns an empty string when the name does not resolve.
- `RecordOverviewPlugin.get_context_data` asks for `contribution-list` with `default=""`. The
  People card already leaves its link out when `all_url` is empty.
- The Contributors page links to the Contributors page of the record above it (a dataset's
  project, a sample's dataset) in two places in `contributors/plugins/shared.py`. Both ask with
  `default=""`, and `contribution_list.html` leaves the button and the link out when the address is
  empty. Removing the plugin from projects must not break a dataset's page.
- An address from `safe_reverse` is `None` when the plugin is gone. Every template that writes an
  entry from one draws the entry only when it has an address: the Manage menus, the project
  overview's links to its datasets and contributors, and the person and organization overviews'
  links to their projects and datasets.
- Each template that uses `{% plugin_url %}` writes its link only when the address is not empty.
  The older `plugin_url` tag in `fairdm/templatetags/fairdm.py` gives an empty string the same way.
  Templates that nothing includes any more are left alone.

### D8. Replacement

`@plugins.register(Model, replaces=Target)`. Everything else is `resolve()` (D3, steps 3 to 6).
The replacement is a different class with its own predicate and permission, so the access decision
is its own with no further work (FR-037). The replaced class contributes no patterns, so its
further views are not served unless the replacement declares views at those segments (FR-038).

Replacing the overview with a class built on the shipped one keeps `OverviewPlaces` in its
ancestry, so the actions and cards are still drawn (scenario 13).

## Story order and what each delivers

One story after another, each from the previous story's accepted commit.

| Story | Delivers |
|---|---|
| US-1 page actions | D1 (registrations only), D2, the navigation-and-action parts of D3 and D4, startup validation, D5 |
| US-2 overview cards | D6, the card parts of D3 and D4 |
| US-3 removal | D1 removals, D3 step 2, D7 |
| US-4 replacement | D3 steps 3 to 6, D8 |

US-1 carries the groundwork, because the first place to be added is what forces the registry to
resolve at all.

## Documentation

`docs/portal-development/create_a_plugin.md`:

- US-1: "Where a plugin appears" and "A page action", with a working example
- US-2: "An overview card", with a working example, including a card with a further view and assets
- US-3: "Removing a plugin"
- US-4: "Replacing a plugin"
- "When a registration is wrong" gains each new refusal in the story that adds it

`docs/portal-development/overview-pages.md` gains the three new blocks. `CONTEXT.md` gains page
action, overview card and Manage menu. The template's own block list is updated with them.

## Risks

- **Existing tests read the registry's private list.** The fixtures in
  `tests/test_contrib/test_plugins/conftest.py` save and restore `_registry`. They are extended to
  save and restore removals in the story that adds them.
- **`resolve()` is called on every overview request** through `OverviewPlaces`. It is a walk over
  a short list. It is not cached in this feature, because tests register plugins after startup and
  a stale cache would hide them. If a profile later shows it matters, the cache belongs on the
  registry and is cleared by `register` and `remove`.
