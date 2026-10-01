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
