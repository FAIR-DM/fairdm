from django.contrib import admin

from .models import Project, ProjectDescription


class DescriptionInline(admin.StackedInline):
    """Inline admin for Project descriptions."""

    model = ProjectDescription
    extra = 0
    max_num = 6


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model.

    Provides search, filtering, and inline editing of project descriptions
    through the Django admin interface.
    """

    search_fields = ("uuid", "name")
    inlines = (DescriptionInline,)
    list_display = (
        "name",
        "status",
        "added",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "image",
                    "name",
                    "status",
                    # "description",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "owner",
                    "visibility",
                    "keywords",
                )
            },
        ),
    )
