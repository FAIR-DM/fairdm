# Implementation Plan: Overview pages for people and organizations

**Branch**: `019-contributor-overview-pages` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Both pages already exist as a working prototype, reviewed with the maintainer over six rounds and
brought onto this branch from `sketch/contributor-profiles`. Its markup, copy and layout are the
settled design. What the prototype does not have is what this plan adds:

- tests for every acceptance scenario, through the rendered pages
- the gaps between the prototype and the specification, found by those tests and fixed
- the visibility rule applied to the Projects and Datasets tabs, and the two blank tabs removed
- documentation for portal developers, two glossary terms and a changelog entry
- the existing tests the prototype broke, brought up to date

Wherever a page's content, wording or look is not changed by a requirement in the spec, the
implementation keeps what the prototype has. Layout, width, stacking and copy get no tests.

## Technical context

**Language/version**: Python 3.13, Django 5.2
**Primary dependencies**: django-mvp 0.25.1 (raised by the prototype), django-cotton,
django-polymorphic, django-allauth. No new dependency. Pillow is declared directly (D8)
**Storage**: no model fields and no migrations. Models gain methods and properties only
**Testing**: pytest, pytest-django, factory-boy, per `docs/contributing/standards/testing.md`.
Tests mirror the source tree
**Target**: the `fairdm` package and the `demo` reference application
**Performance**: not a goal. No query-count tests. Obvious per-row queries are fixed with
`select_related` or `prefetch_related`
**Constraints**: every string translatable (Article VIII). Nothing a viewer may not open reaches
the page or its head (FR-006 to FR-010)

## Starting state

Measured on the branch with the prototype merged (commit 98a231c7), 2026-10-01:

- **6 of 3,282 tests fail.** Five render `overview/includes/pending_action.html`, which the
  prototype turned into the `c-actions.pending` component. One expects `reverse("account-center")`
  to be `/account-center/` and now gets `/account-center/account/`, since the move to django-mvp
  0.25.1.
- **`deptry` fails.** `demo/management/commands/seed_profiles.py` imports `PIL`, which is not a
  declared dependency.
- **The docs check fails.** Six new public names are undocumented: `ContributorOverviewMixin`,
  `active_then_recent`, `fill_slots`, `language_names`, `link_host`, `ranked_shares`.
- The pages have no tests of their own. `ruff`, `mypy` and the build pass.

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every story starts with tests of its acceptance scenarios through the test client, as a visitor and signed in. Tests that fail drive the fixes |
| II Simplicity / III Anti-Abstraction | The one-use `ContributorOverviewMixin` is folded into the `Overview` plugin (D3). No settings, no registry hooks |
| IV Integration-First | Acceptance tests request the real pages |
| V Security | Visibility is decided in one model method and on the QuerySets (D4), never in a template. JSON-LD goes through the existing escaping helper and carries no email |
| VI / XVI Documentation | New components, blocks, model methods and helpers are documented in the story that introduces them |
| VII Dependencies | Pillow declared because the code imports it. `deptry` green |
| VIII i18n | The prototype's templates translate. The tab module's import-time strings move to `gettext_lazy` (D8) |
| X Cohesion | What a contributor has done lives on the models, pure formatting in `profiles.py`, page layout on the plugin |
| XVII Demo | `seed_profiles` reaches every state both pages answer for (FR-033) |

## Design

### D1. Two page templates on the shared skeleton

`contributors/overview/person.html` and `contributors/overview/organization.html` extend
`overview/page.html` and only fill blocks (FR-001). The skeleton gains one block, `overview.name`,
inside its heading, so a page can follow the name with an identifier link. Blocks shared with the
record pages keep their names (FR-003). Blocks only these pages have: `overview.about`,
`overview.records`, `overview.roles`, `overview.future`, `overview.links`,
`overview.affiliations`, `overview.activity`, `overview.members`, `overview.location`,
`overview.hierarchy`.

### D2. Components

The prototype's components stay as they are, each with the annotation header the documentation
standard asks for:

- under the contributors app: `c-card.records`, `c-card.roles`, `c-card.links`,
  `c-card.affiliations` (with `.row`), `c-card.hierarchy` (with `.node`)
- shared: `c-missing` (says what is missing) and `c-actions.pending` (a disabled action that says
  why, replacing the include `overview/includes/pending_action.html`)

`c-card.people` and `c-card.location` gained optional inputs (a title, an accessible label) and
keep their record-page behaviour.

### D3. Where the logic lives

- **Models** say what a contributor has done and what its record holds:
  `Contributor.get_visible_contributions(user)`, `get_role_counts()`, `get_collaborators()`,
  `get_links_display()`, `get_language_names()`, `to_public_schema_org()`;
  `Person.member_since`, `get_affiliation_history()`, `get_profile_completeness()`;
  `Organization.get_current_memberships()`, `has_member()`, `is_managed_by()`,
  `get_hierarchy()`, `get_record_completeness()`; `Affiliation.start_display` / `end_display`;
  `ContributorIdentifier.resolver_url`; `Project.is_active`.
- **`fairdm/contrib/contributors/profiles.py`** holds pure functions with no database access:
  `link_host`, `language_names`, `ranked_shares`, `fill_slots`, `active_then_recent`, `checklist`.
- **The `Overview` plugin** decides layout: which page, how many of each thing, order, wording
  and addresses. The prototype splits it into `ContributorOverviewMixin` plus a registered
  `Overview` class that only mixes it in. A mixin with one user is an abstraction with no second
  caller, so the two become one class, `Overview(OverviewPlugin)`, in
  `plugins/overview.py`, registered there. `plugins/person.py` keeps the Projects and Datasets
  tabs.

### D4. Visibility

One rule, in one place. `Contributor.get_visible_contributions(user)` returns the credits on:

- projects that are public
- datasets that are public and whose project, where they have one, is public. The prototype asks
  only `Dataset.objects`, which leaves out private datasets but would list a public dataset inside
  a private project. The glossary says a private project hides everything beneath it, so the
  project is checked too
- samples and measurements the user may open (`visible_to(user)`) and whose dataset's project,
  where it has one, is public. The extra condition is applied inside
  `get_visible_contributions`, and the shared `visible_to` is left alone. Samples and
  measurements are resolved to visible ids, not loaded as objects, because no card lists them,
  and collaborators are found from those ids without one query condition per credit

Projects and datasets ignore who is asking (FR-006). The collaborators and the role counts are
computed from the returned credits (FR-007), so they follow the same rule without a second
filter.

There is one source for "this contributor's public projects" and one for "this contributor's
public datasets", on the model. For a person they are the credited ones. `Organization` overrides
both to add the projects it owns and the datasets inside them (FR-026), with nothing twice. The
overview's figures and cards and the Projects and Datasets tabs all read those two sources, so a
count cannot disagree with the list its link leads to (SC-003, FR-008). This replaces the
list-building in the prototype's `get_organization_context`.

The page's JSON-LD comes from `to_public_schema_org()`. It drops the email address (FR-009), and
it keeps `affiliation` only when that is the verified, current primary affiliation the header
shows (FR-010): `primary_affiliation()` does not check the affiliation's type or end date, so a
pending or ended primary affiliation would otherwise reach the page head. The change is made in
`to_public_schema_org`, not in the shared Schema.org transform, which projects also call.

Every contributor's page is open to everyone (FR-005). The plugin declares no permission check
beyond the object existing.

### D5. Who keeps a record

- A person's checklist, the "edit profile" stand-in and the first-person empty states are shown
  when `request.user` is that person (FR-030, FR-032).
- An organization's checklist and management menu are shown when
  `Organization.is_managed_by(user)`: a current affiliation of type administrator or owner
  (FR-031). A portal role does not count (spec decision). "Current" uses the existing
  `AffiliationQuerySet.current()`.
- Asking to join is offered to a signed-in user for whom `has_member()` is false and
  `is_managed_by()` is false (FR-025).

### D6. Tabs

The overview tab is labelled like every record's first tab. The `Statistics` and `Network`
plugins, their templates and any tests of them are deleted (FR-002). The Projects and Datasets
tabs keep their "my" titles on the user's own profile.

### D7. Development data

`demo/management/commands/seed_profiles.py` builds on `seed_overviews`, refuses outside
development, uses the three standard accounts and replaces only its own records (FR-033). A test
runs it and requests each seeded page.

### D8. Housekeeping the prototype needs

- **Pillow** is imported by `seed_profiles` to draw placeholder logos. FairDM's image fields
  already need Pillow at run time, so it is declared as a direct dependency instead of being
  reached through another package.
- **`account-center`**: django-mvp 0.25.1 mounts its landing page at `account/` inside
  `mvp.urls` (`mvp/urls.py:45`), and `fairdm/conf/urls.py` includes `mvp.urls` under
  `account-center/`, so the name now resolves to `/account-center/account/`. FairDM keeps its
  address: `fairdm/conf/urls.py` declares its own `account-center/` route to the same landing
  view, ahead of the includes. The existing tests stay as they are, and `/account-center/login/`
  keeps answering.
- **`plugins/person.py`** imports `gettext` as `_` and uses it in class attributes and decorator
  arguments, which bind at import. It imports `gettext_lazy` instead (Article VIII). The
  `gettext` calls inside methods in `plugins/overview.py` run per request and stay.
- **The five `pending_action.html` tests** move to the component: the same assertions against
  `c-actions.pending` (disabled, never submits or links, says why to a pointer and to a screen
  reader). The two that expect a "Coming soon" badge on the button are removed: the maintainer
  took the badge off buttons in review, and FR-012 asks only that the action is disabled and says
  why. Recorded in `decisions.md`.
- **#248** (the Datasets tab error) is already fixed on the branch, and gets a test.

## Project structure

```text
fairdm/
  contrib/contributors/
    models.py                     # D3 methods, D4 visibility
    profiles.py                   # pure helpers
    plugins/overview.py           # Overview (registered here)
    plugins/person.py             # Projects and Datasets tabs, public records only
    templates/contributors/overview/{person,organization}.html
    templates/cotton/card/{records,roles,links,affiliations,hierarchy}.html (+ row, node)
  templates/
    overview/page.html            # + overview.name
    cotton/{missing.html, actions/pending.html}
  core/project/models.py          # Project.is_active
demo/management/commands/seed_profiles.py
docs/portal-development/
  overview-pages.md               # the two contributor pages and their blocks
  contributors.md                 # model methods, helpers
  component_library/cards.md      # new components
CONTEXT.md                        # Collaborator, Member
tests/
  test_contrib/test_contributors/test_profiles.py
  test_contrib/test_contributors/test_models.py          # new Test… classes
  test_contrib/test_contributors/test_plugins/test_overview.py
  test_contrib/test_contributors/test_plugins/test_person.py
  test_core/test_project/test_models.py                  # is_active
  test_templates/                                        # components (declared non-mirror)
  test_demo/                                             # seed command
```
