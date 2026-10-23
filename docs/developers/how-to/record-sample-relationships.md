# How to record sample relationships

A sample relationship records that one sample came from another, such as a subsample cut from a core. You record it in code when you load samples from a script or build them in a view.

To record one by hand in the administration interface, see [How to record that a sample came from another sample](../../administrators/how-to/record-where-a-sample-came-from.md).

## Before you start

Both samples must already be saved. This guide uses `core` for the parent and `section` for the child, both samples of any registered type.

## Steps

1. Create a `SampleRelation` with the child as `source` and the parent as `target`.

   ```python
   from fairdm.core.sample.models import SampleRelation

   SampleRelation.objects.create(source=section, target=core, type="child_of")
   ```

   `child_of` is the only relationship type. The relation has no field for the reason, so put that in a description of the child.

2. Read the relationship from either sample.

   ```python
   core.get_children()       # samples cut from the core
   section.get_parents()     # samples the section came from
   ```

3. Follow the chain further with `get_descendants()` and `get_ancestors()`. Pass `depth` to stop early.

   ```python
   core.get_descendants()          # children, grandchildren and so on
   core.get_descendants(depth=1)   # direct children only
   section.get_ancestors(depth=2)  # parents and grandparents
   ```

4. Find samples across the whole table with `by_relationship()`.

   ```python
   from fairdm.core.sample.models import Sample

   Sample.objects.by_relationship(related_to=core)           # the children of core
   Sample.objects.by_relationship(relationship_type="child_of")  # every sample in any such relation
   ```

   Each method returns a queryset of `Sample` objects, and each result is an instance of its own type.

## The result

The relationship is saved, and the sample's page lists its parents and subsamples. The methods are listed on [Sample model](../reference/sample-model.md#methods).

`SampleRelation` refuses three things, on `save()` as well as in a form:

- A sample related to itself.
- A link whose reverse already exists with the same type. If `section` is a child of `core`, `core` cannot be recorded as a child of `section`.
- The same source, target and type saved twice.

The first two raise a `ValidationError`. The third is refused by a unique constraint, which raises an `IntegrityError` on `save()` and a validation error in a form.
