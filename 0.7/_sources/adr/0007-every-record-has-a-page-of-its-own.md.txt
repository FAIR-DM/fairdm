# ADR 0007 — Every record has a page of its own

**Status:** accepted

## Decision

Every record kind FairDM stores has its own address and its own page, including measurements. A
measurement is not only a component of the sample page it belongs to.

`Measurement.get_absolute_url()` returns the measurement's own address rather than deflecting to its
sample's. The view and template behind that address are separate work; the address itself is a
commitment, not a placeholder.

## Why

Two reasons, and the first is the one that decides it.

**Auditing.** Anything stored has to be inspectable on its own terms — what it says, who contributed
it, when it changed. A record reachable only as a fragment of another record's page has no place to
show that, and no address to cite when someone asks about one specific result.

**A uniform editing interface.** Projects, datasets, samples and measurements are all records, and a
portal developer should not have to learn a different interaction for one of them because it happens
to be small. Giving every record kind the same create, view, edit and delete surface is what keeps
that promise as more record kinds are added.

A previous ruling went the other way, and it is worth naming why it was wrong rather than simply
reversing it. It was taken while specifying where plugins attach, and the answer to that narrow
question — a measurement had no attachment point — was generalised into a claim about pages. The
narrow finding was correct. The generalisation was not, and it removed five plugins on the strength
of it.

A secondary consequence follows: once measurements have pages, plugins can attach to them, and the
plugins removed under the earlier ruling become buildable again.

## Revisit if

A record kind appears that is genuinely a value rather than a record — something with no identity of
its own, no contributors and nothing to audit. That is a real category, and it should be modelled as
a field on its owner rather than given a page it does not need.
