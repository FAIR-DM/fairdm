# Implementation Plan: FairDM Base Views — Documentation & Testing

**Branch**: `012-base-views-docs` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/012-base-views-docs/spec.md`

## Summary

Complete the docstrings for all 7 view classes in `fairdm/views/base.py` using the django-mvp docstring style, write a contributing-docs page at `docs/contributing/base-views.md`, and create an integration test suite at `tests/test_views/test_base.py` that exercises the full request/response cycle for each view class. No behaviour changes to the view classes themselves.

## Technical Context

**Language/Version**: Python 3.13 (per active virtualenv)  
**Primary Dependencies**: Django, django-mvp, django-meta (`MetadataMixin`), django-filter (`FilterView`), django-tables2 (`MVPTableViewMixin`), pytest, pytest-django  
**Storage**: PostgreSQL (test DB via pytest-django)  
**Testing**: pytest + pytest-django; `rf`/`client` fixtures; `RequestFactory`-based integration tests  
**Target Platform**: Django web application (FairDM framework)  
**Project Type**: Framework library  
**Performance Goals**: N/A (documentation + tests only)  
**Constraints**: No runtime behaviour changes. Test assertions use key-presence only for context values (not specific defaults). 100% line coverage of `fairdm/views/base.py`.  
**Scale/Scope**: 7 view classes, 1 test file, 1 docs page

## Constitution Check

*GATE: Must pass before implementation. Re-check after design.*

| Principle | Status | Notes |
|---|---|---|
| I. FAIR-First | ✅ PASS | Feature improves metadata discoverability documentation — directly supports FAIR developer experience |
| II. Domain-Driven Modeling | ✅ PASS | No model changes; existing view design unchanged |
| III. Configuration Over Custom Plumbing | ✅ PASS | Documentation reinforces correct pattern usage |
| IV. Opinionated Defaults | ✅ PASS | Docstrings document existing defaults; no new deps |
| V. Test-First Quality | ✅ PASS | Tests cover all 7 classes; integration tests using `RequestFactory`; 100% line coverage target |
| VI. Documentation Critical | ✅ PASS | This feature *is* the documentation; contributing docs page created |
| VII. Living Demo | ✅ PASS | No demo app changes required; view base classes are already used in demo-adjacent code |

**Gate result**: PASS. No violations. No complexity justification table needed.

## Project Structure

### Documentation (this feature)

```text
specs/012-base-views-docs/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source code changes

```text
fairdm/
└── views/
    └── base.py          ← docstrings updated for all 7 classes

tests/
└── test_views/          ← new directory
    ├── __init__.py      ← new
    └── test_base.py     ← new — integration tests for all 7 view classes

docs/
└── contributing/
    ├── index.md         ← toctree entry added
    └── base-views.md    ← new contributing docs page
```

**Structure Decision**: Django web application, single-project layout. Test directory mirrors `fairdm/views/` per constitution.

## Design

### 1. Docstring format (all 7 classes)

Follow django-mvp's convention. Template per class:

```python
class FairDM<X>View(MetadataMixin, MVP<X>View):
    """<One-sentence purpose>. Use when <scenario>.

    Extends :class:`mvp.views.MVP<X>View` with :class:`meta.views.MetadataMixin`
    to inject SEO metadata context (``meta`` key) into every response.
    Subclass this instead of ``MVP<X>View`` for all FairDM views.

    Config:
        <attr> (<type>): <description>. Default: <value>.

    Override hooks:
        <method>(): <description>.

    Context:
        meta: Injected by ``MetadataMixin``. Contains Open Graph / Twitter Card
            metadata derived from view-level attributes (``title``, ``description``,
            ``image``, etc.).
        <other keys from parent>: See :class:`mvp.views.MVP<X>View`.

    Example::

        class MyView(FairDM<X>View):
            model = MyModel
            <minimal config>
    """
```

Classes with no FairDM-specific attributes (`FairDMTemplateView`, `FairDMDetailView`, `FairDMCreateView`, `FairDMUpdateView`, `FairDMDeleteView`) only need the `Context:` and `Example::` sections since there are no additional `Config:` attributes beyond their parents. `FairDMListView` and `FairDMTableView` both add attributes and need a full `Config:` section.

### 2. Test architecture

Each test class follows this structure:

```python
@pytest.mark.django_db
class TestFairDM<X>View:
    """Integration tests for FairDM<X>View."""

    def test_get_returns_200(self, client, ...):
        ...

    def test_meta_context_key_present(self, client, ...):
        assert "meta" in response.context
```

**URL setup strategy**: Define a minimal concrete subclass and register it in a `urls` module using `pytest-django`'s `@pytest.mark.urls` marker or `override_settings(ROOT_URLCONF=...)` to avoid polluting the global URL conf.

**Factories**: Use `ProjectFactory` and `DatasetFactory` from `fairdm.factories` for model instances. `UserFactory` for authentication.

**Authentication**: `FairDMCreateView`, `FairDMUpdateView`, `FairDMDeleteView` in the framework don't enforce `LoginRequiredMixin` themselves (that's the responsibility of the concrete subclass). Tests will use them without authentication guards in minimal test subclasses.

### 3. Contributing docs page structure (`docs/contributing/base-views.md`)

Sections:

1. **Overview** — Why FairDM has its own view layer (consistency, `MetadataMixin`, framework API)
2. **The three-layer hierarchy** — Django generic views → django-mvp views → FairDM views; diagram or table
3. **Quick reference** — Table: operation → view class → parent → key attributes
4. **View class reference** — One subsection per class with: purpose, when to use, key attributes, code example
5. **SEO metadata with `MetadataMixin`** — Brief explanation of `django-meta` attributes available on all views

## Implementation Order

1. **`fairdm/views/base.py` docstrings** — Pure additive change, zero risk, done first so tests can reference them.
2. **`tests/test_views/test_base.py`** — Written against the documented contracts. Red → Green confirms docstrings match behaviour.
3. **`docs/contributing/base-views.md`** — Written last; uses docstrings and passing tests as source of truth.
4. **`docs/contributing/index.md`** — Single `toctree` entry added.

## Complexity Tracking

No violations. No entries needed.
