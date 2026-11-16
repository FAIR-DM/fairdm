# ADR 0022 — Development accounts are a command that refuses, not a fixture that loads

**Status:** accepted

## Decision

FairDM distributes five development accounts — one for each portal role and one holding none — as a
management command, `create_dev_accounts`, shipped with the package rather than with the demo. It
refuses to run on any environment that is not one FairDM ships a non-production override for, and
creates nothing when it refuses. A second check, `fairdm.E501`, reports any of those five addresses
found on a portal outside development.

## Why

**A fixture cannot refuse anything, and this data must be refusable.** The accounts share a password
that is written down in the documentation and one of them administers the portal. `loaddata` on a
shipped JSON file will load it wherever it is run.

**A fixture is also the wrong shape for this user model.** A person record is polymorphic, so every
row needs a content-type primary key that differs between databases; the password would ship as a
hash pinned to today's hasher parameters; and signing in without a confirmation step needs a
verified email row per account. A command hashes at run time and resolves content types by lookup.

**They ship with the package because their audience is wider than this repository.** A research group
building a portal on FairDM needs to sign in as a curator in *their* portal, and the demo is not
installed there.

**A refusal guards the act, not the state.** A database copied down from production, a dump restored
the wrong way round, or an environment variable changed under a live database all produce accounts
the command would have refused to create. That is what the second check is for.

## Consequences

The environment rule is the framework's own, the same one the production boot guard uses. Nothing
here keys on `DEBUG`.

An address that already belongs to somebody is left alone and the command fails, rather than taking
over an account that happens to share a name with a shipped one.
