# Decisions: an operations control room in the administration interface

## D1 — Access is limited to superusers

The package's own default admits any staff account. FairDM's administration interface goes
further and admits holders of a rights-carrying portal role who are not staff at all
(`fairdm/contrib/admin/sites.py`). Those people curate records and manage contributors.

The panels reach the portal's infrastructure. The cache panel can change and delete entries, and
the background-task panel shows the arguments each task was called with, which can include
personal data. Neither belongs to the people who curate records, so the dashboard is limited to
superusers, the accounts that can already do everything else in the portal.

A portal that wants a narrower or wider rule sets the package's access settings itself. FairDM's
values are defaults a portal's own settings override, the same as every other setting FairDM
supplies.

**ADR:** docs/adr/0043-the-operations-dashboard-is-for-superusers-only.md

## D2 — Which panels every portal gets

The three panels shipped for every portal match the three services every portal already runs:
Redis, the cache held in it, and Celery. None of them adds a service on the server.

The URL and signal panels describe the portal's code, not its running state. They are useful to
the person building a portal and of no use to the person running it, and listing every route and
receiver of a production portal tells an attacker more than it tells an operator. They are offered
only with development settings.

**ADR:** docs/adr/0043-the-operations-dashboard-is-for-superusers-only.md

## D3 — The AI-agent interface stays off

The package offers an interface through which an AI agent can call every panel's tools. It is off
unless a portal turns it on, with a token and a named account. FairDM leaves it off and sets
nothing for it: turning it on is a decision about who outside the portal may reach its
infrastructure, and that belongs to the people running the portal.

**ADR:** none — the package's own default, left as it is. Nothing to inherit.

## D4 — No panels written for FairDM

The published panels are adopted as they are. Writing FairDM's own panels, or restyling the
dashboard to match the portal, would be custom code for something an established package already
does.

**ADR:** none — adopting a package as published is the repo's standing practice, not a new decision.

## D5 — No request leaves the portal, and Redis stays read-only

Found while researching, after the specification was approved, and written into it as FR-013 and
FR-014. Both narrow the feature, so the open spec gate was not re-run.

- The URL panel can send a real HTTP request to an address a user types, to show how it answers.
  That is a request leaving the portal, which the feature rules out, so FairDM turns it off. The
  list of routes stays.
- The Redis panel's key editing, deletion and expiry changes are off unless a portal turns them on
  per instance. FairDM leaves them off. Reading the portal's state is the feature. Changing Redis
  under a running portal is a separate decision for the people running it.

**ADR:** docs/adr/0043-the-operations-dashboard-is-for-superusers-only.md

## D6 — The dashboard is part of FairDM's core, not an addon

The constitution leaves advanced dashboards to addons. This dashboard is about running the portal,
not about its research data. It serves G16, a research group with no operations staff runs its own
portal, and that group is exactly the one that would not know to install an addon. The maintainer
decided it ships with every portal.

**ADR:** none — the maintainer's placement decision for this feature, recorded here and in the specification.

## D7 — The URL and signal panels are development dependencies only

Found at design review. The dashboard finds panels from the packages installed in the
environment, not from the apps a portal turns on. A panel package installed in production but not
turned on would still appear in the administration sidebar, and its link would fail. So FairDM
does not install the two packages for every portal. They are in FairDM's own development
dependencies, and FairDM's development settings turn them on wherever they are installed. A portal
developer who wants them adds the two packages to the portal's development dependencies. This
narrows US2, so the open spec gate was not re-run.

**ADR:** docs/adr/0043-the-operations-dashboard-is-for-superusers-only.md
