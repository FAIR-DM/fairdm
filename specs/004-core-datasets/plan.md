# Plan — 004 The dataset record

Implements `spec.md` against the decisions in `decisions.md` and the findings in `research.md`.

## Shape of the work

Everything lands in `fairdm/core/dataset/` plus two files outside it: the identifier collection in
`fairdm/core/vocabularies.py`, and the licence seeding step in `fairdm/conf/settings/apps.py` with
its command under `fairdm/management/commands/`.

Four things are removed rather than changed, and naming them here keeps the diff honest:

| Removed | Because |
|---|---|
| `Dataset.ROLE_PERMISSIONS` | Names two roles the vocabulary does not contain; no readers (D-010) |
| `DatasetQuerySet.for_user`, `.with_private`, `.get_visible` | No correct implementation exists once the manager filters; `for_user` gates on an undeclared permission (R1) |
| The six property aliases on the related models | No readers, no other core model has them, and one is the cause of #186 (R5, D-012) |
| The export claims in the admin docstring | Advertise actions that do not exist (D-002) |

## Existing seams this work uses rather than reinvents

Named deliberately, because the projects run found a plan introducing a mechanism the repository
already had:

- **Cross-record date validation** — `ProjectDate.clean()` with `_sibling_value()` and `_precedes()`
  (`fairdm/core/project/models.py:196-250`). Followed, not lifted (R2).
- **Vocabulary collections** — `VocabularyBuilder.Meta.collections` and `from_collection()`, as
  `DatasetDate` and `DatasetDescription` already use.
- **The creator field** — `Project.created_by` (`fairdm/core/project/models.py:113`), including its
  `SET_NULL` and its reasoning. Copied field-for-field.
- **Administrative metadata columns** — `ProjectAdmin.get_queryset()` annotates with `Exists()` and
  exposes boolean columns (`fairdm/core/project/admin.py:121-154`). The dataset abstract and DOI
  columns follow that, not a per-row property.
- **The seeding pipeline** — `DJANGO_SETUP_TOOLS` in `fairdm/conf/settings/apps.py:254`, already
  carrying two fixture loads and a vocabulary preload (R4).
- **The date inline formset check** — `ProjectAdmin`'s `DateInlineFormSet`
  (`fairdm/core/project/admin.py:24-67`) validates start against end across the formset's forms,
  because a formset validates every row before saving any of them and a sibling lookup in the
  database misses a row being added in the same submission. The dataset date inline needs the same.

Nothing here introduces a new mechanism. If a task appears to, it is wrong.

## Migrations

Article IX asks for consolidation. This branch produces **two**:

1. One schema migration carrying `created_by`, `base_manager_name`, the `Meta.ordering` change and
   the identifier vocabulary's narrowed choices.
2. Nothing else. The licence seeding is a management command, not a migration (R4, D-018), and the
   alias removal is Python-only — properties are not fields, so they generate no migration.

`makemigrations --check` is green at the end or the work is not finished.

## Indexing decisions (Article IX)

- `Dataset.created_by` — indexed by virtue of being a foreign key. "Which datasets did this user
  create" is a real query.
- `DatasetIdentifier.value` — already `unique=True` and `db_index=True` on the abstract.
- `DatasetDescription.type` and `DatasetDate.type` — already carry named single-column indexes.
- `Dataset.visibility` — **newly indexed.** Once the default manager filters on it, every query the
  framework issues carries `visibility != PRIVATE`, which makes it the most-used predicate in the
  package. It was unindexed while nothing filtered by it by default.

## Complexity tracking (Article II)

- **A second manager** (`all_objects`) is an addition, justified by R1: a filtered default manager
  without an unfiltered base manager makes related-object access raise `DoesNotExist`. Django's own
  guidance requires the pair.
- **No new dependency.**
- **No new abstraction.** The date comparison helpers are duplicated between `ProjectDate` and
  `DatasetDate` on purpose (R2, Article III).

## Authorisations for pre-existing tests

Article I forbids modifying pre-existing tests without a recorded decision. This work modifies
several, and each is authorised here in advance:

| Test | Change | Authority |
|---|---|---|
| `test_models.py` — 20 skipped tests across literature, privacy and `with_private` | Unskipped, rewritten or deleted | D-004, D-016; the stated reasons for the skips no longer hold |
| `test_models.py:321,387,399,409` — `type="Created"` | Changed to a member of the vocabulary | D-008 |
| `test_models.py:599` — `type="ARK"` | Changed to a member of the vocabulary | D-008, R3 |
| `test_models.py:345,443,534` — vocabulary loops | Replaced by member assertions | R3, SC-004 |
| `test_models.py:1245,1262,1273,1295,1303,1311,1320,962,1003,1032` | Rewritten; each asserts something true of every possible value | SC-009 |
| `test_models.py` — `with_private`/`get_visible`/`for_user` tests | Deleted with the methods | R1 |
| `test_admin.py:162,589,634` — runtime `pytest.skip()` | Bodies restored | US-6 |
| `test_forms.py:98,118,188,223,247,262` | Rewritten; each passes on a false premise | SC-009 |
| `test_views.py:387` — body is `if dataset:` | Rewritten to assert the POST succeeded first | SC-009 |
| `test_filters.py` — the five skipped filter tests | Left alone | The filter set is not this specification's (D-001, #186) |
| `fairdm/factories/core.py:275` — `DatasetDateFactory` default type | Changed to a member; alias writes changed to field names | D-008, D-012 |

Anything not on this list is a finding, not a licence.

## Story order

`US-8` first: it carries the manager change, which every other story's tests read through. Then
`US-1`, `US-2`, `US-3` (the related records, independent of each other), `US-4` (the visibility
guarantees on top of the manager), `US-5`, `US-6` (the admin, which needs the identifier inline from
`US-3`), `US-7`.

## Out of scope, restated

The filter set, the portal pages and forms, the detail page, metadata export, the image field,
funding, the role-to-permission map, and enforcing visibility beyond the record's own default. Each
has its owner in `decisions.md`.
