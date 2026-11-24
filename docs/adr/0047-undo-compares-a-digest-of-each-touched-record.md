# ADR 0047: Undo compares a digest of each touched record

**Status:** accepted

## Decision

When an import adds or changes a record, it stores a SHA-256 digest of every concrete field's
stored value, taken inside the import's transaction after the save. For a changed record it
also stores the values it replaced. An undo of that import recomputes the digest of each
record it touched. If any record is missing or has a different digest, or a sample the import
added now has measurements, the undo is refused and changes nothing.

Because `modified` is one of the hashed values, any save, even one that changes no value, counts
as a change since the import.

## Why

A record's `modified` time alone is not enough: a queryset `update()` changes values without
moving it, and a deleted record has no time left to compare. A digest of the stored values
catches both. The undo can then promise that it never removes or reverts work done after the
import.

## Revisit if

A field is added whose stored value changes without anyone editing it, which would refuse undo
for records nobody touched.
