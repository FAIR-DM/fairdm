# Research: Editing person and organization profiles in the portal

Read against `main` at 27a7b65c on 2026-10-01. There are no planning notes and no sketch for this
feature, so everything below is what the plan needs settled.

## What exists

- **The record.** `Contributor` holds `image`, `name`, `alternative_names`, `profile`, `links`
  and `lang`. The three lists are JSON fields. `Organization` adds `type`, `parent`, `city` and
  `country`. There is no separate website field: an organization's website is one of its links,
  and the checklist's "A website" item is met by any link.
- **The pages to edit from.** `contributors/overview/person.html` and `organization.html`, drawn
  by the `Overview` plugin in `fairdm/contrib/contributors/plugins/overview.py`. The edit action,
  the "Edit details" menu entry and the two "write it" prompts in the About card are disabled
  stand-ins (`c-actions.pending`, `menu-disabled`). The checklist component, `c-card.readiness`,
  already draws a "Fix" link for any item that carries a `url`.
- **The pattern for an editing page.** Projects and datasets each register an `Update` class as an
  additional view of their `Overview` plugin: `Plugin` plus `FairDMUpdateView`, mounted at
  `update/`, with a `check(request, obj)` that decides who may open it. `Plugin` is a
  `PermissionRequiredMixin`, so the check runs on every request, GET and POST alike. A visitor
  is redirected to sign in and a signed-in user without the right gets a 403
  (`handle_no_permission` in Django's `contrib/auth/mixins.py`). An additional view is governed
  by its own `check`, not its owner's.
- **Who keeps an organization.** `Organization.is_managed_by(user)`: a current affiliation of type
  administrator or owner. 019 uses it for the checklist and the management menu.
- **Account states.** `Person.account_state` is one of inactive, claimed, invited and ghost. Only
  "claimed" is a person with an active account.
- **The Community Manager role.** A group named `Community Manager`, declared in
  `fairdm/portal_roles.py` with `contributors.change_person` and `contributors.change_organization`.
- **Image uploads.** `fairdm.core.image_utils.validate_image_file_size` refuses a file over 5 MB
  with a message that says the limit, and `ProjectForm` shows how the image field is declared.
- **Unused code in the way.** `Contributor.get_update_url()` reverses `contributor-update`, a name
  no URL carries. `UserProfileForm` in `forms/person.py` is used by nothing and offers first and
  last name, which the specification does not.

## What had to be settled

### The right to edit cannot be a Django permission

`contributors.change_person` is held by the Portal Administrator role as well as the Community
Manager, and the specification gives Portal Administrators no right to edit in the portal. The
rule also depends on the state of the profile being edited, which a model-level permission cannot
express. So the rule is written once, as a method on the record, and asks for membership of the
Community Manager role by name.

### Superusers

The existing organization permission backend lets a superuser manage any organization. The
specification lists who may edit and ends "nobody else", and SC-003 holds every seeded account,
the superuser included, to exactly that list. The editing pages therefore give a superuser
nothing extra. The administration interface, where a superuser can change any record, is
untouched.

### A person's own profile when the account is signed in but not marked claimed

Only an active account can sign in (`ModelBackend.get_user` returns nothing for an inactive user,
and allauth's backend inherits it), so "the signed-in user is this person" is the test for editing
your own profile. A community manager's right cannot rest on `account_state` alone: `is_claimed`
is set only by the claiming and merge services, so an account made with `createsuperuser`, or by
signing up where email verification is off, is active and in use while still reading as invited.
The test is therefore: the account is inactive, or the person is not claimed and has never signed
in.

### Lists in a form

No form field for a list of strings exists in the package. Alternative names and links are short
lists typed by hand, so a text area with one entry per line is enough, and it needs no JavaScript.
Languages are chosen from a fixed list, so they are a multiple-choice field over the ISO 639-1
codes the model's validator accepts, named in the reader's language.

### Website and other links

The form offers "Website" as one field and "Other links" as a list. They are stored together in
`links`, the website first. Reading the form back, the first link is the website. This keeps the
stored shape as it is, so nothing that reads `links` changes and there is no migration.

### A parent that would form a loop

The specification says the administration interface already refuses this. It does not: nothing in
`Organization.clean` or the admin checks the chain. The guard goes into `Organization.clean`, so
the portal's editing page and the administration interface both get it, and the form reports it
on the parent field.

### Leading to the field

Each form field has a stable element id (`id_image`, `id_profile`, and so on). A checklist item's
"Fix" link is the editing page's address with that id as its fragment, so the browser scrolls to
the field.

### How a portal changes the fields

There is no way to replace a registered page's form from a portal's own code. allauth's
`ACCOUNT_FORMS` setting, which this package already sets, is the model: a setting that maps a name
to a dotted path. `FAIRDM_PROFILE_FORMS = {"person": ..., "organization": ...}` does the same for
the two editing pages, and a portal subclasses the shipped form to add or drop fields.

### Migrations and dependencies

None of either. No stored field changes.
