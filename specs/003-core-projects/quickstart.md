# Quickstart Guide: Core Projects MVP

**Phase**: 1 (Design & Contracts)
**Date**: January 14, 2026
**Audience**: Developers implementing the Core Projects MVP feature

## Prerequisites

- FairDM development environment set up (see main README.md)
- Poetry installed and dependencies synced (`poetry install`)
- PostgreSQL running (or SQLite for development)
- Django migrations applied (`poetry run python manage.py migrate`)
- Test database configured

---

## Implementation Workflow

### 1. Model Updates (Test-First)

**Test File**: `tests/unit/core/project/test_models.py`

**Write Tests First** (Red phase):

```python
import pytest
from django.core.exceptions import ValidationError
from fairdm.core.project.models import Project, ProjectDescription, ProjectDate

@pytest.mark.django_db
class TestProjectModel:
    def test_project_creation_with_required_fields(self, project_factory):
        """Test that project can be created with minimal required fields."""
        project = project_factory(name="Test Project", status=0, visibility=0)
        assert project.uuid.startswith("p_")
        assert project.name == "Test Project"

    def test_project_uuid_is_unique(self, project_factory):
        """Test that each project gets a unique UUID."""
        p1 = project_factory()
        p2 = project_factory()
        assert p1.uuid != p2.uuid

class TestProjectDescription:
    def test_duplicate_description_type_raises_validation_error(self, project_factory):
        """Test that adding duplicate description types is prevented."""
        project = project_factory()
        ProjectDescription.objects.create(
            related=project,
            type="Abstract",
            text="First abstract"
        )

        # Attempt to create duplicate should fail
        duplicate = ProjectDescription(
            related=project,
            type="Abstract",
            text="Second abstract"
        )
        with pytest.raises(ValidationError, match="already exists"):
            duplicate.clean()

class TestProjectDate:
    def test_end_date_before_start_date_raises_error(self, project_factory):
        """Test that end date before start date is caught."""
        project = project_factory()
        date_obj = ProjectDate(
            related=project,
            type="Project Start",
            date="2024-12-31",
            end_date="2024-01-01"
        )
        with pytest.raises(ValidationError, match="cannot be before"):
            date_obj.clean()
```

**Implementation** (Green phase):

```python
# In fairdm/core/project/models.py

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Project(BaseModel):
    # ... existing fields ...

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")
        permissions = [
            ("view_project", _("Can view project")),
            ("change_project_metadata", _("Can edit project metadata")),
            ("change_project_settings", _("Can change project settings")),
            ("delete_project", _("Can delete project")),
        ]

class ProjectDescription(AbstractDescription):
    # ... existing fields ...

    class Meta:
        unique_together = [("related", "type")]
        verbose_name = _("project description")
        verbose_name_plural = _("project descriptions")
        ordering = ["order", "added"]

    def clean(self):
        super().clean()
        if self.related_id and self.type:
            existing = ProjectDescription.objects.filter(
                related=self.related, type=self.type
            ).exclude(pk=self.pk).exists()
            if existing:
                raise ValidationError({
                    "type": _("A description of this type already exists for this project.")
                })

class ProjectDate(AbstractDate):
    # ... existing fields ...

    def clean(self):
        super().clean()
        if self.date and self.end_date and self.end_date < self.date:
            raise ValidationError({
                "end_date": _("End date cannot be before start date.")
            })
```

**Run Tests** (should pass now):

```bash
poetry run pytest tests/unit/core/project/test_models.py -v
```

**Create Migration**:

```bash
poetry run python manage.py makemigrations project
poetry run python manage.py migrate
```

---

### 2. Form Implementation (Test-First)

**Test File**: `tests/unit/core/project/test_forms.py`

**Write Tests First**:

```python
import pytest
from fairdm.core.project.forms import ProjectCreateForm, ProjectEditForm

@pytest.mark.django_db
class TestProjectCreateForm:
    def test_form_valid_with_required_fields(self):
        """Test that form is valid with minimal required fields."""
        form = ProjectCreateForm(data={
            "name": "Test Project",
            "status": 0,
            "visibility": 0,
        })
        assert form.is_valid()

    def test_form_invalid_without_name(self):
        """Test that name is required."""
        form = ProjectCreateForm(data={
            "status": 0,
            "visibility": 0,
        })
        assert not form.is_valid()
        assert "name" in form.errors

@pytest.mark.django_db
class TestProjectEditForm:
    def test_cannot_set_public_visibility_for_concept_status(self):
        """Test that Concept projects cannot be made public."""
        form = ProjectEditForm(data={
            "name": "Test",
            "status": 0,  # Concept
            "visibility": 2,  # Public
        })
        assert not form.is_valid()
        assert "visibility" in form.errors
```

**Implementation**:

```python
# In fairdm/core/project/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from fairdm.forms import ModelForm
from .models import Project

class ProjectCreateForm(ModelForm):
    """Streamlined form for project creation."""

    name = forms.CharField(
        label=_("Project name"),
        help_text=_("Enter a descriptive name for your project"),
        max_length=255,
    )
    status = forms.ChoiceField(
        label=_("Status"),
        choices=Project.STATUS_CHOICES.choices,
        initial=Project.STATUS_CHOICES.CONCEPT,
        help_text=_("Select the current phase of your project"),
    )
    visibility = forms.ChoiceField(
        label=_("Visibility"),
        choices=Project.VISIBILITY.choices,
        initial=Project.VISIBILITY.PRIVATE,
        help_text=_("Who should be able to view this project?"),
    )

    class Meta:
        model = Project
        fields = ["name", "status", "visibility", "owner"]

class ProjectEditForm(ModelForm):
    """Comprehensive form for editing project metadata."""

    class Meta:
        model = Project
        fields = [
            "name", "image", "status", "visibility",
            "owner", "funding", "keywords", "tags"
        ]

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        visibility = cleaned_data.get("visibility")

        # Cannot make Concept projects public
        if status == Project.STATUS_CHOICES.CONCEPT and visibility == Project.VISIBILITY.PUBLIC:
            raise ValidationError({
                "visibility": _("Projects in Concept phase cannot be made public. Change status first.")
            })

        return cleaned_data
```

**Run Tests**:

```bash
poetry run pytest tests/unit/core/project/test_forms.py -v
```

---

### 3. View Implementation (Test-First)

**Test File**: `tests/integration/core/project/test_views.py`

**Write Tests First**:

```python
import pytest
from django.urls import reverse
from fairdm.core.project.models import Project

@pytest.mark.django_db
class TestProjectCreateView:
    def test_authenticated_user_can_access_create_view(self, client, user):
        """Test that authenticated users can access create view."""
        client.force_login(user)
        url = reverse("project:project_create")
        response = client.get(url)
        assert response.status_code == 200

    def test_create_project_redirects_to_detail(self, client, user, organization):
        """Test that successful creation redirects to detail view."""
        client.force_login(user)
        url = reverse("project:project_create")
        response = client.post(url, data={
            "name": "New Project",
            "status": 0,
            "visibility": 0,
            "owner": organization.id,
        })
        assert response.status_code == 302
        project = Project.objects.get(name="New Project")
        assert response.url == reverse("project:project_detail", kwargs={"uuid": project.uuid})

@pytest.mark.django_db
class TestProjectDetailView:
    def test_public_project_visible_to_anonymous(self, client, project_factory):
        """Test that public projects are visible to anonymous users."""
        project = project_factory(visibility=2)
        url = reverse("project:project_detail", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_private_project_requires_authentication(self, client, project_factory):
        """Test that private projects require authentication."""
        project = project_factory(visibility=0)
        url = reverse("project:project_detail", kwargs={"uuid": project.uuid})
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login
```

**Implementation**:

```python
# In fairdm/core/project/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.urls import reverse_lazy
from guardian.mixins import PermissionRequiredMixin as ObjectPermissionRequiredMixin
from .models import Project
from .forms import ProjectCreateForm, ProjectEditForm

class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Streamlined project creation view."""
    model = Project
    form_class = ProjectCreateForm
    template_name = "project/project_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Assign permissions to creator
        from guardian.shortcuts import assign_perm
        for perm in ["view_project", "change_project_metadata", "change_project_settings", "delete_project"]:
            assign_perm(f"project.{perm}", self.request.user, self.object)
        return response

    def get_success_url(self):
        return reverse_lazy("project:project_detail", kwargs={"uuid": self.object.uuid})

class ProjectDetailView(DetailView):
    """Project detail view with permissions check."""
    model = Project
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    template_name = "project/project_detail.html"

    def get_queryset(self):
        return Project.objects.with_metadata()

    def dispatch(self, request, *args, **kwargs):
        # Check permissions
        obj = self.get_object()
        if obj.visibility == Project.VISIBILITY.PUBLIC:
            return super().dispatch(request, *args, **kwargs)
        elif not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        # Check object permission
        from guardian.shortcuts import get_objects_for_user
        if not request.user.has_perm("project.view_project", obj):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

**Run Tests**:

```bash
poetry run pytest tests/integration/core/project/test_views.py -v
```

---

### 4. Admin Configuration

**Test File**: `tests/integration/core/project/test_admin.py`

**Write Tests First**:

```python
@pytest.mark.django_db
class TestProjectAdmin:
    def test_admin_can_search_by_name(self, admin_client, project_factory):
        """Test that admin can search projects by name."""
        project_factory(name="Searchable Project")
        project_factory(name="Other Project")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Searchable"})
        assert response.status_code == 200
        assert "Searchable Project" in response.content.decode()
        assert "Other Project" not in response.content.decode()
```

**Implementation**:

```python
# In fairdm/core/project/admin.py

from django.contrib import admin
from .models import Project, ProjectDescription, ProjectDate, ProjectIdentifier

class ProjectDescriptionInline(admin.StackedInline):
    model = ProjectDescription
    extra = 0
    max_num = 10
    fields = ["type", "text", "order"]

class ProjectDateInline(admin.StackedInline):
    model = ProjectDate
    extra = 0
    max_num = 10
    fields = ["type", "date", "end_date", "order"]

class ProjectIdentifierInline(admin.StackedInline):
    model = ProjectIdentifier
    extra = 0
    max_num = 10
    fields = ["type", "identifier", "url", "order"]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "visibility", "owner", "added")
    list_filter = ("status", "visibility", "added")
    search_fields = ("name", "uuid", "owner__name")
    inlines = [ProjectDescriptionInline, ProjectDateInline, ProjectIdentifierInline]
    readonly_fields = ("uuid", "added", "modified")

    fieldsets = (
        (None, {
            "fields": ("uuid", "name", "image", "status", "visibility", "owner")
        }),
        (_("Metadata"), {
            "fields": ("funding", "keywords", "tags")
        }),
        (_("Timestamps"), {
            "fields": ("added", "modified"),
            "classes": ("collapse",)
        }),
    )
```

---

### 5. Template Implementation (Cotton Components)

**Create Components**:

`fairdm/core/project/templates/project/components/project_card.html`:

```django
<c-vars
    project
    show_owner="true"
/>

<div class="card h-100">
    {% if project.image %}
    <img src="{{ project.image.url }}" class="card-img-top" alt="{{ project.name }}">
    {% endif %}
    <div class="card-body">
        <h5 class="card-title">
            <a href="{% url 'project:project_detail' project.uuid %}">{{ project.name }}</a>
        </h5>
        <p class="card-text">
            <span class="badge bg-{{ project.status|status_badge }}">
                {{ project.get_status_display }}
            </span>
            {% if show_owner and project.owner %}
            <small class="text-muted">by {{ project.owner.name }}</small>
            {% endif %}
        </p>
        {% if project.keywords.exists %}
        <div class="mt-2">
            {% for keyword in project.keywords.all|slice:":3" %}
            <span class="badge bg-secondary">{{ keyword.label }}</span>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <div class="card-footer text-muted">
        <small>{% trans "Modified" %} {{ project.modified|timesince }} {% trans "ago" %}</small>
    </div>
</div>
```

**Main List Template** `fairdm/core/project/templates/project/project_list.html`:

```django
{% extends "base.html" %}
{% load cotton %}
{% load i18n %}

{% block content %}
<div class="container">
    <div class="row mb-4">
        <div class="col">
            <h1>{% trans "Projects" %}</h1>
            <a href="{% url 'project:project_create' %}" class="btn btn-primary">
                {% trans "Create Project" %}
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-3">
            <c-project_filters :form="filter_form" />
        </div>
        <div class="col-md-9">
            <div class="row row-cols-1 row-cols-md-2 g-4">
                {% for project in projects %}
                <div class="col">
                    <c-project_card :project="project" />
                </div>
                {% empty %}
                <p>{% trans "No projects found." %}</p>
                {% endfor %}
            </div>

            {% if is_paginated %}
            <nav class="mt-4">
                {% include "pagination.html" %}
            </nav>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

---

### 6. Contract Tests (pytest-playwright)

**Test File**: `tests/contract/core/project/test_creation.py`

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.django_db
def test_complete_project_creation_flow(page: Page, live_server, user, organization):
    """E2E test of project creation workflow."""
    # Login
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("input[name='login']", user.email)
    page.fill("input[name='password']", "password123")
    page.click("button[type='submit']")

    # Navigate to create page
    page.goto(f"{live_server.url}/projects/create/")
    expect(page.locator("h1")).to_contain_text("Create New Project")

    # Fill form
    page.fill("input[name='name']", "E2E Test Project")
    page.select_option("select[name='status']", "0")
    page.select_option("select[name='visibility']", "0")
    page.click("button[type='submit']")

    # Verify redirect to detail page
    expect(page).to_have_url(re.compile(r"/projects/p_[A-Za-z0-9]+/$"))
    expect(page.locator("h1")).to_contain_text("E2E Test Project")
    expect(page.locator(".badge")).to_contain_text("Concept")
```

**Run Contract Tests**:

```bash
poetry run pytest tests/contract/core/project/ -v --headed
```

---

### 7. Update Demo App

**File**: `fairdm_demo/models.py`

```python
"""
Example Project configurations for the FairDM demo application.

This module demonstrates best practices for:
- Custom project types with domain-specific fields
- DataCite funding schema usage
- Proper i18n string wrapping
- Relationship patterns with organizations

See documentation: Developer Guide > Models > Custom Project Types
(docs/developer-guide/models/custom-projects.md)
"""

from fairdm.core.project.models import Project

class ResearchProject(Project):
    """
    Example research project with additional metadata fields.

    Demonstrates:
    - Extending base Project model
    - Adding custom fields for specific research domains
    - Integration with existing infrastructure
    """

    class Meta:
        proxy = True
        verbose_name = _("research project")
```

---

## Development Checklist

### Phase 1: Models & Migrations

- [ ] Update Project model with new permissions
- [ ] Add unique_together to ProjectDescription
- [ ] Add date validation to ProjectDate
- [ ] Update all help_text and verbose_name for i18n
- [ ] Create and apply migrations
- [ ] Run model unit tests

### Phase 2: Forms

- [ ] Implement ProjectCreateForm
- [ ] Implement ProjectEditForm
- [ ] Add form validation logic
- [ ] Create crispy forms layouts
- [ ] Run form unit tests

### Phase 3: Views

- [ ] Implement ProjectCreateView
- [ ] Implement ProjectDetailView
- [ ] Implement ProjectListView
- [ ] Implement ProjectUpdateView
- [ ] Add permission checks
- [ ] Run view integration tests

### Phase 4: Admin

- [ ] Configure ProjectAdmin with inlines
- [ ] Add search and filter configuration
- [ ] Test admin functionality
- [ ] Run admin integration tests

### Phase 5: Templates

- [ ] Create Cotton components (card, filters, metadata)
- [ ] Create list template
- [ ] Create detail template
- [ ] Create form template
- [ ] Test responsive layout

### Phase 6: Contract Tests

- [ ] Write E2E creation flow test
- [ ] Write E2E metadata addition test
- [ ] Write E2E filtering test
- [ ] Run all contract tests with playwright

### Phase 7: Documentation & Demo

- [ ] Update developer guide
- [ ] Update admin guide
- [ ] Update contributor guide
- [ ] Update demo app models with docstrings
- [ ] Link demo code to documentation

---

## Running Tests

### Unit Tests Only

```bash
poetry run pytest tests/unit/core/project/ -v
```

### Integration Tests Only

```bash
poetry run pytest tests/integration/core/project/ -v
```

### Contract Tests Only

```bash
poetry run pytest tests/contract/core/project/ -v --headed
```

### All Project Tests

```bash
poetry run pytest tests/ -k project -v
```

### With Coverage

```bash
poetry run pytest tests/ -k project --cov=fairdm.core.project --cov-report=html
```

---

## Common Issues & Solutions

### Issue: Migration conflicts

**Solution**: Run `python manage.py makemigrations --merge` to create a merge migration

### Issue: Permission denied in tests

**Solution**: Use `guardian.shortcuts.assign_perm()` in test fixtures to grant object permissions

### Issue: Cotton component not rendering

**Solution**: Ensure component is in correct directory and uses `<c-vars>` for parameter definition

### Issue: Date validation not working

**Solution**: Ensure `clean()` method is called; use `full_clean()` in tests

---

## Next Steps

After completing this feature:

1. Run full test suite to ensure no regressions
2. Update documentation (developer, admin, contributor guides)
3. Create demo data fixtures showing best practices
4. Submit pull request with all tests passing
5. Request code review focusing on constitution alignment

---

## Resources

- [Django Forms Documentation](https://docs.djangoproject.com/en/5.1/topics/forms/)
- [django-guardian Documentation](https://django-guardian.readthedocs.io/)
- [django-cotton Documentation](https://django-cotton.com/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [pytest-playwright Documentation](https://playwright.dev/python/docs/test-runners)
- [DataCite Metadata Schema](https://schema.datacite.org/)
- FairDM Constitution (`.specify/memory/constitution.md`)
- FairDM Testing Guide (`.github/instructions/testing.instructions.md`)

---

**Phase 1 Complete** - Ready for Phase 2 (Task Breakdown via `/speckit.tasks` command)
