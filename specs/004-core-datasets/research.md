# Research — 004 The dataset record

Five questions the plan could not answer from the specification alone. Each was settled by reading
the code or the framework, not by preference.

## R1 — What a privacy-first default manager changes, beyond `Dataset.objects`

**Question.** FR-019 requires the ordinary way of reading datasets to exclude private ones.
`DatasetManager` already implements that and is commented out. What else moves when it is switched
on?

**Finding.** Django resolves several things through `Model._default_manager`, which is the first
manager declared. Verified against this repository:

- `ModelAdmin.get_queryset()` calls `self.model._default_manager.get_queryset()`. A privacy-first
  default manager therefore **hides private datasets from the administrative interface**, which
  contradicts US-6 directly — the admin is where a portal is repaired, and an unfinished dataset is
  exactly what an administrator needs to reach.
- A reverse many-to-one manager is built from `related_model._default_manager.__class__`, so
  `project.datasets.all()` would stop returning private datasets. That is right for portal surfaces
  and wrong for the deletion guard, which counts what is attached.
- Forward relations and the deletion collector use `Model._base_manager`. Today that is an
  automatically created plain manager, so cascades and `dataset.project` are unaffected.

**Decision.** Three parts, which is what Django's own guidance for a filtered default manager asks
for:

1. `objects = DatasetManager()` — privacy-first, first declared, so it is the default.
2. `all_objects = DatasetQuerySet.as_manager()` — the explicit, unfiltered route.
3. `Meta.base_manager_name = "all_objects"` — so related-object access and the deletion collector
   keep seeing every row. Without it, following a relation to a private dataset can raise
   `DoesNotExist`.

`DatasetAdmin.get_queryset()` is overridden to use `all_objects`. The administrative interface
seeing private datasets is a requirement, not an oversight, and the override is where that is said
out loud.

**What `with_private()` becomes: nothing.** It is removed, and this is the part worth stating
plainly. Once the exclusion lives in the manager it is already in the SQL by the time a caller holds
a queryset, and no method can take it back out. The present implementation "solves" that by
rebuilding from the model — which is exactly why
`Dataset.objects.filter(project=p).with_private()` returns every dataset in the table.

There is no correct implementation of the method, only correct entry points. `Dataset.objects` is
the ordinary one and `Dataset.all_objects` the explicit one, and a caller chooses before narrowing
rather than after. FR-019 is written to forbid the shape rather than to require the method, because
a widening that silently discards the caller's conditions is worse than no widening at all.

`get_visible()` and `for_user()` go with it. With two visibility levels, `get_visible()` and the
manager's own exclusion select the same rows, so it is a second name for the default. `for_user()`
has no callers and gates on `dataset.view_private`, a permission no model declares, so it can never
return anything but the public set.

## R2 — How the collection-period check is written

**Question.** FR-011 refuses a collection end earlier than the collection start. Is there a pattern
to follow?

**Finding.** Yes, and it is recent and tested. `ProjectDate.clean()`
(`fairdm/core/project/models.py:196-250`) compares against the sibling record rather than within one
instance, because the two dates are two rows. It handles the awkward part: `PartialDate` mixes
precision into its ordering, so two values of different precision cannot be compared directly. Its
`_precedes()` compares at the coarser of the two precisions — years only if either is
year-precision, year and month if either is month-precision, the full date only when both carry day
precision.

**Decision.** `DatasetDate` follows it with `START_TYPE = "CollectionStart"` and
`END_TYPE = "CollectionEnd"`. The comparison helpers are duplicated rather than lifted to
`AbstractDate`: Article III forbids an abstraction without a present second use, and this is the
second use of the *pattern*, not of a shared implementation — samples and measurements carry
different date vocabularies and no equivalent pair. Lifting it becomes right at the third.

## R3 — What the dataset identifier collection contains, and how a collection is declared

**Question.** FR-012 requires an identifier set that applies to datasets. What goes in it and how is
it declared?

**Finding.** `FairDMIdentifiers` (`fairdm/core/vocabularies.py:6`) is a `VocabularyBuilder` whose
`Meta.collections` maps a name to a `Collection` listing member attribute names. `003-core-projects`
added a `Project` collection with `DOI`, `GRANT_NUMBER` and `PROPOSAL_ID`. Binding is
`FairDMIdentifiers.from_collection("Dataset")`, matching how `DatasetDate` and `DatasetDescription`
already bind theirs.

`DOI` is already a member, defined with a definition that reads "a persistent, resolvable link to a
project record" — written for projects and now shared, so its wording needs generalising.

**Decision.** The collection contains `DOI` alone. The old model docstring named "DOI, ARK,
Handle, etc."; both were considered and neither is added, because nothing in the repository or the
roadmap uses them and an unused member is a wrong choice offered to every user. A second scheme is a
three-line addition when one is asked for.

`Dataset.IDENTIFIER_TYPES` moves from `FairDMIdentifiers().choices` to the collection, so the class
attribute and the related model agree.

**The trap this closes.** `GenericModel.__init_subclass__` assigns `cls.type.field.choices` from the
`VOCABULARY`, and Django does not validate `choices` on save. So a row written through
`objects.create()` with any string at all persists silently, which is why the existing suite has
tests using `"Created"` and `"ARK"` as valid values when neither is a member. Tests for this
requirement assert the collection's members **by name**; a test that iterates `VOCABULARY.choices`
proves nothing, since it passes over an empty collection.

## R4 — Seeding the recommended licences

**Question.** FR-007a requires a portal to have the recommended licences without loading them by
hand. Through what mechanism?

**Finding.** `django-content-license` ships `fixtures/creativecommons.json.gz` — seven rows, the six
Creative Commons 4.0 variants plus CC0 1.0 — and no data migration. It declines to curate licences
on purpose. Nothing in FairDM loads it, so a migrated portal has an empty `License` table.

FairDM configures a deployment pipeline at `fairdm/conf/settings/apps.py:254-282` through
`django-setup-tools`: `on_initial` loads the `django-waffle` and `groups` fixtures, `always_run`
calls the vocabulary package's `preload`. Three precedents of the same shape.

`License.name` is `unique=True`, so it is a usable natural key. The fixture's rows carry integer
primary keys, so `loaddata` would collide with a portal that already created a licence at that key —
`get_or_create` on `name` would not.

**Decision.** A management command, `always_run` in the pipeline beside `preload`, creating CC0 1.0,
CC BY 4.0 and CC BY-SA 4.0 through `get_or_create` on `name`. The NC and ND variants are not seeded:
they fail the Open Definition, and a framework named for reusability should not present "no
derivatives" as a recommendation for research data.

Not a data migration. Which licences a portal offers is the portal's decision — the same reasoning
that keeps content-license out of curation — and a pipeline entry is a default a portal can drop,
where a migration is not. A licence row is also editable content with an administrative interface,
and content does not belong in schema history.

The pipeline is not currently invoked by anything (#193). That is the pipeline's defect and does not
change which mechanism is correct.

## R5 — Whether the second names on the related records can be removed

**Question.** FR-014 removes the property aliases (`description_type` for `type`, `date` for
`value`, and the rest). Their docstrings claim "API compatibility". Is anything relying on them?

**Finding.** No. Grepping the package, the demo and the templates finds no reader outside the
dataset app itself. The REST API exposes five scalar fields on a dataset (`fairdm/api/viewsets.py:128`)
and none of these related records, so the compatibility they are named for does not exist. No other
core model has them — `ProjectDate`, `SampleDate` and their siblings carry the field names alone.

Two things do write through them: `DatasetDescriptionFactory` and `DatasetDate` in
`fairdm/factories/core.py`, and `DatasetFilter.date_type`, which uses one as an ORM path
(`field_name="dates__date_type"`) and raises `FieldError` on every application because a property is
not a column.

**Decision.** Removed. The factories move to the real field names. The broken filter is not repaired
here — it belongs to the filter set, which this specification does not own, and it is filed as #186
with the alias removal named as its cause.
