# Research: Core Projects MVP

**Phase**: 0 (Outline & Research)
**Date**: January 14, 2026
**Purpose**: Resolve technical unknowns and establish best practices for implementation

## Research Questions & Findings

### 1. DataCite Metadata Schema for Funding

**Question**: What is the exact structure of DataCite's funding metadata schema?

**Research Approach**: Review DataCite Metadata Schema documentation (v4.4)

**Decision**: Use DataCite FundingReference structure

**Rationale**: DataCite FundingReference is the standard for research funding metadata and includes:

- `funderName` (required): Name of funding provider
- `funderIdentifier` (optional): Unique identifier for funder (e.g., Crossref Funder ID, ROR)
- `funderIdentifierType` (optional): Type of identifier (Crossref Funder ID, ROR, GRID, ISNI, Other)
- `awardNumber` (optional): Grant/award number
- `awardURI` (optional): URI for the award
- `awardTitle` (optional): Title of award/grant

**Implementation**: Store as JSONField with schema validation. Example structure:

```json
{
  "funding": [
    {
      "funderName": "National Science Foundation",
      "funderIdentifier": "https://ror.org/021nxhr62",
      "funderIdentifierType": "ROR",
      "awardNumber": "1234567",
      "awardURI": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=1234567",
      "awardTitle": "Understanding Arctic Climate Change"
    }
  ]
}
```

**Alternatives Considered**:

- Custom schema: Rejected because it would not interoperate with DataCite exports
- Separate FundingSource model: Rejected for MVP to reduce complexity; can be added later if needed

---

### 2. Role-Based Permission Patterns in django-guardian

**Question**: What is the best practice for implementing role-based permissions with django-guardian at the object level?

**Research Approach**: Review django-guardian documentation, FairDM existing permission patterns in core models

**Decision**: Use Guardian's object-level permissions with role-based permission groups

**Rationale**:

- Guardian provides `assign_perm(permission, user_or_group, obj)` for object-level permissions
- Create permission groups per project with role-specific permissions
- Map contributor roles to permission sets at assignment time
- Leverage Guardian's efficient permission checking in views/templates

**Implementation Pattern**:

```python
# In models.py Meta class
permissions = [
    ("view_project", "Can view project"),
    ("change_project_metadata", "Can edit project metadata"),
    ("change_project_settings", "Can change project settings"),
    ("delete_project", "Can delete project"),
]

# Permission mapping by role
ROLE_PERMISSIONS = {
    "PrincipalInvestigator": ["view_project", "change_project_metadata", "change_project_settings", "delete_project"],
    "DataManager": ["view_project", "change_project_metadata"],
    "Contributor": ["view_project"],
}

# Assignment pattern (in view/signal)
from guardian.shortcuts import assign_perm

def add_contributor(project, user, role):
    permissions = ROLE_PERMISSIONS.get(role, ["view_project"])
    for perm in permissions:
        assign_perm(f"project.{perm}", user, project)
```

**Alternatives Considered**:

- Django's built-in permissions: Too coarse-grained, no object-level support
- Custom permission middleware: Overly complex, reinvents guardian's wheel
- Field-level permissions: Too granular for MVP, adds significant complexity

---

### 3. Unique Constraints for ProjectDescription Types

**Question**: How to enforce one description per type at database level while maintaining usability?

**Research Approach**: Review Django unique_together constraints, existing FairDM patterns

**Decision**: Use `unique_together` constraint on (project, type) with helpful validation errors

**Rationale**:

- Database-level constraint prevents race conditions
- Django's model validation catches issues before save
- Form validation provides user-friendly messaging
- Existing FairDM models use similar patterns

**Implementation**:

```python
class ProjectDescription(AbstractDescription):
    VOCABULARY = FairDMDescriptions.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta:
        unique_together = [("related", "type")]
        verbose_name = _("project description")
        verbose_name_plural = _("project descriptions")

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
```

**Alternatives Considered**:

- Application-level only: Race condition risk
- Multiple descriptions same type: Violates requirement from clarification session
- Soft uniqueness with warnings: Would allow invalid state

---

### 4. Streamlined Project Creation Forms

**Question**: How to implement GitHub-style streamlined creation while supporting future metadata addition?

**Research Approach**: Review django-crispy-forms patterns, existing FairDM form patterns

**Decision**: Two separate forms - ProjectCreateForm (minimal) and ProjectEditForm (comprehensive)

**Rationale**:

- Separate forms clearly communicate different workflows
- Create form has only required fields: name, status, visibility, owner
- Edit form includes all metadata fields with inline formsets for descriptions/dates/identifiers
- Reduces cognitive load on creation
- Matches user expectation from clarification (GitHub-like simplicity)

**Implementation Pattern**:

```python
class ProjectCreateForm(ModelForm):
    """Streamlined form for project creation - GitHub-style minimal fields."""

    class Meta:
        model = Project
        fields = ["name", "status", "visibility", "owner"]

class ProjectEditForm(ModelForm):
    """Comprehensive form for editing project metadata."""

    class Meta:
        model = Project
        fields = [
            "name", "image", "status", "visibility", "owner",
            "funding", "keywords", "tags"
        ]
```

**Alternatives Considered**:

- Single form with conditional field display: More complex, harder to maintain
- Wizard-style multi-step: Too heavyweight for simple creation
- All fields in create form: Violates requirement for streamlined creation

---

### 5. Query Optimization for Project Lists

**Question**: How to achieve <1s load time and <5 queries for project detail views with 10k projects?

**Research Approach**: Review Django select_related/prefetch_related patterns, existing FairDM QuerySet optimizations

**Decision**: Use custom QuerySet methods with strategic prefetch_related

**Rationale**:

- `select_related` for ForeignKey relationships (owner organization)
- `prefetch_related` for reverse ForeignKey relationships (descriptions, dates, identifiers, contributors)
- Custom QuerySet methods encapsulate optimization logic
- Pagination limits result set (50 per page)

**Implementation Pattern**:

```python
class ProjectQuerySet(models.QuerySet):
    def with_metadata(self):
        """Optimize queries for detail view."""
        return self.select_related(
            "owner"
        ).prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors__contributor",
            "keywords",
            "tags"
        )

    def with_list_data(self):
        """Optimize queries for list view."""
        return self.select_related("owner").prefetch_related("keywords")

# In views
class ProjectDetailView(DetailView):
    queryset = Project.objects.with_metadata()

class ProjectListView(ListView):
    queryset = Project.objects.with_list_data()
    paginate_by = 50
```

**Alternatives Considered**:

- No optimization: Would exceed query budget
- Caching: Premature for MVP, adds complexity
- Denormalization: Violates normalization principles, harder to maintain

---

### 6. Bootstrap 5 + Cotton Component Patterns for Project UI

**Question**: What Cotton component patterns should be used for consistent project UI?

**Research Approach**: Review existing FairDM Cotton components, Bootstrap 5 card/form patterns

**Decision**: Create reusable Cotton components: ProjectCard, ProjectMetadataPanel, ProjectFilterForm

**Rationale**:

- Cotton components ensure UI consistency across application
- Encapsulate Bootstrap 5 markup patterns
- Reusable across list/detail/dashboard views
- Maintainable - changes propagate automatically

**Component Structure**:

```
fairdm/core/project/templates/project/components/
├── project_card.html          # Card display for list view
├── project_metadata.html       # Metadata display for detail view
├── project_filters.html        # Filter form sidebar
└── project_form_fields.html    # Reusable form field layouts
```

**Alternatives Considered**:

- Template includes: Less composable than Cotton components
- Inline template code: Harder to maintain, inconsistent
- React/Vue components: Violates server-rendered requirement

---

### 7. Django Admin Inline Formsets for Related Metadata

**Question**: What's the best pattern for editing descriptions/dates/identifiers inline in admin?

**Research Approach**: Review Django admin inline documentation, existing FairDM admin patterns

**Decision**: Use StackedInline for better UX with related metadata

**Rationale**:

- StackedInline provides clearer visual hierarchy than TabularInline
- Allows for longer text fields (descriptions)
- Existing FairDM pattern (seen in current admin.py)
- Supports extra=0 for cleaner initial display

**Implementation Pattern**:

```python
class ProjectDescriptionInline(admin.StackedInline):
    model = ProjectDescription
    extra = 0
    max_num = 10
    fields = ["type", "text", "order"]

class ProjectDateInline(admin.StackedInline):
    model = ProjectDate
    extra = 0
    max_num = 10
    fields = ["type", "date", "end_date"]

class ProjectIdentifierInline(admin.StackedInline):
    model = ProjectIdentifier
    extra = 0
    max_num = 10
    fields = ["type", "identifier", "url"]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [
        ProjectDescriptionInline,
        ProjectDateInline,
        ProjectIdentifierInline,
    ]
```

**Alternatives Considered**:

- TabularInline: Cramped for long text fields
- Separate admin pages: More clicks, worse UX
- Custom admin templates: Unnecessary complexity for standard pattern

---

### 8. i18n String Wrapping Best Practices

**Question**: What are the Django i18n best practices for user-facing strings?

**Research Approach**: Review Django i18n documentation, existing FairDM i18n patterns

**Decision**: Use `gettext_lazy` (_) for all user-facing strings in models/forms/admin, `gettext` for views

**Rationale**:

- `gettext_lazy` delays translation until string is rendered (required for model/form definitions)
- `gettext` for immediate translation (views, logic)
- Existing FairDM pattern consistently uses this approach
- Supports multiple languages without code changes

**Implementation Checklist**:

- [ ] Model verbose_name, verbose_name_plural, help_text
- [ ] Form field labels, help_text, error messages
- [ ] Admin list_display labels, fieldset titles
- [ ] Template strings (use {% trans %} and {% blocktrans %})
- [ ] Validation error messages
- [ ] Success/info messages

**Pattern**:

```python
from django.utils.translation import gettext_lazy as _

class Project(BaseModel):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("Enter the project name.")
    )

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")
```

**Alternatives Considered**:

- English-only: Violates constitutional requirement
- Runtime translation: Too late for model/form strings
- Translation libraries other than Django's: Unnecessary complexity

---

## Summary of Decisions

| Topic | Decision | Key Technology/Pattern |
|-------|----------|----------------------|
| Funding Schema | DataCite FundingReference | JSONField with validation |
| Permissions | Object-level with role mapping | django-guardian + permission groups |
| Description Uniqueness | unique_together constraint | Database + model validation |
| Creation Forms | Separate create/edit forms | django-crispy-forms |
| Query Optimization | Custom QuerySet methods | select_related + prefetch_related |
| UI Components | Reusable Cotton components | Bootstrap 5 + Cotton |
| Admin Inlines | StackedInline formsets | Django admin |
| Internationalization | gettext_lazy throughout | Django i18n |

All research questions resolved with no remaining clarifications needed. Ready for Phase 1 (Design & Contracts).
