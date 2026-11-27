# ADR 0020 — A missing role is answered four ways, and never by blocking repair

**Status:** accepted

## Decision

A portal role that goes missing is answered in the order the answers can fire:

1. Deleting or renaming a shipped role through the portal is refused, by receivers that hold for
   every ORM writer and by an administration class that explains the refusal to whoever clicked.
2. Bringing the database up to date installs any role that is missing and restores the rights of
   one that was edited.
3. On the production baseline, a portal whose roles are missing refuses to start and names them
   (`fairdm.E500`).
4. In development nothing is blocked, and `manage.py check --deploy` reports the same condition.

The refusal in (3) stands down for the command that performs (2).

## Why

**The likely cause is an administrator tidying up.** Refusing the deletion where it is attempted
means the condition mostly never arises, and the person doing it learns why rather than meeting a
server error.

**A single hard refusal cannot work.** The check runs in `AppConfig.ready()`, which fires before
`migrate` does anything, and `post_migrate` is the only thing that installs the roles. A production
portal upgrading to the version that introduced them would refuse to boot *and* refuse to migrate,
with no route back from inside the portal.

**Silence is worse than either.** A portal missing a role goes on serving every page while part of
its access rules quietly stops being enforced, and nobody finds out until somebody cannot do their
job or somebody else can.

**This is stricter than the framework's answer to a missing vocabulary**, which warns and names the
command. The difference is what the absence costs: a missing vocabulary leaves every page working
with nothing to pick from, and a missing role changes who may do what.

## Consequences

An absent or unreadable group table reports nothing at all. A database that has never been migrated
is a different condition from a portal missing its roles, and only the second is a fault.

The guard holds for every ORM writer and not against raw SQL, which the design accepts: a role
removed that way is restored on the next update. Tests that need a role to be missing disconnect the
receivers by a named fixture, modelling that route explicitly rather than weakening the guard.
