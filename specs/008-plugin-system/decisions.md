# Decisions — 008 The plugin system

This records the audit behind the rewritten `spec.md`, dated 2026-08-17. Each entry states what the
previous specification said, what the code did, which way it was settled and why. It exists so a
later reader can tell a deliberate narrowing from an oversight.

The previous specification was written on 2026-02-17 and implemented the same day. Six months later
the implementation was cut back sharply: the composition class, the validation module and the
navigation data structures were deleted, the base class fell from 507 lines to 274, and eleven test
modules covering composition, navigation, validation, permissions and template resolution went with
them. The reason given at the time, and confirmed during this audit, was that the original had
reinvented facilities the framework already had and solved problems it did not have.

So most of the distance between this specification and the code is not drift. It is a deliberate
reduction that was never written down. What this audit adds is the writing down, plus the parts of
the reduction that went further than intended and left working behaviour missing.

---

## D1 — Composition stays; the container that held it does not

**Previous specification**: User Story 4 and FR-009 to FR-013, FR-015, FR-019, FR-025 and FR-028
described a `PluginGroup` — a class wrapping several plugins, registered in their place, giving them
a shared address prefix and a single navigation entry.

**Code**: no such class. `group.py` was 152 lines and was deleted. What replaced it is a list of
view classes declared on the plugin itself, used once in the whole codebase, documented nowhere and
covered by no test.

**Settled**: the container is gone for good. Composition remains a requirement and moves onto the
plugin, which declares the additional view classes belonging to it.

**Why**: the container existed to hold a relationship the plugin could hold itself. Registering a
wrapper rather than a view meant the registration decorator accepted two unrelated kinds of thing,
and the wrapper then had to forward a permission, a predicate and a navigation entry to the views
it held. Declaring the views on the plugin removes the forwarding and the second kind of thing.

**Left open**: how the declaration is written, and how an additional view's address, permission and
record access are resolved. The current list attribute is the starting point, not the answer, and
is researched during planning.

---

## D2 — The decorator is the only place a navigation entry is declared

**Previous specification**: FR-022 and the Key Entities section described a `menu` dictionary on the
plugin class, with keys `label`, `icon` and `order`.

**Code**: both exist and only one is read. The registry builds the navigation entry from the
decorator's keyword arguments, falling back to the view's page title and icon. It never looks at the
`menu` attribute. Ten plugins across four modules declare a `menu` dictionary that nothing reads,
and eight registrations pass a position that is discarded.

**Settled**: the decorator carries label, icon and position. The `menu` attribute is removed rather
than deprecated, and position is honoured.

**Why**: the dictionary belonged to the deleted navigation system, which built its own tab objects.
The framework's navigation package supplies entries, and the registry is the point where a plugin
meets a model, so it is the natural place to say how the entry should read. Two ways to configure
one thing is what let ten plugins configure it through the way that does nothing.

---

## D3 — A registered plugin appears in navigation unless it declines

**Previous specification**: FR-003 and User Story 2 scenario 4 made a navigation entry conditional
on declaring a `menu` dictionary with a label. No dictionary meant no entry.

**Code**: every registered plugin gets an entry. The function that builds it is annotated as
returning `None` and documented as returning `None`, but every path returns an entry, so the guard
that was meant to skip plugins without navigation never fires. There is no way to decline one.

**Settled**: an entry by default, with an explicit way to decline.

**Why**: attaching a page to a record and wanting it listed is the ordinary case, and the previous
default made the ordinary case carry configuration. The code already had this default, by accident.
What it lacked was the opt out, which a plugin reached only from a button inside another page needs.

---

## D4 — The measurement registrations are removed

**Previous specification**: SC-013 required every core model to support plugin registration.

**Code**: five plugins are registered against `Measurement` and none can be served. The measurement
address configuration never mounts plugin addresses, there is no measurement navigation, and the
measurement detail view is documented in its own docstring as a placeholder deferred to a future
feature.

**Settled**: the five registrations are deleted. A measurement is a component of the sample page and
has no page of its own, so it has no navigation and no attachment point. This is the design, not a
gap.

**Why**: a registration that cannot be served is worse than no registration, because it reads as a
working feature. Keeping them would also have required inventing an attachment point for a record
type that is not meant to have one.

**Consequence outside this specification**: the later roadmap item on attachment points names
measurements as its motivating example and lists serving the measurement plugins as a deliverable.
That premise is wrong and the item is corrected in the same change.

---

## D5 — The location record is wired

**Previous specification**: covered by SC-013 in the same breath as measurements.

**Code**: one plugin registered against the location record, and the line that would mount its
addresses is commented out, referring to an interface that no longer exists.

**Settled**: wire it.

**Why**: unlike measurements, location detail pages are meant to accept plugins, so the attachment
point is real and only the wiring is missing. Its existing address is keyed by coordinates rather
than by identifier, so the mount shape is a planning question.

---

## D6 — The predicate and the permission are different questions

**Previous specification**: User Story 5 and FR-014, FR-016 and FR-017 described permission-based
visibility as one mechanism, naming the attribute `required_permission`.

**Code**: two mechanisms, neither working. The attribute is named `permission`, it gates access but
is never consulted when building a navigation entry, and its object-level branch cannot change an
outcome — the model-level test above it has already established that the user holds the permission
globally, at which point the object-level query returns everything. A user holding only an
object-level permission is refused, which is the reverse of what the specification asked for. The
predicate, `check`, is called two incompatible ways: through the instance with one argument in
dispatch, where binding silently makes the plugin the first argument, and as a plain attribute with
a different signature by the navigation package. Nothing can satisfy both, and the one helper the
package exports for writing predicates refuses every request when used.

**Settled**: both stay, with distinct jobs. The predicate decides whether a navigation entry
appears, for this user and this record, including narrowing a plugin to one subtype of a polymorphic
model. It is the navigation package's own mechanism, passed through rather than reimplemented. The
permission decides whether a page may be opened and belongs to each view class, not to the plugin.

**Why**: the multi-view case forces the split. A plugin's read view and its edit view want different
permissions, so a permission cannot live on the plugin as a whole. A predicate about whether
something should be listed is not the same question and does not decompose per view.

---

## D7 — Hidden implies refused, and refused implies hidden

**Previous specification**: silent. It required permission checks to hide entries and to block
direct addresses, but treated those as two requirements rather than one guarantee.

**Code**: they are neither coupled nor individually correct. A predicate excluding a user hides the
entry and, because of the binding defect above, refuses everyone. A permission the user lacks
refuses the page and shows the entry anyway.

**Settled**: one guarantee. A surface that is not shown is not reachable, and one that is not
reachable is not shown — expressed once and consulted by both navigation and access.

**Why**: this is a security property that fails while looking like it succeeded. An author writes a
predicate to hide a curation page, does not also set a permission, sees the entry vanish, and
concludes the page is restricted. It is reachable by typing the address. The two mechanisms have to
be one decision seen twice, or the surface's most likely misuse produces a published page.

**Left open**: how a per-plugin predicate and per-view permissions combine into a single decision
consulted from two places without duplicating it. Researched during planning.

---

## D8 — Validation is rebuilt, at registration

**Previous specification**: FR-023, FR-026, FR-032, FR-033 and SC-011 required configuration errors
to be detected before runtime with clear messages.

**Code**: nothing validates anything. The validation module was 397 lines carrying ten checks —
missing attributes, duplicate names, address collisions, invalid path characters, malformed
permission strings, missing templates — and it was deleted. Two plugins may claim one path on one
model and the framework serves whichever imported first. Four registrations in the import and export
module pass no model at all and would raise if that module were ever routed. The documentation still
instructs readers to run the check command and lists all ten codes.

**Settled**: rebuilt here, and enforced when the registration is made rather than by the check
framework.

**Why**: this surface is used by people who cannot read the framework's internals, and a
registration that silently does nothing is the failure that let a shipped feature sit inert for six
months. Registration happens at import, so it fails on every start including production; the check
framework runs from management commands, so a check never fires on a production boot. That is the
same reasoning settled for the model registry, and the two should behave alike.

---

## D9 — The template lookup chain is removed

**Previous specification**: FR-006 and FR-007 and User Story 3 required a hierarchy searching
model-specific, then app-specific, then default template locations, respecting polymorphic
inheritance.

**Code**: no chain exists. The single hand-written attempt, on an unrelated base class, reads an
attribute no class defines and would raise; all three templates it would have returned are missing
files. Six per-model template files sit in the tree that no code names and that extend a base
template which does not exist, so none of them could render if they were selected.

**Settled**: removed. Template selection is Django's, overridable per view class. The six unreachable
template files are deleted.

**Why**: a plugin is a Django view. Restating Django's template resolution in framework-specific
terms is the reinvention pattern that motivated the cut back, and the evidence that it was never
load-bearing is that it has been absent for six months without anyone noticing.

---

## D10 — Render-error isolation is removed

**Previous specification**: FR-027 and FR-028 and SC-008 required a template error in one plugin not
to prevent other plugins on the page from rendering.

**Code**: no error handling around rendering anywhere in the package.

**Settled**: removed as inapplicable.

**Why**: each plugin is a page, not a panel composited into a shared page. There are no other
plugins rendering alongside it to be isolated from. The requirement described an architecture the
system does not have and never had.

---

## D11 — The navigation trail stays and is finished

**Previous specification**: FR-004 required a trail showing the record's list, the record and the
plugin.

**Code**: the trail renders with both addresses hardcoded — the list entry points at the site root
and the record entry at a dead anchor — behind comments marking each as unfinished.

**Settled**: kept, with the addresses resolved.

**Why**: the comments record the intent, and a trail whose links do not navigate is worse than no
trail. The nested hierarchy the previous specification asked for, walking from project to dataset to
sample, is not reinstated: nothing in the code ever walked it and no requirement depends on it.

---

## D12 — A plugin registered against several models serves each independently

**Previous specification**: FR-024 required the same plugin class to be registerable for several
model types, and User Story 1 scenario 3 required it to appear on all of them.

**Code**: registration records the class against each model, and then address generation assigns the
model onto the class itself. Whichever model's address configuration imports last wins for every
mount, so one of the two serves the wrong record type. No test exercises it; the one test covering
multi-model registration asserts only that the class appears in each model's list.

**Settled**: the requirement stands and the defect is fixed. Each mount resolves against its own
model.

**Why**: this is the mechanism by which a reusable plugin distributed by an addon attaches to more
than one record type, which is the point of the surface. It has never worked.

---

## D13 — Permission checking delegates to the framework's own call

**Previous specification**: FR-017 required both model-level and object-level permission checks.

**Code**: fifteen lines that test the model-level permission, then import the object-level
permission library and run a query whose result cannot differ, as set out in D6.

**Settled**: one call to the framework's permission check, passing the record. The configured
backends resolve object-level permissions, which is what the object-level library installs itself to
do.

**Why**: the requirement is right and the implementation reimplemented the backend it was already
running. Delegating stops the plugin system from having an opinion about which permission backends a
portal runs.

**Amended 2026-08-17, during planning**: "one call" is wrong. `ModelBackend._get_permissions`
returns an empty set as soon as an object is passed, so `has_perm(perm, obj)` consults only the
object-level backends and would refuse a user holding the permission globally with no object row —
a regression against the code this replaces. The correct expression is two calls,
`has_perm(p) or has_perm(p, obj)`, which is what guardian's own view mixin does. The delegation
principle stands; the single call does not. See `research.md` §2.

---

## Not settled here

- **How additional views are declared and resolved** (D1). The current list attribute works for its
  single use; whether it is the right surface, and how an additional view's address, permission and
  record access resolve, is a planning question.
- **How the predicate and the permissions combine into one decision** (D7). The guarantee is fixed;
  the mechanism is not.
- **The mount shape for location plugins** (D5), whose existing address is keyed by coordinates.
- **Deriving attachment points from model registration**, and a startup report of what attached
  where. Both belong to the later roadmap item and are named out of scope in the specification.
