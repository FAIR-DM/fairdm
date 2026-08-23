from allauth.account.models import EmailAddress
from dal import autocomplete
from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied
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


class AffiliationForm(forms.ModelForm):
    """The single place that gates writing an Admin/Owner affiliation (Route 1).

    Holding an OWNER affiliation *is* what ``contributors.manage_organization``
    means (``OrganizationPermissionBackend``), so setting an affiliation's
    ``type`` to ADMIN or OWNER -- or changing one that already carries one of
    those types, including demoting, deleting, or merely editing its end date
    -- is itself a management act. Each requires ``manage_organization`` on the
    organisation in question. Superusers already hold that permission through
    ``has_perm``, so no separate superuser branch is needed here.

    ``AffiliationAdmin``, ``AffiliationInline`` and ``MemberInline`` each build
    a per-request subclass of this form via ``bind_affiliation_form_user`` so
    the rule is written once and reached from every route that can write a
    ``type``.
    """

    class Meta:
        model = Affiliation
        fields = "__all__"

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def _user_can_manage(self, organization):
        return bool(self.user) and self.user.has_perm(
            "contributors.manage_organization", organization
        )

    def clean(self):
        cleaned_data = super().clean()

        management_types = (
            Affiliation.MembershipType.ADMIN,
            Affiliation.MembershipType.OWNER,
        )
        new_type = cleaned_data.get("type")
        target_organization = cleaned_data.get("organization") or getattr(
            self.instance, "organization", None
        )

        if (
            new_type in management_types
            and target_organization is not None
            and not self._user_can_manage(target_organization)
        ):
            self.add_error(
                "type",
                _(
                    "You do not have permission to set this affiliation to Admin "
                    "or Owner for %(organization)s."
                )
                % {"organization": target_organization},
            )

        if self.instance.pk:
            original_type = self.instance.type
            original_organization = self.instance.organization
            if (
                original_type in management_types
                and original_organization is not None
                and not self._user_can_manage(original_organization)
            ):
                self.add_error(
                    None,
                    _(
                        "You do not have permission to change this Admin or Owner "
                        "affiliation with %(organization)s."
                    )
                    % {"organization": original_organization},
                )

        return cleaned_data


def bind_affiliation_form_user(form_class, user):
    """Return a subclass of ``form_class`` with ``user`` bound as its default.

    ``AffiliationForm.clean()`` needs the acting user to evaluate
    ``manage_organization``. The standalone admin and both inlines each build
    one of these per request -- in ``get_form``/``get_formset`` -- so the check
    always runs against whoever actually submitted the form.
    """

    class BoundAffiliationForm(form_class):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("user", user)
            super().__init__(*args, **kwargs)

    return BoundAffiliationForm


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
    form = AffiliationForm
    fields = [("organization", "type", "is_primary")]
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Bind the requesting user into ``AffiliationForm`` (Route 1)."""
        kwargs["form"] = bind_affiliation_form_user(self.form, request.user)
        return super().get_formset(request, obj, **kwargs)


class MemberInline(admin.StackedInline):
    """Inline for managing organization members (from Organization perspective)."""

    model = Affiliation
    form = AffiliationForm
    fk_name = "organization"  # Specify which FK to use (Affiliation -> Organization)
    fields = [("person", "type", "is_primary")]
    extra = 0
    verbose_name = "Member"
    verbose_name_plural = "Members"

    def get_formset(self, request, obj=None, **kwargs):
        """Bind the requesting user into ``AffiliationForm`` (Route 1)."""
        kwargs["form"] = bind_affiliation_form_user(self.form, request.user)
        return super().get_formset(request, obj, **kwargs)


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

    def get_actions(self, request):
        """Drop the merge/claim-link actions for a non-superuser (Route 2).

        ``merge_view`` and ``claim_link_view`` themselves are the load-bearing
        gate -- this only keeps the interface from offering an action that
        would redirect a non-superuser into a page that refuses them.
        """
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop("merge_person_action", None)
            actions.pop("generate_claim_link_action", None)
        return actions

    @admin.display(description=_("Account state"))
    def account_state(self, obj):
        """Report the account state derived from the stored claim and active fields (D8).

        Reads the state off the person rather than working it out again here, so this
        column cannot come to disagree with what the rest of the application means by
        claimed, invited, ghost or inactive.
        """
        return obj.account_state.label

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
        """Render the claim link page for a Person.

        Superuser-only (Route 2): a claim token is a credential, and minting
        one is not an ordinary staff operation. Gated first, before anything
        else in this view -- including the reverse() call for
        "contributors:claim-profile", which currently raises NoReverseMatch
        for an unrelated, already-reported reason (that URL is commented out
        in ``urls.py``). Refusing here first keeps this permission check
        observable on its own.
        """
        if not request.user.is_superuser:
            raise PermissionDenied

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
        """Render the merge confirmation/execution page for a Person.

        Superuser-only (Route 2): merging destroys the discarded person's
        identity and moves their affiliations (including any OWNER one),
        object-level permissions, confirmed emails and social account onto
        the surviving record. That is not an ordinary staff operation.
        """
        if not request.user.is_superuser:
            raise PermissionDenied

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


class OrganizationActionForm(ActionForm):
    """Adds the new-owner selector to the organisation changelist's action bar (T135, FR-046).

    Django renders every visible field on ``action_form`` alongside the action dropdown
    (``admin/actions.html``), so this needs no new template. The transfer action reads the
    value straight off ``request.POST`` rather than validating the form, matching how the
    Django admin's own action-form examples do it.
    """

    new_owner = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label=_("New owner"),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    base_model = Contributor
    show_in_index = True
    inlines = [MemberInline, SubOrganizationInline]
    action_form = OrganizationActionForm
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
        """Transfer ownership of the selected organization to the chosen member (FR-046).

        The affiliation-record change (demoting the incumbent, promoting the new owner) is
        ``Organization.transfer_ownership()``'s job, not this action's -- it is not
        reimplemented here (T135). The object-level ``manage_organization`` check below must
        run, and must run before the transfer: without it, any account holding the
        model-level ``change_organization`` permission could transfer any organisation
        (design review SEC-001).
        """
        from django.core.exceptions import ValidationError

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

        # Check user has manage_organization permission -- object-level, not the model-level
        # change permission that merely got them into this action (SEC-001).
        if not request.user.has_perm("contributors.manage_organization", org):
            self.message_user(
                request,
                f"You don't have permission to manage organization '{org.name}'.",
                level="error",
            )
            return

        new_owner_pk = request.POST.get("new_owner")
        new_owner = (
            Person.objects.filter(pk=new_owner_pk).first() if new_owner_pk else None
        )
        if new_owner is None:
            self.message_user(
                request,
                "Select a new owner from the action bar before running this action.",
                level="error",
            )
            return

        try:
            org.transfer_ownership(new_owner)
        except ValidationError as exc:
            self.message_user(request, "; ".join(exc.messages), level="error")
            return

        self.message_user(
            request,
            f"Transferred ownership of '{org.name}' to {new_owner}. "
            f"The previous owner is now an administrator.",
            level="success",
        )


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    """Administer affiliations directly, outside the person/organisation inlines (US10).

    Writing ``type`` is gated by ``AffiliationForm`` (Route 1): a non-superuser
    lacking ``manage_organization`` on the affiliation's organisation cannot set
    it to Admin or Owner, and cannot change one that already is. That covers
    the write; ``has_change_permission``/``has_delete_permission`` below cover
    the surrounding change/delete routes for an existing Admin or Owner row the
    same way, and ``get_queryset`` scopes the changelist itself.
    """

    form = AffiliationForm
    list_display = ["person", "organization", "type", "is_primary"]
    list_filter = ["type", "is_primary"]
    autocomplete_fields = ["person", "organization"]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = bind_affiliation_form_user(self.form, request.user)
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        """Scope a non-superuser to affiliations of organisations they manage.

        Expressed as a subquery through ``AffiliationQuerySet.owners()`` --
        the single place the "current OWNER" rule lives -- rather than a
        Python loop that resolves each organisation in turn.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        managed_organization_ids = (
            Affiliation.objects.owners()
            .filter(person=request.user)
            .values_list("organization_id", flat=True)
        )
        return qs.filter(organization_id__in=managed_organization_ids)

    def has_change_permission(self, request, obj=None):
        """Refuse changing a given affiliation without ``manage_organization``
        on its organisation -- whatever the affiliation's own type is,
        since a non-manager should not be able to reach the change form for
        someone else's row and, via ``AffiliationForm``, promote it there.

        ``obj is None`` (the changelist's own permission check) is left to the
        ordinary model-level permission so the changelist still works.
        """
        if obj is not None and not request.user.has_perm(
            "contributors.manage_organization", obj.organization
        ):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Refuse deleting a given affiliation without ``manage_organization``
        on its organisation. See ``has_change_permission`` above."""
        if obj is not None and not request.user.has_perm(
            "contributors.manage_organization", obj.organization
        ):
            return False
        return super().has_delete_permission(request, obj)


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
