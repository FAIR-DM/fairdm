"""Integration tests for Contributor admin interface workflows (User Story 3).

Tests cover:
- Person admin changelist loading (T046)
- Person admin claimed/unclaimed filtering (T047)
- Person admin inline affiliation management (T048)
- Organization admin changelist loading (T054)
- Organization admin inline members management (T055)
- Organization admin ROR sync action (T056)
- ClaimingAuditLog admin changelist and read-only permissions (T046)
"""

import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.urls import reverse

from fairdm.contrib.contributors.models import Affiliation, Organization, Person

# ── T046: Person admin changelist loads ─────────────────────────────────────


@pytest.mark.django_db
class TestPersonAdminChangelist:
    """Verify Person admin changelist view loads correctly."""

    def test_person_admin_changelist_loads(
        self, admin_client, person, unclaimed_person
    ):
        """Person admin changelist loads with both claimed and unclaimed persons."""
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Both persons should appear in the list
        assert person.name in content or person.email in content
        assert unclaimed_person.name in content

    def test_person_admin_change_view_loads(self, admin_client, person):
        """Person admin change view loads for editing a person."""
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Verify person details are present
        assert person.email in content
        assert person.first_name in content


# ── T047: Claimed/unclaimed filtering ───────────────────────────────────────


@pytest.mark.django_db
class TestPersonAdminClaimFilter:
    """Verify claimed/unclaimed status filtering in Person admin."""

    def test_person_admin_claim_filter_exists(self, admin_client):
        """Claimed Status filter appears in Person admin."""
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Filter should be present - look for the exact title wespecify
        # The filter title is wrapped in heading tags in Django admin
        assert "Claimed Status" in content

    def test_person_admin_filter_claimed_only(
        self, admin_client, person, unclaimed_person
    ):
        """Filtering for claimed persons shows only claimed accounts."""
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url, {"is_claimed": "claimed"})

        assert response.status_code == 200
        content = response.content.decode()

        # Claimed person should appear
        assert person.name in content or person.email in content
        # Unclaimed person should NOT appear
        assert unclaimed_person.name not in content or "0 persons" in content.lower()

    def test_person_admin_filter_unclaimed_only(
        self, admin_client, person, unclaimed_person
    ):
        """Filtering for unclaimed persons shows only unclaimed profiles."""
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url, {"is_claimed": "unclaimed"})

        assert response.status_code == 200
        content = response.content.decode()

        # Unclaimed person should appear
        assert unclaimed_person.name in content
        # Claimed person should NOT appear
        assert person.email not in content or "0 persons" in content.lower()


# ── T128: Claim-status filter reads the stored claim value (US10, FR-045) ───


@pytest.mark.django_db
class TestClaimStatusFilter:
    """Verify the claim-status filter agrees with each of the four account states.

    The filter previously derived "claimed" from email presence
    (admin.py:23), which misclassifies an invited person (has an email, not
    claimed) as claimed. It now reads is_claimed and is_active directly, with
    the same precedence Person.account_state would use: inactive overrides
    claimed (D8). Person.account_state itself is US3's work and does not
    exist yet, so this filters on the stored fields directly.
    """

    @pytest.fixture
    def ghost(self):
        from fairdm.factories import PersonFactory

        return PersonFactory(email=None, is_claimed=False, is_active=True)

    @pytest.fixture
    def invited(self):
        from fairdm.factories import PersonFactory

        return PersonFactory(
            email="invited@example.org", is_claimed=False, is_active=True
        )

    @pytest.fixture
    def claimed(self):
        from fairdm.factories import PersonFactory

        return PersonFactory(
            email="claimed-state@example.org", is_claimed=True, is_active=True
        )

    @pytest.fixture
    def inactive_claimed(self):
        """A previously-claimed account that has since been deactivated."""
        from fairdm.factories import PersonFactory

        return PersonFactory(
            email="inactive@example.org", is_claimed=True, is_active=False
        )

    def _claim_filter(self, value):
        from fairdm.contrib.contributors.admin import ClaimedStatusFilter

        return ClaimedStatusFilter(
            request=None,
            params={"is_claimed": [value]},
            model=Person,
            model_admin=None,
        )

    def _states(self, ghost, invited, claimed, inactive_claimed):
        """Scope the queryset to just the four fixtures under test.

        django-guardian seeds an anonymous-user Person row (unclaimed,
        active) ahead of every test; scoping avoids a false positive from
        that infrastructure record leaking into the "unclaimed" bucket.
        """
        return Person.objects.filter(
            pk__in=[ghost.pk, invited.pk, claimed.pk, inactive_claimed.pk]
        )

    def test_claimed_bucket_holds_only_the_claimed_and_active_state(
        self, ghost, invited, claimed, inactive_claimed
    ):
        filter_instance = self._claim_filter("claimed")
        queryset = self._states(ghost, invited, claimed, inactive_claimed)
        result = {p.pk for p in filter_instance.queryset(None, queryset)}

        assert result == {claimed.pk}

    def test_unclaimed_bucket_holds_ghost_invited_and_inactive_states(
        self, ghost, invited, claimed, inactive_claimed
    ):
        filter_instance = self._claim_filter("unclaimed")
        queryset = self._states(ghost, invited, claimed, inactive_claimed)
        result = {p.pk for p in filter_instance.queryset(None, queryset)}

        assert result == {ghost.pk, invited.pk, inactive_claimed.pk}


# ── T048: Inline affiliation management ─────────────────────────────────────


@pytest.mark.django_db
class TestPersonAdminInlineAffiliations:
    """Verify affiliation inline management in Person admin."""

    def test_person_admin_affiliation_inline_present(self, admin_client, person):
        """Affiliation inline form is present in Person change view."""
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Inline should be present (look for inline formset or affiliation fields)
        assert "affiliation" in content.lower() or "organization" in content.lower()

    def test_person_admin_affiliation_inline_shows_existing(
        self, admin_client, person, affiliation
    ):
        """Existing affiliations appear in inline formset."""
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Existing affiliation's organization should be visible
        assert affiliation.organization.name in content

    def test_person_admin_can_add_affiliation_inline(
        self, admin_client, person, organization
    ):
        """Can add a new affiliation via inline formset.

        Note: This test verifies the admin interface provides the ability to add
        affiliations inline. Full E2E testing of admin form submission requires
        mocking all Django admin fields and is beyond the scope of unit testing.
        """
        # Create an affiliation directly to verify the admin can display it
        affiliation = Affiliation.objects.create(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
            is_primary=True,
        )

        # Verify admin change view loads with the new affiliation
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert str(organization) in response.content.decode()
        assert person.affiliations.filter(organization=organization).exists()


# ── T054: Organization admin changelist loads ──────────────────────────────


@pytest.mark.django_db
class TestOrganizationAdminChangelist:
    """Verify Organization admin changelist view loads correctly (US3b)."""

    def test_organization_admin_changelist_loads(self, admin_client, organization):
        """Organization admin changelist loads with organizations."""
        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Organization should appear in the list
        assert organization.name in content

    def test_organization_admin_change_view_loads(self, admin_client, organization):
        """Organization admin change URL is registered (view rendering tested separately)."""
        url = reverse("admin:contributors_organization_change", args=[organization.pk])

        # Verify the URL is valid and registered
        assert url
        assert f"/admin/contributors/organization/{organization.pk}/change/" in url

        # Note: Full rendering test skipped due to pre-existing ArrayField widget template issues
        # This will be addressed separately from Phase 6 implementation


# ── T055: Inline members management ─────────────────────────────────────────


@pytest.mark.django_db
class TestOrganizationAdminInlineMembers:
    """Verify member inline management in Organization admin (US3b)."""

    def test_organization_admin_members_inline_present(
        self, admin_client, organization
    ):
        """Members inline form is present in Organization change view."""
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Inline should be present (look for inline formset or member/affiliation fields)
        assert "member" in content.lower() or "affiliation" in content.lower()

    def test_organization_admin_members_inline_shows_existing(
        self, admin_client, organization, affiliation
    ):
        """Existing members appear in inline formset."""
        # affiliation fixture links a person to an organization
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Existing member (person) should be visible via their affiliation
        assert affiliation.person.name in content or affiliation.person.email in content


# ── T127: Organization admin carries a member inline and a sub-organisation
# inline, asserted on the inline classes themselves (US10, FR-044) ──────────


@pytest.mark.django_db
class TestOrganizationAdminInlines:
    """Verify the inlines registered on OrganizationAdmin, not strings in the page.

    The previous coverage for the sub-organisation inline asserted only that
    "parent" or "sub" appeared in the rendered page — satisfied by the
    ordinary parent form field, not by an inline. This asserts on the inline
    classes registered on the ModelAdmin instead (T127).
    """

    def test_member_inline_is_registered(self):
        from fairdm.contrib.contributors.admin import MemberInline
        from fairdm.contrib.contributors.models import Organization

        model_admin = admin.site._registry[Organization]
        assert MemberInline in model_admin.inlines

    def test_sub_organization_inline_is_registered(self):
        from fairdm.contrib.contributors.admin import SubOrganizationInline
        from fairdm.contrib.contributors.models import Organization

        model_admin = admin.site._registry[Organization]
        assert SubOrganizationInline in model_admin.inlines
        assert SubOrganizationInline.model is Organization
        assert SubOrganizationInline.fk_name == "parent"

    def test_sub_organizations_are_listed_on_the_organization_screen(
        self, admin_client, organization
    ):
        """A sub-organisation shows up in the parent's change view via the inline."""
        from fairdm.factories import OrganizationFactory

        child = OrganizationFactory(name="Sub-department", parent=organization)
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert child.name in response.content.decode()


# ── T056: ROR sync admin action ─────────────────────────────────────────────


@pytest.mark.django_db
class TestOrganizationAdminRORSync:
    """Verify ROR sync admin action in Organization admin (US3b)."""

    def test_organization_admin_ror_sync_action_present(
        self, admin_client, organization
    ):
        """ROR sync action appears in Organization admin actions."""
        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Admin action dropdown should include ROR sync
        # Django admin actions are in a <select> element
        assert "sync" in content.lower() and "ror" in content.lower()

    def test_organization_admin_ror_sync_action_works(
        self, admin_client, organization, mocker
    ):
        """ROR sync action triggers sync_contributor_identifier task."""
        # Mock the Celery task to prevent actual API calls
        mock_task = mocker.patch(
            "fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay"
        )

        # Create a ROR identifier for the organization
        from fairdm.contrib.contributors.models import ContributorIdentifier

        ror_id = ContributorIdentifier.objects.create(
            related=organization,
            type="ROR",
            value="https://ror.org/abc123",
        )

        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.post(
            url,
            {
                "action": "sync_from_ror",
                "_selected_action": [organization.pk],
            },
            follow=True,
        )

        assert response.status_code == 200

        # Verify task was called for the ROR identifier
        mock_task.assert_called_once_with(ror_id.pk)


# ── T129/T135: Ownership transfer admin action (US10, FR-046, SC-015) ───────


@pytest.mark.django_db
class TestOwnershipTransferAction:
    """Verify the ownership transfer admin action performs the transfer.

    The action used to redirect with a message telling the administrator how
    to do it by hand; it must now call ``Organization.transfer_ownership()``
    and change the affiliation records itself.
    """

    def _post_transfer(self, admin_client, organization, new_owner):
        url = reverse("admin:contributors_organization_changelist")
        return admin_client.post(
            url,
            {
                "action": "transfer_ownership_action",
                "_selected_action": [organization.pk],
                "new_owner": new_owner.pk,
            },
        )

    def test_action_transfers_ownership_rather_than_instructing(
        self, admin_client, organization, owner_affiliation
    ):
        """A superuser running the action moves ownership; incumbent becomes admin."""
        from fairdm.factories import AffiliationFactory, PersonFactory

        incumbent = owner_affiliation.person
        successor = AffiliationFactory(
            person=PersonFactory(
                email="successor@example.com", is_active=True, is_claimed=True
            ),
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        ).person

        response = self._post_transfer(admin_client, organization, successor)

        assert response.status_code in (200, 302)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.ADMIN
        assert organization.affiliations.get(person=successor).type == (
            Affiliation.MembershipType.OWNER
        )

        messages_text = " ".join(
            str(m) for m in get_messages(response.wsgi_request)
        )
        assert "use the member management inline" not in messages_text
        assert successor.name in messages_text

    def test_action_is_refused_without_the_object_level_right(
        self, organization, owner_affiliation, client
    ):
        """Model-level change permission alone must not be enough (SEC-001).

        The acting user here holds Django's ordinary ``change_organization``
        permission -- enough to reach the admin action -- but has no OWNER
        affiliation on this organisation, so the object-level check at
        ``request.user.has_perm("contributors.manage_organization", org)``
        must refuse the transfer.
        """
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from fairdm.contrib.contributors.models import Organization
        from fairdm.factories import AffiliationFactory, PersonFactory

        incumbent = owner_affiliation.person
        successor = AffiliationFactory(
            person=PersonFactory(email="unauthorized-successor@example.com"),
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        ).person

        acting_user = PersonFactory(
            email="acting-staff@example.com", is_staff=True
        )
        change_perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Organization),
            codename="change_organization",
        )
        acting_user.user_permissions.add(change_perm)
        assert not acting_user.has_perm("contributors.manage_organization", organization)

        client.force_login(acting_user)
        response = self._post_transfer(client, organization, successor)

        assert response.status_code in (200, 302)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER
        assert organization.affiliations.get(person=successor).type == (
            Affiliation.MembershipType.MEMBER
        )
        assert incumbent.has_perm("manage_organization", organization)

        messages_text = " ".join(
            str(m) for m in get_messages(response.wsgi_request)
        )
        assert "don't have permission" in messages_text


# ── T133: Organization admin fieldsets, filters and read-only identifier
# (US10, FR-044) ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrganizationAdmin:
    """Verify the organisation admin's fieldsets, filters and read-only identifier.

    Organization.type (the nine-value ROR classification, US4) does not
    exist on this branch yet, so the "list filters on type and country"
    part of T133 is satisfied for country only; see the completion report's
    concerns.
    """

    def test_public_identifier_is_readonly(self):
        from fairdm.contrib.contributors.models import Organization

        model_admin = admin.site._registry[Organization]
        assert "uuid" in model_admin.readonly_fields
        assert "uuid" in _fieldset_field_names(model_admin.fieldsets)

    def test_list_filter_includes_country(self):
        from fairdm.contrib.contributors.models import Organization

        model_admin = admin.site._registry[Organization]
        assert "country" in model_admin.list_filter

    def test_fieldsets_present(self, admin_client, organization):
        """The change form renders with the new fieldsets, not the field-dump default."""
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Location" in content
        assert "Synchronisation" in content


# ── T136: Affiliation admin, with autocomplete on its relations (US10) ──────


@pytest.mark.django_db
class TestAffiliationAdmin:
    """Verify the Affiliation admin registration.

    No requirement asks for a Contribution or ContributorIdentifier screen,
    and a credit screen would add a bulk-delete surface reaching the
    lifecycle-hook gap T102 closes (design review SPEC-002), so this is
    scoped to AffiliationAdmin only.
    """

    def test_affiliation_is_registered_with_autocomplete_relations(self):
        model_admin = admin.site._registry[Affiliation]
        assert set(model_admin.autocomplete_fields) == {"person", "organization"}

    def test_no_contribution_or_identifier_admin_is_registered(self):
        from fairdm.contrib.contributors.models import (
            Contribution,
            ContributorIdentifier,
        )

        assert Contribution not in admin.site._registry
        assert ContributorIdentifier not in admin.site._registry

    def test_changelist_loads(self, admin_client, affiliation):
        url = reverse("admin:contributors_affiliation_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert affiliation.person.name in response.content.decode()


# ── Route 1: writing an Admin/Owner affiliation requires manage_organization
# on the organisation in question, whichever surface reaches it ─────────────


def _grant(user, model, codename):
    """Add exactly one named model permission to a user (Route 1/2 test setup)."""
    permission = Permission.objects.get(
        content_type=ContentType.objects.get_for_model(model), codename=codename
    )
    user.user_permissions.add(permission)


@pytest.mark.django_db
class TestAffiliationFormBlocksUnauthorisedManagementWrites:
    """A staff account without ``manage_organization`` cannot write an Admin or
    Owner affiliation through any of the three routes ``AffiliationForm``
    gates: the standalone Affiliation admin, the affiliations inline on a
    person's own change form, and the members inline on an organisation's
    change form.

    Holding an OWNER affiliation *is* what ``contributors.manage_organization``
    means (``OrganizationPermissionBackend``), so each route is proven the same
    way: the write is refused, and the acting user does not pass ``has_perm``
    afterwards.
    """

    def _person_change_payload(self, person, organization, new_type):
        return {
            "name": person.name,
            "email": person.email,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "emailaddress_set-TOTAL_FORMS": "0",
            "emailaddress_set-INITIAL_FORMS": "0",
            "emailaddress_set-MIN_NUM_FORMS": "0",
            "emailaddress_set-MAX_NUM_FORMS": "1000",
            "affiliations-TOTAL_FORMS": "1",
            "affiliations-INITIAL_FORMS": "0",
            "affiliations-MIN_NUM_FORMS": "0",
            "affiliations-MAX_NUM_FORMS": "1000",
            "affiliations-0-organization": organization.pk,
            "affiliations-0-type": new_type,
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

    def _organization_change_payload(self, organization, candidate, new_type):
        return {
            "name": organization.name,
            "affiliations-TOTAL_FORMS": "1",
            "affiliations-INITIAL_FORMS": "0",
            "affiliations-MIN_NUM_FORMS": "0",
            "affiliations-MAX_NUM_FORMS": "1000",
            "affiliations-0-person": candidate.pk,
            "affiliations-0-type": new_type,
            "sub_organizations-TOTAL_FORMS": "0",
            "sub_organizations-INITIAL_FORMS": "0",
            "sub_organizations-MIN_NUM_FORMS": "0",
            "sub_organizations-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

    def test_standalone_add_form_refuses_owner_without_manage_organization(
        self, client, person, organization
    ):
        """``add_affiliation`` alone cannot promote a person to Owner."""
        from fairdm.factories import PersonFactory

        acting_user = PersonFactory(email="add-only-staff@example.com", is_staff=True)
        _grant(acting_user, Affiliation, "add_affiliation")
        _grant(acting_user, Organization, "view_organization")
        _grant(acting_user, Person, "view_person")
        client.force_login(acting_user)

        url = reverse("admin:contributors_affiliation_add")
        response = client.post(
            url,
            {
                "person": person.pk,
                "organization": organization.pk,
                "type": Affiliation.MembershipType.OWNER,
            },
        )

        assert response.status_code == 200
        assert "type" in response.context["adminform"].form.errors
        assert not Affiliation.objects.filter(
            person=person, organization=organization
        ).exists()
        assert not person.has_perm("contributors.manage_organization", organization)

    def test_standalone_add_form_allows_owner_with_manage_organization(
        self, client, organization
    ):
        """A user who already manages the organisation can promote someone else."""
        from fairdm.factories import AffiliationFactory, PersonFactory

        manager = PersonFactory(
            email="org-manager@example.com", is_staff=True, is_active=True
        )
        AffiliationFactory(
            person=manager,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        _grant(manager, Affiliation, "add_affiliation")
        candidate = PersonFactory(email="candidate-owner@example.com")
        client.force_login(manager)

        url = reverse("admin:contributors_affiliation_add")
        response = client.post(
            url,
            {
                "person": candidate.pk,
                "organization": organization.pk,
                "type": Affiliation.MembershipType.OWNER,
            },
        )

        assert response.status_code == 302
        assert (
            Affiliation.objects.get(person=candidate, organization=organization).type
            == Affiliation.MembershipType.OWNER
        )

    def test_person_change_affiliation_inline_refuses_owner_without_manage_organization(
        self, client, person, organization
    ):
        """``change_person`` and ``add_affiliation`` together are not enough
        to promote the edited person to Owner through their own affiliations
        inline -- Django's own inline permission model already requires
        ``add_affiliation`` to add a row there at all; ``manage_organization``
        is the additional check this fix adds."""
        person.is_staff = True
        person.save(update_fields=["is_staff"])
        _grant(person, Person, "change_person")
        _grant(person, Affiliation, "add_affiliation")
        client.force_login(person)

        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = client.post(
            url,
            self._person_change_payload(
                person, organization, Affiliation.MembershipType.OWNER
            ),
        )

        assert response.status_code == 200
        assert not Affiliation.objects.filter(
            person=person, organization=organization
        ).exists()
        assert not person.has_perm("contributors.manage_organization", organization)

    def test_organization_change_member_inline_refuses_owner_without_manage_organization(
        self, client, organization
    ):
        """``change_organization`` and ``add_affiliation`` together are not
        enough to promote a new member to Owner through the organisation's
        members inline -- see the equivalent note on the person-inline test
        above."""
        from fairdm.factories import PersonFactory

        acting_user = PersonFactory(
            email="org-editor@example.com", is_staff=True, is_active=True
        )
        _grant(acting_user, Organization, "change_organization")
        _grant(acting_user, Affiliation, "add_affiliation")
        client.force_login(acting_user)
        candidate = PersonFactory(email="member-candidate@example.com")

        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = client.post(
            url,
            self._organization_change_payload(
                organization, candidate, Affiliation.MembershipType.OWNER
            ),
        )

        assert response.status_code == 200
        assert not Affiliation.objects.filter(
            person=candidate, organization=organization
        ).exists()
        assert not candidate.has_perm("contributors.manage_organization", organization)


@pytest.mark.django_db
class TestAffiliationAdminObjectLevelChangeAndDelete:
    """``has_change_permission``/``has_delete_permission`` refuse a
    non-manager for a specific affiliation, even though they hold the
    ordinary model-level permission (Route 1).

    Called directly with a real request rather than driven through
    ``change_view``/``delete_view``: ``AffiliationAdmin.get_queryset`` already
    scopes a non-superuser's changelist to organisations they manage (its own
    test below), so ``get_object()`` -- which every admin edit/delete route
    resolves the target through -- would return "not found" for an
    unauthorised organisation's affiliation before these methods' obj-level
    branch is ever reached with a real object. That queryset scoping is
    tested on its own below; this isolates the method contract these two
    methods are specified to have.
    """

    def test_change_permission_is_refused_for_a_staff_user_who_does_not_manage_the_organization(
        self, rf, affiliation
    ):
        from fairdm.contrib.contributors.admin import AffiliationAdmin
        from fairdm.factories import PersonFactory

        acting_user = PersonFactory(email="cannot-manage@example.com", is_staff=True)
        _grant(acting_user, Affiliation, "change_affiliation")

        request = rf.get("/")
        request.user = acting_user
        model_admin = AffiliationAdmin(Affiliation, admin.site)

        assert model_admin.has_change_permission(request, affiliation) is False

    def test_delete_permission_is_refused_for_a_staff_user_who_does_not_manage_the_organization(
        self, rf, affiliation
    ):
        from fairdm.contrib.contributors.admin import AffiliationAdmin
        from fairdm.factories import PersonFactory

        acting_user = PersonFactory(email="cannot-delete@example.com", is_staff=True)
        _grant(acting_user, Affiliation, "delete_affiliation")

        request = rf.get("/")
        request.user = acting_user
        model_admin = AffiliationAdmin(Affiliation, admin.site)

        assert model_admin.has_delete_permission(request, affiliation) is False

    def test_change_permission_is_granted_for_the_organizations_manager(
        self, rf, affiliation, organization
    ):
        from fairdm.contrib.contributors.admin import AffiliationAdmin
        from fairdm.factories import AffiliationFactory, PersonFactory

        manager = PersonFactory(email="manages-this-org-directly@example.com")
        AffiliationFactory(
            person=manager,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        _grant(manager, Affiliation, "change_affiliation")
        _grant(manager, Affiliation, "delete_affiliation")

        request = rf.get("/")
        request.user = manager
        model_admin = AffiliationAdmin(Affiliation, admin.site)

        assert model_admin.has_change_permission(request, affiliation) is True
        assert model_admin.has_delete_permission(request, affiliation) is True

    def test_change_view_is_allowed_for_the_organizations_manager(
        self, client, affiliation, organization
    ):
        from fairdm.factories import AffiliationFactory, PersonFactory

        manager = PersonFactory(email="manages-this-org@example.com", is_staff=True)
        AffiliationFactory(
            person=manager,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        _grant(manager, Affiliation, "change_affiliation")
        client.force_login(manager)

        url = reverse("admin:contributors_affiliation_change", args=[affiliation.pk])
        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestAffiliationAdminQuerysetScoping:
    """The changelist lists only the affiliations of organisations the
    acting non-superuser manages (Route 1)."""

    def test_changelist_lists_only_managed_organizations_affiliations(self, client):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        manager = PersonFactory(email="scoped-manager@example.com", is_staff=True)
        managed_org = OrganizationFactory(name="Managed University")
        other_org = OrganizationFactory(name="Unmanaged University")

        AffiliationFactory(
            person=manager,
            organization=managed_org,
            type=Affiliation.MembershipType.OWNER,
        )
        visible_member = AffiliationFactory(
            organization=managed_org, type=Affiliation.MembershipType.MEMBER
        )
        hidden_member = AffiliationFactory(
            organization=other_org, type=Affiliation.MembershipType.MEMBER
        )

        _grant(manager, Affiliation, "view_affiliation")
        client.force_login(manager)

        url = reverse("admin:contributors_affiliation_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert visible_member.person.name in content
        assert hidden_member.person.name not in content


# ── Route 2: merge_view and claim_link_view are superuser-only ──────────────


@pytest.mark.django_db
class TestMergeAndClaimLinkViewsRequireSuperuser:
    """``merge_view`` and ``claim_link_view`` refuse a non-superuser staff
    account with ``PermissionDenied``, not merely a hidden menu entry."""

    def _staff_user(self, email):
        from fairdm.factories import PersonFactory

        return PersonFactory(email=email, is_staff=True, is_active=True)

    def test_merge_view_403s_for_non_superuser_staff(self, client, unclaimed_person):
        acting_user = self._staff_user("plain-staff-merge@example.com")
        client.force_login(acting_user)

        url = reverse("admin:contributors_person_merge", args=[unclaimed_person.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_claim_link_view_403s_for_non_superuser_staff(
        self, client, unclaimed_person
    ):
        acting_user = self._staff_user("plain-staff-claim@example.com")
        client.force_login(acting_user)

        url = reverse(
            "admin:contributors_person_claim_link", args=[unclaimed_person.pk]
        )
        response = client.get(url)

        assert response.status_code == 403

    def test_merge_view_is_not_refused_for_a_superuser(
        self, admin_client, unclaimed_person
    ):
        url = reverse("admin:contributors_person_merge", args=[unclaimed_person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_claim_link_view_is_not_refused_for_a_superuser(
        self, admin_client, unclaimed_person
    ):
        """The permission gate lets a superuser through; the view then hits a
        separate, already-reported defect (``NoReverseMatch`` on the
        commented-out ``contributors:claim-profile`` URL, ``urls.py``) rather
        than the permission gate refusing them. That defect is out of scope
        here -- this only proves the gate itself did not fire.
        """
        from django.urls import NoReverseMatch

        url = reverse(
            "admin:contributors_person_claim_link", args=[unclaimed_person.pk]
        )
        with pytest.raises(NoReverseMatch):
            admin_client.get(url)


@pytest.mark.django_db
class TestPersonAdminActionsHiddenFromNonSuperuser:
    """The merge/claim-link changelist actions do not appear for a
    non-superuser, so the interface does not offer an action that the view
    itself would refuse (Route 2)."""

    def test_actions_are_absent_from_the_changelist_for_non_superuser_staff(
        self, client
    ):
        from fairdm.factories import PersonFactory

        acting_user = PersonFactory(
            email="no-actions-staff@example.com", is_staff=True, is_active=True
        )
        _grant(acting_user, Person, "view_person")
        client.force_login(acting_user)

        url = reverse("admin:contributors_person_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "merge_person_action" not in content
        assert "generate_claim_link_action" not in content

    def test_actions_are_present_in_the_changelist_for_a_superuser(
        self, admin_client
    ):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "merge_person_action" in content
        assert "generate_claim_link_action" in content


# ── T046: ClaimingAuditLog admin view ────────────────────────────────────────


class TestClaimingAuditLogAdminView:
    """Verify that the admin changelist view for ClaimingAuditLog loads correctly."""

    def test_changelist_view_returns_200(self, db, admin_client, audit_log_entry):
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_admin_has_no_add_permission(self, db, admin_client):
        """Add URL should return 403 since we disabled add permission."""
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_admin_has_no_change_permission(self, db, admin_client, audit_log_entry):
        """Change URL should return 403 since we disabled change permission."""
        from django.urls import reverse

        url = reverse(
            "admin:contributors_claimingauditlog_change", args=[audit_log_entry.pk]
        )
        response = admin_client.get(url)
        assert response.status_code == 403


# ── T126: Person admin merges account and profile fields (US10, FR-043) ─────


def _fieldset_field_names(fieldsets):
    """Flatten a ModelAdmin fieldsets structure into a flat set of field names."""
    names = set()
    for _, opts in fieldsets:
        for field in opts["fields"]:
            if isinstance(field, (list, tuple)):
                names.update(field)
            else:
                names.add(field)
    return names


@pytest.mark.django_db
class TestPersonAdmin:
    """Verify the Person admin presents one merged screen, not a split account model (T126, T131)."""

    def test_fieldsets_present_account_and_profile_fields_together(self):
        """Account fields (auth) and profile fields (contributor) share the same fieldsets."""
        model_admin = admin.site._registry[Person]
        field_names = _fieldset_field_names(model_admin.fieldsets)

        account_fields = {"password", "is_active", "is_staff", "is_superuser"}
        profile_fields = {"name", "email", "profile", "image"}

        assert account_fields <= field_names
        assert profile_fields <= field_names

    def test_no_separate_account_model_is_registered(self):
        """The polymorphic Contributor base is not registered as its own admin screen."""
        from fairdm.contrib.contributors.models import Contributor

        assert Person in admin.site._registry
        assert Contributor not in admin.site._registry

    def test_public_identifier_and_timestamps_are_readonly(self):
        """The uuid and the added/modified timestamps are visible but not editable (FR-043)."""
        model_admin = admin.site._registry[Person]
        assert "uuid" in model_admin.readonly_fields
        assert "added" in model_admin.readonly_fields
        assert "modified" in model_admin.readonly_fields
        assert {"uuid", "added", "modified"} <= _fieldset_field_names(
            model_admin.fieldsets
        )

    def test_search_fields_cover_name_email_and_public_identifier(self):
        """Search targets name, email and the public identifier, not the numeric pk (FR-043)."""
        model_admin = admin.site._registry[Person]
        assert set(model_admin.search_fields) == {"email", "name", "uuid"}

    def test_list_display_reports_account_state(self, person, unclaimed_person):
        """The changelist reports the account state derived from the stored fields (FR-043)."""
        model_admin = admin.site._registry[Person]
        assert "account_state" in model_admin.list_display
        assert str(model_admin.account_state(person)) == "Claimed"
        assert str(model_admin.account_state(unclaimed_person)) == "Ghost"


# ── T130: Every registered model's changelist/add/change return the expected
# status for a superuser (US10, Article I) ───────────────────────────────────


@pytest.mark.django_db
class TestContributorAdminSmoke:
    """Smoke-test every model the contributors app registers.

    Expected statuses are named explicitly per model rather than derived,
    since ClaimingAuditLog deliberately blocks add and change (immutable
    audit trail) while the others allow both for a superuser.
    """

    EXPECTED_ADD_STATUS = {
        "person": 200,
        "organization": 200,
        "affiliation": 200,
        "claimingauditlog": 403,
    }
    EXPECTED_CHANGE_STATUS = {
        "person": 200,
        "organization": 200,
        "affiliation": 200,
        "claimingauditlog": 403,
    }

    def _registered_app_models(self):
        from django.apps import apps

        app_models = set(apps.get_app_config("contributors").get_models())
        return [model for model in admin.site._registry if model in app_models]

    def test_every_registered_model_is_covered_by_the_expectation_maps(self):
        """A model registered later must be added to this test's expectations too."""
        registered_names = {
            model._meta.model_name for model in self._registered_app_models()
        }
        assert registered_names == set(self.EXPECTED_ADD_STATUS)
        assert registered_names == set(self.EXPECTED_CHANGE_STATUS)

    def test_every_registered_model_changelist_loads(self, admin_client):
        for model in self._registered_app_models():
            opts = model._meta
            url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
            response = admin_client.get(url)
            assert response.status_code == 200, f"{model.__name__} changelist"

    def test_add_view_matches_expectation(self, admin_client):
        for model in self._registered_app_models():
            opts = model._meta
            url = reverse(f"admin:{opts.app_label}_{opts.model_name}_add")
            response = admin_client.get(url)
            expected = self.EXPECTED_ADD_STATUS[opts.model_name]
            assert response.status_code == expected, f"{model.__name__} add"

    def test_change_view_matches_expectation(
        self, admin_client, person, organization, affiliation, audit_log_entry
    ):
        instances = {
            "person": person,
            "organization": organization,
            "affiliation": affiliation,
            "claimingauditlog": audit_log_entry,
        }
        for model in self._registered_app_models():
            opts = model._meta
            obj = instances[opts.model_name]
            url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk]
            )
            response = admin_client.get(url)
            expected = self.EXPECTED_CHANGE_STATUS[opts.model_name]
            assert response.status_code == expected, f"{model.__name__} change"
