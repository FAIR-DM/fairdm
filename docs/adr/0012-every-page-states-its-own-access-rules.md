# ADR 0012 — Every page states its own access rules

**Status:** accepted

## Decision

Every registered page states both the permission it requires and the visibility rule it applies. No
page relies on inheriting either from the page it belongs to.

This holds even where inheritance appears to be available, and even where the owning page's rule is
identical to the one being written out.

## Why

**Inheriting a visibility rule did not work, and nothing said so.** The rule is resolved from the
page class, while the link back to the owning page is only ever attached to the page instance. The
lookup therefore finds nothing and falls back to the page's own permissive default. Measured on a
private project, for a user holding the model-level right to change projects and no grant on that
record: the project's own page refused with 403 and its update page returned 200.

That defect is being fixed where it lives. This decision stands regardless of the fix, because of
what the incident showed about the shape of the risk.

**A rule that silently does not apply is worse than no rule.** The page carrying it reads as
guarded. Anyone auditing it sees a declared rule on the owning page, reasonably concludes the
belonging pages are covered, and stops looking. An absent rule at least looks absent.

**Stating it is cheap and checkable by reading.** One line per page, verifiable without running
anything, with no dependence on how the surrounding machinery resolves ownership today. Inheritance
saves a line and costs the ability to answer "what guards this page" from the page itself.

**A record fetched for a page is fetched without filtering.** The machinery deliberately reads past
any filtered manager, on the assumption that the page checks for itself. A page that does not check is therefore
unguarded over exactly the records that would otherwise have been invisible.

## Consequences

Repetition is expected and is not a target for removal. Two pages stating the same rule is the
intended state, not duplication awaiting a refactor.

Permission strings are written out rather than derived from the record type. Deriving them breaks on
the polymorphic record types, where a concrete subclass would produce a permission nothing grants,
because grants are normalised to the base type.

Tests for this behaviour go through a real request. A test exercising the decision helper directly
passes whether or not the page ever consults it, which is precisely how the defect above survived
having a test written for it.
