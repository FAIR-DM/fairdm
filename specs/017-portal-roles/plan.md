# Implementation Plan: Portal roles and the people who hold them

**Branch**: `017-portal-roles` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/017-portal-roles/spec.md`

## Summary

Four portal roles are declared once, in code, as a name plus the permissions that name holds. A
`post_migrate` receiver reconciles them into every portal on every update — renaming the three
legacy groups in place, so the people already in them carry across — receivers and an
administration class on `Group` refuse to delete or rename a shipped role, and a
production-critical system check refuses to boot a portal that is missing one, standing down for
the command that repairs the condition. One extra authentication backend carries a permission held through one of those
roles - and through nothing else - down to individual records, which is what makes the rights reach
the pages that ask. The
administration interface stops asking for `is_staff` alone and accepts a holder of a rights-carrying
role. A management command creates five named development accounts and refuses to run outside
development, and a second check reports any of those accounts found on a production portal. The
Person administration form stops offering `is_superuser`, `is_staff` and `password` to anyone who
is not a superuser, because the Community Manager's `change_person` right would otherwise be a
route to superuser. A public page lists who holds which role, reachable from the Community menu.

No new models. No new dependencies. The four roles are `auth.Group` rows; what is new is that
FairDM owns their definition.

## Technical context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.1/5.2, django-guardian (already present, via the framework's own
backend subclasses), django-allauth, django-flex-menus. Nothing added.

**Storage**: PostgreSQL in production, SQLite in development. `auth.Group`, `auth.Permission` and
the existing `Person.groups` relation only.

**Testing**: pytest + pytest-django, factory-boy. `tests/` mirrors the source tree (Article X).

**Target Platform**: Linux server

**Project Type**: Django framework package with a demo application

**Performance Goals**: The team page renders in a bounded number of queries irrespective of how
many people hold roles; the permission backend adds no query to a request that does not ask an
object-level question.

**Constraints**: The boot check runs inside `AppConfig.ready()`, before `migrate` has created
anything, so it must distinguish an unmigrated database from a portal missing its roles. The
development accounts must be impossible to create on the production baseline.

**Scale/Scope**: Four roles, five development accounts, one new page, five group-name call sites
removed, two superuser gates replaced.

## Constitution check

*Gate: passed before Phase 0, re-checked after Phase 1.*

| Article | Bearing on this feature | Verdict |
|---|---|---|
| I — Test-First | Every behaviour here is testable without a browser: reconciliation, refusal, the check, the backend, the command, the page. A smoke test per new route is required, and there is one new route. | Pass — each task names its failing test first. |
| II — Simplicity | The alternative designs (a stored `is_staff` flag, a JSON fixture, a data migration) were each rejected in `research.md` for being more machinery, not less. | Pass — nothing in Complexity Tracking. |
| III — Anti-Abstraction | One new backend class, one declarations class, no base classes, no registry, no hooks. The roles are data on a class, not a plugin point. | Pass. |
| IV — Integration-First | The acceptance scenarios read "sign in as X, open Y", and the tests follow them: client-level tests against the admin, the pages and the command, rather than unit tests of a receiver in isolation. | Pass. |
| V — Security & data-safety | This feature *is* an access-control change. Every permission granted is enumerated in one module and asserted in a test that pins the exact set, so a widened role cannot pass unnoticed. The development accounts carry a published password and are refused outside development. | Pass, and the security lens at the design review covers it. |
| VI / XVII — Documentation | `docs/portal-administration/roles.md` is rewritten, `managing_users_and_permissions.md` is reconciled against it, and `CONTEXT.md` gains the two terms. Documentation ships in the story that changes the behaviour it describes. | Pass. |
| VIII — Internationalization | Role names and every message a person reads are wrapped in `gettext_lazy`. A role's name is stored in English and translated for display. | Pass. |
| IX — Data-model conventions | No new models, so no new fields needing `help_text` and `verbose_name`. | Not applicable. |
| X — Test structure | New test modules mirror the source, including `tests/test_management/test_commands/` for a management command, which is where this suite already mirrors that package. | Pass, after the design review corrected the command's test path. |
| XI — Cohesion | The declarations and the three functions that read them are one class, `PortalRoles`, not a module of loose functions — they share a subject, which is the article's own test. The receivers live with the app that owns the models they guard. | Pass, after the design review corrected an earlier reading of this row. |
| XVIII — Living demo | The development accounts ship with the package rather than the demo, and the demo's documentation points at the command that creates them. | Pass. |

## Project structure

### Documentation (this feature)

```text
specs/017-portal-roles/
├── plan.md              # This file
├── spec.md              # Approved at the specification gate
├── research.md          # What the framework already does, and what it settles
├── decisions.md         # Rationale, including the options not taken
├── progress.md          # Gate outcomes and run narrative
├── quickstart.md        # How an administrator and a developer use this
└── tasks.md             # The task graph
```

### Source code

```text
fairdm/
├── portal_roles.py               # NEW - PortalRoles: the four roles and what each holds
├── permissions.py                # NEW - PortalRolePermissionBackend (model level reaches records)
├── apps.py                       # connect the post_migrate receiver
├── conf/
│   ├── checks.py                 # NEW checks: fairdm.E500 roles present, E501 dev accounts absent
│   └── settings/
│       ├── auth.py               # register the backend
│       └── apps.py               # drop the groups fixture from the setup pipeline
├── management/commands/
│   └── create_dev_accounts.py    # NEW - the five development accounts
├── menus/menus.py                # the Community group gains the team page
├── fixtures/groups.json          # DELETED - replaced by the declarations
└── contrib/
    ├── admin/sites.py            # administration access for role holders; the Group admin class
    ├── contributors/
    │   ├── choices.py            # DefaultGroups removed
    │   ├── models.py             # Person.is_data_admin removed
    │   ├── receivers.py          # refuse deletion and renaming of a shipped role
    │   ├── admin.py              # narrow the Person form; permission-gate claims and merges
    │   ├── urls.py               # the team page route
    │   ├── views/                # the team page view (directory exists)
    │   └── templates/            # the team page template (directory exists)
    ├── plugins/utils.py          # the group-name branch removed
    ├── import_export/views.py    # two more group-name branches removed
    └── templatetags/fairdm.py    # the group-name branch removed

tests/
├── test_portal_roles.py
├── test_permissions.py
├── test_conf/test_checks.py
├── test_management/test_commands/test_create_dev_accounts.py
├── test_contrib/test_admin/test_sites.py
├── test_contrib/test_admin/test_group_admin.py
├── test_contrib/test_contributors/test_admin.py
├── test_contrib/test_contributors/test_permissions.py
└── test_contrib/test_contributors/test_views/test_team.py
```

**Structure decision**: the framework package as it stands. The role declarations sit at
`fairdm/portal_roles.py` — the qualified name, because this codebase already spends the bare word
"roles" on contribution roles and FR-039 exists to keep the two apart — because a portal role spans
the whole framework — it grants rights over core
records *and* over contributor records — so it belongs to neither app alone. The receivers guarding
`Group` live in `fairdm/contrib/contributors/receivers.py`, where this codebase already keeps
receivers over auth-adjacent models.

## Phases

### Phase 0 — Foundational

None. US-1 is the foundation: every later story reads the declarations it creates, so it is built
first and alone.

### Phase 1 — US-1, the roles arrive with the framework (P1)

`fairdm/portal_roles.py` declares the four roles on one class, each a name and an explicit list of
permissions — including the Portal Administrator's, which holds no right to edit a group, because a
role that can edit groups can rewrite its own rights. `reconcile()` renames the three legacy groups
in place first, so their members carry across, then creates what is missing, sets each role's
permission set to the declaration, and leaves membership untouched. A `post_migrate` receiver with
no sender and a `dispatch_uid` calls it. `fairdm/fixtures/groups.json` and its `loaddata` line go, along with `DefaultGroups` and the
administrator documentation describing five roles that never existed.

The Data Curator's permission list is derived from what the three group-name call sites could reach
(research R9), so that US-2 removes them without narrowing anybody's rights.

### Phase 2 — US-2, a role decides what its holder can do (P1)

`PortalRolePermissionBackend` answers an object-level question with the model-level permission the
person holds, registered after the existing backends, carrying the exclusion for
`contributors.manage_organization` that the framework already documents. `CustomAdminSite`
and its login form accept a holder of a rights-carrying role, and the Person administration form
stops offering `is_superuser`, `is_staff` and `password` to a non-superuser. The five group-name
call sites go, each in the same commit as the test pinning the behaviour that replaces it, and the
superuser gates on profile claims and merges become permission questions the Community Manager
role can answer.

### Phase 3 — US-3, the roles cannot be lost by accident (P2)

`pre_delete` and `pre_save` receivers on `Group` refuse to remove or rename a shipped role, and a
`Group` administration class turns that refusal into something the person who clicked can read.
`fairdm.E500` joins the production-critical check subset, tolerating an unmigrated database, naming
every missing role at once, and standing down for the command that installs them.

### Phase 4 — US-4, signing in as each role (P2)

`create_dev_accounts` creates the five accounts, idempotently, each with a confirmed email address,
and refuses to run when the resolved environment is not `development`. It refuses rather than
adopts when an address already belongs to somebody. `fairdm.E501` reports any of those five
addresses found on a production portal, because the command's refusal guards the act of loading
and not the state a database copy can produce.

### Phase 5 — US-5, the portal team page (P3)

A view, a template and a route in `fairdm/contrib/contributors`, plus the menu entry. Public,
grouped by role in declaration order, empty roles omitted, names and profile links only.

### Ordering and parallelism

US-1 → US-2 → US-3 → US-4 → US-5, sequentially. The last three are independent of one another, but
all five read `fairdm/roles.py` and three write into the same test tree, so one worktree at a time
applies.

## Risks

| Risk | Mitigation |
|---|---|
| The object-level fallback widens rights beyond the roles. | It did, and it was narrowed: only a permission held through one of the four shipped roles reaches records. The wider rule reopened a disclosure guard an earlier feature had put in deliberately, which four of its tests caught. The suite now pins the refusal for a direct grant and for a portal's own group as well as the yes for a role holder. |
| Third-party administration code calls `staff_member_required` rather than going through the admin site. | A smoke test signs in as each role and reaches the administration index and one changelist. Anything bypassing the site surfaces there. |
| Removing `is_data_admin` and the template-tag branch narrows somebody's rights in a portal relying on them. | The Data Curator's permission list is built from exactly what those call sites reached, and the removal lands in the story that grants them. |
| `fairdm.E500` fires during `migrate` on a fresh production database and blocks setup. | The check reports nothing when the group table is absent or unreadable, and a test covers a database with no tables. |
| The development accounts reach a production portal. | The command refuses on any resolved environment other than `development`, the same rule the production boot guard uses, and a test asserts nothing is created. `fairdm.E501` then reports any that arrived by some route the command never saw, such as a database copy. |
| An upgraded production portal cannot start and cannot migrate, because the boot refusal fires before the thing that installs the roles. | The refusal stands down for the command that repairs the condition, and T024 covers exactly that upgrade path. This was a critical design-review finding, and it is the reason `migrate` is named in T025. |
| The people already in the legacy groups lose their rights silently. | Reconciliation renames the legacy rows rather than leaving them, which carries the membership rows across untouched. T004 covers it. |
| `contributors.change_person` becomes a route to superuser through the Person administration form. | The form drops `is_superuser`, `is_staff` and `password` for a request whose user is not a superuser, and T015 asserts a Community Manager cannot set the flag on anybody. |
| The object-level fallback answers a permission the framework deliberately refuses to derive. | The backend carries the same explicit exclusion for `contributors.manage_organization` that `fairdm/core/permissions.py` already documents, and T011 covers it. |

## Complexity tracking

No constitution violations to justify.
