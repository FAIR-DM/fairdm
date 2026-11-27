# ADR 0006 — What the registry generates carries the framework's mixins

**Status:** accepted

## Decision

The form and filter set the registry generates for a registered type are built on the framework's
mixins for that record kind. A portal that registers a sample or measurement type and writes neither
a form nor a filter class still receives the mixins' widgets, dataset scoping and declared filters.

A portal that supplies its own form or filter class inherits from the same mixins, so both routes
converge on one behaviour.

## Why

A mixin that only reaches developers who write their own classes reaches precisely the people who
needed it least. The whole point of registration is that a type gets a working interface without
writing one, so the generated path is the one that has to carry the behaviour — the hand-written
path can always add to it.

This was already true for samples and had never been true for measurements. Registering a
measurement type produced a form with none of the framework's field configuration and a filter set
carrying only the filters derivable from the model's own fields. The gap was invisible because
nothing failed: the generated components existed, worked, and were simply poorer than the ones the
documentation described.

The rule generalises past these two record kinds. Any future record kind the registry generates for
inherits the same obligation, and the test that a portal's registered type gets the framework's
behaviour belongs beside the registry rather than beside each record kind.

## Revisit if

A record kind needs generated components that deliberately differ from what a hand-written class
gets. That would be a real divergence rather than an oversight, and it should be stated on the
record kind rather than left as a missing wire.
