# Implementation Plan: Editing person and organization profiles in the portal

**Branch**: `020-profile-editing` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

One editing page for a contributor, mounted at `contributor/<uuid>/update/` as an additional view
of the existing overview plugin, the way projects and datasets do it. It shows a person form or an
organization form depending on the record. Who may open and save it is decided by one method on
the record. The overview pages swap their disabled stand-ins for working links wherever that
method says yes, and each checklist item this feature can fix links to its field.

## Technical context

**Language/version**: Python 3.13, Django 5.2
**Primary dependencies**: django-mvp, django-cotton, crispy-forms, easy-thumbnails,
django-countries. No new dependency
**Storage**: no model fields and no migrations
**Testing**: pytest, pytest-django, factory-boy, per `docs/contributing/standards/testing.md`.
Tests mirror the source tree and request the real pages through the test client
**Target**: the `fairdm` package and the `demo` reference application
**Constraints**: every string translatable (Article VIII). The right to edit is checked on every
request (FR-005). Layout, width, stacking and copy get no tests

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Each story starts with tests of its acceptance scenarios through the test client, for every kind of account the story names |
| II Simplicity / III Anti-Abstraction | One page class and two forms. One list field, used four times. One setting, modelled on `ACCOUNT_FORMS` |
| IV Integration-First | Acceptance tests open and submit the real page |
| V Security | The right to edit lives in one model method, checked by the page on GET and POST, never in a template. Uploads are size-checked and must be images. Links must be web addresses |
| VI / XVI Documentation | Each story documents the public names it introduces, and the user and administrator guides change in the story that changes what they describe |
| VII Dependencies | None added |
| VIII i18n | All labels, help text and messages are translatable |
| X Cohesion | The rule on the models, the fields in the forms, the wiring in the plugin |
| XVII Demo | `seed_profiles` reaches every account and profile state the three stories name |

## Complexity tracking

| Addition | Why it is needed | Simpler alternative, and why not |
|---|---|---|
| `FAIRDM_PROFILE_FORMS` setting | FR-022 requires a documented way for a portal to change the fields | Re-registering the page: a registered page cannot be replaced or removed from a portal's code. The model configuration's `form_class`: contributors have no model configuration |
| `LinesField` | Three list fields across two forms, and no list field exists | A JSON text box: a person would have to type brackets and quotes |

## Design

### D1. Who may edit: `is_editable_by(user)`

`Contributor.is_editable_by(user)` returns False for a visitor and for an inactive user, and is
overridden on both subclasses:

- **`Person`**: True when the user is this person. Otherwise True only when the user is a
  community manager and the person has no active account: the account is inactive, or the
  person is not claimed and has never signed in (`last_login` is None). `account_state` alone is
  not enough, because an account made with `createsuperuser`, or by signing up on a portal that
  does not verify email addresses, is active and in use without being marked claimed.
- **`Organization`**: True when `is_managed_by(user)` or the user is a community manager.

"Is a community manager" is `PortalRoles.is_held_by(user, PortalRoles.COMMUNITY_MANAGER)`, a new
class method next to the role's declaration: an active user in the group of that name. Superusers
and every other role get nothing from it (FR-004).

### D2. The page: `Update`

`fairdm/contrib/contributors/plugins/update.py`, class `Update(Plugin, FairDMUpdateView)`, listed
in `Overview.extra_views`:

- `url_path = "update"`, so the address is `contributor/<uuid>/update/` and its name is
  `contributor:overview-update`
- `check = staticmethod(lambda request, obj: obj is not None and obj.is_editable_by(request.user))`
  written as a named module function. `Plugin` runs it on every request, so a right lost while
  the page is open refuses the save (FR-005, FR-003a, US-3 scenario 5)
- `get_form_class()` returns the portal's entry in `FAIRDM_PROFILE_FORMS` for the record's kind,
  and the shipped form when the setting or that key is absent
- on success: a "saved" message and a redirect to the overview page (FR-018). The page's cancel
  link goes to the same place
- the page title is "Edit profile" for a person and "Edit organization" for an organization
- editing your own profile adds one line saying that email, password and connected sign-ins are
  managed in the account centre, with a link (FR-010)

`Contributor.get_update_url()` reverses the new name. The unused `UserProfileForm` is deleted.

### D3. The forms

`fairdm/contrib/contributors/forms/profile.py`:

- **`LinesField`**: a `CharField` on a text area, one entry per line. It returns a list with
  blank lines dropped and repeats removed, first occurrence kept (FR-014). An optional
  per-entry validator reports the first bad entry by its text.
- **`PersonProfileForm`**: `image`, `first_name`, `last_name`, `name`, `alternative_names`,
  `profile`, `links`, `lang` (FR-007). `name` is required. `links` entries must be `http` or `https` addresses. `lang` is a
  multiple choice over the ISO 639-1 codes the model's validator accepts.
- **`OrganizationProfileForm`**: `image`, `name`, `alternative_names`, `type`, `parent`, `city`,
  `country`, `profile`, `website`, `links` (FR-008). `website` and `links` are read from and
  written to the stored `links` list, website first. `parent` offers every other organization and
  refuses the organization itself and anything beneath it, with a message on the field (FR-012).
- Both: the fields are grouped under headings, drawn as fieldsets, with short related fields
  side by side on a wide screen.
- Both: the image field follows `ProjectForm` (`validate_image_file_size`, a clearable input), so
  a photo or logo can be removed (FR-015) and an oversized one is refused with the limit named.
  The widget's `id` is Django's default, `id_<field>`.

`Organization.clean()` gains the loop check, using a new `Organization.get_descendant_ids()`, so
the administration interface refuses the same choice.

`FAIRDM_PROFILE_FORMS` in `fairdm/conf/settings/` maps `person` and `organization` to the two
shipped forms (FR-022).

### D4. The overview pages

The `Overview` plugin adds to the context:

- `can_edit`: `contributor.is_editable_by(user)`
- `update_url`: the editing page's address
- on each checklist item this feature can fix, `url`: the editing page's address with the field's
  id as its fragment. Person: photo `#id_image`, biography `#id_profile`, links `#id_links`.
  Organization: logo `#id_image`, type `#id_type`, city and country `#id_city`, description
  `#id_profile`, website `#id_website` (the item is met by any link, and the website field is
  where the first one is typed). ORCID, primary affiliation and ROR stay as they are
  (FR-017)

Templates:

- **Person header**: when `can_edit`, a working "Edit profile" button. The "Contact" stand-in is
  still shown to anyone looking at someone else's profile.
- **Person About card**: the "Write your biography" stand-in becomes a link to `#id_profile`.
- **Organization header**: when `can_manage`, the menu's "Edit details" entry is a working link
  and the other two stay disabled. When `can_edit` but not `can_manage` (a community manager),
  a single "Edit details" button and no menu (US-3 scenario 1, edge case "one edit action").
- **Organization About card**: "Write a description" becomes a link to `#id_profile`.
- The checklist stays limited to the people who keep the record (US-3 scenario 11).

### D5. Demo data

`seed_profiles` already makes an owned organization, an unclaimed profile, an inactive account
and an organization with nothing recorded. It gains what the stories need and lacks: an
administrator, an ordinary member and an administrator whose affiliation has ended on the owned
organization, and sign-in accounts holding the Community Manager and Data Curator roles
(`community-manager.user@example.com`, `data-curator.user@example.com`).

### D6. Documentation

- `docs/portal-administration/roles.md`: who may edit person and organization profiles (FR-021)
- `docs/user-guide/account_management/`: editing your profile. A new page for editing an
  organization's profile. Both linked from the guide's index
- `docs/portal-development/contributors.md`: `FAIRDM_PROFILE_FORMS`, the two forms, `LinesField`,
  `is_editable_by`, with an example that runs (FR-022, SC-008)
- `docs/portal-administration/managing-unclaimed-profiles.md`: correcting a profile from the portal
- `CHANGELOG.md`

## Stories and order

The stories run one after another, each from the previous story's accepted commit.

1. **US-1**: `is_editable_by` for a person's own profile, `LinesField`, `PersonProfileForm`, the
   `Update` page, the setting, the person overview wiring, and their documentation.
2. **US-2**: `OrganizationProfileForm`, the loop guard, `is_editable_by` for owners and
   administrators, the organization overview wiring, seed data, and their documentation.
3. **US-3**: the community manager rule on both records, `PortalRoles.is_held_by`, the edit action
   for a community manager on both pages, seed accounts, and the administrator documentation.

## Risks

- **A portal that overrides the overview templates** keeps its disabled stand-ins until it adopts
  the new blocks. Named in the changelog.
- **`FieldTracker` and `auto_now`** on `Contributor.save` are unaffected: the page saves through
  the model form.
