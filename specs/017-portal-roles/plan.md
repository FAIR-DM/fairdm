# Implementation Plan: Portal roles and the people who hold them

**Branch**: `017-portal-roles` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/017-portal-roles/spec.md`

## Summary

Four portal roles are declared once, in code, as a name plus the permissions that name holds. A
`post_migrate` receiver reconciles them into every portal on every update, receivers on `Group`
refuse to delete or rename them, and a production-critical system check refuses to boot a portal
that is missing one. One extra authentication backend carries a model-level permission held through
a role down to individual records, which is what makes the rights reach the pages that ask. The
administration interface stops asking for `is_staff` alone and accepts a holder of a rights-carrying
role. A management command creates five named development accounts and refuses to run outside
development. A public page lists who holds which role, reachable from the Community menu.

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

**Scale/Scope**: Four roles, five development accounts, one new page, three call sites removed.

## Constitution check

*Gate: passed before Phase 0, re-checked after Phase 1.*

| Article | Bearing on this feature | Verdict |
|---|---|---|
| I — Test-First | Every behaviour here is testable without a browser: reconciliation, refusal, the check, the backend, the command, the page. A smoke test per new route is required, and there is one new route. | Pass — each task names its failing test first. |
| II — Simplicity | The alternative designs (a stored `is_staff` flag, a JSON fixture, a data migration) were each rejected in `research.md` for being more machinery, not less. | Pass — nothing in Complexity Tracking. |
| III — Anti-Abstraction | One new backend class, one new module of declarations, no base classes, no registry, no hooks. The role definitions are data in a module, not a plugin point. | Pass. |
| IV — Integration-First | The acceptance scenarios read "sign in as X, open Y", and the tests follow them: client-level tests against the admin, the pages and the command, rather than unit tests of a receiver in isolation. | Pass. |
| V — Security & data-safety | This feature *is* an access-control change. Every permission granted is enumerated in one module and asserted in a test that pins the exact set, so a widened role cannot pass unnoticed. The development accounts carry a published password and are refused outside development. | Pass, and the security lens at the design review covers it. |
| VI / XVII — Documentation | `docs/portal-administration/roles.md` is rewritten, `managing_users_and_permissions.md` is reconciled against it, and `CONTEXT.md` gains the two terms. Documentation ships in the story that changes the behaviour it describes. | Pass. |
| VIII — Internationalization | Role names and every message a person reads are wrapped in `gettext_lazy`. A role's name is stored in English and translated for display. | Pass. |
| IX — Data-model conventions | No new models, so no new fields needing `help_text` and `verbose_name`. | Not applicable. |
| X — Test structure | New test modules mirror the source: `tests/test_roles.py`, `tests/test_permissions.py`, `tests/test_conf/test_checks.py` (exists), `tests/test_contrib/test_contributors/test_views/test_team.py`, `tests/test_management/test_create_dev_accounts.py`. | Pass. |
| XI — Cohesion | The declarations and the one function that reads them stay in a single module; the receivers live with the app that owns the models they guard. | Pass. |
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
├── roles.py                      # NEW - the four roles and the permissions each holds
├── permissions.py                # NEW - PortalRolePermissionBackend (model level reaches records)
├── apps.py                       # connect the post_migrate receiver
├── conf/
│   ├── checks.py                 # NEW check fairdm.E300 - the portal roles are present
│   └── settings/
│       ├── auth.py               # register the backend
│       └── apps.py               # drop the groups fixture from the setup pipeline
├── management/commands/
│   └── create_dev_accounts.py    # NEW - the five development accounts
├── menus/menus.py                # the Community group gains the team page
├── fixtures/groups.json          # DELETED - replaced by the declarations
└── contrib/
    ├── admin/sites.py            # administration access for role holders
    ├── contributors/
    │   ├── choices.py            # DefaultGroups removed
    │   ├── models.py             # Person.is_data_admin removed
    │   ├── receivers.py          # refuse deletion and renaming of a shipped role
    │   ├── urls.py               # the team page route
    │   ├── views/                # NEW - the team page view
    │   └── templates/            # NEW - the team page template
    ├── plugins/utils.py          # the group-name branch removed
    └── templatetags/fairdm.py    # the group-name branch removed

tests/
├── test_roles.py
├── test_permissions.py
├── test_conf/test_checks.py
├── test_management/test_create_dev_accounts.py
└── test_contrib/test_contributors/test_views/test_team.py
```

**Structure decision**: the framework package as it stands. The role declarations sit at
`fairdm/roles.py` because a portal role spans the whole framework — it grants rights over core
records *and* over contributor records — so it belongs to neither app alone. The receivers guarding
`Group` live in `fairdm/contrib/contributors/receivers.py`, where this codebase already keeps
receivers over auth-adjacent models.

## Phases

### Phase 0 — Foundational

None. US-1 is the foundation: every later story reads the declarations it creates, so it is built
first and alone.

### Phase 1 — US-1, the roles arrive with the framework (P1)

`fairdm/roles.py` declares the four roles, each a name and an explicit list of permissions. A
reconcile function creates missing roles, sets each one's permission set to the declaration, and
leaves membership untouched. A `post_migrate` receiver with no sender and a `dispatch_uid` calls
it. `fairdm/fixtures/groups.json` and its `loaddata` line go, along with `DefaultGroups` and the
administrator documentation describing five roles that never existed.

The Data Curator's permission list is derived from what the three group-name call sites could reach
(research R9), so that US-2 removes them without narrowing anybody's rights.

### Phase 2 — US-2, a role decides what its holder can do (P1)

`PortalRolePermissionBackend` answers an object-level question with the model-level permission the
person holds, registered after the existing backends. `CustomAdminSite.has_permission` and its
login form accept a holder of a rights-carrying role. The three group-name call sites go, each in
the same commit as the test pinning the behaviour that replaces it.

### Phase 3 — US-3, the roles cannot be lost by accident (P2)

`pre_delete` and `pre_save` receivers on `Group` refuse to remove or rename a shipped role and say
why. `fairdm.E300` joins the production-critical check subset, tolerating an unmigrated database
and naming every missing role at once.

### Phase 4 — US-4, signing in as each role (P2)

`create_dev_accounts` creates the five accounts, idempotently, each with a confirmed email address,
and refuses to run when the resolved environment is not `development`. It refuses rather than
adopts when an address already belongs to somebody.

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
| The object-level fallback widens rights beyond the roles: anybody holding a model permission directly now holds it on every instance. | That is the intended rule and it matches Django's own admin. The suite pins it for a direct grant as well as for a role holder, so the widening is stated rather than incidental. |
| Third-party administration code calls `staff_member_required` rather than going through the admin site. | A smoke test signs in as each role and reaches the administration index and one changelist. Anything bypassing the site surfaces there. |
| Removing `is_data_admin` and the template-tag branch narrows somebody's rights in a portal relying on them. | The Data Curator's permission list is built from exactly what those call sites reached, and the removal lands in the story that grants them. |
| `fairdm.E300` fires during `migrate` on a fresh production database and blocks setup. | The check reports nothing when the group table is absent or unreadable, and a test covers a database with no tables. |
| The development accounts reach a production portal. | The command refuses on any resolved environment other than `development`, the same rule the production boot guard uses, and a test asserts nothing is created. |

## Complexity tracking

No constitution violations to justify.
