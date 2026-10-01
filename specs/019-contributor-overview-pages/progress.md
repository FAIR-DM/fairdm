# Progress: 019-contributor-overview-pages

- 2026-10-01: build branch cut from main with the reviewed prototype merged in (98a231c7). Plan and tasks written against the specification. Baseline: 6 pre-existing tests red, `deptry` and the docs check red, all folded into US-1.

## 2026-10-01T10:14Z · Implementer US1 · T001

- Did: declared Pillow in `pyproject.toml` and re-locked; added FairDM's `account-center/` route to django-mvp's landing view in `fairdm/conf/urls.py`; moved three `TestPendingAction` tests to `c-actions.pending` and deleted the two badge tests; `plugins/person.py` imports `gettext_lazy`.
- Verified: `uv run pytest tests/test_conf/test_urls.py tests/test_templates/test_includes.py -q -n0` (15 passed, exit 0); `uv run pre-commit run --all-files` (all hooks passed, deptry included).
- Next: T002, the pure helpers.
- Watch: the route sits after the `mvp.urls` include, not before it, because Django reverses a name to the last pattern that carries it. See decisions.md.
