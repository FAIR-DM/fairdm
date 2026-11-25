# Planning notes: FS-042 Find a record from anywhere in the portal

Notes for the build. Each one must be answered by name.

## The prototype

This feature comes from the prototype on the `prototype-mobile-dock` branch. Its hand-over is
`PROTOTYPE.md` at the branch root, and this feature is its "feature 1, Find a record from anywhere".
Its record of decisions is https://github.com/FAIR-DM/fairdm/issues/717. The prototype's search is in
`fairdm/search.py`, `fairdm/apps.py`, `fairdm/conf/urls.py` and the `app.navbar.end` block of
`fairdm/templates/base.html`.

## Built on django-mvp's search

Sam, 2026-11-25: "The search page functionality should be built off what django-mvp already
provides. It doesn't have to match our prototype 100%." The results page, the dialog, the header
button and the field are django-mvp's `mvp.search` as it ships, with one search kind per record
type.

## The look this feature ports

`fairdm/templates/base.html`, the `app.navbar.end` block: the header's search field and button and
the search dialog, landing at the same path. The prototype places them with
`<c-mvp.search.field />`, `<c-mvp.search.button />` and `<c-mvp.search.dialog />`, which is what
django-mvp's `mvp.actions.search` action draws. They are ported, not redrawn. This feature lands before
https://github.com/FAIR-DM/fairdm/issues/719, which waits on a django-mvp release. So the block
keeps the "Create new" button that is there on `main` and adds the search beside it. Removing
"Create new" is that issue's work, not this feature's.

## Shared piece: search kinds

`fairdm/search.py` in the prototype repeats the same shape seven times (model, fields to match,
visibility, result line). The rebuild writes one base kind that takes those four.

The fields to match should come from each record type's own list search (the `q` filter on its
filter set) rather than a second list of field names, so the two cannot drift (`decisions.md`, D1).

## Visibility per record type

Each kind's records are the ones the person may open (`decisions.md`, D2). On `main`:
`Dataset.all_objects.visible_to(user)`, `Sample.objects.visible_to(user)`,
`Measurement.objects.visible_to(user)`. Projects have `get_visible()` and the shared
`accessible_to(user, level)`, and no `visible_to` of their own. People follow `Person.objects.real()`,
as the people list does.
