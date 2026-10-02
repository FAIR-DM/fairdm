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
