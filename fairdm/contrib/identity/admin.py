from django.contrib import admin
from django.utils.html import format_html
from parler.admin import TranslatableAdmin
from solo.admin import SingletonModelAdmin

from .models import Authority, Identity


@admin.register(Identity)
class IdentityAdmin(TranslatableAdmin, SingletonModelAdmin):
    """Unified admin interface for portal identity and branding."""

    fieldsets = (
        (
            "Portal Branding",
            {
                "fields": (
                    ("logo_light", "logo_dark"),
                    ("icon_light", "icon_dark"),
                ),
                "description": "Upload brand assets for light and dark themes. SVG recommended for logos.",
            },
        ),
        (
            "Portal Identity",
            {
                "fields": (
                    ("name", "short_name"),
                    "description",
                    "keywords",
                ),
            },
        ),
        (
            "Governing Authority",
            {
                "fields": ("authority_link",),
                "description": "Manage the governing authority/organization information separately.",
            },
        ),
    )
    readonly_fields = ("authority_link",)

    def authority_link(self, obj):
        """Provide a link to manage the Authority singleton."""
        from django.urls import reverse

        authority_url = reverse("admin:identity_authority_change")
        return format_html(
            '<a href="{}" class="button">Manage Governing Authority →</a>',
            authority_url,
        )

    authority_link.short_description = "Authority Management"

    def has_add_permission(self, request):
        """Only one instance allowed (singleton)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Cannot delete the singleton instance."""
        return False


@admin.register(Authority)
class AuthorityAdmin(TranslatableAdmin, SingletonModelAdmin):
    """Admin interface for governing authority information."""

    fieldsets = (
        (
            "Authority Branding",
            {
                "fields": (
                    ("logo_light", "logo_dark"),
                    ("icon_light", "icon_dark"),
                ),
                "description": "Upload brand assets for the governing authority.",
            },
        ),
        (
            "Authority Information",
            {
                "fields": (
                    ("name", "short_name"),
                    "description",
                    "url",
                    "contact",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        """Only one instance allowed (singleton)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Cannot delete the singleton instance."""
        return False
