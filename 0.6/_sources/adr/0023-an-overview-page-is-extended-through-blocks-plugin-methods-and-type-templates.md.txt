# ADR 0023 — An overview page is extended through blocks, plugin methods and type templates

**Status:** accepted

## Decision

The overview pages of projects, datasets, samples and measurements share one template,
`overview/page.html`, and one set of named blocks under `overview.`. A block that means the same
thing on two pages has the same name on both.

What a page computes lives on its `Overview` plugin as methods. What every page computes the same
way (credits, people, identifiers, citation, timeline, licence, the two charts) lives on
`RecordOverviewPlugin`, which all four subclass. Samples and measurements subclass it through
`TypedOverviewPlugin`, which chooses the page's template by the record's type. A type's own
template is `<app_label>/<model_name>_overview.html`, then its nearest ancestor's, then the shared
page. No registration step is involved.

So a portal changes an overview page in one of three ways:

- It overrides a template and fills blocks, for what the page shows.
- It subclasses a plugin and overrides one method, for what the page computes.
- It adds a template named for its sample or measurement type, for a type's own fields.

## Why

Before this, each page built its own header, side column, citation and people card, and a portal
that had extended one page learned nothing about extending another.

A module of functions can only be monkey-patched, which is not a supported interface. A method on
the plugin is one a portal can override. The view is also the class Django already gives this
logic.

Choosing the template by name keeps the framework ignorant of a portal's types. Samples and
measurements are the records portals subclass. Projects and datasets have fixed schemas, so they
are changed by overriding their template in the usual way.

## Revisit if

A fifth record type gets an overview page and needs something none of the three routes offer, or
portals start overriding the same plugin method the same way, which would mean it belongs in the
framework.
