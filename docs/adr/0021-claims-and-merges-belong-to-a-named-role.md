# ADR 0021 — Profile claims and merges belong to a named role, not to superusers

**Status:** accepted

## Decision

Minting a profile claim link and merging one person record into another are decided by permissions
the Community Manager role holds, rather than by `is_superuser`.

## Why

**The reasoning that made them superuser-only is still sound, and it no longer points where it did.**
A claim token is a credential, and a merge destroys the discarded person's identity, so neither is an
ordinary staff operation. That was written when the only alternative to a superuser was anybody
carrying the staff flag — a flag every administrative helper had. A role a portal administrator
grants to a named person is a third thing, and it is exactly the person whose job this is.

**Looking after people is a role the framework now ships.** Leaving the two operations that job most
needs behind a superuser account means either the work does not get done or somebody is handed a
superuser account to do it, which is the outcome the role set exists to prevent.

## Consequences

A portal that wants these operations to stay with the deployer removes the permissions from the
role. A superuser continues to hold everything.

The reasoning in the views' own docstrings is superseded by this record rather than deleted: the
argument it makes is right about staff flags and is why the replacement is a role rather than a
wider flag.
