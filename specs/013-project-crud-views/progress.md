# Progress — 013 Managing a project through the portal

## 2026-08-24T12:50:39+02:00 · Implementer US3 · T001

**Did**: Exported `ProjectDateFactory` from `fairdm/factories/__init__.py`, alongside the
already-exported `ProjectDescriptionFactory` and `ProjectIdentifierFactory`.

**Verified**: `poetry run pytest tests/test_core/test_project/test_factories.py -q` — 2 passed.

**Next**: T002.

**Watch**: the package docstring's "Relations" list (`fairdm/factories/__init__.py:50-55`) was
already incomplete before this task — it omits `ProjectDescriptionFactory`/`ProjectIdentifierFactory`
and several dataset/sample equivalents. Left as-is rather than rewritten out of scope; see `concerns`
in the completion report.

---

## 2026-08-24T12:54:01+02:00 · Implementer US3 · T002

**Did**: Added `fairdm/core/related_records.py` — `RelatedRecordInline` (the shared row-set base:
`fields = ("type", "value")`, `extra = 0`) and four subclasses naming only their model:
`ProjectDateInline`, `ProjectIdentifierInline`, `DatasetDateInline`, `DatasetIdentifierInline`.

Hit a real bug mid-task: `fields` as a list is the same list object `BaseInlineFormSet.__init__`
mutates in place (appends the parent FK's name), so the first formset built from any subclass
permanently corrupted the shared base class attribute for every other subclass. Reproduced with a
failing test, fixed by declaring `fields` as a tuple (Django's own copy-on-write branch for that
case), kept the regression test. See `decisions.md` (Implementer decisions, this task).

**Verified**: `poetry run pytest tests/test_core/test_related_records.py -q` — 12 passed.
`poetry run ruff check fairdm/core/related_records.py tests/test_core/test_related_records.py` — clean.

**Next**: T004 (built next, out of brief order — see `decisions.md`).

**Watch**: nothing.

---

## 2026-08-24T12:54:06+02:00 · Implementer US3 · T004

**Did**: Added `fairdm/core/descriptions.py` — `VocabularyDescriptionsForm`, a plain `forms.Form`
generating one `CharField` per concept in `related_model.VOCABULARY`, labelled with the concept's
name and helped by its definition. `save()` writes, updates or deletes one row per area
(whitespace-only treated as blank).

Originally built in the same module as T002's row sets; split into its own file before committing
so each task's commit stays clean and the module boundary matches who consumes each piece later
(portal row sets vs. the descriptions page). See `decisions.md`.

**Verified**: `poetry run pytest tests/test_core/test_descriptions.py -q` — 6 passed.
`poetry run ruff check fairdm/core/descriptions.py tests/test_core/test_descriptions.py` — clean.

**Next**: T003.

**Watch**: nothing.

---

## 2026-08-24T12:56:01+02:00 · Implementer US3 · T003

**Did**: Added `fairdm/core/formsets.py` — `date_ordering_formset(start_type, end_type, noun)`,
returning a `BaseInlineFormSet` refusing a backwards pair across the whole formset (logic and
message lifted from `ProjectAdmin.DateInlineFormSet`, generalised to take its noun as a parameter).
Pointed `fairdm/core/project/admin.py` and `fairdm/core/dataset/admin.py` at it; deleted the
duplicate `DateInlineFormSet` class body in both (the module-level name stays, now bound to the
shared factory's return value, so `DateInline.formset = DateInlineFormSet` needed no further
change). Removed the now-unused `ValidationError`/`BaseInlineFormSet`/`PartialDate` imports from
both admin modules.

The dataset message's wording narrows from "collection end date"/"collection start date" to the
shared template's "end date"/"start date" (with "dataset" as the noun) — no test asserts on the
literal string, but recorded in `decisions.md` since it's user-facing text that changed on purpose.

**Verified**: `poetry run pytest tests/test_core/test_formsets.py tests/test_core/test_project/test_admin.py tests/test_core/test_dataset/test_admin.py -q`
— 64 passed (5 new + 59 pre-existing, all pre-existing ones still green with no edits).
`poetry run ruff check fairdm/core/formsets.py fairdm/core/project/admin.py fairdm/core/dataset/admin.py tests/test_core/test_formsets.py` — clean.

**Next**: T005.

**Watch**: nothing.

---

## 2026-08-24T12:57:22+02:00 · Implementer US3 · T005

**Did**: Added `tests/test_core/test_project/conftest.py` — `public_project`, `private_project`,
`user_with_change_permission`, `user_with_delete_permission`, `user_with_no_permission`. The three
user fixtures each build their own project and carry it as an in-memory `.project` attribute on the
returned user, so a test can assert the grant using only the one fixture it asked for. See
`decisions.md`.

**Verified**: `poetry run pytest tests/test_core/test_project/test_conftest.py -q` — 5 passed.
`poetry run pytest tests/test_core/test_project -q` — 146 passed (whole package, no regressions from
the new conftest). `poetry run ruff check tests/test_core/test_project/conftest.py tests/test_core/test_project/test_conftest.py` — clean.

**Next**: story complete. Full-suite verify at the completion report.

**Watch**: nothing.
