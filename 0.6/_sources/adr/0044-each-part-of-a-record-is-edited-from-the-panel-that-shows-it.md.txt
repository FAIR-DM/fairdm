# ADR 0044: Each part of a record is edited from the panel that shows it

**Status:** accepted

## Decision

A record's overview page has no central editing menu. Each of the six shared editing pages of
decision 0026 is reached from the place on the overview page that shows what it changes:

- the header's Edit opens the record's details, and the Details panel carries the same Edit
- the keywords carry their own Edit, or Add keywords when the record has none
- the descriptions, a sample's or measurement's notes, the key dates and the identifiers each carry
  an Edit on their panel
- Delete is the last line of the Details panel
- the People panel carries Manage, which leads to the Contributors tab

`edit_links` in `fairdm/core/editing.py` gives the address of each page the viewer may use, keyed by
the part of the record the page changes, and an overview page draws a control only for a part that
has one. Who may open each page is unchanged: the rule of decision 0026 decides both the page and
whether its control is drawn.

This supersedes the part of decision 0026 that reaches the pages from a Manage menu in the record's
header. The rest of decision 0026 stands.

## Why

The redesigned overview pages agreed in https://github.com/FAIR-DM/fairdm/issues/668 put each fact
on one panel. A menu in the header named the pages by what they edit, so a reader had to translate
"Identifiers" in the menu into the Identifiers section further down the page. An Edit beside the
thing it changes needs no translation, and a page whose reader may edit nothing on it looks the same
as before with the controls taken away.

## Consequences

- `manage_menu` and `<c-actions.manage>` are removed. A portal that filled the `overview.manage`
  block to add an entry to the menu adds its own button there instead, beside the header's Edit, or
  an Edit control on the panel its action changes.
- `RecordEditingPage.menu_label` and `menu_icon` are replaced by `part`, which names the key of a
  page's link.
- A part with no panel on a page has no control there. A sample or measurement with no notes shows
  no notes panel, so its descriptions page is reached by its address until that page shows an empty
  notes panel.
