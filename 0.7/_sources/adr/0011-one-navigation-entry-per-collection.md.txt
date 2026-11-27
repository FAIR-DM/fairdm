# ADR 0011 — One navigation entry per collection of pages

**Status:** accepted

## Decision

A group of pages that belong together contributes exactly one entry to a record's navigation. The
entry points at the group's own page, and that page draws links to the rest.

For a project, the entry is the project's page. Updating it, describing it and deleting it are pages
belonging to that entry and take no entry of their own.

A page that needs to be reached from the navigation directly is asking to be a group of its own, and
that is a deliberate choice rather than the default.

## Why

**The navigation is a shared, finite surface.** Every add-on registering a page against a record
draws from the same strip. If each page takes an entry, a portal with a handful of add-ons has a
navigation listing every action anyone can perform on a record. That is not navigation; it is an
index, and it is worst for the person who knows least about the portal.

**Actions belong next to what they act on.** A link to update a record's descriptions is more useful
beside the descriptions than in a strip at the top of the page, because next to the descriptions it
carries the context of what is about to be changed. Moving those links onto the group's own page
shortens the strip, and it also puts them somewhere better.

**The mechanism already exists and was being worked around.** Pages belonging to another page have
always been supported and have never generated navigation entries. That was read once as a gap to
route around by registering separately, which is how a page ended up with an entry it should not
have had. It is the design, not a limitation.

## Consequences

The group's own page becomes responsible for the discoverability of everything below it. A page
reachable by address but linked from nowhere is worse off under this rule than under one entry per
page, so a new belonging page is not finished until its group's page links to it.

Every belonging page must still state its own access rules. Sharing a navigation entry is not
sharing a permission, and the entry's visibility says nothing about who may open what it leads to.
See ADR 0012.

A group whose page grows a long list of links is a signal that the group is really two groups. The
answer then is a second entry, not a longer list.
