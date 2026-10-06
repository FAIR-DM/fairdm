# ADR 0027 — A card's own views open only where the card would be drawn

**Status:** accepted

## Decision

An overview card has no address. It is drawn by `Card.render_card` inside the overview, and only
for a viewer its `check` and `permission` admit.

A further view that a card owns, such as the address a form in the card posts to, is served only
when the card would be drawn for that viewer on that record. `Card.admits` decides it: the record
type's overview must open for the viewer, and then the card's own predicate and permission must
pass. `Plugin.has_permission` asks it before the view's own rule.

A further view of a page is decided by its own predicate and permission, as before.

## Why

The author of a card sees the overview as the gate: the card appears on a page that already
decided whether this viewer may see the record. A card with no rule of its own is a normal thing
to write. Without this rule, its further view on a private record would be open to anyone who
knew the address, because plugin views read records past the manager that hides private ones.

Drawing a card by dispatching it as a view was rejected. A view that refuses answers with a
redirect or an error page of its own, which has no meaning for a fragment of another page.

The rule for pages was left alone because changing it would alter how every existing plugin's
further views are refused.

## Revisit if

The two rules are brought together, in a change that is allowed to alter how existing plugins
behave. Or cards come to be loaded after the page, each from its own address.
