# Migration Guides

Step-by-step instructions for upgrading past a breaking change. Each section covers one feature
branch; read the one that matches what changed under you.

## 005 — The sample record (status, identifiers, factories, permissions)

This feature rewrote several parts of the `Sample` record that were shipped broken: the status
vocabulary, the identifier vocabulary, direct-creation of the base `Sample`, and object-level
permissions on a specimen. If your portal has data or code touching any of these, read the
matching section below before you upgrade.

### Sample status: every value becomes "unknown" — irreversible

`Sample.status` previously drew its terms from a vocabulary fetched over HTTP from
`vocabulary.odm2.org` (`complete`, `ongoing`, `planned`, `unknown`) — terms that describe a
data-collection activity, not where a physical specimen is. It now draws from a local vocabulary
of custody states: `available`, `in_use`, `stored`, `destroyed`, `unknown`.

None of the old terms maps onto a custody state — nothing in the data says whether a sample
recorded as `"complete"` is available, in use, or something else — so there is no mapping to
apply. Migration `sample.0008_migrate_sample_status_to_unknown` rewrites **every** sample's
`status` to `unknown`, unconditionally, and its reverse operation is a no-op: the previous values
are discarded and cannot be reconstructed after the migration runs.

**Before you migrate:**

1. If you need a record of what each sample's status was before the change, export it first —
   for example:

   ```python
   import csv
   from fairdm.core.sample.models import Sample

   with open("sample_status_backup.csv", "w", newline="") as f:
       writer = csv.writer(f)
       writer.writerow(["uuid", "name", "status"])
       for sample in Sample.objects.values_list("uuid", "name", "status"):
           writer.writerow(sample)
   ```

   Run this against your production database **before** deploying the migration — once it has
   run, the old values are gone.
2. Decide whether any of your portal's own code reads `sample.status` and compares it against
   `"complete"`, `"ongoing"`, `"planned"`, or `"available"` as a form default. All four break:
   the first three are no longer valid vocabulary members at all (reading a row that still held
   one raised `ValueError` even before this migration, since a `ConceptField` cannot decode a
   value outside its current vocabulary), and `"available"` was never a real member of the old
   vocabulary in the first place — the form that defaulted to it was itself a defect.
3. Update any of your own code, filters, or reports built against the old four-term vocabulary
   to use the new five: `available`, `in_use`, `stored`, `destroyed`, `unknown`.

**After you migrate**, every sample reads as `unknown` until someone sets it explicitly. A status
can move to any other status from any status, including back out of `destroyed` — there is no
terminal state.

### `SampleFactory` is now abstract

`fairdm.factories.SampleFactory` no longer builds a bare `Sample` — nothing does, by any route
(see below). If your portal's test suite calls `SampleFactory()` directly, or relies on
`MeasurementFactory()` or `SampleRelationFactory()` picking a sample on your behalf, both broke:
`MeasurementFactory.sample` and both ends of `SampleRelationFactory` lost their defaults along
with the base factory.

**What to do:**

1. Write a concrete factory for each of your own specimen types, subclassing
   `fairdm.factories.SampleFactory` the way `fairdm_demo.factories.RockSampleFactory` does:

   ```python
   from fairdm.factories import SampleFactory
   from myapp.models import RockSample

   class RockSampleFactory(SampleFactory):
       class Meta:
           model = RockSample
   ```

2. Replace every `SampleFactory(...)` call in your own tests with your own concrete factory.
3. Pass a concrete sample explicitly wherever you previously relied on a default:

   ```python
   # Before
   measurement = MeasurementFactory()

   # After
   measurement = MeasurementFactory(sample=RockSampleFactory())
   ```

See [Custom Samples](../portal-development/models/custom-samples.md#testing-custom-samples) for
the full pattern.

### The base `Sample` record can no longer be created, by any route

Creating a bare `Sample` — through `Sample.objects.create()`, `.save()`, a form, the admin, or
fixture loading — now raises `ValidationError` unconditionally. Only a registered specimen
subclass (`RockSample`, `WaterSample`, your own type) can be created. If any of your portal's own
code, fixtures, or data migrations construct a base `Sample` directly, it will start failing.

Search your codebase for `Sample.objects.create(`, `Sample(` followed by `.save()`, and any
fixture file with `"model": "sample.sample"` (rather than your own subclass's model label), and
retarget each at a concrete specimen type.

### Sample identifiers: vocabulary narrowed to IGSN and DOI, plus normalisation

`SampleIdentifier`'s type vocabulary previously drew from the same set used for people,
organisations and projects (ORCID, ResearcherID, ROR, Wikidata, ISNI, a funder identifier, a
grant number, a proposal identifier) — none of which names a specimen, and it had no IGSN member
at all. It is now its own collection, containing exactly **IGSN** and **DOI**.

**Before you migrate:**

1. Check whether any sample in your database carries an identifier of one of the old, now-invalid
   types. The type field is a plain `CharField` — Django does not validate choices on save — so an
   existing row can hold a stale type that would now fail `full_clean()`. Query for it:

   ```python
   from fairdm.core.sample.models import SampleIdentifier

   valid = set(SampleIdentifier.VOCABULARY.values)  # {"IGSN", "DOI"}
   stale = SampleIdentifier.objects.exclude(type__in=valid)
   ```

   There is no automatic migration for these — decide per record whether to retype, delete, or
   leave them (they remain readable; only re-validating them via `full_clean()` will now fail).

2. If your portal code creates `SampleIdentifier` rows with `type="barcode"` or any other type
   outside `{"IGSN", "DOI"}`, that type is no longer valid. A local lab barcode belongs in
   `local_id` on the sample itself, not in the identifier vocabulary.

**Two behaviours are new and apply to every identifier value**, not only samples:

- **Normalisation.** A common display prefix — `https://doi.org/`, `http://doi.org/`,
  `https://igsn.org/`, `hdl.handle.net/`, `doi:`, `igsn:` — is stripped before the value is
  compared or stored. If your code stores or compares raw identifier strings including one of
  these prefixes, it now sees the stripped form.
- **Global uniqueness.** An identifier value must be unique across every record type that
  carries identifiers — project, dataset, sample and measurement — not only within samples. If
  your portal (or its test data) reused an identifier value across two different record types,
  that reuse now fails validation.

IGSN's own format check changed too: IGSN allocation moved to DataCite in 2023, so there is no
longer a single prefix or suffix pattern. An IGSN now validates as any DataCite DOI
(`10.NNNN/…`, case-insensitive) or the legacy `10273/…` handle. If your portal validated IGSNs
against the old `^10273/[A-Z0-9]{9,}$` pattern in its own code, that pattern now rejects real,
currently-issued IGSNs and should be removed in favour of the record's own validation.

### The authentication backend swap — retarget any direct guardian calls

`guardian.backends.ObjectPermissionBackend` is no longer in `AUTHENTICATION_BACKENDS`.
`fairdm.core.permissions.PolymorphicObjectPermissionBackend` replaces it, and
`SILENCED_SYSTEM_CHECKS = ["guardian.W001"]` is set because the warning that backend would
otherwise raise no longer applies — every backend in the chain derives from the replacement.

This matters because a permission declared on a polymorphic base (e.g. `sample.change_sample`)
could never be checked or granted correctly against a specimen subclass instance before this
change — `guardian.backends.ObjectPermissionBackend` raised `WrongAppError` on the check side, and
`guardian.shortcuts.assign_perm` filed the grant under the wrong content type on the assignment
side. Both are now fixed, but only when the call goes through FairDM's own helpers.

**If your portal code calls `guardian.shortcuts.assign_perm`, `remove_perm`, `get_perms`, or
`get_objects_for_user` directly against a sample, a measurement, or an organisation/person,
switch it to the matching function in `fairdm.core.utils`:**

```python
# Before
from guardian.shortcuts import assign_perm
assign_perm("change_sample", user, rock_sample)   # silently files under the wrong content type

# After
from fairdm.core.utils import assign_perm
assign_perm("change_sample", user, rock_sample)   # normalises to the record that owns the permission
```

The same substitution applies to `remove_perm`, `get_perms`, and `get_objects_for_user`. Calls
against a non-polymorphic model (a plain `Dataset`, for instance) are unaffected either way — the
FairDM helpers are safe to use everywhere, since they only normalise the object when the
permission actually needs it.

### Sample editing pages now require a permission

The Edit, Descriptions, Keywords and Key Dates plugins on a sample previously admitted every
request, including an anonymous one — no permission was declared, and the framework treats an
undeclared permission as "open to everyone". They now declare `permission = "sample.change_sample"`.

If your portal built its own view, template, or link assuming these surfaces were reachable
without authorisation, that assumption no longer holds. Grant `sample.change_sample` (directly, or
by inheritance from `dataset.change_dataset` on the sample's dataset) to whichever users or groups
should retain access, using `fairdm.core.utils.assign_perm` as shown above.
