# ADR 0004 — A portal's apps are registered ahead of FairDM's

**Status:** accepted

## Decision

Apps a portal declares through `fairdm.setup(apps=[...])` are placed ahead of FairDM's own apps and
ahead of the third-party set in `INSTALLED_APPS`, behind only the Django contrib apps that must load
first. A portal shipping a template or static file at the same path as a FairDM one has its own file
served.

`INSTALLED_APPS` is composed as an explicit, commented sequence of groups rather than one literal
list with the portal's apps interpolated at the end.

## Why

Django's app-directories template loader walks `INSTALLED_APPS` in order and returns the first match,
and `staticfiles` resolves the same way. FairDM previously appended portal apps last, so a portal
template at a FairDM path was never reached — the file sat in the repository looking effective and
did nothing, with no error to say so.

Overriding a framework template is the ordinary way a portal makes itself its own, and it is the
thing FairDM's own documentation encourages. A framework that cannot be overridden at its most
common extension point pushes portals into forks.

This is a breaking change with a quiet failure mode in the other direction: a portal that already
ships a shadowing template will find it served where it was previously inert. That is the intended
behaviour and the reason it is called out in the release notes rather than absorbed silently.

## Revisit if

FairDM needs a template that a portal must not be able to override — a security-relevant fragment, or
something the framework's own correctness depends on. That is a real case, and the answer is to place
it somewhere app-directory resolution does not reach, rather than to reorder the list back.
