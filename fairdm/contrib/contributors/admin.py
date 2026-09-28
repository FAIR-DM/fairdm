"""Admin for contributors, affiliations, claiming and the claiming audit log."""

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
    """Gate writing an Admin or Owner affiliation on ``manage_organization``.

    Setting a type to ADMIN or OWNER, or changing an affiliation that already has one, is a
    management act, so it needs ``manage_organization`` on the organisation. Superusers hold
    that permission already. The admin and both inlines bind the acting user through
    ``bind_affiliation_form_user``, so every route that writes a type reaches this rule.

    Args:
        *args: Passed to ``ModelForm``.
        user: The user submitting the form.
        **kwargs: Passed to ``ModelForm``.
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
        """Refuse setting or changing an Admin or Owner affiliation without ``manage_organization``."""
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

    Built per request so the permission check runs against whoever submitted the form.

    Args:
        form_class: The affiliation form class.
        user: The requesting user.

    Returns:
        The bound form class.
    """

    class BoundAffiliationForm(form_class):
        """Affiliation form with the requesting user preset."""

        def __init__(self, *args, **kwargs):
            kwargs.setdefault("user", user)
            super().__init__(*args, **kwargs)

    return BoundAffiliationForm


class ClaimedStatusFilter(admin.SimpleListFilter):
    """Filter people by claimed or unclaimed status.

    Reads ``is_claimed`` rather than the email, since an invited person has an email but
    has not claimed. A deactivated account no longer counts as claimed.
    """

    title = _("Claimed Status")
    parameter_name = "is_claimed"

    def lookups(self, request, model_admin):
        """Offer claimed and unclaimed."""
        return (
            ("claimed", _("Claimed")),
            ("unclaimed", _("Unclaimed")),
        )

    def queryset(self, request, queryset):
        """Narrow to claimed or unclaimed people."""
        if self.value() == "claimed":
            return queryset.filter(is_active=True, is_claimed=True)
        elif self.value() == "unclaimed":
            return queryset.exclude(is_active=True, is_claimed=True)
        return queryset


class AccountEmailInline(admin.TabularInline):
    """Inline for a person's email addresses."""

    model = EmailAddress
    fields = ["email", "primary", "verified"]
    extra = 0


class ContributionInline(admin.StackedInline):
    """Inline for contributions."""

    extra = 1
    fields = ("profile", "roles")


class ContributorInline(admin.StackedInline):
    """Inline for a contributor's profile."""

    model = Contributor
    fields = ["profile"]
    extra = 0


class AffiliationInline(admin.StackedInline):
    """Inline for a person's affiliations, gated by ``AffiliationForm``."""

    model = Affiliation
    form = AffiliationForm
    fields = [("organization", "type", "is_primary")]
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Bind the requesting user into ``AffiliationForm``."""
        kwargs["form"] = bind_affiliation_form_user(self.form, request.user)
        return super().get_formset(request, obj, **kwargs)


class MemberInline(admin.StackedInline):
    """Inline for an organisation's members, gated by ``AffiliationForm``."""

    model = Affiliation
    form = AffiliationForm
    fk_name = "organization"
    fields = [("person", "type", "is_primary")]
    extra = 0
    verbose_name = "Member"
    verbose_name_plural = "Members"

    def get_formset(self, request, obj=None, **kwargs):
        """Bind the requesting user into ``AffiliationForm``."""
        kwargs["form"] = bind_affiliation_form_user(self.form, request.user)
        return super().get_formset(request, obj, **kwargs)


class IdentifierInline(admin.StackedInline):
    """Inline for a contributor's identifiers."""

    model = ContributorIdentifier
    fields = ["type", "value"]
    extra = 0


class SubOrganizationInline(admin.TabularInline):
    """Inline for an organisation's sub-organisations."""

    model = Organization
    fk_name = "parent"
    fields = ["name"]
    extra = 0
    verbose_name = _("Sub-organization")
    verbose_name_plural = _("Sub-organizations")


@admin.register(Person)
class UserAdmin(BaseUserAdmin, HijackUserAdminMixin, ImportExportModelAdmin):
    """Admin for people, with import, claim links, merging and duplicate suggestions."""

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
    }
    readonly_fields = ["synced_data", "last_synced", "uuid", "added", "modified"]
    fieldsets = (
        (
            "Basic info",
            {
                "fields": (
                    "image",
                    ("first_name", "last_name"),
                    "name",
                    "email",
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
            {"fields": ("groups",)},
        ),
    )

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

    # Without hiding these, `contributors.change_person` would be a route to superuser.
    _SUPERUSER_ONLY_FIELDS = ("is_superuser", "is_staff", "password")

    def get_fieldsets(self, request, obj=None):
        """Drop the account-escalation fields for a non-superuser.

        ``groups`` is dropped too unless the user holds ``auth.view_group``, as a group
        membership grants a role's rights.
        """
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets
        excluded = set(self._SUPERUSER_ONLY_FIELDS)
        if not request.user.has_perm("auth.view_group"):
            excluded.add("groups")
        narrowed = []
        for name, options in fieldsets:
            fields = tuple(
                field for field in options["fields"] if field not in excluded
            )
            if fields:
                narrowed.append((name, {**options, "fields": fields}))
        return narrowed

    def get_form(self, request, obj=None, **kwargs):
        """Drop ``password`` from the built form for a non-superuser."""
        # `password` is a declared form field, which the metaclass re-adds whatever the fieldsets say.
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields.pop("password", None)
        return form

    def _may_manage_persons(self, request):
        """Check whether the user may claim or merge profiles, which needs ``contributors.change_person``.

        Args:
            request: The current request.

        Returns:
            True when the user holds the permission.
        """
        return request.user.has_perm("contributors.change_person")

    def get_actions(self, request):
        """Drop the merge and claim-link actions for users the views would refuse."""
        actions = super().get_actions(request)
        if not self._may_manage_persons(request):
            actions.pop("merge_person_action", None)
            actions.pop("generate_claim_link_action", None)
        return actions

    @admin.display(description=_("Account state"))
    def account_state(self, obj):
        """Show the person's derived account state."""
        return obj.account_state.label

    @admin.action(description=_("Merge selected Person into another"))
    def merge_person_action(self, request, queryset):
        """Redirect to the merge page for the one selected person."""
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
        """Redirect to the claim-link page for the one selected person."""
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

    _DISMISSED_KEY = "contributors_dismissed_candidates"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add possible duplicates, minus those dismissed this session, to the change form."""
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
        """Dismiss a duplicate candidate for this session and return to the change page.

        Args:
            request: The current request.
            pk: The person being edited.
            candidate_pk: The candidate to dismiss.

        Returns:
            A redirect to the person's change page.
        """
        from django.shortcuts import redirect
        from django.urls import reverse

        dismissed = set(request.session.get(self._DISMISSED_KEY, []))
        dismissed.add(candidate_pk)
        request.session[self._DISMISSED_KEY] = list(dismissed)
        return redirect(reverse("admin:contributors_person_change", args=[pk]))

    def get_urls(self):
        """Add the claim-link, merge and dismiss-candidate routes."""
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
        """Render the claim link page for a person.

        A claim token is a credential, so the permission check comes first.

        Args:
            request: The current request.
            pk: The person's primary key.

        Returns:
            The rendered page.

        Raises:
            PermissionDenied: The user may not manage people.
        """
        if not self._may_manage_persons(request):
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
        """Render the merge page for a person and merge them into the chosen person on POST.

        Merging deletes the discarded person and moves their affiliations, permissions, emails
        and social account, so the permission check comes first.

        Args:
            request: The current request.
            pk: The primary key of the person to discard.

        Returns:
            The rendered page, or a redirect to the surviving person after a merge.

        Raises:
            PermissionDenied: The user may not manage people.
        """
        if not self._may_manage_persons(request):
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
    """Add a new-owner selector to the organisation changelist's action bar.

    The transfer action reads the value from ``request.POST`` without validating this form.

    Attributes:
        new_owner: The person to become owner.
    """

    new_owner = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label=_("New owner"),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin for organisations, with ROR sync and ownership transfer actions."""

    base_model = Contributor
    show_in_index = True
    inlines = [MemberInline, SubOrganizationInline]
    action_form = OrganizationActionForm
    list_display = ["name", "city", "country", "lat", "lon"]
    list_filter = ["country"]
    search_fields = ["name"]
    readonly_fields = ["synced_data", "last_synced", "uuid", "added", "modified"]
    # `alternative_names`, `links` and `lang` are JSON arrays that break the widget, so they are left out.
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
    ]

    def get_readonly_fields(self, request, obj: Organization | None = None):
        """Make the synced fields read-only once the organisation has synced data."""
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
        """Queue a ROR sync for each selected organisation that has a ROR identifier."""
        from fairdm.contrib.contributors.tasks import sync_contributor_identifier

        synced_count = 0
        for org in queryset:
            ror_identifier = org.identifiers.filter(type="ROR").first()

            if ror_identifier:
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
        """Transfer the selected organisation to the member chosen in the action bar."""
        from django.core.exceptions import ValidationError

        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one organization to transfer ownership.",
                level="error",
            )
            return

        org = queryset.first()

        if not org.members.exists():
            self.message_user(
                request,
                f"Organization '{org.name}' has no members. Add members before transferring ownership.",
                level="error",
            )
            return

        # Object-level: the model-level change permission alone would let anyone transfer any organisation.
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
    """Administer affiliations directly, gated by ``manage_organization`` on each organisation."""

    form = AffiliationForm
    list_display = ["person", "organization", "type", "is_primary"]
    list_filter = ["type", "is_primary"]
    autocomplete_fields = ["person", "organization"]

    def get_form(self, request, obj=None, **kwargs):
        """Bind the requesting user into ``AffiliationForm``."""
        kwargs["form"] = bind_affiliation_form_user(self.form, request.user)
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        """Limit a non-superuser to affiliations of organisations they own."""
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
        """Refuse changing an affiliation without ``manage_organization`` on its organisation."""
        if obj is not None and not request.user.has_perm(
            "contributors.manage_organization", obj.organization
        ):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Refuse deleting an affiliation without ``manage_organization`` on its organisation."""
        if obj is not None and not request.user.has_perm(
            "contributors.manage_organization", obj.organization
        ):
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ClaimingAuditLog)
class ClaimingAuditLogAdmin(admin.ModelAdmin):
    """Read-only list of claiming audit log entries, which are immutable."""

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
        """Never allow adding an entry."""
        return False

    def has_view_permission(self, request, obj=None):
        """Allow the list but not an entry's detail page."""
        if obj is not None:
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """Never allow changing an entry."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Never allow deleting an entry."""
        return False
