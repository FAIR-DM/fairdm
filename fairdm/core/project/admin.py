"""Django admin configuration for projects."""

import json

from django.contrib import admin
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from ..choices import ProjectStatus
from ..formsets import date_ordering_formset
from .models import Project, ProjectDate, ProjectDescription, ProjectIdentifier
from .transforms import to_datacite, to_json_ld


class DescriptionInline(admin.StackedInline):
    """Inline admin for project descriptions."""

    model = ProjectDescription
    extra = 0
    max_num = 6


DateInlineFormSet = date_ordering_formset(
    ProjectDate.START_TYPE,
    ProjectDate.END_TYPE,
    _("The project's end date (%(end)s) cannot be before its start date (%(start)s)."),
)


class DateInline(admin.TabularInline):
    """Inline admin for project dates."""

    model = ProjectDate
    formset = DateInlineFormSet
    extra = 0
    max_num = 10


class IdentifierInline(admin.TabularInline):
    """Inline admin for project identifiers."""

    model = ProjectIdentifier
    extra = 0
    max_num = 5


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for projects, with bulk status changes and JSON and DataCite export."""

    search_fields = ("uuid", "name", "owner__name", "identifiers__value")

    inlines = (DescriptionInline, DateInline, IdentifierInline)

    list_display = (
        "name",
        "status",
        "visibility",
        "owner",
        "has_abstract",
        "has_start_date",
        "added",
    )
    list_filter = ("status", "visibility", "added")
    list_per_page = 50

    def get_queryset(self, request):
        """Annotate the abstract and start-date flags on the queryset itself."""
        # Without the annotations, each display method runs an `.exists()` query per row.
        return (
            super()
            .get_queryset(request)
            .annotate(
                _has_abstract=Exists(
                    ProjectDescription.objects.filter(
                        related=OuterRef("pk"), type="Abstract"
                    )
                ),
                _has_start_date=Exists(
                    ProjectDate.objects.filter(
                        related=OuterRef("pk"), type=ProjectDate.START_TYPE
                    )
                ),
            )
        )

    @admin.display(boolean=True, description=_("Abstract"))
    def has_abstract(self, obj):
        """Return whether the project carries an abstract description."""
        return obj._has_abstract

    @admin.display(boolean=True, description=_("Start date"))
    def has_start_date(self, obj):
        """Return whether the project carries a start date."""
        return obj._has_start_date

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

    actions = [
        "make_concept",
        "make_active",
        "make_completed",
        "export_json",
        "export_datacite",
    ]

    @admin.action(description=_("Mark selected projects as Concept"))
    def make_concept(self, request, queryset):
        """Set the selected projects to Concept status."""
        updated = queryset.update(status=ProjectStatus.CONCEPT)
        self.message_user(
            request, _("%(count)d project(s) marked as Concept.") % {"count": updated}
        )

    @admin.action(description=_("Mark selected projects as Active"))
    def make_active(self, request, queryset):
        """Set the selected projects to In progress, which the admin labels Active."""
        updated = queryset.update(status=ProjectStatus.IN_PROGRESS)
        self.message_user(
            request, _("%(count)d project(s) marked as Active.") % {"count": updated}
        )

    @admin.action(description=_("Mark selected projects as Completed"))
    def make_completed(self, request, queryset):
        """Set the selected projects to Complete status."""
        updated = queryset.update(status=ProjectStatus.COMPLETE)
        self.message_user(
            request, _("%(count)d project(s) marked as Completed.") % {"count": updated}
        )

    @admin.action(description=_("Export selected projects as JSON"))
    def export_json(self, request, queryset):
        """Export the selected projects as schema.org JSON-LD."""
        # `to_json_ld` does no prefetching of its own, and an action can cover the whole changelist.
        queryset = queryset.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors__contributor",
            "contributors__roles",
        )
        projects_data = [to_json_ld(project) for project in queryset]

        response = HttpResponse(
            json.dumps(projects_data, indent=2), content_type="application/json"
        )
        response["Content-Disposition"] = 'attachment; filename="projects_export.json"'
        return response

    @admin.action(description=_("Export selected projects as DataCite JSON"))
    def export_datacite(self, request, queryset):
        """Export the selected projects as DataCite JSON."""
        queryset = queryset.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors__contributor",
            "contributors__roles",
        )
        datacite_records = [to_datacite(project) for project in queryset]

        response = HttpResponse(
            json.dumps(datacite_records, indent=2), content_type="application/json"
        )
        response["Content-Disposition"] = (
            'attachment; filename="projects_datacite.json"'
        )
        return response
