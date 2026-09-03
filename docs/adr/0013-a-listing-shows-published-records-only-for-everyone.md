# ADR 0013 — A listing shows published records only, for everyone

**Status:** accepted

## Decision

A portal-wide listing of a sample or measurement type shows the records held in published datasets,
and shows the same rows to every viewer. Signing in changes nothing about a listing. A researcher
does not see their own unpublished records mixed into one.

This is a rule about portal-wide listings. It says nothing about a page scoped to a dataset, a
project or a single record, each of which answers its own access question.

## Why

The obvious alternative is to show each viewer what they are entitled to see, which is what most
portals do and what "browse the records" suggests on first reading. It costs more than it returns.

**Every listing becomes viewer-dependent.** Nothing about the page can be cached across viewers.
Every filter's choice list has to be computed per viewer, or it leaks the existence of records the
page itself excluded. Every column added later inherits the obligation to get the same rule right
again, and the failure mode is silent.

**What it buys is small.** A researcher looking for their own unpublished records is on their
dataset's page, not scanning a portal-wide listing of every sample in the portal.

**The uniform rule turns a leak into a test.** One assertion, made once, covers every viewer:
signed out, signed in, the records' own owner, an administrator. Under the entitlement reading the
same assurance needs a case per role and is never quite complete.

## Consequences

A portal upgrading to a version carrying this rule finds its listings empty until an administrator
publishes something. That is the intended state. The alternative, defaulting existing datasets to
published, publishes data nobody chose to publish.

A dataset-scoped listing that shows a researcher their own records is a separate thing to build,
and it does not inherit this rule.
