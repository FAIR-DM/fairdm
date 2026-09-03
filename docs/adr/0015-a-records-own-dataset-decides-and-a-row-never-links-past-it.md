# ADR 0015 — A record's own dataset decides, and a row never links past it

**Status:** accepted

## Decision

A record appears in a listing if and only if the dataset it belongs to is published. No rule
reaches through a relation to decide presence.

Separately, where a row would name or link a record the visitor cannot read, it shows neither the
name nor the link. The cell keeps its place and carries a placeholder that names nothing: the
sample column reads `Unpublished`, and the dataset column keeps its icon without the anchor around
it. What must not survive is the record's own name and its address.

The same test governs every choice list a filter offers. A filter is a second way to read a
listing, so a name withheld from a cell must not be available from a dropdown beside it.

## Why

**Deciding by the record's own dataset is the only rule that stays true as the graph grows.** A
measurement may belong to a different dataset than the sample it was made on: provenance crossing
dataset boundaries is a principle here, not an accident. Any rule that reaches through a relation
has to be re-derived for every relation added afterwards, and the version that was not re-derived
is the one that leaks.

**The link half is the part that is easy to miss.** Without it, a listing that correctly excludes
an unpublished sample from the sample listing hands out that sample's name and address from the
measurement listing instead. Membership of a listing must never become a route to a record that is
not itself readable.

**"Cannot read" is wider than "not published".** Since publication is independent of visibility
(ADR 0014), the common shape is a published but private dataset. Its records belong in every
listing, and the dataset column on those rows would otherwise link to a page the same visitor is
refused. The rows stay, because publication alone decides presence. The link does not.

## Consequences

Every column that renders a related record applies the same test the sample and dataset columns
apply. A new linked column added later without it is a leak, not a cosmetic omission.

A placeholder in a listing is a meaningful state, not missing data, and is worth reading as "there
is a record here you may not read".

Filter choice lists are scoped where the listing resolves its filter set, not where the framework
generates one. A registration may supply its own filter set or build it in a method of its own,
and a rule enforced only inside the generator does not reach either.
