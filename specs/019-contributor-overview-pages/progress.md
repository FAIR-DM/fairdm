# Progress: 019-contributor-overview-pages

- 2026-10-01: build branch cut from main with the reviewed prototype merged in (98a231c7). Plan and tasks written against the specification. Baseline: 6 pre-existing tests red, `deptry` and the docs check red, all folded into US-1.

## 2026-10-01T10:14Z · Implementer US1 · T001

- Did: declared Pillow in `pyproject.toml` and re-locked; added FairDM's `account-center/` route to django-mvp's landing view in `fairdm/conf/urls.py`; moved three `TestPendingAction` tests to `c-actions.pending` and deleted the two badge tests; `plugins/person.py` imports `gettext_lazy`.
- Verified: `uv run pytest tests/test_conf/test_urls.py tests/test_templates/test_includes.py -q -n0` (15 passed, exit 0); `uv run pre-commit run --all-files` (all hooks passed, deptry included).
- Next: T002, the pure helpers.
- Watch: the route sits after the `mvp.urls` include, not before it, because Django reverses a name to the last pattern that carries it. See decisions.md.

## 2026-10-01T10:14Z · Implementer US1 · T002

- Did: added `test_profiles.py` with a class per helper (`link_host`, `language_names`, `ranked_shares`, `fill_slots`, `active_then_recent`).
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_profiles.py -q -n0` (18 passed, exit 0, all green on first run against the prototype). Mutated the `www.` prefix, the reserved slot and the active sort in `profiles.py` and watched three of the tests fail; restored the file afterwards. `uv run pre-commit run --all-files` clean.
- Next: T003, model tests.
- Watch: none.

## 2026-10-01T10:17Z · Implementer US1 · T003

- Did: added a `credited_world` fixture (a person credited on public and private projects, datasets, samples and measurements, with a mate on each private record) and ten test classes in `test_models.py` for visible contributions, the public project and dataset sources (`get_public_projects`, `get_public_datasets`, which do not exist yet), role counts, collaborators, affiliation history, member since, affiliation date display, `to_public_schema_org`, link display and identifier resolver URLs.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_models.py -q -n0` gives 12 failed, 192 passed. The 12 failures are the new tests that find real gaps: private-project datasets, samples and measurements listed, roles and collaborators known only through them counted, a pending or ended primary affiliation in the schema.org data, and the two missing source methods. I read each failure and each is the symptom, not a fixture error. Mutating the collaborator tie order, the affiliation sort and filter, and the member-since states failed the matching tests; models.py restored. `uv run pre-commit run --all-files` clean.
- Next: T004, component tests.
- Watch: the tree is red on purpose until T006, which fixes these.
