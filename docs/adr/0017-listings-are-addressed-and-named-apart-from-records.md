# ADR 0017 — Listings are addressed and named apart from records

**Status:** accepted

## Decision

A type's listing lives under an address prefix of its own, distinct from the record addresses ADR
0010 governs, and its URL name follows the `<name>-list` convention the portal's other listings
already use.

Two registrations that would resolve to the same listing address are refused when the server
starts, with an error naming both types and the address they contend for.

## Why

**A listing is not a record, so ADR 0010 does not reach it.** Folding listings in beside the record
addresses would put a slug and an identifier at the same position in the path, which reads as one
scheme and behaves as two.

**The naming convention is the part with an argument against it.** Renaming existing view names is
churn with nothing visible to show for it. It is done anyway, because a break with the repository's
own convention is a defect rather than a preference, and the whole cost is one reverse lookup per
caller.

**A silent collision is the worst outcome.** Two types whose models share a name would otherwise
give one of them a listing and the other nothing, with no error anywhere. Refusing at start-up
turns it into a message naming both.

## Consequences

Reverse a listing by `<name>-list`. Nothing constructs a listing address as a string.

A caller left on an old view name does not fail loudly: the menu library swallows the resulting
lookup failure and logs a warning. Renaming a listing means finding its callers rather than waiting
for something to break.
