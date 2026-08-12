# Goals

These are the standing directions `fairdm` works toward. Each one is a capability or
quality to steer by, not a task that gets ticked off. Whether any goal has been served well enough
is decided in the roadmap, the feature specs, and review, never by the goal itself.

This file carries no version numbers or release plan; that lives in the roadmap. For what the
package is, what it stays out of, and the principles that settle a close call, read the
*Scope & philosophy* section of the [README](README.md).

Importance is a tag on each goal, not a ranking:

- **Essential** — not worth adopting without it.
- **Expected** — a complete, dependable version is expected to have it.
- **Aspirational** — a genuine want whose absence never makes the package incomplete.

| ID | Goal | Importance | Status | Notes |
|----|------|------------|--------|-------|
| G1 | A core data model of projects, datasets, samples, measurements and contributors that domain schemas can extend and rely on | Essential | | |
| G2 | Registering a model is enough to get a working portal surface, with configuration needed only where a default is wrong | Essential | | |
| G3 | Addons and community-specific views attach to the core models without changes to the framework | Essential | | |
| G4 | Contributions can be recorded and revised against any object in the core model | Essential | | |
| G5 | A modern, extensible interface that every portal gets by default, with no frontend work | Essential | | |
| G6 | Core records can be created and edited by hand through the portal | Essential | | |
| G7 | Development and production settings stay out of a portal's way while remaining configurable where it matters | Essential | | |
| G8 | Portal roles and their permissions ship with the framework, so running a portal is a standard job rather than a bespoke setup | Essential | | |
| G21 | Records in the core model can be searched, sorted and filtered from the portal | Essential | | |
| G9 | Data and metadata are reachable by machines through a documented API | Expected | | |
| G10 | Round-trip import and export of tabular data | Expected | | |
| G11 | Private and public data sit side by side, controlled per object | Expected | | |
| G12 | A dataset moves from working state to visible through a checked process | Expected | | |
| G13 | Dataset metadata is complete enough for a formal-publication addon to submit it unaided | Expected | | |
| G14 | External identifiers for people, organisations and samples are carried through the record | Expected | | |
| G15 | A research group with no operations staff can deploy and run its own portal | Expected | | |
| G16 | A domain schema built by one community installs as a package in another portal | Expected | | |
| G17 | The framework grows through addons while the core stays small | Expected | | |
| G22 | A dataset carries versions, so an earlier state of it stays retrievable and citable | Expected | | |
| G18 | Portals exchange data with one another | Aspirational | | |
| G19 | A portal supports the research community around it, not only its data | Aspirational | | |
| G20 | Contributors use a portal in their own language and regional conventions | Aspirational | | |

_Written 2026-08-12. Revise as the goals change._
