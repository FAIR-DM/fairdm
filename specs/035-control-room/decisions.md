# Decisions: an operations control room in the administration interface

## Access is limited to superusers

The package's own default admits any staff account. FairDM's administration interface goes
further and admits holders of a rights-carrying portal role who are not staff at all
(`fairdm/contrib/admin/sites.py`). Those people curate records and manage contributors.

The panels reach the portal's infrastructure. The Redis panel can read and delete any key, which
includes cached pages and sessions held in the cache. The background-task panel shows the
arguments each task was called with, which can include personal data. Neither belongs to the
people who curate records, so the dashboard is limited to superusers, the accounts that can
already do everything else in the portal.

A portal that wants a narrower or wider rule sets the package's access settings itself. FairDM's
values are defaults a portal's own settings override, the same as every other setting FairDM
supplies.

## Which panels every portal gets

The three panels shipped for every portal match the three services every portal already runs:
Redis, the cache held in it, and Celery. None of them adds a service or a dependency on the
server.

The URL and signal panels describe the portal's code, not its running state. They are useful to
the person building a portal and of no use to the person running it, and listing every route and
receiver of a production portal tells an attacker more than it tells an operator. They are offered
only with development settings.

## The AI-agent interface stays off

The package offers an interface through which an AI agent can call every panel's tools. It is off
unless a portal turns it on, with a token and a named account. FairDM leaves it off and sets
nothing for it: turning it on is a decision about who outside the portal may reach its
infrastructure, and that belongs to the people running the portal.

## No panels written for FairDM

The published panels are adopted as they are. Writing FairDM's own panels, or restyling the
dashboard to match the portal, would be custom code for something an established package already
does.
