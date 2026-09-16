# Research — 017 Portal roles and the people who hold them

What the framework already does, and what each of those findings settles. Every claim here was
read from the code on the branch's base commit (`1a03eec`).

## R1 — There are already three group names, and they carry no permissions

`DefaultGroups` in `fairdm/contrib/contributors/choices.py` names `Portal Administrators`,
`Data Administrators` and `Developers`. `fairdm/fixtures/groups.json` creates those three groups
with no permissions attached, and `DJANGO_SETUP_TOOLS` in `fairdm/conf/settings/apps.py` loads it
under `on_initial` only — so a portal that was set up before the fixture existed, or set up without
django-setup-tools, has never had it, and one that has it holds three empty groups.

Three places then decide rights by matching the name of one of them:

| Where | What it grants |
|---|---|
| `Person.is_data_admin` (`contributors/models.py:786`) | `True` for a superuser or any member of `Data Administrators` |
| `has_perms` template tag (`templatetags/fairdm.py:213`) | any permission the template asks about |
| `check_has_edit_permission` (`contrib/plugins/utils.py:46`) | edit rights on the plugin's instance |

**Settles:** the role set replaces these rather than joining them (FR-019, FR-036). Nothing else in
the framework reads a group, so the replacement is confined to those three call sites and their
tests.

## R2 — Object-level permissions already have a backend chain, and model-level rights do not reach it

`AUTHENTICATION_BACKENDS` (`fairdm/conf/settings/auth.py`) is `ModelBackend`, allauth's backend,
then `PolymorphicObjectPermissionBackend` and three subclasses of it. The guardian backend is not
listed directly, and `guardian.W001` is silenced for that reason.

The gap that matters here is Django's own: `ModelBackend.has_perm(user, perm, obj)` returns `False`
whenever `obj` is not `None`. A portal role granting `change_dataset` at model level therefore
answers `True` for `user.has_perm("dataset.change_dataset")` and `False` for
`user.has_perm("dataset.change_dataset", some_dataset)` — and every access decision in this
codebase that matters passes the object.

**Settles:** the role's rights reach records through one more backend in the chain, which answers an
object-level question with the model-level permission the person holds. The rule it implements is
the one Django's own admin already follows — `ModelAdmin.has_change_permission` ignores its `obj`
argument by default — so a model-level right meaning "every instance of this model" is the
framework's existing semantics, not a new one. No permission row is written per record (FR-020).

## R3 — Reaching the administration interface is `is_staff`, and there is a custom admin site to hang the change on

`fairdm.contrib.admin.sites.CustomAdminSite` is already installed as the default admin site.
Django's `AdminSite.has_permission()` asks for `is_active and is_staff`, and its login form
(`AdminAuthenticationForm.confirm_login_allowed`) refuses a person who is not staff, so overriding
one without the other leaves a role holder able to reach the interface only if they are already
signed in.

Two candidate mechanisms:

1. **Derive it.** Override `has_permission()` and the admin login form on `CustomAdminSite` to
   accept a holder of a rights-carrying role. Nothing is stored, so nothing can drift.
2. **Store it.** Keep `is_staff` as the mechanism and maintain it from role membership with a
   receiver.

**Settles: derive.** Storing means reconciling on every route by which membership changes — adding,
removing, clearing, deleting the group, deleting the person, `loaddata` — and the framework already
prefers derived answers in exactly this area (`Person.account_state` derives from three fields,
`OrganizationPermissionBackend` derives from a current affiliation rather than a stored grant, and
its docstring says why). The risk carried is third-party admin code calling
`staff_member_required` directly rather than going through the site; the installed admin add-ons are
reached through the admin site's own URLs, and a smoke test per role covers it.

## R4 — The production boot refusal already exists and takes new checks by tag

`FairDMConfig._check_production_configuration` (`fairdm/apps.py`) runs the check registry filtered
to `DeployTags.production_critical` whenever the resolved environment is not `development`, and
raises `SystemCheckError` naming every failure at once. `fairdm/conf/checks.py` registers the
existing members of that subset, one of which (`fairdm.E102`) already reads `DATABASES`.

**Settles:** the missing-role condition is one more check with that tag (FR-015, FR-017), not a new
mechanism. Two constraints fall out of where it runs:

- `ready()` runs before `migrate` does its work, so the check must treat "the tables are not there
  yet" and "the tables are there and the roles are not" as different answers, and only fail on the
  second (FR-016). `django.db.utils.ProgrammingError`/`OperationalError` on the group table is the
  first case.
- The check is registered at module import, so it participates in `manage.py check --deploy`
  regardless of environment, which is what gives development the on-demand report (FR-017).

## R5 — Installation belongs to `post_migrate`, not to a migration

A data migration runs once. FR-009 and FR-011 need the roles installed and their rights restored on
*every* update, including on portals that predate this work, which is what `post_migrate` gives.

`django.contrib.auth` creates `Permission` rows in its own `post_migrate` receiver, per application,
and `INSTALLED_APPS` lists `fairdm` before `fairdm.core.*` and `fairdm.contrib.contributors`. A
receiver connected with `sender=FairDMConfig` would therefore run before the permissions it needs
exist. Connected **without** a sender it runs once per application config, by which point the last
run sees every permission. It is idempotent, so the repeats converge rather than conflict.

**Settles:** one `post_migrate` receiver, no sender, `dispatch_uid` to keep it single, tolerant of a
permission that does not exist yet (it will on a later pass).

## R6 — Refusing deletion has a precedent in this codebase

`refuse_off_vocabulary_role` (`contributors/apps.py`) connects an `m2m_changed` receiver to enforce
a rule the model layer could not, and the reason is written down at the call site: `full_clean()`
never runs on a plain `save()`, so the signal is the only place the rule holds for every writer.

**Settles:** `pre_delete` and `pre_save` receivers on `Group`, raising, are the framework's own
idiom for this (FR-012, FR-013). They hold for the administration interface, which is what the
specification asks for, and they hold for any other ORM writer as a side effect. They do not hold
against raw SQL, which the specification already accepts.

## R7 — The demo's development accounts have no home yet, and a fixture is the wrong shape for them

`generate_fake_data` builds projects, datasets, samples and measurements. `seed_licenses` seeds
reference data. `DJANGO_SETUP_TOOLS` creates one superuser from environment variables. Nothing
creates a named account, and `fairdm/fixtures/` holds two `loaddata` fixtures.

A JSON fixture was the obvious route and does not survive contact with this user model:

- `Person` subclasses `Contributor`, which is polymorphic, so every fixture row must carry a
  correct `polymorphic_ctype` id — a content-type primary key that differs between databases.
- The password would ship as a pre-computed Argon2 hash, pinned to today's hasher parameters, and
  silently stops matching when they change.
- Being able to sign in without confirming an address means an allauth `EmailAddress` row per
  account, with `verified=True`, which the fixture would also have to pin by id.

**Settles:** a management command that creates the accounts through the ORM (FR-022 to FR-029). It
hashes the password at run time, resolves content types by lookup, and can refuse outright when the
resolved environment is not `development` — a `loaddata` of a shipped JSON file cannot refuse
anything. "Fixture" in the request means shipped development data, and this is the form of it that
works.

## R8 — The Community menu group exists and takes a third entry

`fairdm/menus/menus.py` declares a `MenuGroup("Community")` holding `People` and `Organizations`,
each a `MenuItem` with a `view_name` and an icon.

**Settles:** the team page is a third `MenuItem` in that group (FR-032), and the page itself is an
ordinary view in `fairdm/contrib/contributors`, where `people-list` and `organization-list` already
live.

## R9 — What the Data Curator's rights have to cover

`is_data_admin` and the plugin edit check currently grant a member of `Data Administrators` edit
rights over any instance a plugin renders, and the template tag grants any permission a template
asks about. Removing them narrows nobody's rights only if the Data Curator role holds the model
permissions for `Project`, `Dataset`, `Sample` and `Measurement` and their attached records —
descriptions, dates, contributions — and the object-level fallback from R2 carries them to
instances.

**Settles:** the role's permission list is derived from the models the three call sites could reach,
and the story that removes them is the same story that grants them, so no window exists where a
curator can do less than a data administrator could.
