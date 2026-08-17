# Feature Specification: The plugin system

**Feature Branch**: `008-plugin-system`

**Created**: 2026-02-17 · **Rewritten**: 2026-08-17

**Status**: Draft

**Goals**: G3 — addons and community-specific views attach to the core models without changes to
the framework.

**Roadmap**: R8 — the plugin system.

**Input**: A portal or an addon needs to add pages to a record type the framework already serves:
an analysis view on samples, a curation form on datasets, a summary on contributors. The plugin
system is the surface through which that happens. A developer writes a view class, registers it
against a core model, and the framework supplies the URL, the navigation entry and access to the
record. This specification describes that surface and the guarantees it makes. It does not describe
the plugins the framework happens to ship.

## Clarifications

### Session 2026-08-17

- Q: The previous specification devoted a user story and eight requirements to a `PluginGroup`
  class that composed several plugins under one prefix and one navigation entry. No such class
  exists. Was its removal deliberate? → A: Deliberate. Composition stays, but a plugin declares
  its additional view classes itself rather than being wrapped by a container. The container was
  one of several abstractions the earlier implementation invented for problems it did not have.
  How a plugin declares those views is settled during planning, not here.
- Q: Tab appearance was specified as a `menu` dict on the plugin class carrying label, icon and
  order. Registration also accepts those as keyword arguments, and only the keyword arguments are
  read. Which is the surface? → A: The decorator. The `menu` dict belonged to an earlier
  dataclass-based navigation system that no longer exists. It is removed rather than deprecated in
  place, because ten plugins currently declare one that nothing reads.
- Q: Does a registered plugin appear in navigation by default, or only when it asks to? → A: By
  default, with an explicit opt out. The previous specification had the opposite default, which
  meant the common case carried configuration.
- Q: Five plugins are registered against `Measurement` and none can be served, because a
  measurement has no page of its own. Is that a defect or the design? → A: The design. A
  measurement is a component of the sample page, so it has no navigation of its own and no
  attachment point. The five registrations are removed.
- Q: A plugin's location record has the same shape but no wiring at all. Same treatment? → A: No,
  wire it. Location detail views need to accept plugins, so the attachment point is real and only
  the wiring is missing.
- Q: Two mechanisms guard a plugin: `check`, a predicate, and `permission`, a permission string.
  What does each decide? → A: `check` decides whether a navigation entry appears, for this user
  and for this record, including narrowing a plugin to one subtype of a polymorphic model. It is
  the navigation package's own mechanism and the plugin system passes it through rather than
  reimplementing it. `permission` decides whether a page may be opened, and it belongs to each view
  class rather than to the plugin, because a plugin's read view and its edit view want different
  answers.
- Q: How do the two interact? → A: They are one decision seen from two sides. A surface that is
  hidden is also refused, and a surface that is refused is also hidden. Splitting them lets an
  author write a predicate to hide a page, forget the permission, and leave it reachable by typing
  the URL, which reads as secured and is not. The rule is fixed here. The mechanism that enforces
  it in both places without duplicating the decision is settled during planning.
- Q: Registration is currently unvalidated: two plugins may claim the same path on one model, and
  the framework serves whichever imported first. Is validation part of this surface, or does it
  belong with the later work on attachment points? → A: Part of this surface. A registration that
  cannot work is refused when it is made, naming what is wrong.
- Q: The previous specification required a template lookup chain searching model-specific, then
  app-specific, then default locations. Nothing implements it. Rebuild or remove? → A: Remove. A
  plugin is a Django view and template selection is Django's, already overridable per class. The
  chain restated a framework feature in framework-specific terms.
- Q: The previous specification required a template error in one plugin not to prevent others on
  the page from rendering. Is that achievable? → A: It does not apply. Each plugin is a page, not a
  panel within one, so there are no sibling plugins to isolate from. The requirement described an
  architecture the system does not have.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a view and get a working page (Priority: P1)

A portal developer has written a view class that summarises a sample's analysis history. They add
the registration decorator naming `Sample`, restart, and the page is served at a predictable
address with an entry in the sample's local navigation, without editing a URL configuration or a
template.

**Why this priority**: this is the surface. Every other story extends it, and none of them has
value without it.

**Independent Test**: register a minimal view against a core model, request the generated address,
and confirm the page is served and the navigation entry is present.

**Acceptance Scenarios**:

1. **Given** a view class registered against `Sample`, **When** the portal starts, **Then** the
   plugin is served at a path derived from its class name beneath the sample's detail address
2. **Given** that registration, **When** a sample detail page is requested, **Then** the local
   navigation contains an entry pointing at the plugin
3. **Given** a plugin that sets an explicit path segment, **When** its address is generated,
   **Then** the explicit segment is used in place of the derived one
4. **Given** a plugin registered against two core models, **When** each model's page is requested,
   **Then** each serves the plugin against its own records, independently of the other

---

### User Story 2 - Reach the record without disturbing the view (Priority: P1)

A portal developer registers an existing update view as a plugin. The view already resolves its own
object, renders its own form and redirects on success. Registering it does not change any of that,
and the view can also reach the core record its page hangs from.

**Why this priority**: a plugin is a view first. If registration takes over the hooks a view class
relies on, only views written for the plugin system can be plugins, and the surface stops being
general.

**Independent Test**: register a stock Django view that resolves its own object, and confirm both
that its own behaviour is unchanged and that the core record is reachable from it.

**Acceptance Scenarios**:

1. **Given** a plugin whose view class resolves its own object, **When** the page is served,
   **Then** the view's own resolution is used and is not overridden by the plugin system
2. **Given** any plugin, **When** its page is served, **Then** the core record identified by the
   address is available to the view and in the template context
3. **Given** an address naming a record that does not exist, **When** the page is requested,
   **Then** the response is 404
4. **Given** a plugin page, **When** it renders, **Then** its navigation trail resolves to the
   record's list page and to the record itself
5. **Given** a plugin adding its own template context, **When** the page renders, **Then** both its
   context and what the system supplies are present
6. **Given** a plugin declaring the stylesheets and scripts its page needs, **When** the page
   renders, **Then** those assets are included in the response

---

### User Story 3 - What is visible and what is reachable are the same set (Priority: P1)

A portal developer restricts a curation plugin so that it appears only for users who may curate.
They express that once. A user who does not qualify sees no entry and, on typing the address
directly, is refused.

**Why this priority**: the failure this prevents is a security failure that reads as a success. An
author who hides an entry and believes they have restricted the page has published it.

**Independent Test**: restrict a plugin, then as an unqualified user confirm both that the
navigation entry is absent and that a direct request is refused; as a qualified user confirm both
are present.

**Acceptance Scenarios**:

1. **Given** a plugin whose predicate excludes the current user, **When** the record's page is
   requested, **Then** no navigation entry for that plugin appears
2. **Given** the same plugin and user, **When** the plugin's address is requested directly,
   **Then** the request is refused
3. **Given** a plugin whose view requires a permission the user lacks, **When** the record's page
   is requested, **Then** no navigation entry for that plugin appears
4. **Given** a plugin narrowed to one subtype of a polymorphic model, **When** a record of another
   subtype is viewed, **Then** the plugin is neither listed nor reachable for that record
5. **Given** a plugin with no predicate and no permission, **When** any user views the record,
   **Then** the plugin is listed and reachable

---

### User Story 4 - A registration that cannot work is refused when it is made (Priority: P1)

A portal developer mistypes a registration: two plugins claiming one path, a decorator with no
model, a path segment containing a character a URL cannot carry. The portal refuses to start and
names the plugin, the model and the problem, rather than starting and quietly serving one of them.

**Why this priority**: the surface is used by people who cannot read the framework's internals. A
registration that silently does nothing is the failure mode that let a whole shipped feature sit
inert.

**Independent Test**: make each malformed registration in turn and confirm the failure, its
message, and that it names the offending plugin.

**Acceptance Scenarios**:

1. **Given** two plugins registered against one model claiming the same name, **When** the portal
   starts, **Then** it refuses and names both plugins and the model
2. **Given** two plugins registered against one model claiming the same path segment, **When** the
   portal starts, **Then** it refuses and names the collision
3. **Given** a registration naming no model, **When** the portal starts, **Then** it refuses and
   names the plugin
4. **Given** a registration naming something that is not a core model, **When** the portal starts,
   **Then** it refuses and says what was passed
5. **Given** a path segment containing characters a URL segment cannot carry, **When** the portal
   starts, **Then** it refuses and names the segment
6. **Given** a plugin whose additional views collide with each other or with the plugin's own path,
   **When** the portal starts, **Then** it refuses and names the collision
7. **Given** the same plugin name registered against two different models, **When** the portal
   starts, **Then** it starts, because names are unique per model rather than globally

---

### User Story 5 - One plugin, several related views (Priority: P2)

A portal developer builds a contributor management feature: a list, an add form, an edit form and a
remove confirmation. They declare the three secondary views on the plugin. All four share one
address prefix and one navigation entry, and each secondary view carries its own permission.

**Why this priority**: most real features are more than one page, and without composition each page
becomes its own top-level entry, which fills the navigation with steps of a single workflow.

**Independent Test**: declare a plugin with secondary views, then confirm each is served beneath the
plugin's prefix, that only one navigation entry exists, and that a secondary view's own permission
is enforced.

**Acceptance Scenarios**:

1. **Given** a plugin declaring secondary views, **When** the portal starts, **Then** each is
   served at its own segment beneath the plugin's path
2. **Given** that plugin, **When** the record's page is requested, **Then** exactly one navigation
   entry appears for the plugin and none for its secondary views
3. **Given** a secondary view declaring a permission its parent does not, **When** a user lacking
   it requests that view, **Then** the request is refused while the parent remains reachable
4. **Given** a secondary view, **When** it is served, **Then** it reaches the core record on the
   same terms as the plugin itself

---

### User Story 6 - Control the navigation entry, or decline it (Priority: P2)

A portal developer registers a plugin reached only from a button inside another page, and does not
want it in the navigation. They decline the entry at registration. On another plugin they set the
label, the icon and the position of the entry, and the navigation reflects all three.

**Why this priority**: the default is right for most plugins, so this is refinement rather than
foundation. But a plugin that cannot decline an entry has no way to exist as a secondary page.

**Independent Test**: register one plugin declining its entry and one setting label, icon and
position, then confirm the first is absent from navigation and still reachable, and the second
appears as specified.

**Acceptance Scenarios**:

1. **Given** a plugin declining a navigation entry, **When** the record's page is requested,
   **Then** no entry appears and the plugin remains reachable at its address
2. **Given** plugins registered with positions, **When** the navigation renders, **Then** entries
   appear in position order rather than registration order
3. **Given** a plugin registered with a label and an icon, **When** the navigation renders, **Then**
   both are used
4. **Given** a plugin registered with neither, **When** the navigation renders, **Then** the entry
   carries a name derived from the view class and the framework's default icon

---

### Edge Cases

- A plugin is registered against a model that has no page of its own, so nothing can serve it.
- A plugin's path segment collides with an address the framework already serves for that record.
- Two plugins on different models share a name, which is permitted.
- The same view class is registered twice against one model.
- A predicate raises rather than returning a decision, while rendering navigation.
- A plugin declares a secondary view that is itself registered as a plugin.
- A record's page is requested by a user who may see the record but not any of its plugins.
- A polymorphic record is viewed as its base type, where a plugin is narrowed to a subtype.

## Requirements *(mandatory)*

### Functional Requirements

**Registration and addresses**

- **FR-001**: A decorator MUST register a view class against one or more core models
- **FR-002**: A registered plugin MUST be served at a path derived from its class name, beneath the
  address of the record it attaches to
- **FR-003**: A plugin MUST be able to declare an explicit path segment in place of the derived one
- **FR-004**: A plugin registered against several models MUST serve each model independently, with
  no registration affecting the behaviour of another
- **FR-005**: Plugin addresses MUST be reachable by name through the record's namespace

**Reaching the record**

- **FR-006**: The core record identified by the address MUST be available to the plugin's view
- **FR-007**: The core record MUST be present in the template context
- **FR-008**: Registration MUST NOT override view behaviour the plugin's own class defines,
  including its object resolution, its form handling and its template selection
- **FR-009**: A request naming a record that does not exist MUST return 404
- **FR-010**: A plugin page MUST carry a navigation trail whose entries resolve to real addresses

**Navigation**

- **FR-011**: Registration MUST add an entry for the plugin to the record's local navigation by
  default
- **FR-012**: A registration MUST be able to decline the navigation entry, leaving the plugin
  reachable at its address
- **FR-013**: A registration MUST accept the entry's label, icon and position
- **FR-014**: Entries MUST appear in position order
- **FR-015**: An entry with no declared label MUST carry a name derived from the view class, and
  one with no declared icon MUST carry the framework's default
- **FR-016**: A plugin MUST NOT be able to configure its navigation entry through a class
  attribute, since registration is the only place that declaration is made

**Visibility and access**

- **FR-017**: A plugin MUST be able to declare a predicate deciding whether its navigation entry
  appears, evaluated per user and per record
- **FR-018**: Each view class MUST be able to declare the permission required to open it,
  independently of the plugin it belongs to
- **FR-019**: A plugin surface that is not shown MUST NOT be reachable, and one that is not
  reachable MUST NOT be shown
- **FR-020**: The predicate MUST be evaluated by the same call for navigation and for access, so
  that the two cannot disagree
- **FR-021**: Permission checking MUST use the framework's own permission call, so that
  object-level permissions are resolved by the configured backends rather than by the plugin system

**Composition**

- **FR-022**: A plugin MUST be able to declare additional view classes belonging to it
- **FR-023**: Each additional view MUST be served at its own segment beneath the plugin's path
- **FR-024**: Additional views MUST share the plugin's single navigation entry and MUST NOT receive
  entries of their own
- **FR-025**: Additional views MUST reach the core record on the same terms as the plugin itself
- **FR-026**: An additional view MUST be able to declare its own permission

**Validation at registration**

- **FR-027**: A registration naming no model, or naming something that is not a core model, MUST be
  refused
- **FR-028**: Two plugins registered against one model with the same name MUST be refused
- **FR-029**: Two plugins registered against one model with the same path segment MUST be refused
- **FR-030**: A path segment that cannot appear in an address MUST be refused
- **FR-031**: Colliding paths among a plugin's additional views, or between them and the plugin's
  own path, MUST be refused
- **FR-032**: The same plugin name registered against different models MUST be permitted
- **FR-033**: Every refusal MUST name the plugin, the model and the problem
- **FR-034**: Refusals MUST occur when the registration is made, so that a portal cannot start
  carrying one

**Assets and context**

- **FR-035**: A plugin MUST be able to declare stylesheets and scripts its page requires
- **FR-036**: A plugin MUST be able to add its own template context alongside what the system
  supplies

### Key Entities

- **Plugin**: a view class registered against one or more core models, served at an address beneath
  that record's, carrying a navigation entry unless it declines one, and optionally owning further
  view classes. Its declarable surface is its path segment, its predicate, its permission, its
  additional views, its assets and its context.
- **Registration**: the association between a view class and a core model, made by the decorator,
  carrying the navigation entry's label, icon and position. Validated when made. A plugin's name is
  unique per model.
- **Local navigation**: the set of entries shown on a record's pages, one per registered plugin that
  has not declined and whose predicate admits the current user and record.
- **Additional view**: a view class belonging to a plugin, served beneath the plugin's path, sharing
  the plugin's navigation entry and declaring its own permission.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer adds a working page to a core record by writing a view class and one
  decorator, with no edit to any URL configuration, template or framework file
- **SC-002**: An addon distributed as a package registers plugins on a portal that has never heard
  of it, and they are served
- **SC-003**: No plugin surface can be reached by a user for whom it is not shown
- **SC-004**: A malformed registration prevents the portal from starting, and the message names the
  plugin responsible
- **SC-005**: A multi-page feature is served under one address prefix and occupies one navigation
  entry
- **SC-006**: A stock Django view is registerable as a plugin without alteration to how it resolves
  its object, handles its form or selects its template
- **SC-007**: Every core model that serves a detail page accepts plugin registrations, and every
  registration made against such a model is served
- **SC-008**: The navigation entries a user sees on a record are exactly the plugins they may open

## Assumptions

- Plugin authors know Django's class-based views; the system adds registration and attachment, not
  a view framework of its own.
- Navigation entries, their rendering and their predicate mechanism are provided by the navigation
  package the framework already depends on.
- Permission resolution, including object-level permissions, is provided by the configured
  authentication backends.
- Each plugin is a page in its own right rather than a panel composited into a shared page.
- Template selection is Django's, overridable per view class in the ordinary way.

## Out of scope

- Deriving attachment points from model registration, so that a model the framework has never seen
  gains them without wiring. That is the later roadmap item on attachment.
- A startup report listing every registered plugin and where it attached, which belongs with the
  same later work.
- The plugins the framework itself ships, except where one is evidence about whether this surface
  holds.
- Client-side plugins and plugins rendered without a server round trip.
- A template lookup chain of the plugin system's own, which Django already provides.
