# Progress: 020-profile-editing

- 2026-10-01: build branch cut from main at 27a7b65c. Started while #383 was still open, on the maintainer's instruction. Research, plan and tasks written against the specification.

## 2026-10-01T16:05:00Z · Implementer US1 · T001
- Did: wrote `TestLinesField` and `TestPersonProfileForm` in `tests/test_contrib/test_contributors/test_forms/test_profile.py` (new package, with a conftest holding the image upload and a complete submission).
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_forms -q -n0` fails at collection with `ModuleNotFoundError: fairdm.contrib.contributors.forms.profile`, which is the expected red. `uv run pre-commit run --all-files` passes.
- Next: T002, the `is_editable_by` tests.
- Watch: `validate_image_file_size` raises without a code, so the oversize case is asserted on the field only. The tests stay red until T005.

## 2026-10-01T16:15:00Z · Implementer US1 · T002
- Did: added `TestPersonIsEditableBy` (own profile, own profile when not marked claimed, another person, visitor, somebody else's superuser, and the Data Curator, Developer and Portal Administrator roles), `TestOrganizationIsEditableBy` (nobody yet) and `TestContributorUpdateUrl` (the address resolves to `contributor:overview-update`) to `test_models.py`.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_models.py -q -n0 -k "TestPersonIsEditableBy or TestOrganizationIsEditableBy or TestContributorUpdateUrl"` gives 11 failed, for `AttributeError: no attribute 'is_editable_by'` and `NoReverseMatch: contributor-update`. That is the expected red. `uv run pre-commit run --all-files` passes.
- Next: T003, the page tests.
- Watch: the organization test lives in its own class so the next story can extend it.

## 2026-10-01T16:30:00Z · Implementer US1 · T003
- Did: wrote `test_plugins/test_update.py` with `TestPersonUpdate` (scenarios 2 to 6 and 8 to 11 against the real page, a superuser who is somebody else, a missing profile, the changed name on a credited record) and `TestProfileFormsSetting` (setting absent, naming the other kind only, naming a portal form, the shipped default). Moved the `image_upload` and `profile_data` fixtures from the new `test_forms/conftest.py` up to `test_contributors/conftest.py` so the form tests and the page tests share them; no existing fixture changed.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_plugins/test_update.py -q -n0` stops at collection with `ModuleNotFoundError: fairdm.contrib.contributors.forms.profile`, the expected red. `uv run pre-commit run --all-files` passes.
- Next: T004, the overview tests.
- Watch: the checks on message level and field error codes, not wording. The credited-record test requests the project's overview, so it will show whether that page lists its credits; if not, T005 moves it to the page that does.

## 2026-10-01T16:45:00Z · Implementer US1 · T004
- Did: added to `TestPersonOverview` the header edit link on a person's own profile, each checklist item's link and fragment (photo `#id_image`, biography `#id_profile`, links `#id_links`; ORCID unchanged, primary affiliation without a link), the About prompt's link to `#id_profile`, and no link to the editing page on someone else's profile for a visitor, a signed-in person, staff and a superuser.
- Changed a pre-existing test, as `tasks.md` allows for a disabled stand-in this story brings to life: `TestPersonChecklist::test_the_person_is_offered_editing_in_place_of_the_contact_action` pinned the edit action and the biography prompt as disabled buttons. It now asserts that a person's own page has no disabled stand-in in the header or the About card, while someone else's page still has the Contact one. Nothing else in the file changed.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_plugins/test_overview.py -q -n0 -k "TestPersonOverview or TestPersonChecklist"` gives 8 failed, 47 passed. The failures are `NoReverseMatch: overview-update` and the stand-in still being disabled. That is the expected red. `uv run pre-commit run --all-files` passes.
- Next: T005, the implementation.
- Watch: the organization page is untouched in this story.

## 2026-10-01T17:30:00Z · Implementer US1 · T005
- Did, in four commits:
  - `Contributor.is_editable_by` (False), the `Person` override (the signed-in active person themself), `get_update_url()` reversing `contributor:overview-update`, and `UserProfileForm` deleted with its imports.
  - `forms/profile.py` with `LinesField`, `language_choices` and `PersonProfileForm`; `FAIRDM_PROFILE_FORMS` in `conf/settings/auth.py`; the ISO 639-1 code set moved to `ISO_639_1_CODES` in `validators.py`.
  - `plugins/update.py` with `Update` (its own named `check`, `get_form_class` reading the setting) added to `Overview.extra_views`, and `contributors/plugins/update.html` for a Save and Cancel pair and the account centre line.
  - The person overview: `can_edit` and `update_url` in the context, a working edit link, the About prompt linking to `#id_profile`, and checklist links to `#id_image`, `#id_profile` and `#id_links`. The Contact stand-in still shows on anyone else's profile.
- Pre-existing tests changed (named per `tasks.md`): the three `TestPersonChecklist` tests that asserted the ORCID link was the checklist's only link now assert on the ORCID link itself (see decisions D13). The disabled-stand-in test changed in T004.
- Verified: `uv run pytest tests/test_contrib/test_contributors -q -n0` gives 733 passed. `uv run pre-commit run --all-files` passes. `uv run python manage.py makemigrations --check --dry-run` proposes only a third-party `orbit` migration, none for fairdm. Mutation probes: removing the image size validator, removing the language de-duplication and replacing the page's `check` with True each made the matching tests fail, and restoring them made them pass.
- Next: T006, the documentation.
- Watch: `Person.clean` raises errors keyed to `email` and `identifiers`, which the editing form does not carry. Django's model form raises `ValueError` for an error on a field the form lacks, so a person whose stored ORCID identifier is malformed gets a server error on save (a request posting only a name against such a person answered 500). A malformed identifier can only be stored by bypassing `ContributorIdentifier.clean`. Left alone and reported in the completion report.

## 2026-10-01T18:00:00Z · Implementer US1 · T006
- Did: wrote `docs/user-guide/account_management/editing_your_profile.md` and listed it in the account management index and the user guide's contents. Added "Editing a profile" to `docs/portal-development/contributors.md` (`is_editable_by`, the `Update` page, `PersonProfileForm`, `LinesField`, `language_choices`, `FAIRDM_PROFILE_FORMS`, and a portal form that adds the given and family name). Updated `docs/portal-development/overview-pages.md` (the person's edit link, the checklist links, the new `can_edit` and `update_url` context values). Added the changelog entries under Added, Removed and Fixed.
- The example of a portal adding a field is exercised by `TestProfileFormsSetting::test_a_field_the_portals_form_adds_is_saved_with_the_rest`, which uses the same subclass the guide shows. The `LinesField` example was run in a scratch test and printed `['https://example.org', 'https://example.net']`.
- Verified: `forge verify --repo . --base origin/main --steps docs` passes. Its first run flagged `language_choices` as undocumented and the removed module-level `User` in `forms/person.py` as stale on ten pages that quote `User` for another meaning; the first is documented now and the second is avoided by keeping the `User` line as it was. `uv run --group docs sphinx-build` builds the pages, with no warning for any page this story wrote or changed (the build still stops at the theme's index template and warns on three missing screenshots and an index outside any contents list, none of them from this story).
- Next: the full verify and the completion report.
- Watch: the administrator guide (`portal-administration/roles.md`) and the page on editing an organization belong to the next two stories and are not written here.

## 2026-10-01T16:20:00Z · Implementer US2 · T007
- Did: added `TestOrganizationDescendantIds` (none, children, grandchildren, parent and siblings left out, a loop already stored ends), `TestOrganizationParentLoop` (the organization itself, a child and a grandchild refused on `parent`; an unrelated organization, one with children of its own and an unsaved one accepted) and filled in `TestOrganizationIsEditableBy` (owner and administrator may; an ordinary or pending member, a stranger, a visitor, an ended administrator, a deactivated administrator, a Data Curator and a superuser may not; an organization with no keepers is editable by none of them).
- Changed a pre-existing test, as `tasks.md` allows for a stand-in this story brings to life: `TestOrganizationIsEditableBy::test_nobody_may_edit_it_yet` pinned that nobody may edit an organization. It is replaced by the cases above.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_models.py -q -n0 -k "TestOrganizationDescendantIds or TestOrganizationParentLoop or TestOrganizationIsEditableBy"` gives 9 failed, 12 passed. The failures are `AttributeError: no attribute 'get_descendant_ids'`, `DID NOT RAISE ValidationError` for the loop, and `is_editable_by` returning False for an owner and an administrator. That is the expected red.
- Next: T008, the form tests.
- Watch: the passing tests are guards for rules that already hold (an unrelated parent, a member being refused) and stay in to keep the implementation from over-reaching.

## 2026-10-01T16:40:00Z · Implementer US2 · T008
- Did: added `TestOrganizationProfileForm` to `test_forms/test_profile.py` (the exact field set, every field saved, the website shown from and saved as the first stored link with no repeat, clearing the website keeping the other links, non-web addresses refused on their field, a required name, type and country outside their lists refused, the organization itself and one beneath it refused as parent with code `parent_loop` on the `parent` field, a refused parent storing nothing and keeping the rest typed, an unrelated parent and one with children of its own accepted, clearing the parent leaving the sub-organizations, the logo cleared and size-limited). The `organization_profile_data` fixture sits beside `profile_data` in `test_contributors/conftest.py`.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_forms -q -n0` stops at collection with `ImportError: cannot import name 'OrganizationProfileForm'`, the expected red.
- Next: T009, the page tests.
- Watch: the error code `parent_loop` is mine, set on the model's loop refusal in T011.

## 2026-10-01T17:00:00Z · Implementer US2 · T009
- Did: added `TestOrganizationUpdate` to `test_plugins/test_update.py` against the real page: scenarios 2 to 6 and 8 to 11 for the owner, an administrator, a member, a stranger, a Data Curator, a superuser, an ended administrator, a deactivated administrator and a visitor; the form it opens with; every field stored; a changed name on a project the organization owns and on a member's profile; a loop parent refused on the field for itself, a child and a grandchild; the parent cleared with its children left; the cleared name keeping the rest typed; a refused type, country and link; a removed logo; the checklist counting what was filled in after the save; no input for the ROR identifier, members or owner; an organization nobody keeps refused to everyone but a community manager. Every refused request asserts nothing stored.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_plugins/test_update.py -q -n0 -k TestOrganizationUpdate` stops at collection with `ImportError: cannot import name 'OrganizationProfileForm'`, the expected red. `uv run pre-commit run --all-files` passes.
- Next: T010, the overview tests.
- Watch: a deactivated administrator is redirected to sign in, not refused with 403, because Django signs the account out first (brief and decisions D10).
