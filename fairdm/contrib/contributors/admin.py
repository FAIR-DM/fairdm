from allauth.account.models import EmailAddress
from dal import autocomplete
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from hijack.contrib.admin import HijackUserAdminMixin
from import_export.admin import ImportExportModelAdmin
from jsonfield_toolkit.models import ArrayField

from fairdm.db import models

from .models import (
    Affiliation,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)
from .resources import PersonResource


class ClaimedStatusFilter(admin.SimpleListFilter):
    """Filter persons by claimed/unclaimed status."""

    title = _("Claimed Status")
    parameter_name = "is_claimed"

    def lookups(self, request, model_admin):
        """Return filter options."""
        return (
            ("claimed", _("Claimed (has email)")),
            ("unclaimed", _("Unclaimed (no email)")),
        )

    def queryset(self, request, queryset):
        """Apply filter to queryset."""
        if self.value() == "claimed":
            return queryset.exclude(email__isnull=True).exclude(email="")
        elif self.value() == "unclaimed":
            return queryset.filter(Q(email__isnull=True) | Q(email=""))
        return queryset


class AccountEmailInline(admin.TabularInline):
    model = EmailAddress
    fields = ["email", "primary", "verified"]
    extra = 0


class ContributionInline(admin.StackedInline):
    # model = Contribution
    extra = 1
    fields = ("profile", "roles")


class ContributorInline(admin.StackedInline):
    model = Contributor
    fields = ["profile"]
    extra = 0


class AffiliationInline(admin.StackedInline):
    model = Affiliation
    fields = [("organization", "type", "is_primary")]
    extra = 0


class MemberInline(admin.StackedInline):
    """Inline for managing organization members (from Organization perspective)."""

    model = Affiliation
    fk_name = "organization"  # Specify which FK to use (Affiliation -> Organization)
    fields = [("person", "type", "is_primary")]
    extra = 0
    verbose_name = "Member"
    verbose_name_plural = "Members"


class IdentifierInline(admin.StackedInline):
    model = ContributorIdentifier
    fields = ["type", "value"]
    extra = 0


# class OrganizationInline(admin.StackedInline):
#     model = Organization
#     fields = ["profile"]
#     extra = 0


@admin.register(Person)
class UserAdmin(BaseUserAdmin, HijackUserAdminMixin, ImportExportModelAdmin):
    base_model = Contributor
    show_in_index = True
    resource_classes = [PersonResource]
    skip_import_confirm = True
    inlines = [AccountEmailInline, AffiliationInline, IdentifierInline]
    list_display = [
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_active",
    ]
    list_filter = (
        ClaimedStatusFilter,
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "affiliations",
    )
    exclude = ("username",)
    formfield_overrides = {
        models.ManyToManyField: {"widget": autocomplete.ModelSelect2Multiple(url="admin:autocomplete")},
        # models.ImageField: {
        #     "widget": ClientsideCroppingWidget(
        #         width=1200,
        #         height=1200,
        #         preview_width=150,
        #         preview_height=150,
        #         # format="webp",  # "jpeg", "png", "webp
        #     )
        # },
        # models.JSONField: {"widget": FlatJSONWidget},
    }
    readonly_fields = ["synced_data", "last_synced"]
    # fieldsets for modifying user
    fieldsets = (
        (
            "Basic info",
            {
                "fields": (
                    "image",
                    ("first_name", "last_name"),
                    "name",
                    "email",
                    # "alternative_names",
                    # "links",
                    "profile",
                    "last_synced",
                )
            },
        ),
        (
            _("Account"),
            {
                "fields": (
                    "password",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "groups",
                    # "user_permissions",
                )
            },
        ),
    )

    # fieldsets for creating new user
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    ("first_name", "last_name"),
                    "email",
                    "password1",
                    "password2",
                )
            },
        ),
    )

    search_fields = ("email", "id", "name")
    ordering = ("last_name",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    base_model = Contributor
    show_in_index = True
    inlines = [MemberInline]  # Add inline for managing members
    list_display = ["name", "city", "country", "lat", "lon"]
    search_fields = ["name"]
    readonly_fields = ["synced_data", "last_synced"]
    exclude = ("alternative_names", "links", "lang")  # Exclude ArrayFields to avoid widget issues
    actions = ["sync_from_ror", "transfer_ownership_action"]  # Add ROR sync and ownership transfer actions
    formfield_overrides = {
        # Use simple Textarea for ArrayFields to avoid missing widget template issues
        ArrayField: {"widget": admin.widgets.AdminTextareaWidget},
    }

    def get_readonly_fields(self, request, obj: Organization | None = None):
        if obj and obj.synced_data:
            return [
                "name",
                "alternative_names",
                "lang",
                "links",
                "lat",
                "lon",
                "city",
                "country",
                *self.readonly_fields,
            ]

        return self.readonly_fields

    @admin.action(description="Sync from ROR")
    def sync_from_ror(self, request, queryset):
        """Trigger ROR sync for selected organizations."""
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        synced_count = 0
        for org in queryset:
            # Find ROR identifier for this organization
            ror_identifier = org.identifiers.filter(type="ROR").first()

            if ror_identifier:
                # Trigger async sync task
                sync_contributor_identifier.delay(ror_identifier.pk)
                synced_count += 1

        if synced_count > 0:
            self.message_user(
                request,
                f"Triggered ROR sync for {synced_count} organization(s).",
                level="success",
            )
        else:
            self.message_user(
                request,
                "No organizations with ROR identifiers found.",
                level="warning",
            )

    @admin.action(description="Transfer Ownership")
    def transfer_ownership_action(self, request, queryset):
        """Transfer ownership for selected organization (single selection only)."""
        from django.shortcuts import redirect
        from django.urls import reverse

        # Validate single selection
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one organization to transfer ownership.",
                level="error",
            )
            return

        org = queryset.first()

        # Check if organization has members
        if not org.members.exists():
            self.message_user(
                request,
                f"Organization '{org.name}' has no members. Add members before transferring ownership.",
                level="error",
            )
            return

        # Check user has manage_organization permission
        if not request.user.has_perm("contributors.manage_organization", org):
            self.message_user(
                request,
                f"You don't have permission to manage organization '{org.name}'.",
                level="error",
            )
            return

        # Redirect to organization change page with info message about ownership transfer
        # The actual transfer should be done via the transfer_ownership view or through
        # a custom admin intermediate page (not implemented here for simplicity)
        self.message_user(
            request,
            f"To transfer ownership of '{org.name}', use the member management inline below. "
            f"Promote a member to OWNER role - the current owner will be automatically demoted to ADMIN.",
            level="info",
        )

        # Redirect to organization change page
        url = reverse("admin:contributors_organization_change", args=[org.pk])
        return redirect(url)
