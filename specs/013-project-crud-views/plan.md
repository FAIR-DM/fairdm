# Implementation Plan: Project CRUD Views

**Branch**: `013-project-crud-views` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)
**Propagated**: 2026-05-11 — Updated from spec.md refinement: `ProjectForm` as single update form; `ProjectCreateForm` inherits it; `ProjectUpdateForm` removed.
**Propagated**: 2026-05-11 — Updated from spec.md refinement: `TypedChoiceField(coerce=int)` for `status` and `visibility`; concept-private validation rule removed.
**Input**: Feature specification from `/specs/013-project-crud-views/spec.md`

## Summary

Bring the Project model's list, create, update, and delete views into conformance with FairDM base view classes, wire all four URL patterns under the `<model_name>-<action_name>` naming convention, and enforce a model-level guard that blocks deletion of projects with publicly visible datasets. The create view already largely conforms; the update view needs its base class migrated; the delete view must be created from scratch. All views redirect to `project-detail` (create, update) or `project-list` (delete) on success.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: Django 5.x, django-guardian (object permissions), django-filter (ProjectFilter), FairDM base views (`FairDMListView`, `FairDMCreateView`, `FairDMUpdateView`, `FairDMDeleteView`), crispy-forms (existing forms)  
**Storage**: PostgreSQL (primary); SQLite (test/dev)  
**Testing**: pytest, pytest-django  
**Target Platform**: Django web application (server-rendered)  
**Project Type**: Web application — model CRUD views  
**Performance Goals**: N/A for this scope  
**Constraints**: No new migrations required; no new model fields; no UI design work; `ProjectUpdateForm` removed in favour of `ProjectForm` as the single update/base form  
**Scale/Scope**: 4 view classes, 1 URL pattern addition, 1 signal handler modification, 1 custom exception class, 1 form class removed (`ProjectUpdateForm`), 1 form class promoted to base (`ProjectForm`), 1 form class updated to inherit it (`ProjectCreateForm`), test coverage additions

## Constitution Check

### Pre-design gate assessment

| Principle | Status | Notes |
|-----------|--------|-------|
| I. FAIR-First | ✅ Pass | List view exposes public projects; visibility control is preserved |
| II. Domain-Driven Modeling | ✅ Pass | Views are wired to the existing `Project` model with no ad-hoc logic |
| III. Configuration Over Plumbing | ✅ Pass | All views use the FairDM base class layer; no raw Django generic views |
| IV. Opinionated Defaults | ✅ Pass | Uses django-guardian for permissions, established patterns |
| V. Test-First Quality | ✅ Pass | Smoke tests + behaviour tests required before merging (see data-model.md) |
| VI. Documentation Critical | ✅ Pass | No public settings or template blocks added; no doc update needed |
| VII. Living Demo | ✅ Pass | `fairdm_demo` is unaffected by these changes |

No violations. No Complexity Tracking entry needed.

### Post-design re-check

Re-check after Phase 1 design confirmed no new violations:

- `PublicDatasetsProtect` is a thin exception class, not a pattern-level architectural addition
- No new models, migrations, or public APIs introduced

## Project Structure

### Documentation (this feature)

```text
specs/013-project-crud-views/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks — not created here)
```

No `contracts/` directory needed — this feature exposes no external API or public interface contracts.

### Source Code (affected files)

```text
fairdm/core/project/
├── forms.py             # Promote ProjectForm to full base; ProjectCreateForm inherits it;
│                        # remove ProjectUpdateForm
├── models.py            # Add PublicDatasetsProtect exception; narrow pre_delete signal
├── views.py             # Update ProjectListView.order_by; fix ProjectCreateView.get_success_url;
│                        # migrate ProjectUpdateView base class and form_class; add ProjectDeleteView
└── urls.py              # Add project-delete URL pattern

tests/test_core/test_project/
└── test_views.py        # Add smoke tests + deletion behaviour tests
```

**Structure Decision**: In-place modification of existing files only. No new modules. No new templates. The list-item template (`project/project_card.html`) already exists.

## Complexity Tracking

No constitution violations to justify.

---

## Phase 0: Research

**Status**: Complete — see [research.md](research.md)

Key findings:

| # | Unknown | Resolution |
|---|---------|------------|
| R-001 | Creation-date ordering field | `added` (auto_now_add from `fairdm.db.models.Model`) |
| R-002 | Pre-delete signal scope | Exists but too broad; narrows to PUBLIC datasets; raises `PublicDatasetsProtect` |
| R-003 | List-item template | Already exists at `project/project_card.html` |
| R-004 | `get_absolute_url` vs `project-detail` | Different URLs; create view `get_success_url` must be changed |
| R-005 | UpdateView migration | Simple base-class swap; all other attrs stay |
| R-006 | DeleteView design | ~~Custom `post()` with name-check~~ `require_confirmation = True` + `form_valid()` override for `PublicDatasetsProtect` (BUG-001) |
| R-007 | Delete URL path | `projects/<str:uuid>/delete/` |
| R-008 | Exception class location | Module level in `models.py` above signal handler |

---

## Phase 1: Design

**Status**: Complete — see [data-model.md](data-model.md)

### Key design decisions

#### 1. `PublicDatasetsProtect` exception

```python
class PublicDatasetsProtect(Exception):
    def __init__(self, datasets):
        self.datasets = datasets
        super().__init__(...)
```

Defined in `models.py` so both the signal handler (also in `models.py`) and `ProjectDeleteView` (in `views.py`) can import it from the same location without circular imports.

#### 2. Narrowed `pre_delete` signal

```python
@receiver(pre_delete, sender=Project)
def prevent_project_deletion_with_datasets(sender, instance, **kwargs):
    public_datasets = instance.datasets.filter(visibility=Visibility.PUBLIC)
    if public_datasets.exists():
        raise PublicDatasetsProtect(public_datasets)
```

Replaces the existing handler body. Guard no longer fires for private-only datasets.

#### 3. `ProjectListView` ordering expansion

```python
order_by = [
    ("name", _("Name (A-Z)")),
    ("-name", _("Name (Z-A)")),
    ("added", _("Date created (oldest first)")),
    ("-added", _("Date created (newest first)")),
]
```

#### 4. `ProjectCreateView.get_success_url` correction

```python
def get_success_url(self):
    return reverse("project-detail", kwargs={"uuid": self.object.uuid})
```

Replaces `return self.object.get_absolute_url()` (which resolves to `project:overview`, a different URL).

#### 5. `ProjectUpdateView` base class migration

```python
# Before
class ProjectUpdateView(LoginRequiredMixin, UpdateView):

# After
class ProjectUpdateView(LoginRequiredMixin, FairDMUpdateView):
    form_class = ProjectForm  # was ProjectUpdateForm — removed in FR-028 refinement
```

The `form_class` changed from `ProjectUpdateForm` to `ProjectForm` (see design decision #8 below). All other attrs (`get_object()`, `get_success_url()`) stay.

#### 6. `ProjectDeleteView` (new)

> **Bugfix**: 2026-05-11 — BUG-001 Original design used a custom `post()` with a manual `confirm_name` check. This bypassed `MVPDeleteView`'s `require_confirmation` mechanism and resulted in no name-input field being rendered in the template. Corrected below.

```python
class ProjectDeleteView(LoginRequiredMixin, FairDMDeleteView):
    model = Project
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("project-list")
    require_confirmation = True  # renders DeleteConfirmForm in template

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.has_perm("delete_project", obj):
            raise PermissionDenied
        return obj

    def get_confirmation_value(self):
        """User must type the exact project name."""
        return self.object.name

    def form_valid(self, form):
        """Catch PublicDatasetsProtect before delegating to MVPDeleteView."""
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect as e:
            context = self.get_context_data(protected_datasets=e.datasets)
            return self.render_to_response(context)
```

Key points:

- `require_confirmation = True` activates `DeleteConfirmForm` in the template — the user sees a text input labelled "Type the name to confirm".
- `get_confirmation_value()` returns `self.object.name`; `DeleteConfirmForm.clean_confirmation()` strips whitespace and compares.
- No `post()` override. The form validation path handles both the name-mismatch error (via `DeleteConfirmForm`) and the public-dataset guard (via `form_valid()`).
- `HttpResponseRedirect` import no longer needed in `views.py` for this view.

#### 7. `project-delete` URL pattern

```python
path("projects/<str:uuid>/delete/", ProjectDeleteView.as_view(), name="project-delete"),
```

Added after the `project-update` pattern in `urls.py`.

#### 8. Form hierarchy — `ProjectForm` as base (FR-028 refinement)

`ProjectUpdateForm` is removed. `ProjectForm` becomes the single full form class: it declares all fields (`image`, `name`, `status`, `visibility`, `owner`, `funding`) with explicit widgets and help_texts, and sets up the owner queryset in `__init__` (conditional on field presence to support subclasses that exclude it). ~~`ProjectForm.clean()` enforces the concept-private rule~~ — that rule is removed (2026-05-11); concept projects may be made public. `ProjectForm` requires no cross-field `clean()` logic.

The `status` and `visibility` fields MUST use `TypedChoiceField(coerce=int)` so submitted string values are coerced to integers automatically by field validation. No manual `isinstance(x, str): int(x)` conversion in `clean()` is needed or permitted.

`ProjectCreateForm` inherits `ProjectForm` and:

1. Restricts `class Meta(ProjectForm.Meta)` `fields` to `["name", "status", "visibility"]`
2. Overrides the `visibility` field with a `TypedChoiceField(coerce=int)` using a `RadioSelect` widget
3. ~~Overrides `clean()` to bypass the concept-private rule~~ — no `clean()` override needed; the rule no longer exists

```python
class ProjectForm(ModelForm):
    status = forms.TypedChoiceField(
        choices=ProjectStatus.choices,
        coerce=int,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    visibility = forms.TypedChoiceField(
        choices=Visibility.choices,
        coerce=int,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    # ... other fields unchanged
    # No clean() override required


class ProjectCreateForm(ProjectForm):
    visibility = forms.TypedChoiceField(
        choices=Visibility.choices,
        coerce=int,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    class Meta(ProjectForm.Meta):
        fields = ["name", "status", "visibility"]
    # No clean() override required
```

The `ProjectUpdateView.form_class` is updated from `ProjectUpdateForm` to `ProjectForm`.

---

## Implementation Notes

### Test-first order (Constitution Principle V)

Tests MUST be written and observed failing before each implementation step:

1. Write smoke test for `project-delete` GET → observe 404/import error → add view + URL
2. Write deletion behaviour tests → observe failures → implement `ProjectDeleteView` with `require_confirmation = True` and `form_valid()` (BUG-001: NOT a custom `post()`)
3. Write `pre_delete` guard tests → observe failures → update signal handler
4. Write ordering test for `added` → observe failure → update `ProjectListView.order_by`
5. Write redirect test for create view → observe failure (if currently points to `project:overview`) → update `get_success_url`
6. Run full smoke suite → fix `ProjectUpdateView` base class → verify no regressions

**Bugfix**: 2026-05-11 — BUG-001 Updated from bugfix patch

### No migration needed

`PublicDatasetsProtect` is a Python exception class, not a model change. The signal handler change is code-only. No `manage.py makemigrations` step required.

### Import additions in `views.py`

```python
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from fairdm.views import FairDMUpdateView, FairDMDeleteView
from .models import PublicDatasetsProtect
```

Remove `from django.views.generic import ..., UpdateView` once `FairDMUpdateView` replaces it (check if `UpdateView` is still used by `ProjectDetailView` before removing the import).
