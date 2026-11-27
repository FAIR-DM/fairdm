# ADR 0038 — Each autocomplete scope is its own view

**Status:** accepted

## Decision

A record autocomplete serves one scope, and the scope is an attribute of its view class:

- `public`: public records, to everyone.
- `view`: public records and the private ones its user may view.
- `edit`: the records its user may edit.
- `profile`: one person's records, private ones only to that person.

`scoped_view()` makes the subclass for each scope, and each has its own address. A field that
places a record inside another uses `edit`. A field that links to a record uses `view`. A filter
on a public list uses `public`, whoever is signed in.

A field validates a submitted value through its scoped view's `offered()` for the request's user,
with the field's own settings, and never through django-tomselect's validation.

## Why

A field must never offer or accept a record its user may not see, and a list filter on a public
page must never reveal a private one. django-tomselect validates a value against a view it rebuilds
as `view_class()`, which drops anything passed to `as_view()`, set up with the current page's
query string. A scope passed at registration was therefore lost at validation, and a page's own
search narrowed the check. A class per scope, checked through the view's own rule, closes both.

## Revisit if

django-tomselect validates against the view its field names, with that view's arguments and
without the page's query string.
