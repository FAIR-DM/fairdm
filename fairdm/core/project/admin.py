from django.contrib import admin

from .models import Project, ProjectDescription


class DescriptionInline(admin.StackedInline):
    model = ProjectDescription
    extra = 0
    max_num = 6


# class DateInline(admin.StackedInline):
#     model = ProjectDate
#     extra = 0
#     max_num = 6


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
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
