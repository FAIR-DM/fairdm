# ADR 0026: A record's editing pages are six shared pages

**Status:** accepted

## Decision

A project, a dataset, a sample and a measurement are edited through the same six pages: edit
details, descriptions, keywords, key dates, identifiers and delete. Each page is one plugin class in
`fairdm/core/editing.py`, registered on all four models, and a sample type or measurement type a
portal registers receives them with no work beyond its registration. Each page is a registration of
its own with no tab, not an additional view of the record's overview. Dates and identifiers are
edited on pages of their own and not as rows on the details page.

The pages are reached from a Manage menu in the record's header. `manage_menu` lists the pages the
viewer may use, in a fixed order, and `<c-actions.manage>` draws it on all four overview pages.

Each page states its own access, as decision 0012 asks. The attribute that states it, `access`,
is written on every page, and the rule that reads it lives on the class every page inherits,
`RecordEditingPage`, not on an owning page, because one plugin registered on four models has one
`permission` attribute and needs four. The rule is the same on every request, a view and a save:

- A person who may neither see the record nor hold the right on it is told the record does not
  exist.
- A visitor who may see the record and may not use the page is sent to sign in.
- A signed-in person who may see the record and may not use the page is refused with a 403.

The right needed is the right to change the record for the five editing pages and the right to
delete it for the delete page. Both are the rights the portal already checks, so nobody gains or
loses the ability to change or delete a record.

This supersedes decision 0008.

## Why

Before this, the pages that edit a record existed three times. A project and a dataset each had an
update page, a descriptions page and a delete page registered as additional views of the overview,
a sample had four pages built on generic bases, and a measurement had none. A change made to one
did not reach the others, and a measurement could not be corrected through the portal.

Decision 0008 gave a record one page for its attributes with its dates and identifiers as rows on
it, and registered that page as an additional view. An additional view cannot be registered on
four models at once, and it inherits its owner's visibility check but never its permission. A page
registered on its own can be shared by every record type, and the dates and identifiers, which are
the pieces that differ most between record types, are better edited on pages of their own.

Answering 404 only for a viewer who may not see the record, and 403 for one who may, follows from
what the answer would otherwise disclose. A private project's team member who holds the view level
was told a record they can open did not exist when they asked for a page they could not use.

## Consequences

- A portal developer writes nothing to give a registered sample or measurement type its editing
  pages. A type controls what the details page offers through its registry configuration.
- A request for an editing page of a private project or dataset that a signed-in viewer may open
  now answers 403 where it answered 404.
- The addresses of the pages being replaced are not kept. There are no redirects.
- An addon cannot remove or replace one of these pages on a record type.
