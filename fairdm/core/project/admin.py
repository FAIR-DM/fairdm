import json

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef
from django.forms import BaseInlineFormSet
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from partial_date import PartialDate

from ..choices import ProjectStatus
from .export import to_datacite, to_json_ld
from .models import Project, ProjectDate, ProjectDescription, ProjectIdentifier


class DescriptionInline(admin.StackedInline):
    """Inline admin for Project descriptions."""

    model = ProjectDescription
    extra = 0
    max_num = 6


class DateInlineFormSet(BaseInlineFormSet):
    """Refuses a backwards Start/End pair across the whole formset.

    A formset validates every form before any of them saves, so
    `ProjectDate.clean()`'s sibling lookup - a database query - sees no
    unsaved sibling when both the start and the end are new rows in the
    same submission, and each form's individual validation short-circuits.
    This reads the Start and End values directly off the forms' own
    `cleaned_data` instead, so the pair is checked whichever of the two (or
    both) is unsaved.
    """

    def clean(self):
        super().clean()

        start_value = None
        end_value = None
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            value = form.cleaned_data.get("value")
            if not value:
                continue
            # The form field stores the raw string; the model field's
            # `PartialDate` conversion only happens on `full_clean()`, which
            # a formset's own `clean()` runs before, so it is done here too.
            if not isinstance(value, PartialDate):
                value = PartialDate(value)
            if form.cleaned_data.get("type") == ProjectDate.START_TYPE:
                start_value = value
            elif form.cleaned_data.get("type") == ProjectDate.END_TYPE:
                end_value = value

        if start_value is None or end_value is None:
            return

        if ProjectDate._precedes(end_value, start_value):
            raise ValidationError(
                _(
                    "The project's end date (%(end)s) cannot be before "
                    "its start date (%(start)s)."
                )
                % {"start": start_value, "end": end_value}
            )


class DateInline(admin.TabularInline):
    """Inline admin for Project dates."""

    model = ProjectDate
    formset = DateInlineFormSet
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
    search_fields = ("uuid", "name", "owner__name", "identifiers__value")

    # Inline editors
    inlines = (DescriptionInline, DateInline, IdentifierInline)

    # List view configuration
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
        """Annotate the abstract/start-date flags on the queryset itself.

        `list_per_page` is 50, and without this the two display methods
        below would each run a `.exists()` query per row - 100 extra
        queries on a full page. `Exists()` subqueries fold both checks into
        the single query the changelist already runs.
        """
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
        """Whether the project carries an abstract description (FR-021)."""
        return obj._has_abstract

    @admin.display(boolean=True, description=_("Start date"))
    def has_start_date(self, obj):
        """Whether the project carries a start date (FR-021)."""
        return obj._has_start_date

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
    actions = [
        "make_concept",
        "make_active",
        "make_completed",
        "export_json",
        "export_datacite",
    ]

    @admin.action(description=_("Mark selected projects as Concept"))
    def make_concept(self, request, queryset):
        """Bulk action to set projects to Concept status."""
        updated = queryset.update(status=ProjectStatus.CONCEPT)
        self.message_user(
            request, _("%(count)d project(s) marked as Concept.") % {"count": updated}
        )

    @admin.action(description=_("Mark selected projects as Active"))
    def make_active(self, request, queryset):
        """Bulk action to set projects to Active status.

        "Active" maps to `ProjectStatus.IN_PROGRESS`: work is under way,
        as distinct from `PLANNING`, which precedes it.
        """
        updated = queryset.update(status=ProjectStatus.IN_PROGRESS)
        self.message_user(
            request, _("%(count)d project(s) marked as Active.") % {"count": updated}
        )

    @admin.action(description=_("Mark selected projects as Completed"))
    def make_completed(self, request, queryset):
        """Bulk action to set projects to Completed status."""
        updated = queryset.update(status=ProjectStatus.COMPLETE)
        self.message_user(
            request, _("%(count)d project(s) marked as Completed.") % {"count": updated}
        )

    @admin.action(description=_("Export selected projects as JSON"))
    def export_json(self, request, queryset):
        """Bulk action to export projects as schema.org JSON-LD (FR-024).

        An admin action can apply to the whole filtered queryset, and
        `to_json_ld` walks each project's descriptions, dates, identifiers
        and contributors - plus a roles query per contribution - with no
        prefetching of its own, so the selection is prefetched here before
        mapping over it.
        """
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
        """Bulk action to export projects in DataCite JSON format (FR-023).

        Same reasoning as `export_json` above - prefetch the selection
        before mapping `to_datacite` over it.
        """
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
