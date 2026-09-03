# ADR 0016 — The framework indexes the fields it searches by default

**Status:** accepted

## Decision

A registration declares which of its type's fields search covers. Where it declares none, search
covers the record's name.

The framework indexes what it searches by default, and no further. A field a model author names in
`search_fields` is the author's to index, and the documentation says so.

A declared path that names no field, or that resolves to a field a substring match cannot read, is
refused when the server starts rather than on the first search a visitor types.

## Why

**The declaration and the schema are the parts that cannot be retrofitted.** A better search
mechanism can be dropped in later over types that have already said what searching them means. It
cannot be dropped in over types that have not, and adding indexes to a populated portal is a
migration nobody wants to run.

**The matching itself is one mechanism serving every listing.** Ranking, tolerance of partial or
misspelled words, and search spanning more than one record type belong to that mechanism when it is
built. Building a lesser version of it per listing is how a portal ends up with two.

**Enforcing the index obligation would fire on correct code.** Refusing a registration over a
performance property means the framework rejecting a model that works. Stating the obligation in
the documentation puts it where the author making the decision will read it.

**Refusing a bad declaration at start-up rather than at search time** is the difference between a
misconfiguration the developer sees immediately and one a visitor finds. Searchability is a
question about a field's type: a substring match reads text, so a number, a boolean, a date or a
geometry is refused. It cannot be asked as a question about lookups, because Django registers
`icontains` on every field type there is.

## Consequences

Search behaviour is a property of a registration, readable from it without running anything.

A portal that adds a searchable field and no index gets a sequential scan, and that is the portal's
call to make. The framework does not prevent it.
