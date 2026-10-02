"""Where portal staff see who sent what."""

from django.contrib import admin

from .models import ContactMessage, ProblemReport


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Every Contact message's sender, record, subject and time. There is no text to show."""

    list_display = ["sent", "sender", "subject", "content_type", "record"]
    list_filter = ["subject", "content_type"]
    search_fields = ["sender__name", "sender__email"]
    date_hierarchy = "sent"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProblemReport)
class ProblemReportAdmin(admin.ModelAdmin):
    """Every reported problem with its text, its state and who resolved it."""

    list_display = [
        "created",
        "reporter",
        "state",
        "content_type",
        "record",
        "resolved_by",
    ]
    list_filter = ["state", "content_type"]
    search_fields = ["reporter__name", "reporter__email", "description"]
    date_hierarchy = "created"
