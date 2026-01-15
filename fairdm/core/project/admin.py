import json

from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from .models import Project, ProjectDescription, ProjectDate, ProjectIdentifier


class DescriptionInline(admin.StackedInline):
    """Inline admin for Project descriptions."""

    model = ProjectDescription
    extra = 0
    max_num = 6


class DateInline(admin.TabularInline):
    """Inline admin for Project dates."""

    model = ProjectDate
    extra = 0
    max_num = 10


class IdentifierInline(admin.TabularInline):
    """Inline admin for Project identifiers."""

    model = ProjectIdentifier
    extra = 0
    max_num = 5


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model.

    Provides comprehensive search, filtering, inline editing, and bulk
    operations for project management through the Django admin interface.

    **Features:**
    - Search by name, UUID, and owner
    - Filter by status, visibility, and date added
    - Inline editing of descriptions, dates, and identifiers
    - Bulk status change operations
    - Bulk export as JSON or DataCite format
    """

    # Search configuration
    search_fields = ("uuid", "name", "owner__name")

    # Inline editors
    inlines = (DescriptionInline, DateInline, IdentifierInline)

    # List view configuration
    list_display = ("name", "status", "visibility", "owner", "added")
    list_filter = ("status", "visibility", "added")
    list_per_page = 50

    # Fieldsets for organized form display
    fieldsets = (
        (
            None,
            {
                "fields": ("image", "name", "status"),
                "description": _("Basic project information"),
            },
        ),
        (
            _("Access & Visibility"),
            {
                "fields": ("owner", "visibility"),
                "classes": ("collapse",),
                "description": _("Control who can access this project"),
            },
        ),
        (
            _("Organization"),
            {
                "fields": ("keywords",),
                "classes": ("collapse",),
                "description": _("Keywords for project discovery"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("funding",),
                "classes": ("collapse",),
                "description": _("Additional project metadata (JSON)"),
            },
        ),
    )

    # Bulk actions
    actions = ["make_concept", "make_active", "make_completed", "export_json", "export_datacite"]

    @admin.action(description=_("Mark selected projects as Concept"))
    def make_concept(self, request, queryset):
        """Bulk action to set projects to Concept status."""
        updated = queryset.update(status=0)
        self.message_user(request, _("%(count)d project(s) marked as Concept.") % {"count": updated})

    @admin.action(description=_("Mark selected projects as Active"))
    def make_active(self, request, queryset):
        """Bulk action to set projects to Active status."""
        updated = queryset.update(status=1)
        self.message_user(request, _("%(count)d project(s) marked as Active.") % {"count": updated})

    @admin.action(description=_("Mark selected projects as Completed"))
    def make_completed(self, request, queryset):
        """Bulk action to set projects to Completed status."""
        updated = queryset.update(status=2)
        self.message_user(request, _("%(count)d project(s) marked as Completed.") % {"count": updated})

    @admin.action(description=_("Export selected projects as JSON"))
    def export_json(self, request, queryset):
        """Bulk action to export projects as JSON."""
        projects_data = []
        for project in queryset:
            data = {
                "uuid": str(project.uuid),
                "name": project.name,
                "status": project.status,
                "visibility": project.visibility.value if hasattr(project.visibility, "value") else project.visibility,
                "added": project.added.isoformat() if project.added else None,
                "modified": project.modified.isoformat() if project.modified else None,
            }
            projects_data.append(data)

        response = HttpResponse(json.dumps(projects_data, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="projects_export.json"'
        return response

    @admin.action(description=_("Export selected projects as DataCite JSON"))
    def export_datacite(self, request, queryset):
        """Bulk action to export projects in DataCite JSON format."""
        datacite_records = []
        for project in queryset:
            # Basic DataCite structure
            record = {
                "id": str(project.uuid),
                "type": "dois",
                "attributes": {
                    "titles": [{"title": project.name}],
                    "publicationYear": project.added.year if project.added else None,
                    "types": {"resourceTypeGeneral": "Project"},
                },
            }
            datacite_records.append(record)

        response = HttpResponse(json.dumps(datacite_records, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="projects_datacite.json"'
        return response
