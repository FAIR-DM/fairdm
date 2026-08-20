from allauth.account.models import EmailAddress
from dal import autocomplete
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from hijack.contrib.admin import HijackUserAdminMixin
from import_export.admin import ImportExportModelAdmin

from fairdm.db import models

from .models import (
    Affiliation,
    ClaimingAuditLog,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)
from .resources import PersonResource


class ClaimedStatusFilter(admin.SimpleListFilter):
    """Filter persons by claimed/unclaimed status.

    Reads the stored claim value (``is_claimed``), not the email address
    (D8): an invited person has an email but has not claimed their account,
    so email presence alone misclassifies them. "Claimed" also respects the
    same precedence Person.account_state would use -- an account that has
    since been deactivated no longer counts as claimed, even though
    is_claimed is still True. Person.account_state itself is US3's work and
    does not exist yet, so this reads is_claimed/is_active directly.
    """

    title = _("Claimed Status")
    parameter_name = "is_claimed"

    def lookups(self, request, model_admin):
        """Return filter options."""
        return (
            ("claimed", _("Claimed")),
            ("unclaimed", _("Unclaimed")),
        )

    def queryset(self, request, queryset):
        """Apply filter to queryset."""
        if self.value() == "claimed":
            return queryset.filter(is_active=True, is_claimed=True)
        elif self.value() == "unclaimed":
            return queryset.exclude(is_active=True, is_claimed=True)
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


class SubOrganizationInline(admin.TabularInline):
    """Inline listing an organization's sub-organizations (self-referencing parent FK)."""

    model = Organization
    fk_name = "parent"
    fields = ["name"]
    extra = 0
    verbose_name = _("Sub-organization")
    verbose_name_plural = _("Sub-organizations")


@admin.register(Person)
class UserAdmin(BaseUserAdmin, HijackUserAdminMixin, ImportExportModelAdmin):
    base_model = Contributor
    show_in_index = True
    change_form_template = "contributors/admin/change_form.html"
    resource_classes = [PersonResource]
    skip_import_confirm = True
    inlines = [AccountEmailInline, AffiliationInline, IdentifierInline]
    list_display = [
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "account_state",
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
        models.ManyToManyField: {
            "widget": autocomplete.ModelSelect2Multiple(url="admin:autocomplete")
        },
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
    readonly_fields = ["synced_data", "last_synced", "uuid", "added", "modified"]
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
                    "uuid",
                    "last_synced",
                    ("added", "modified"),
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

    search_fields = ("email", "name", "uuid")
    ordering = ("last_name",)
    actions = ["generate_claim_link_action", "merge_person_action"]

    @admin.display(description=_("Account state"))
    def account_state(self, obj):
        """Report the account state derived from the stored claim/active fields (D8).

        A total function so the four states cannot overlap: inactive if the
        account is deactivated, otherwise claimed, otherwise invited if an
        email address is present, otherwise ghost.
        """
        if not obj.is_active:
            return _("Inactive")
        if obj.is_claimed:
            return _("Claimed")
        if obj.email:
            return _("Invited")
        return _("Ghost")

    @admin.action(description=_("Merge selected Person into another"))
    def merge_person_action(self, request, queryset):
        """Redirect to a merge confirmation page for the selected Person(s)."""
        from django.shortcuts import redirect
        from django.urls import reverse

        if queryset.count() != 1:
            self.message_user(
                request,
                _("Please select exactly one Person to merge."),
                level="error",
            )
            return

        person = queryset.first()
        url = reverse("admin:contributors_person_merge", args=[person.pk])
        return redirect(url)

    @admin.action(description=_("Generate claim link for selected Person"))
    def generate_claim_link_action(self, request, queryset):
        """Generate a shareable one-time claim link for an unclaimed Person."""
        from django.shortcuts import redirect
        from django.urls import reverse

        if queryset.count() != 1:
            self.message_user(
                request,
                _("Please select exactly one Person to generate a claim link for."),
                level="error",
            )
            return

        person = queryset.first()
        url = reverse("admin:contributors_person_claim_link", args=[person.pk])
        return redirect(url)

    # ------------------------------------------------------------------
    # Fuzzy match panel
    # ------------------------------------------------------------------

    _DISMISSED_KEY = "contributors_dismissed_candidates"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Inject fuzzy-match duplicate candidates into the change-form context."""
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )

        extra_context = extra_context or {}
        try:
            person = Person.objects.get(pk=object_id)
        except Person.DoesNotExist:
            return super().change_view(request, object_id, form_url, extra_context)

        dismissed: set = set(request.session.get(self._DISMISSED_KEY, []))
        all_candidates = find_duplicate_candidates(person)
        candidates = [c for c in all_candidates if c["person"].pk not in dismissed]
        extra_context["fuzzy_candidates"] = candidates
        return super().change_view(request, object_id, form_url, extra_context)

    def dismiss_candidate_view(self, request, pk, candidate_pk):
        """Store a dismissed candidate in the session and redirect back to change page."""
        from django.shortcuts import redirect
        from django.urls import reverse

        dismissed = set(request.session.get(self._DISMISSED_KEY, []))
        dismissed.add(candidate_pk)
        request.session[self._DISMISSED_KEY] = list(dismissed)
        return redirect(reverse("admin:contributors_person_change", args=[pk]))

    def get_urls(self):
        from django.urls import path as url_path

        urls = super().get_urls()
        custom_urls = [
            url_path(
                "<int:pk>/claim-link/",
                self.admin_site.admin_view(self.claim_link_view),
                name="contributors_person_claim_link",
            ),
            url_path(
                "<int:pk>/merge/",
                self.admin_site.admin_view(self.merge_view),
                name="contributors_person_merge",
            ),
            url_path(
                "<int:pk>/dismiss-candidate/<int:candidate_pk>/",
                self.admin_site.admin_view(self.dismiss_candidate_view),
                name="contributors_person_dismiss_candidate",
            ),
        ]
        return custom_urls + urls

    def claim_link_view(self, request, pk):
        """Render the claim link page for a Person."""
        from django.shortcuts import get_object_or_404
        from django.template.response import TemplateResponse
        from django.urls import reverse

        from fairdm.contrib.contributors.models import ClaimingAuditLog
        from fairdm.contrib.contributors.utils.tokens import generate_claim_token

        person = get_object_or_404(Person, pk=pk)
        token = generate_claim_token(person)
        claim_url = request.build_absolute_uri(
            reverse("contributors:claim-profile", kwargs={"token": token})
        )
        audit_log = ClaimingAuditLog.objects.for_person(person.pk).order_by(
            "-timestamp"
        )[:20]

        context = {
            **self.admin_site.each_context(request),
            "person": person,
            "claim_url": claim_url,
            "token": token,
            "audit_log": audit_log,
            "opts": self.model._meta,
            "title": _("Generate Claim Link"),
        }
        return TemplateResponse(
            request,
            "contributors/admin/claim_person.html",
            context,
        )

    def merge_view(self, request, pk):
        """Render the merge confirmation/execution page for a Person."""
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, redirect
        from django.template.response import TemplateResponse
        from django.urls import reverse

        from fairdm.contrib.contributors.exceptions import ClaimingError
        from fairdm.contrib.contributors.forms.person import MergePersonForm
        from fairdm.contrib.contributors.services.merge import merge_persons

        person = get_object_or_404(Person, pk=pk)

        if request.method == "POST":
            form = MergePersonForm(request.POST, exclude_pk=person.pk)
            if form.is_valid():
                keep = form.cleaned_data["merge_into"]
                try:
                    merge_persons(person_keep=keep, person_discard=person)
                    messages.success(
                        request,
                        _("Successfully merged %(discard)s into %(keep)s.")
                        % {"discard": person, "keep": keep},
                    )
                    return redirect(
                        reverse("admin:contributors_person_change", args=[keep.pk])
                    )
                except ClaimingError as exc:
                    messages.error(request, str(exc))
        else:
            form = MergePersonForm(exclude_pk=person.pk)

        context = {
            **self.admin_site.each_context(request),
            "person": person,
            "form": form,
            "opts": self.model._meta,
            "title": _("Merge Person"),
        }
        return TemplateResponse(
            request,
            "contributors/admin/merge_person.html",
            context,
        )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    base_model = Contributor
    show_in_index = True
    inlines = [MemberInline, SubOrganizationInline]
    list_display = ["name", "city", "country", "lat", "lon"]
    list_filter = ["country"]
    search_fields = ["name"]
    readonly_fields = ["synced_data", "last_synced", "uuid", "added", "modified"]
    # alternative_names, links and lang are JSON array fields that trigger widget
    # issues; they are simply left out of the fieldsets below rather than excluded.
    fieldsets = (
        (
            None,
            {"fields": ("image", "name", "profile", "parent", "uuid")},
        ),
        (
            _("Location"),
            {"fields": ("city", "country", "location")},
        ),
        (
            _("Synchronisation"),
            {"fields": ("last_synced", "synced_data", ("added", "modified"))},
        ),
    )
    actions = [
        "sync_from_ror",
        "transfer_ownership_action",
    ]  # Add ROR sync and ownership transfer actions

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


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    """Administer affiliations directly, outside the person/organisation inlines (US10)."""

    list_display = ["person", "organization", "type", "is_primary"]
    list_filter = ["type", "is_primary"]
    autocomplete_fields = ["person", "organization"]


@admin.register(ClaimingAuditLog)
class ClaimingAuditLogAdmin(admin.ModelAdmin):
    """Read-only admin view for ClaimingAuditLog entries.

    All claim events are immutable by design — add, change, and delete are disabled.
    """

    list_display = [
        "timestamp",
        "method",
        "source_person",
        "target_person",
        "initiated_by",
        "success",
    ]
    list_filter = ["method", "success"]
    search_fields = ["source_person__name", "target_person__name", "initiated_by__name"]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        # Allow changelist (obj is None) but block the change detail page.
        if obj is not None:
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
