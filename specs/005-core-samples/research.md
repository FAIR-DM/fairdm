# Research — 005 The sample record

Four questions the specification deferred, settled against primary sources and against the code
rather than assumed. Dates are 2026-08-18/19.

## R1 — What format should a stored IGSN be validated against?

**Answer: there is no stable IGSN pattern. Validate as a DOI, case-insensitively, and accept the
legacy Handle form.**

IGSN allocation moved to DataCite. IGSN e.V. announced the migration complete on 2023-09-27
(https://ev.igsn.org/news): "All new IGSN IDs will be registered in the DOI system through
DataCite", with legacy Handles resolvable "for the foreseeable future". DataCite's own announcement
(https://datacite.org/blog/igsn-and-datacite-partnership/, 2021-10-28) says existing Handles were
"aliased to the DOIs to ensure that these continue to resolve". Confirmed live against the Handle
API: `10273/BGRB5054RX05201` returns an `HS_ALIAS` record pointing at `10.60510/BGRB5054RX05201`.

**An IGSN is now an ordinary DataCite DOI, and they are spread across many prefixes.** Querying the
DataCite API for repositories of type `igsnCatalog` returns 38 repositories, 38 distinct DOI
prefixes and about 13.9 million registered IGSN DOIs. `10273` is not among them. DataCite expects
the count to grow — its registration guide requires a separate catalog repository, and therefore a
separate prefix, per IGSN registry, and its setup guidance says one organisation may hold several.

So a prefix-anchored regex is structurally wrong, not merely out of date. Sampling 687 real IGSN
DOIs across all 38 catalogs shows the shipped pattern `^10273/[A-Z0-9]{9,}$` fails on every clause:

| Clause | Verdict |
|---|---|
| `10273/` prefix | rejects every IGSN currently in circulation |
| `[A-Z0-9]` only | 25.5% of suffixes carry a hyphen, a dot or a forward slash |
| `{9,}` | observed suffix lengths run 7–23; `10.60516/AU1101` has six |
| case-sensitive | DOIs are case-insensitive; DataCite's API lowercases and doi.org uppercases the same identifier |

Real values, each retrieved from a source page: `10.58052/SSH000SUA` (SESAR),
`10.60510/BGRB5054RX05201` (GFZ), `10.58108/CSRWA275` (CSIRO), `10.71928/M-202600319-N00325`,
`10.25706/DIGITALCSIC-IGSN/622135` — the last carrying a slash inside its suffix, so parsing must
not split on `/` more than once.

**Rule adopted.** Normalise away `https://doi.org/`, `https://igsn.org/`, `hdl.handle.net/`, `doi:`
and `igsn:`; then accept `^10\.\d{4,9}/\S+$` case-insensitively, or the legacy `^10273/\S+$`. Do
not constrain the suffix. A regex cannot distinguish an IGSN from any other DOI — only resolving
against `api.datacite.org` and checking `resourceTypeGeneral == "PhysicalObject"` can, and that is
a network call this record does not make.

Not established: whether any IGSN was issued under `10273` and never migrated. Both organisations
call the migration complete; neither publishes a reconciliation count.

## R2 — Why object permissions fail on a specimen type, and how to fix it

**Answer: normalise the object to its base instance before the guardian check, in one shared
backend, and take raw guardian out of the backend chain.**

Verified against a live database rather than inferred:

| Call | Result |
|---|---|
| `assign_perm("change_sample", user, rock_sample)` | `Permission.DoesNotExist` |
| `assign_perm("change_sample", user, rock_sample.get_non_polymorphic_instance())` | succeeds |
| `user.has_perm("sample.change_sample", rock_sample)` | `WrongAppError` |
| `user.has_perm("sample.change_sample", rock_sample.get_non_polymorphic_instance())` | `True` |

The mechanism: permissions are declared on `Sample`, app label `sample`; a portal's specimen type
lives in its own app, so `RockSample` has app label `fairdm_demo`.
`guardian.backends.ObjectPermissionBackend.has_perm` compares the permission's app label against
both the instance's app label and its content type's, and raises when neither matches
(`guardian/backends.py:99`). `WrongAppError` subclasses `GuardianError`, not `PermissionDenied`, so
Django's `_user_has_perm` does not catch it.

`SamplePermissionBackend` sits at position 5 in `AUTHENTICATION_BACKENDS`
(`fairdm/conf/settings/auth.py:47`), behind raw guardian at position 3. **It is never reached for a
specimen type, so its whole permission map is dead code.** `OrganizationPermissionBackend` at
position 4 delegates any non-organisation object straight back into the same guardian path, so
reordering alone cannot fix it — a denial still falls through to a raising backend.

On the assignment side the failure is different from what the skipped tests claim: guardian
resolves the content type of `RockSample`, then looks for a `change_sample` permission under it.
That row does not exist, because `change_sample` belongs to the `sample.sample` content type. The
skip reasons in both the sample and the measurement test files misattribute this to `WrongAppError`.

Options weighed and rejected:

- **Check under the subclass's own app label** (`fairdm_demo.change_rocksample`) — breaks dataset
  inheritance, and the four permissions declared in `Sample.Meta.permissions` do not exist for
  subclasses at all, since Django `Meta` is not inherited in multi-table inheritance. `import_data`
  would become unassignable.
- **Reorder the backends** — fixes the granted path only; denials still reach a raising backend.
- **Catch `WrongAppError` in the sample backend** — the backend is never reached, and the
  permission row cannot be stored anyway.
- **`GUARDIAN_GET_CONTENT_TYPE`** — fixes both sides globally, but retargets every guardian call and
  breaks the API's subclass-scoped permission scheme.
- **Direct foreign-key permission models** — guardian selects them by content type, so one declared
  against `Sample` would not be chosen for a `RockSample`. Every portal type would need its own
  table.

**Adopted:** a guardian-derived backend that normalises the object through the existing
`get_non_polymorphic_instance` helper (`fairdm/core/utils.py:28`) **only when** the permission's app
label mismatches the instance's own but matches its polymorphic base's. The gate matters: applied
unconditionally, `Organization` would normalise to `Contributor` and orphan every existing
organisation permission. Raw guardian leaves the backend chain so that no backend can delegate
around the normalisation, and the sample, measurement and organisation backends re-parent onto it.

Measurements carry the identical defect and inherit the fix. That is not scope creep — the fix is
one shared backend and cannot be written for samples alone without leaving a blind delegator in
front of it.

## R3 — Vocabularies: enumeration, the identifier collection, and the status replacement

**Why the validators raise.** `VocabularyBase.__iter__` returns `self.choices`, which is a list, not
an iterator, so `for item in self.VOCABULARY` raises `TypeError: iter() returned non-iterator of
type 'list'` before the loop body runs. The subscript `item["id"]` was wrong too — `choices` holds
`(name, label)` tuples — but it never executes. The repo's own idiom is `VOCABULARY.values`, used at
nine sites including `fairdm/factories/core.py:498` and `:528` for these very models.

Projects and datasets do not perform this check at all. Membership there is enforced by the choices
Django attaches in `GenericModel.__init_subclass__` (`fairdm/core/abstract.py:248`). That makes the
three `clean()` bodies partly redundant with the field-level validator — worth noting, but the
specification requires a validation verdict with a message naming the type, which the field-level
validator alone does not give.

**Adding IGSN and a sample collection.** A member is declared as a dict attribute on
`FairDMIdentifiers`; the attribute name becomes the stored database value. A `Sample` collection
with members `["IGSN", "DOI"]` goes in `Meta.collections`, and `SampleIdentifier.VOCABULARY` becomes
`FairDMIdentifiers.from_collection("Sample")`. The single-member `choices` workaround already in
that file does not apply to a two-member collection and stays only for the `Dataset` one.

Loose end: `IdentifierLookup` (`fairdm/contrib/contributors/choices.py:39`) has no IGSN or DOI key,
so `get_root_url()` returns `None` for both. Adding IGSN without an entry leaves a specimen's
identifier unlinked.

**What a `ConceptField` stores.** The concept's local name, as plain text in a `CharField`, with
`max_length` derived from the longest member name — which is why the column is `max_length=8` today
and becomes 9 once `destroyed` is a member. Reading a row whose stored value is absent from the
field's vocabulary raises `ValueError` from `from_db_value`, including through `values_list`.

**Consequences for the status change.** The data migration is mandatory, not tidiness: leaving
`complete`, `ongoing` or `planned` in the column makes every subsequent read of those samples throw.
It must rewrite through `QuerySet.update()` or raw SQL, never by iterating instances, because
iterating invokes the very conversion that raises. The column exists only on the base table, so one
statement covers every specimen type.

The replacement is a `VocabularyBuilder` in `fairdm/core/vocabularies.py`, matching the other four,
rather than an `IntegerChoices` — the field is already a `ConceptField`, and SKOS gives each custody
state a definition, which is what makes the vocabulary readable. Two mechanical points the current
class gets wrong: `Meta.name` is unset, which is why the status filter queries an empty vocabulary
name and is permanently blank; and the "unknown" member must keep its lowercase name for the
existing default to survive.

**The remote fetch is a startup cost, not a lazy one.** `ConceptField.__init__` instantiates the
vocabulary in the `Sample` class body, so the ODM2 graph is fetched while Django loads apps, and
again during `makemigrations` and `migrate`. It is cached in Redis with no expiry, so a warm cache
hides it. There is no timeout on the fetch and only `HTTPError` is handled — a hung socket takes app
loading with it. This is the repository's only `RemoteVocabulary`; removing it removes the surface
entirely.

**Four incompatible status vocabularies are live in the tree at once**: what the code fetches
(complete, ongoing, planned, unknown), what the form and two tests assert (`available`), what the
administrator documentation describes (Available, Used, Archived, Destroyed, Loan), and what this
specification requires. Two tests contradict each other directly and both pass, because an unsaved
instance holds a plain string while a loaded one holds a concept, and concepts define no equality.

## R4 — The filter mixin, and blocking the base record

**The filter mixin.** django-filter collects declared filters in its metaclass, from the class body
and from any base carrying `declared_filters`. A plain mixin has neither, so its declared filters
are inert class attributes. Its `__init__` still runs through the method resolution order, which is
why the dataset-queryset widening works and only the declared filter is lost.

The repository already has the right pattern: `BaseListFilter` (`fairdm/core/filters.py:7`) is a
`FilterSet` subclass with no `Meta` at all, declaring the same `image` filter character for
character. Projects and datasets inherit it and receive the filter; the sample mixin is a copy of it
into a plain class, where it stopped working. Omitting `Meta` is what makes it usable as an abstract
base — the metaclass short-circuits before it can complain about a missing `fields`.

For the registry, `TableFactory` already solves the identical problem with a
`get_base_table_class()` hook that returns a sample or measurement base by model. `FilterFactory`
hardcodes `FilterSet` instead. The change is the same hook, one class over. Its `except Exception`
fallback path takes no base class, so a model that trips it silently loses the mixin.

`MeasurementFilterMixin` is a plain class too. It declares nothing today, so nothing is lost — but
the first filter added to it disappears silently.

**Blocking the base record.** django-polymorphic constructs base instances on every read:
`_get_real_instances` fetches base-class rows first and then upcasts them by content type. So a
guard in `__init__` or `__new__` would fire on the framework's own read path and break every sample
query. On the write side polymorphic only wraps `save()` to set the content type, and never
constructs or saves a base instance, so a write-side guard is safe.

| Guard | Catches | Misses |
|---|---|---|
| `save()` override | direct save, `objects.create()`, forms, admin, factories | fixture loading, `bulk_create` |
| `pre_save` receiver with `sender=Sample` | all of the above **and** fixture loading | `bulk_create`, `update`, raw SQL |
| manager `create()` override | `objects.create()` only | everything else |
| `Meta.abstract` | everything | impossible — relations require the concrete table |
| database check constraint | everything | content type ids are not portable across installs |

A `pre_save` receiver is the only single mechanism covering fixture loading, because Django sends
`pre_save` even for raw saves, and it scopes itself correctly: a subclass instance sends its own
class as sender, so the receiver never fires for one. `Sample.clean()` stays alongside it, so that
forms and the administrative interface produce a validation error rather than a server error.

**The cost is in the factories, not the guard.** `SampleFactory` declares the base model, and two
other factories reach it without naming it — `MeasurementFactory.sample` and both ends of
`SampleRelationFactory`. Base-sample creation reaches 218 test functions. Two edits carry about 215
of them: retargeting the sample factory, and the plugin test fixture that calls
`Sample.objects.create` directly. The rest need a re-run, not an edit.
