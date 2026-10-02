# Feature Specification: Plugins contribute page actions and overview cards, and can be removed or replaced

**Feature Branch**: `021-plugin-actions-and-cards`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G3: addons and community-specific views attach to the core models without changes to the
framework. G18: the framework grows through addons while the core stays small.

**Roadmap**: none. No roadmap item covers this. R8 delivered the plugin system this extends, and
R18 (plugins attach to any registered model) is separate work that this does not start.

**Input**: A plugin can add a page beside a record's overview and nothing else (#401). Two other
places on a record's page are closed to it: the dropdown of actions any visitor can take, and the
cards on the overview. An addon that wants a "Follow" action or an activity card has nowhere to put
either. An addon also cannot take a plugin away. Once FairDM registers one it stays, so an addon
with a better map cannot replace the one that ships. A plugin should be able to contribute a page
action or an overview card the same way it contributes a page, under the same rule that what is
hidden is also refused. A registered plugin should be removable and replaceable. This is the first
of seven features planned together in #397, and the map (#405) and the contact and report actions
(#407) are built on it.

## Clarifications

### Session 2026-10-02

These questions were settled while writing the specification, from the request and from the plan it
belongs to (#397). The reasoning behind each is in `decisions.md`.

- Q: The request speaks of tabs. The glossary says tabs were removed from the plugin system as a
  term. What does this specification call them? → A: A plugin page with a navigation entry, as
  specification 008 does. "Tab" is how that entry looks on the page and is not a term of the
  plugin system.
- Q: There are four ways something appears on a record's page: a navigation entry, a page action,
  a Manage menu entry and an overview card. Which of them can a plugin ask for? → A: Three. A
  navigation entry, as today, a page action, or an overview card. The Manage menu is not a place a
  plugin can ask for in this feature. It stays as each page builds it, for people with rights over
  the record.
- Q: How does a plugin say it is an action or a card? → A: When it is registered, in the same
  declaration that already carries its label, icon and position. A registration names one place. A
  registration that names none gets a navigation entry, so every plugin registered today behaves as
  it did.
- Q: What is a page action? → A: A plugin like any other, with its own address, whose entry sits in
  the page actions dropdown in place of the local navigation. Choosing the action takes the visitor
  to that address. What happens there is the plugin's business.
- Q: A card is drawn inside the overview and is not a page. How does "what is hidden is also
  refused" apply to it? → A: The same decision that governs any plugin decides whether the card is
  drawn for this viewer and this record. When it is not, nothing of the card reaches the response.
  A card has no page and no navigation entry of its own. Any further views it owns, such as the
  address a form inside the card posts to, are refused to a viewer the card is hidden from.
- Q: Which pages have the dropdown, and where? → A: The overview page of a project, dataset, sample,
  measurement, person and organization, among the header's actions. It is not added to a record's
  other pages.
- Q: The pages already have header buttons, such as citing and sharing. Do they move into the
  dropdown? → A: No. They stay as they are. This feature adds the dropdown and ships no action of
  its own, so on a portal with no addon the dropdown is not shown.
- Q: Where do contributed cards go on the overview? → A: A card says whether it belongs in the wide
  column or the side column, and goes in the side column when it says neither. Contributed cards
  follow the cards the page already has in that column. Among themselves they are ordered by
  position.
- Q: A replacement takes over from the plugin it replaces. What happens to the address and the
  navigation entry? → A: The replacement answers at the same address and under the same name, so
  every link to it keeps working. It appears in the same place. Its entry keeps the label, icon
  and position of the plugin it replaced unless the replacement states its own.
- Q: Addons load in an order the portal developer does not control. Does removal depend on it? →
  A: No. A removal or a replacement has the same result whether it is declared before or after the
  plugin it names is registered.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An addon adds an action any visitor can take (Priority: P1)

An addon author wants every dataset to offer a way to follow it. They write the view and register
it against the dataset as a page action. Every dataset's overview now has a dropdown of actions
with theirs in it, and choosing it takes the visitor to the addon's page. A visitor who is not
allowed to use the action does not see it, and is refused if they type its address.

**Why this priority**: The contact and report actions (#407) and every addon that offers something
to do with a record need this place. Without it they have nowhere to go but the navigation, which
is for pages about the record.

**Independent Test**: Register a minimal plugin as a page action against one record type. Open that
record's overview as a visitor and confirm the action is offered and leads to the plugin. Restrict
it, and confirm that an excluded visitor neither sees it nor can open its address.

**Acceptance Scenarios**:

1. **Given** a plugin registered against datasets as a page action, **When** a visitor opens a
   dataset's overview, **Then** the page offers a dropdown of actions that contains it and leads to
   the plugin's address for that dataset.
2. **Given** that registration, **When** the dataset's local navigation is drawn, **Then** it has no
   entry for the plugin.
3. **Given** a page action whose predicate excludes the current visitor, **When** they open the
   overview, **Then** the action is not offered, and a direct request for its address is refused.
4. **Given** a page action whose view requires a permission the visitor lacks, **When** they open
   the overview, **Then** the action is not offered, and a direct request for its address is
   refused.
5. **Given** several page actions registered with positions, **When** the dropdown is drawn,
   **Then** they appear in position order, and two with the same position appear in the same order
   on every start of the portal.
6. **Given** a record type with no page actions, or a visitor for whom every action is hidden,
   **When** the overview is opened, **Then** no dropdown of actions is shown.
7. **Given** a visitor who is not signed in and a page action with no restriction, **When** they
   open the overview, **Then** the action is offered to them.
8. **Given** a person with rights over a record, **When** they open its overview, **Then** the page
   actions and the Manage menu are offered separately, and no page action appears in the Manage
   menu.
9. **Given** a page action registered against contributors and narrowed to people, **When** an
   organization's overview is opened, **Then** the action is neither offered nor reachable for that
   organization.
10. **Given** a page action registered for each of projects, datasets, samples, measurements,
    people and organizations, **When** each kind of overview is opened, **Then** each offers its
    action.

---

### User Story 2 - An addon adds a card to the overview (Priority: P1)

An addon author wants a project's overview to show its recent activity. They write a card and
register it against the project as an overview card. Every project's overview now shows the card
after the cards the page already had. It has no page of its own and no navigation entry. A viewer
who is not allowed to see it gets an overview with no trace of it.

**Why this priority**: The overview is the page a visitor lands on. Today an addon can only change
it by overriding the template, which two addons cannot both do.

**Independent Test**: Register a minimal plugin as an overview card against one record type. Open
that record's overview and confirm the card is drawn with the record in hand. Restrict it, and
confirm an excluded viewer's page carries nothing of it.

**Acceptance Scenarios**:

1. **Given** a plugin registered against projects as an overview card, **When** a project's overview
   is opened, **Then** the card's content is part of the page and was drawn with that project.
2. **Given** that registration, **When** the project's local navigation and its page actions are
   drawn, **Then** neither has an entry for the card.
3. **Given** an overview card whose predicate excludes the current viewer, or whose permission they
   lack, **When** they open the overview, **Then** nothing of the card is in the response.
4. **Given** an overview card that owns a further view, and a viewer the card is hidden from,
   **When** that viewer requests the further view's address, **Then** the request is refused.
5. **Given** a card registered for the side column and a card registered for the wide column,
   **When** the overview is opened, **Then** each is drawn in its column, after the cards the page
   already has there.
6. **Given** a card registered with no column, **When** the overview is opened, **Then** it is drawn
   in the side column.
7. **Given** several cards in one column registered with positions, **When** the overview is
   opened, **Then** they appear in position order, and two with the same position appear in the
   same order on every start of the portal.
8. **Given** a record type with no contributed cards, **When** its overview is opened, **Then** the
   page is as it was before this feature, with no empty region where cards would go.
9. **Given** an overview card that raises while it is being drawn, **When** the overview is opened,
   **Then** the rest of the page is served, the failing card is left out, and the failure is
   recorded for the portal's operators.
10. **Given** an overview card narrowed to one sample type, **When** a sample of another type is
    opened, **Then** the card is not drawn.
11. **Given** a card registered for each of projects, datasets, samples, measurements, people and
    organizations, **When** each kind of overview is opened, **Then** each shows its card.
12. **Given** an overview card that declares stylesheets and scripts, **When** an overview showing
    it is served, **Then** those assets are included, and they are not included for a viewer the
    card is hidden from.

---

### User Story 3 - A portal or an addon takes a registered plugin away (Priority: P2)

A portal developer runs a portal whose samples have no meaningful location, and wants the map that
FairDM ships gone from them. They declare that the map is removed from samples. It no longer
appears on a sample's page and its address no longer answers. It stays on datasets, where they did
not remove it. Pages that used to link to it leave the link out.

**Why this priority**: The core stays small only if what it ships can be declined. Removal is also
half of what replacement needs.

**Independent Test**: Register a plugin against two record types, remove it from one, and confirm
that on the first its entry is gone, its address is not found and its name no longer resolves,
while the second is untouched.

**Acceptance Scenarios**:

1. **Given** a plugin registered against samples and then removed from samples, **When** a sample's
   page is opened, **Then** the plugin has no navigation entry, page action or card there.
2. **Given** that removal, **When** the plugin's former address is requested, **Then** the response
   is the same as for an address that never existed.
3. **Given** that removal, **When** code asks for the plugin's address by name, **Then** the name
   does not resolve.
4. **Given** a plugin registered against samples and datasets and removed from samples only,
   **When** a dataset's page is opened, **Then** the plugin is served there as before.
5. **Given** a removed plugin that owned further views, **When** any of their addresses is
   requested, **Then** none is served.
6. **Given** a removal declared before the plugin it names is registered, and the same removal
   declared after, **When** the portal starts in each case, **Then** the outcome is the same.
7. **Given** a removal naming a plugin that is not registered against that record type, **When**
   the portal starts, **Then** it refuses and names the removal and the record type.
8. **Given** a page FairDM ships that links to a plugin, and that plugin removed, **When** the page
   is opened, **Then** it is served without the link and without an error.
9. **Given** a removal naming the plugin served at a record's own address, **When** the portal
   starts, **Then** it refuses and says that this plugin can be replaced but not removed.
10. **Given** a removed plugin that stored data, **When** the portal starts, **Then** the stored
    data is untouched.

---

### User Story 4 - An addon swaps a shipped plugin for its own (Priority: P2)

An addon author has built a richer map than the one FairDM ships. They register theirs as a
replacement for it. On every page that had the shipped map, theirs is now served at the same
address, in the same position in the navigation. Every link that pointed at the map still works,
and the shipped map is no longer reachable anywhere.

**Why this priority**: This is what lets FairDM ship a basic version of something without extension
points (#405). Anyone who needs more replaces it whole.

**Independent Test**: Register a plugin, register a second as its replacement, and confirm the
second is served at the first's address under the first's name, that the first is not served at
all, and that the navigation has one entry in the original position.

**Acceptance Scenarios**:

1. **Given** a plugin and a second registered as its replacement on datasets, **When** the first
   plugin's address on a dataset is requested, **Then** the replacement is served.
2. **Given** that replacement, **When** code asks for the address by the first plugin's name,
   **Then** it resolves to the replacement.
3. **Given** that replacement stating no label, icon or position, **When** the page is drawn,
   **Then** there is one entry, in the place the first plugin's was, carrying the first plugin's
   label, icon and position.
4. **Given** a replacement stating its own label, icon or position, **When** the page is drawn,
   **Then** the entry uses what the replacement stated and keeps the rest.
5. **Given** a replacement, **When** the page is drawn, **Then** the access decision is the
   replacement's own: its predicate and its permissions, and nothing of the replaced plugin's.
6. **Given** a replaced plugin that owned further views, **When** their addresses are requested,
   **Then** none is served unless the replacement declares a view at that address.
7. **Given** a plugin registered against datasets and projects and replaced on datasets only,
   **When** a project's page is opened, **Then** the original is served there as before.
8. **Given** a replacement declared before the plugin it names is registered, and the same
   replacement declared after, **When** the portal starts in each case, **Then** the outcome is the
   same.
9. **Given** two plugins each registered as the replacement for the same plugin on one record
   type, **When** the portal starts, **Then** it refuses and names both.
10. **Given** those two, and one of them removed by the portal, **When** the portal starts,
    **Then** it starts and the other is the replacement.
11. **Given** a replacement naming a plugin that is not registered against that record type, or one
    that has been removed from it, **When** the portal starts, **Then** it refuses and names the
    replacement and the record type.
12. **Given** a replacement that names a different place from the plugin it replaces, such as a
    card replacing a page, **When** the portal starts, **Then** it refuses and names both.
13. **Given** a replacement for a record's overview that is built on the overview FairDM ships,
    **When** the overview is opened, **Then** page actions and contributed cards appear on it as
    they did on the original.

---

### Edge Cases

- A record type has page actions, and every one of them is hidden from this visitor. No dropdown is
  shown, the same as when there are none.
- A predicate raises while the dropdown or the cards are being drawn. The entry or card is treated
  as hidden and the failure is recorded, as the local navigation already does.
- A plugin is registered as a page action or an overview card against a record type whose page
  offers no such place, such as a location. The portal refuses to start and names the plugin and
  the record type.
- A registration names a place that does not exist, or names a column for something that is not a
  card. It is refused when it is made.
- A registration declines its entry and also asks to be a page action. The plugin is served at its
  address and is not offered in the dropdown, as a page that declines its navigation entry is today.
- The same plugin is wanted as a page and as a card. That is two plugins, one for each place.
- A page action and a page on one record type claim the same name or path segment. The registration
  is refused, as it is between two pages today.
- A card's name clashes with another plugin's on the same record type. It is refused the same way,
  because the name is what a removal or a replacement refers to.
- A replacement is itself replaced. That is allowed when the second names the first replacement,
  and the address stays the original one.
- A plugin is both removed and replaced on one record type by different declarations. The portal
  refuses to start and names both.
- A card is drawn on a private record. The overview decides whether the page opens at all, and a
  card is never drawn on a page that was refused.
- A card has nothing to show for this record. It is still drawn, and what it says is the card's own
  business. The page does not hide it.
- A portal overrides an overview template and drops the places where actions and cards are drawn.
  Nothing is shown there, and the actions remain reachable at their addresses.

## Requirements *(mandatory)*

### Functional Requirements

**Where a plugin appears**

- **FR-001**: A registration MUST be able to name the place its plugin appears: the local
  navigation, the page actions, or the overview cards. It names exactly one.
- **FR-002**: A registration that names no place MUST get a navigation entry, so that every
  registration made before this feature behaves as it did.
- **FR-003**: The place MUST be declared at registration, alongside the label, icon and position,
  and not through an attribute of the plugin class.
- **FR-004**: The rules specification 008 sets for every plugin MUST hold in all three places: one
  access decision for showing and for opening, narrowing to a subtype, unique names per record
  type, and refusal of a registration that cannot work.
- **FR-005**: A plugin registered as a page action or an overview card against a record type whose
  page offers no such place MUST be refused when the portal starts, naming the plugin and the
  record type.

**Page actions**

- **FR-006**: The overview page of a project, dataset, sample, measurement, person and organization
  MUST offer the record's page actions together in one dropdown among the header's actions.
- **FR-007**: A page action MUST be a plugin served at its own address beneath the record's, and
  choosing the action MUST lead to that address for the record being viewed.
- **FR-008**: A page action MUST NOT have an entry in the local navigation.
- **FR-009**: The dropdown MUST list exactly the page actions the current visitor may open for this
  record, whether or not they are signed in. An action that is not listed MUST be refused when its
  address is requested.
- **FR-010**: A registration MUST accept the action's label, icon and position, with the same
  defaults a navigation entry has.
- **FR-011**: Actions MUST appear in position order. Actions with equal positions MUST appear in an
  order that is the same on every start of the portal.
- **FR-012**: When the dropdown would list nothing for this visitor, it MUST NOT be shown.
- **FR-013**: The page actions MUST be separate from the Manage menu. A page action MUST NOT appear
  in the Manage menu, and this feature MUST NOT change what the Manage menu holds or who sees it.
- **FR-014**: The actions the overview pages already offer in their headers MUST stay where they
  are.

**Overview cards**

- **FR-015**: The overview page of a project, dataset, sample, measurement, person and organization
  MUST draw the overview cards registered for that record type.
- **FR-016**: An overview card MUST be drawn inside the overview, with the record being viewed and
  the current request available to it. It MUST NOT have a page or a navigation entry of its own,
  and MUST NOT appear among the page actions.
- **FR-017**: A card MUST be drawn only for a viewer and a record its access decision admits. For
  anyone else, nothing of the card may be in the response.
- **FR-018**: A card MUST be able to own further views, as any plugin can. Those views MUST be
  refused to a viewer the card is hidden from.
- **FR-019**: A registration MUST be able to say whether a card belongs in the overview's wide
  column or its side column. A card that says neither MUST go in the side column.
- **FR-020**: Contributed cards MUST follow the cards the page already has in their column. Among
  themselves they MUST appear in position order, and cards with equal positions MUST appear in an
  order that is the same on every start of the portal.
- **FR-021**: With no contributed cards to draw, an overview MUST be as it was before this feature.
- **FR-022**: A card that fails while being drawn MUST be left out, MUST NOT prevent the rest of the
  overview from being served, and MUST leave a record of the failure for the portal's operators.
- **FR-023**: A card MUST be able to declare stylesheets and scripts. They MUST be included on an
  overview that draws the card and left out when it does not.
- **FR-024**: A card MUST be drawn whenever its access decision admits the viewer, including when
  it has nothing to show. What it says then is the card's own.

**Removing a plugin**

- **FR-025**: A portal or an addon MUST be able to remove a registered plugin from a record type,
  whichever place it appears in and whoever registered it.
- **FR-026**: A removed plugin MUST NOT be shown on that record type's pages, MUST NOT be served at
  its former address or at the addresses of views it owned, and its name MUST NOT resolve to an
  address. A request for a former address MUST get the same response as an address that never
  existed.
- **FR-027**: A removal MUST apply to the record type it names and to no other.
- **FR-028**: A removal MUST have the same result whether it is declared before or after the plugin
  it names is registered.
- **FR-029**: A removal naming a plugin that is not registered against that record type MUST be
  refused when the portal starts.
- **FR-030**: The plugin served at a record's own address MUST NOT be removable. An attempt MUST be
  refused when the portal starts, and the refusal MUST say that the plugin can be replaced.
- **FR-031**: Removing a plugin MUST NOT delete or alter anything stored.
- **FR-032**: Every page FairDM ships that links to a plugin MUST be served without that link, and
  without an error, when the plugin has been removed.

**Replacing a plugin**

- **FR-033**: A portal or an addon MUST be able to register a plugin as the replacement for a
  registered plugin on a record type.
- **FR-034**: A replacement MUST be served at the address of the plugin it replaces and under its
  name, so that every link to that address and every lookup by that name reaches the replacement.
  The replaced plugin MUST NOT be served on that record type.
- **FR-035**: A replacement MUST appear in the same place as the plugin it replaces. One naming a
  different place MUST be refused.
- **FR-036**: A replacement's entry MUST keep the label, icon and position of the plugin it
  replaces, except for any of them the replacement states itself. A replacement card keeps the
  column the same way.
- **FR-037**: The access decision for a replacement MUST be the replacement's own. Nothing of the
  replaced plugin's predicate or permissions carries over.
- **FR-038**: Views the replaced plugin owned MUST NOT be served. The replacement's own further
  views are served beneath the same address.
- **FR-039**: A replacement MUST apply to the record type it names and to no other, and MUST have
  the same result whether it is declared before or after the plugin it names is registered.
- **FR-040**: Two replacements for one plugin on one record type MUST be refused when the portal
  starts. Removing one of them MUST settle the conflict in favour of the other.
- **FR-041**: A replacement naming a plugin that is not registered against that record type, or one
  that is also removed from it, MUST be refused when the portal starts.
- **FR-042**: A replacement MUST itself be replaceable and removable, like any registered plugin.

**Refusals and documentation**

- **FR-043**: Every refusal in this specification MUST name the plugin or plugins, the record type
  and the problem, and MUST stop the portal from starting.
- **FR-044**: The developer documentation MUST describe the three places a plugin can appear, how to
  register for each, how to remove a plugin and how to replace one, each with a working example.

### Key Entities

- **Plugin**: as specification 008 defines it. It gains one more thing declared at registration:
  the place it appears.
- **Place**: where a registration puts its plugin on a record's page. One of the local navigation,
  the page actions or the overview cards.
- **Page action**: a plugin offered in the dropdown of actions on a record's overview, open to any
  visitor the plugin admits. It is served at its own address.
- **Manage menu**: the menu on a record's overview that holds what people with rights over the
  record can do to it. It is separate from the page actions, and plugins do not register for it in
  this feature.
- **Overview card**: a plugin drawn as a card inside a record's overview, in the wide column or the
  side column. It has no page and no navigation entry.
- **Removal**: a declaration that a registered plugin is not served on one record type.
- **Replacement**: a plugin registered to stand in for another on one record type. It takes over
  the other's name, address and place.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An addon adds an action to a record's page with one view class and one registration,
  and edits no template, URL configuration or framework file.
- **SC-002**: An addon adds a card to a record's overview the same way, and two addons that each
  add one both appear on the same page.
- **SC-003**: No page action or overview card reaches a visitor it is hidden from: the actions a
  visitor is offered are exactly those they may open, and a card's content is in the response only
  for a viewer it admits.
- **SC-004**: A portal with no addons shows no dropdown of actions and no extra cards, and its
  overview pages are unchanged by this feature.
- **SC-005**: An addon replaces a plugin FairDM ships, and every link, bookmark and lookup by name
  that reached the shipped plugin reaches the replacement.
- **SC-006**: After a plugin is removed from a record type, no page of that record type shows it,
  links to it or serves it, and no page FairDM ships fails for want of it.
- **SC-007**: The result of removals and replacements does not depend on the order in which the
  portal's applications are loaded.
- **SC-008**: A removal or replacement that cannot work stops the portal from starting, with a
  message naming what is wrong.
- **SC-009**: Every plugin registered before this feature is served, listed and refused exactly as
  it was.

## Assumptions

- The plugin system is the one specification 008 describes. Its access decision, its validation at
  registration and its addresses are reused, not rebuilt.
- The overview pages are those of specifications 018 and 019. Their header, their two columns and
  the order of their own cards are unchanged.
- A person's page and an organization's page are both pages of a contributor. A plugin for one of
  them registers against contributors and narrows itself, as plugins already do for subtypes.
- Removal and replacement are declared in code by a portal developer or an addon author and take
  effect when the portal starts. There is no setting or administration page for them.
- Record types other than the six named, including ones a portal or an addon defines, do not offer
  page actions or contributed cards yet. That follows R18.
- The glossary in `CONTEXT.md` describes the code as it stands. It gains entries for page action,
  overview card and Manage menu when this is built.

## Out of scope

- Any particular action or card. Contact and report a problem are #407, and download, API access
  and the rest listed in #397 arrive with the features that need them.
- Moving the cards the overview pages already have, or their header buttons, onto the plugin
  system.
- Letting a plugin add an entry to the Manage menu. The editing pages that sit there are #404.
- The map, and retiring the location overview plugin, which are #405.
- A redirect from a removed plugin's address to somewhere else.
- Attachment points for record types the framework has not seen, and a startup report of what is
  registered where. Both belong to R18.
