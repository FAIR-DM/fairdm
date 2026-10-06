# ADR 0026 — What a record type serves is worked out from every plugin declaration

**Status:** accepted

## Decision

The plugin registry keeps each declaration as it was made: registrations, with the place they name
and any plugin they replace, and removals. It never edits that list. `PluginRegistry.resolve(model)`
works out from the whole set what a record type serves, as a list of mounts. A removal drops a
registration. A replacement is served under the name and at the address of the plugin it replaces.
URL patterns, the local navigation, the page actions and the overview cards are all built from the
mounts, and from nothing else.

`resolve()` also refuses a set of declarations that cannot work. It runs for every record type at
the end of `FairDMConfig.ready()`, straight after the `plugins` modules are imported, so a portal
with such a declaration does not start. It runs again when a record type's URL patterns are built.

A record type offers page actions and overview cards when one of its plugins is built on
`OverviewPlaces`, the mixin that draws them. There is no separate list of record types.

## Why

An addon cannot control whether it loads before or after the application whose plugin it removes
or replaces. If a removal edited the list of registrations when it was declared, its effect would
depend on whether the plugin had been registered yet. Working the answer out from the whole set
gives the same result in any order.

Building all four things from one answer is what makes a removed plugin absent everywhere at once.
With separate walks over the registrations, a plugin could lose its address and keep its entry.

A removal or a replacement can only be judged once every declaration is known. Django's system
checks do not run when a WSGI server starts, and the URL configuration is not imported until the
first request. The end of plugin discovery is the earliest point that sees every `plugins` module,
and it runs on every way of starting.

The mixin decides which record types offer the two places because it is the class that draws
them. A list kept beside it would be a second thing to keep in step, and a replacement overview
built on the shipped one keeps the places with no further declaration.

## Revisit if

Resolving on each overview request shows up in a profile. A cache then belongs on the registry,
cleared by `register` and `remove`. Or addons begin declaring plugins somewhere other than a
`plugins` module, which the validation at startup would not see until the URLs are built.
