# Decisions: 021-plugin-actions-and-cards

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The request (#401) and the plan it belongs to (#397) are the maintainer's own, and what
they state is taken as given: the four ways something appears on a record's page, the six pages that
get a page actions dropdown, that the dropdown is open to any visitor and separate from the Manage
menu, that a registered plugin can be removed or replaced, and that no particular action or card is
part of this feature.

## For Sam to confirm

Each of these changes what gets built, and none was stated in #401 or #397.

1. The Manage menu is not a place a plugin can register for. A plugin can ask for a navigation
   entry, a page action or an overview card. The editing pages of #404 stay linked from the Manage
   menu by the pages themselves. The cost is that an addon cannot add a Manage entry, which
   fairdm-publishing will probably want for registering a DOI.
2. The page actions dropdown is on the overview page only. A record's other pages do not carry it.
3. The header buttons the overview pages already have (cite, share and the rest) stay as buttons.
   With no addon installed, the dropdown is not shown at all until #407 ships its two actions.
4. Contributed cards follow the page's own cards in their column and cannot be placed between
   them. The cards FairDM ships today are not moved onto the plugin system.
5. A replacement always takes over the name and address of what it replaces. An addon that wants
   its plugin at a different address removes the original and registers its own separately.
6. The overview can be replaced and cannot be removed.
7. No sketch is planned before the build. The dropdown goes in the header's existing actions slot
   and uses a component the pages already have, and this feature ships no action or card of its own
   to design.

## How the interpretation was confirmed

Nobody was asked. The reading below was written from the request, the plan in #397, the sibling
requests #402 to #407, specifications 008, 018, 019 and 020, and the plugin code as it stands, and
was treated as confirmed.

A plugin gains a declared place: the local navigation as today, the page actions, or the overview
cards. The overview page of a project, dataset, sample, measurement, person and organization gets
a dropdown of page actions and draws contributed cards. The rule that what is hidden is also
refused holds in all three places. A registered plugin can be removed from a record type, or
replaced on it by another that takes over its address. The feature ships the mechanism and no
action or card of its own.

## "Tab" is not used as a term

`CONTEXT.md` says tabs were removed from the plugin system as a term and should not come back. The
request uses the word for what specification 008 calls a plugin page with a navigation entry. The
specification follows 008 and mentions "tab" once, to tie the request's wording to it.

## One registration, one place

A registration names exactly one place. The alternative, one plugin appearing as both a page and a
card, would need rules for which of the two an access decision or a removal refers to. An addon
that wants an activity page, an activity card and a follow action registers three plugins.

## The place is declared at registration

Specification 008 (FR-016) made registration the only place a navigation entry is configured, after
ten plugins carried a class attribute nothing read. The place a plugin appears is the same kind of
declaration, so it goes in the same spot. The keyword that carries it is for planning.

## A page action is an ordinary plugin with its entry somewhere else

This keeps addresses, permissions, further views and validation exactly as they are. It also makes
"what is hidden is also refused" hold with no new rule, since the action has an address to refuse.
An action that acts at once, such as following a record, is still a request to that address.

## How "hidden is also refused" applies to a card

A card has no address, so there is nothing to refuse for the card itself. The rule becomes: the
single access decision decides whether the card is drawn, and nothing of it reaches a viewer it
excludes. Further views a card owns are refused through the owning plugin's predicate, which is how
the access decision already treats additional views.

## A failing card does not take the page down

Specification 008 dropped the requirement that one plugin's error must not stop others from
rendering, because each plugin was a page and had no siblings. Cards bring siblings back. An addon's
card that raises would otherwise break the overview of every record, so it is left out and the
failure recorded. This matches what the local navigation does when a predicate raises.

## A card with nothing to show is still drawn

Specification 018 (FR-003) rules that a card the page has is always shown and says what is missing.
The framework cannot know whether a contributed card is empty, so it draws every card the viewer
may see and leaves the wording to the card. A card that should disappear for some records says so
through its predicate.

## Two columns, side by default

The overview has a wide column and a side column, and both hold cards. An activity card belongs in
the wide one and a small facts card in the side one, so the card chooses. The side column is the
default because that is where the page's own facts cards live.

## Ties in position are stable

Navigation entries with equal positions fall back to registration order today, which depends on the
order applications load. For actions and cards the specification asks only that the order is the
same on every start. What breaks the tie is for planning.

## No dropdown when there is nothing in it

The request asks what the page shows when there are no actions. An empty dropdown offers nothing and
specification 018 (SC-005) already rules that no button on an overview does nothing when pressed. The same applies when
every action is hidden from this visitor.

## Record types that offer the two places

The request names six pages. A plugin registered as an action or a card against anything else, such
as a location or a model an addon defines, is refused at startup. Silently accepting it would
repeat the failure 008 was written to end, where a registration did nothing and nobody was told.
Opening the places to other record types belongs to R18.

## Removal is per record type and independent of load order

A plugin is registered per record type, so it is removed per record type. An addon cannot control
whether it loads before or after the application whose plugin it removes, so the result may not
depend on it. That also means a removal naming something that is not there can only be judged once
everything is loaded, which is why those refusals happen when the portal starts.

## A removed address answers as if it never existed

No redirect and no notice. A removed plugin is not part of the portal, and a special response would
tell a visitor something was taken away.

## Shipped pages survive a removal

FairDM's own pages link to plugins by name, such as the count on a People card that leads to the
full list of contributors. If that plugin is removed, the page would fail on the lookup. The
specification requires those pages to leave the link out. This is the part of removal most likely
to be missed in the build, so it has its own requirement (FR-032).

## The overview cannot be removed

A record's own address is where every link to the record leads. Removing the plugin served there
would leave every record of that type unreachable. Replacing it is allowed.

## A replacement keeps the address and the name

FairDM's pages, addon code and bookmarks all reach a plugin by its address or its name. If a
replacement had its own, every one of them would break, and FR-032 would then hide links that
should have worked. So the replacement answers under the replaced plugin's name and address. Label,
icon and position carry over unless restated, because the usual case is a better version of the
same thing in the same spot. Access rules do not carry over: a replacement is new code and states
its own.

## Competing replacements are refused, and a removal settles them

Two addons replacing one plugin cannot both win, and picking by load order would be the silent
behaviour 008 rules out. The portal refuses to start. A portal developer who has installed both
removes the one they do not want, and the other stands.

## Removal and replacement are code, not configuration

Both are declared by a portal developer or an addon author and take effect at startup. A setting or
an administration page would let a running portal lose addresses without a deployment, and nothing
in the request asks for it.

## Sketch

Recorded as not needed, for the reason in item 7 above.

# Decisions made while planning

## D1. What a record type serves is worked out from the declarations, never edited into them

**Decision**: the registry keeps registrations and removals as they were made. One method,
`PluginRegistry.resolve(model)`, works out what is served, and the URL patterns, the navigation,
the page actions and the cards are all built from its result.
**Why**: a removal or a replacement must give the same result whether it is declared before or
after the plugin it names (FR-028, FR-039). Editing the list when a removal arrives cannot do that.
**Revisit if**: resolving on each overview request shows up in a profile. The cache then belongs on
the registry and is cleared by `register` and `remove`.

## D2. Removals and replacements are judged at the end of plugin discovery, and again when URLs are built

**Decision**: `FairDMConfig.ready()` validates every record type straight after it imports the
`plugins` modules. Building a record type's URLs validates it again.
**Why**: system checks do not run when a WSGI server starts, and the URL configuration is not
imported until the first request. The end of discovery is the earliest point at which every
documented declaration is known, and it runs on every way of starting.
**Revisit if**: addons start declaring plugins somewhere other than a `plugins` module.

## D3. A record type offers page actions and cards when its overview is built on `OverviewPlaces`

**Decision**: the registry refuses an action or a card on a record type none of whose plugins
carries the mixin that draws them. The same mixin, or being served at the record's own address, is
what marks the plugin that cannot be removed. There is no separate list of record types.
**Why**: the class that draws the places is the fact. A list beside it would be a second thing to
keep in step, and a replacement overview built on the shipped one keeps the places with no
further declaration.
**Revisit if**: R18 opens the places to record types the framework has not seen.

## D4. A card is drawn by a method, not dispatched as a view

**Decision**: `Card` gives a card a template, a context and `render_card(request, record)`. A card
is refused at registration unless it can be drawn this way.
**Why**: dispatching a view to draw a fragment would run its permission handling, which answers
with a redirect or an error page of its own.
**Revisit if**: cards need to be loaded after the page, each at its own address.

## D5. Actions and cards with equal positions are ordered by name

**Decision**: the sort key is the position, then the plugin's name. The navigation keeps
registration order for equal positions.
**Why**: names are unique per record type, so the order is the same on every start (FR-011,
FR-020). The navigation is left alone because existing plugins must be listed exactly as they
were (SC-009).
**Revisit if**: the navigation's order for equal positions is reported as unstable.

## D6. The position keyword stays `order`

**Decision**: a registration states its position with the existing `order` keyword in all three
places. The specification's "position" is that keyword.
**Why**: a second keyword for the same thing would leave two ways to say it.
**Revisit if**: never, short of renaming it everywhere.

## D7. A card's further views need the card's whole access decision

**Decision**: a further view owned by a card is refused unless the card would be drawn for this
viewer: the record's overview opens for them, and the card's own predicate and permission pass.
Further views of pages stay governed by their own predicate and permission, as they are today.
**Why**: FR-018 says a card's views are refused to anyone the card is hidden from, and a card is
never drawn on an overview that was refused. An author who writes a card sees the overview as the
gate, so a card with no predicate on a private record must not serve its views to a stranger.
Changing the rule for pages would alter how existing plugins are refused (SC-009).
**Revisit if**: the two rules are unified in a later feature that may change existing behaviour.

## D8. Findings from the design review, and what was done with each

**Decision**: twelve findings, two high. All applied as edits to the plan, the tasks and the
research. The sample overview is not at the sample's own address, so the overview is identified by
the mixin as well as by address. The Contributors page links to the record above it and is covered
by the removal work, with the Manage menus and the other entries whose address can come back
empty. A fixture that rebuilds the URL patterns gives the page tests somewhere to stand. A
replacement is left out of the segment comparison on both sides, carries over a declined entry,
and can be removed even when it replaces an overview. The tests of removal and replacement go in
the module that mirrors `registration.py`. `mount_name` was dropped because nothing read it.
**Why**: each was verified against the code the plan names.
**Revisit if**: never. This is a record of one review.

## D9. Story 1 builds only the places and options its tests need

**Decision**: `Place` has `NAVIGATION` and `ACTION`. The card place and the `Column` values arrive
with the card story. Until then a `column` given in any registration is refused, whatever its place.
`Mount` carries no column field yet. `resolve()` runs steps 1, 6 and 7 as small functions in
`checks.py`, so the later steps slot in between them.
**Why**: the brief limits this story to what its tests need, and a place that nothing can draw
would be accepted at registration and then mounted as a page.
**Revisit if**: the card story finds a reason to keep a column on a mount from the start.

## D10. `resolve()` is asked on every overview request and on every build of the patterns

**Decision**: `get_page_actions` calls `resolve()` each time. The overview mixin asks for the
actions on each request, and `get_urls_for_model` asks when a record type's patterns are built.
Nothing is cached.
**Why**: the plan says tests register plugins after startup, so a cache would hide them. The work
is a walk over a short list.
**Revisit if**: a profile shows the walk matters. The cache then belongs on the registry and is
cleared by `register`.

## D11. The page tests rebuild URL modules rather than patch resolvers

**Decision**: the `plugin_sandbox` fixture imports the six record-type URL modules, their core
include module and the root URL configuration again, then clears the URL caches. It does not edit
cached resolvers.
**Why**: `include()` builds a resolver whose list of patterns is cached after first use, and
clearing Django's own caches does not reach it. Importing the modules again builds fresh resolvers
from the registry and needs no knowledge of resolver internals.
**Revisit if**: a record type is mounted by a module the fixture does not list.

## D12. A card can only be registered as a card

**Decision**: a `Card` subclass registered with no place, or as a page action, is refused when
registered. A registration with `place="card"` is refused unless the class is built on `Card` and
has a `template_name` or draws itself with its own `render_card`.
**Why**: a card has no page, so a navigation entry or an action for one would name an address
that does not exist, and reversing it would fail while the overview was being drawn.
**Revisit if**: a plugin should be usable as both a page and a card, which the specification
settles as two plugins.

## D13. A card's further views find the overview as the first mount built on `OverviewPlaces`

**Decision**: `Card.admits` resolves the record type, takes the first mount whose class is built on
`OverviewPlaces`, asks `can_open` for it with the record, and then asks `can_open` for the card.
`Plugin.has_permission` calls it only when the owner read from `self.plugin_class` is a card.
**Why**: the shipped record types register exactly one such mount each, and a replacement
overview keeps the mixin in its ancestry. Reading the owner from the instance is what lets a card's
views be decided by the card, while a further view of a page is still decided by its own rule.
**Revisit if**: a record type registers two overviews, such as one per subtype. The mount whose
predicate admits this record would then have to be chosen.

## D14. Each drawn card sits in a wrapper that does not take part in the layout

**Decision**: the loops in `overview/page.html` write each card inside
`<div class="contents" data-contributed-card="wide|side">`.
**Why**: the framework never inspects a card's output, so a card that draws nothing is still
visible to a test and to a script through the hook. The wrapper uses `display: contents`, so the
column's spacing treats the card's own element as the item.
**Revisit if**: a card needs a styling hook on the element that holds it.

## D15. A removal is judged by its own function and has its own wording

**Decision**: `checks.validate_removals` refuses a removal that names nothing registered for the
record type, or the record type's overview. `checks.is_overview(mount)` holds the rule: built on
`OverviewPlaces`, or served at the record's own address. Refusals are written by
`_fail_removal`, as `removal of '<name>' from <Model>: <problem>`, and are still a
`PluginRegistrationError`.
**Why**: `_fail` writes `<plugin> registered against <Model>: ...`, which reads wrongly for a
removal. The overview rule is a function of a mount so that the clause about `replaces` can be
added where the rule lives, and so the page tests can use the rule rather than copy it.
**Revisit if**: a record type may have two overviews, for instance one per subtype.

## D16. A Manage menu with no entry left is not drawn

**Decision**: on the sample overview, where all four entries lead to removable plugins, the
Manage dropdown is drawn only when at least one of its entries has an address. On the project,
dataset, person and organization pages the menu always keeps an entry the overview owns, so only
the entries that can disappear are guarded.
**Why**: a trigger that opens an empty menu is a link to nothing, which is what removal must not
leave behind. Entries and anchors that are drawn are untouched.
**Revisit if**: a Manage menu is meant to stay as a visible landmark with nothing in it.

## D17. The removable plugins are read from the registry when the tests are collected

**Decision**: the parameters of the overview tests in
`tests/test_templates/test_overview_removed_plugins.py` come from `registry.resolve(model)` for
each record type with an overview page, minus the mount `is_overview` names.
**Why**: each case needs its own rebuilt URL configuration, and a parameter per plugin keeps one
failure from hiding the next. Nothing else adds to the registry before collection, so a plugin
FairDM registers later is still covered without editing the file. The location record type has
no overview page to open, so it is not in the list.
**Revisit if**: a test fixture or an addon registers plugins before collection.

## D18. The fixtures learn removals with the implementation, and two more pages are touched

**Decision**: `isolate_registry` and `PluginSandbox` save and restore removals in the commit that
adds the place removals are kept, not in the test-writing commit. The Contributors section of
`contributors.md` and a short section of `overview-pages.md` say what a removal does to the pages
they describe, besides the page the task names.
**Why**: the fixtures read the attribute the registry creates, so they cannot run before it
exists, and the tree has to be green between commits. Both pages describe addresses and links that
a removal now takes away.
**Revisit if**: the fixtures should hold removals in a place that exists before the registry does.
