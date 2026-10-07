# Migration Guides

Step-by-step instructions for upgrading past a breaking change. Each section covers one change;
read the one that matches what changed under you.

## 024 - A record's editing pages are six shared pages

A project, a dataset, a sample and a measurement are now edited and deleted through six pages
that are written once and registered on all four: edit details, descriptions, keywords, key
dates, identifiers and delete. See [Record editing pages](../portal-development/record-editing-pages.md)
for what each page does. The pages they replace are removed, and no redirect is left behind.
Nothing in the database changes. Check your portal's own code for these:

- **URL names on projects and datasets**: `project:overview-update`, `project:overview-descriptions`,
  `project:overview-delete` and the same three on `dataset` no longer exist. Reverse
  `project:edit`, `project:descriptions` and `project:delete` instead, and the same names on
  `dataset`. The update address moves from `<record address>/update/` to
  `<record address>/edit/`, so a link written by hand to `/update/` now answers 404.
- **URL names on samples**: `sample:basic-information` no longer exists. Reverse
  `sample:descriptions` for the descriptions page and `sample:edit` for the sample's own
  fields. `sample:keywords` and `sample:key-dates` keep their names and addresses and now serve the
  shared pages. A measurement has all six names in the `measurement` namespace.
- **Classes you subclassed**: `UpdatePlugin` and `DeletePlugin` (in `fairdm.core.plugins`) and
  `DescriptionsPlugin`, `KeyDatesPlugin` and `KeywordsPlugin` (the module
  `fairdm.contrib.generic.plugins`, which no longer exists) are gone, with the project, dataset
  and sample `Update`, `Edit`, `Descriptions`, `Keywords`, `KeyDates` and `Delete` plugins. A page
  of your own that edits or deletes a record builds on `FairDMUpdateView` or `FairDMDeleteView`
  together with `Plugin`. To change what the shared pages do, subclass the class in
  `fairdm.core.editing` and register it for your model. The project and dataset `Overview`
  plugins no longer build on the `CRUDDirectoryMixin` of django-mvp, so the `directory` and
  `crud_views` attributes and the `show_update_action`, `show_descriptions_action` and
  `show_delete_action` methods are gone from them, and `visible_to_holder_of` is removed from the
  project and dataset plugin modules. A subclass of either overview that read one of these reads
  `manage_menu` instead (see the overview context below).
- **Templates**: `plugins/descriptions.html`, `plugins/key-dates.html` and
  `dataset/plugins/update.html` are removed. The row-set page is now `editing/rows.html`, and
  the delete page is `editing/delete_record.html`. A template of yours that extended one of the
  removed names extends the page you need from the shared ones, or `form_view.html`.
- **Overview context**: a sample's overview no longer sets `urls` or `can_edit`, and a project's
  and a dataset's no longer set `urls.delete`, `directory` or `crud_views`. The addresses and the
  menu are in `manage_menu`, a list of entries each carrying a `label`, an `icon`, a `url` and a
  `destructive` flag, built for the signed-in person by
  `fairdm.core.editing.manage_menu(request, record)`. Read the entry you want from that list
  rather than from the old keys.
- **Dates and identifiers**: a project's and a dataset's dates and identifiers are no longer rows
  on the details page. A form of yours that posts `dates-` or `identifiers-` fields to the `edit`
  page now posts them to the `key-dates` or `identifiers` page of the record.
- **Your own Manage menu**: a template that overrides `overview.actions` to draw a Manage
  dropdown now fills `overview.manage` instead, with
  `<c-actions.manage :entries="manage_menu">` and any extra entries in its slot. The shared
  overview draws the menu in that block, so an override of `overview.actions` that keeps
  `{{ block.super }}` and draws its own dropdown shows two.
- **Who gets 404 and who gets 403**: a signed-in person who may see a project or a dataset and
  may not use one of its editing pages is now refused with 403. The old pages answered 404 to
  every refusal on a private record. A person who may not see the record still gets 404, and a
  visitor who may see it is sent to sign in.
- **Portal-wide change rights on samples**: the editing pages of a sample now answer 404 to a
  person who holds `sample.change_sample` for the whole portal, has no level on the sample and
  may not see it. The old pages opened for them. Give the people who should keep access a level
  on the sample or on its dataset, on the Contributors tab. A Data Curator is unaffected.

## 022 - Access to a record is a level on its contribution

A project, dataset, sample or measurement is now opened, changed and managed according to the
level (view, edit or manage) that a person holds on their contribution to it, or to the record
above it. Permissions stored in django-guardian for those four kinds of record grant nothing any
more. See [Managing Users and Permissions](../portal-administration/managing_users_and_permissions.md)
for what each level allows and for what the upgrade does to the permissions your portal holds.

Bringing the database up to date converts them for you. Check your portal's own code for these:

- **`AUTHENTICATION_BACKENDS`**: remove the two backends that passed a dataset's permissions down
  to its samples and measurements. They lived in `fairdm.core.sample.permissions` and
  `fairdm.core.measurement.permissions`, and both modules are gone.
  `fairdm.contrib.contributors.permissions.RecordLevelBackend` is added to FairDM's own list. If
  your settings build the list themselves, add it after
  `fairdm.core.permissions.PolymorphicObjectPermissionBackend`.
- **Granting access in code**: `assign_perm` and `remove_perm`, whether guardian's or the ones in
  `fairdm.core.utils`, no longer give a person access to a project, dataset, sample or
  measurement. List the person at a level instead, with
  `Crediting(record).add(person)` followed by `Crediting(record).update(contribution, roles=[], level=ContributionLevel.EDIT)`.
- **Listing records a user may act on**: `get_objects_for_user` on those four models no longer
  finds anything. Use `Dataset.all_objects.with_level(user, ContributionLevel.VIEW)`, or
  `accessible_to(user, level)`, which also includes every record for someone a portal role gives
  the right to change datasets. Call either on `Dataset.all_objects`: `Dataset.objects` leaves
  private datasets out.
- **Deleting samples and measurements**: this now needs the manage level. Before, the right to
  change the dataset was enough for samples.

## The demo application moved to `demo/`

The reference application shipped with FairDM used to live in `fairdm_demo/` and was imported as
`fairdm_demo`. It now lives in `demo/` and is imported as `demo`. Its Django app label changed
with it, from `fairdm_demo` to `demo`.

Nothing else about it changed. Every model, factory, filter, table, plugin and configuration class
keeps the name it had.

**If you install the demo application in your own portal**, update the name you pass to
`fairdm.setup()`:

```python
# Before
fairdm.setup(apps=["fairdm_demo"])

# After
fairdm.setup(apps=["demo"])
```

**If you import from it**, update the import path. The factories are the usual case, since the
documentation points at them as reference implementations:

```python
# Before
from fairdm_demo.factories import RockSampleFactory

# After
from demo.factories import RockSampleFactory
```

**If you refer to its models by label** in `ForeignKey` strings, `apps.get_model()` calls,
permission codenames or content-type lookups, replace `fairdm_demo` with `demo` in each one.

**If you have a database holding demo data**, the app label change moves every table the
application owns: `fairdm_demo_rocksample` becomes `demo_rocksample`, and so on for each of its
models. The demo application is a reference implementation rather than something a portal is
expected to deploy with real data, so the simplest path is to drop and recreate the database.

To keep the data instead, do all of this **before you start the application under the new name**,
and before running `migrate`:

1. Rename each of the application's tables from `fairdm_demo_<model>` to `demo_<model>`.
2. Update its rows in `django_migrations`, setting `app` from `fairdm_demo` to `demo`.
3. Update its rows in `django_content_type`, setting `app_label` from `fairdm_demo` to `demo`.

Permissions need no separate step. Both Django's own permission rows and django-guardian's
object-level grants reference a content type by id, so they follow the rows corrected in step 3.

If the application has already started under the new name, step 3 fails on a uniqueness error:
Django creates a content type per model the first time it needs one, so the database now holds a
`demo` row and a `fairdm_demo` row for the same model. Delete the newly created `demo` rows first —
they are the empty ones, and nothing has been granted against them yet — then run step 3, which
carries the original rows and everything filed against them across.

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
   `fairdm.factories.SampleFactory` the way `demo.factories.RockSampleFactory` does:

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

The pages that edit a sample (its details, descriptions, keywords and key dates) previously
admitted every request, including an anonymous one, because no permission was declared and the framework
treats an undeclared permission as "open to everyone". They now require `sample.change_sample`.

If your portal built its own view, template, or link assuming these surfaces were reachable
without authorisation, that assumption no longer holds. Give the people who should retain access
the edit level on the sample or on its dataset, on the Contributors tab. See
[022 - Access to a record is a level on its contribution](#022-access-to-a-record-is-a-level-on-its-contribution).
