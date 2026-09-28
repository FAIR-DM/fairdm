"""Tests for the contributor admin workflows."""

import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.test import RequestFactory
from django.urls import reverse

from fairdm.contrib.contributors.models import Affiliation, Organization, Person


@pytest.mark.django_db
class TestPersonAdminChangelist:
    def test_person_admin_changelist_loads(
        self, admin_client, person, unclaimed_person
    ):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert person.name in content or person.email in content
        assert unclaimed_person.name in content

    def test_person_admin_change_view_loads(self, admin_client, person):
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert person.email in content
        assert person.first_name in content


@pytest.mark.django_db
class TestPersonAdminClaimFilter:
    def test_person_admin_claim_filter_exists(self, admin_client):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_person_admin_filter_claimed_only(
        self, admin_client, person, unclaimed_person
    ):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url, {"is_claimed": "claimed"})

        assert response.status_code == 200
        content = response.content.decode()

        assert person.name in content or person.email in content
        assert unclaimed_person.name not in content or "0 persons" in content.lower()

    def test_person_admin_filter_unclaimed_only(
        self, admin_client, person, unclaimed_person
    ):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url, {"is_claimed": "unclaimed"})

        assert response.status_code == 200
        content = response.content.decode()

        assert unclaimed_person.name in content
        assert person.email not in content or "0 persons" in content.lower()


@pytest.mark.django_db
class TestClaimStatusFilter:
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
        """Scope the queryset to just the four fixtures under test."""
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


@pytest.mark.django_db
class TestPersonAdminInlineAffiliations:
    def test_person_admin_affiliation_inline_present(self, admin_client, person):
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_person_admin_affiliation_inline_shows_existing(
        self, admin_client, person, affiliation
    ):
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert affiliation.organization.name in content

    def test_person_admin_can_add_affiliation_inline(
        self, admin_client, person, organization
    ):
        affiliation = Affiliation.objects.create(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
            is_primary=True,
        )

        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert str(organization) in response.content.decode()
        assert person.affiliations.filter(organization=organization).exists()


@pytest.mark.django_db
class TestOrganizationAdminChangelist:
    def test_organization_admin_changelist_loads(self, admin_client, organization):
        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert organization.name in content

    def test_organization_admin_change_view_loads(self, admin_client, organization):
        url = reverse("admin:contributors_organization_change", args=[organization.pk])

        assert url
        assert f"/admin/contributors/organization/{organization.pk}/change/" in url


@pytest.mark.django_db
class TestOrganizationAdminInlineMembers:
    def test_organization_admin_members_inline_present(
        self, admin_client, organization
    ):
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_organization_admin_members_inline_shows_existing(
        self, admin_client, organization, affiliation
    ):
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert affiliation.person.name in content or affiliation.person.email in content


@pytest.mark.django_db
class TestOrganizationAdminInlines:
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
        from fairdm.factories import OrganizationFactory

        child = OrganizationFactory(name="Sub-department", parent=organization)
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert child.name in response.content.decode()


@pytest.mark.django_db
class TestOrganizationAdminRORSync:
    def test_organization_admin_ror_sync_action_present(
        self, admin_client, organization
    ):
        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert 'value="sync_from_ror"' in content

    def test_organization_admin_ror_sync_action_works(
        self, admin_client, organization, mocker
    ):
        mock_task = mocker.patch(
            "fairdm.contrib.contributors.tasks.sync_contributor_identifier.delay"
        )

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

        mock_task.assert_called_once_with(ror_id.pk)


@pytest.mark.django_db
class TestOwnershipTransferAction:
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

        messages_text = " ".join(str(m) for m in get_messages(response.wsgi_request))
        assert "use the member management inline" not in messages_text
        assert successor.name in messages_text

    def test_action_is_refused_without_the_object_level_right(
        self, organization, owner_affiliation, client
    ):
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

        acting_user = PersonFactory(email="acting-staff@example.com", is_staff=True)
        change_perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Organization),
            codename="change_organization",
        )
        acting_user.user_permissions.add(change_perm)
        assert not acting_user.has_perm(
            "contributors.manage_organization", organization
        )

        client.force_login(acting_user)
        response = self._post_transfer(client, organization, successor)

        assert response.status_code in (200, 302)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER
        assert organization.affiliations.get(person=successor).type == (
            Affiliation.MembershipType.MEMBER
        )
        assert incumbent.has_perm("manage_organization", organization)

        messages_text = " ".join(str(m) for m in get_messages(response.wsgi_request))
        assert "don't have permission" in messages_text


@pytest.mark.django_db
class TestOrganizationAdmin:
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
        url = reverse("admin:contributors_organization_change", args=[organization.pk])
        response = admin_client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestAffiliationAdmin:
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


def _grant(user, model, codename):
    """Add exactly one named model permission to a user."""
    permission = Permission.objects.get(
        content_type=ContentType.objects.get_for_model(model), codename=codename
    )
    user.user_permissions.add(permission)


@pytest.mark.django_db
class TestAffiliationFormBlocksUnauthorisedManagementWrites:
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


@pytest.mark.django_db
class TestMergeAndClaimLinkViewsRequireSuperuser:
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
        from django.urls import NoReverseMatch

        url = reverse(
            "admin:contributors_person_claim_link", args=[unclaimed_person.pk]
        )
        with pytest.raises(NoReverseMatch):
            admin_client.get(url)


@pytest.mark.django_db
class TestMergeAndClaimLinkViewsAdmitACommunityManager:
    def test_merge_view_proceeds_for_a_community_manager(
        self, client, unclaimed_person
    ):
        manager = _community_manager("merge-manager@example.com")
        client.force_login(manager)

        url = reverse("admin:contributors_person_merge", args=[unclaimed_person.pk])
        response = client.get(url)

        assert response.status_code == 200

    def test_claim_link_view_proceeds_for_a_community_manager(
        self, client, unclaimed_person
    ):
        from django.urls import NoReverseMatch

        manager = _community_manager("claim-manager@example.com")
        client.force_login(manager)

        url = reverse(
            "admin:contributors_person_claim_link", args=[unclaimed_person.pk]
        )
        with pytest.raises(NoReverseMatch):
            client.get(url)

    def test_a_person_holding_a_role_without_change_person_is_still_refused(
        self, client, unclaimed_person
    ):
        from django.contrib.auth.models import Group

        from fairdm.factories import PersonFactory
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        curator = PersonFactory(email="curator-only@example.com", is_active=True)
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        client.force_login(curator)

        url = reverse("admin:contributors_person_merge", args=[unclaimed_person.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_the_actions_are_offered_to_a_community_manager_in_the_changelist(
        self, client
    ):
        manager = _community_manager("actions-manager@example.com")
        client.force_login(manager)

        url = reverse("admin:contributors_person_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "merge_person_action" in content
        assert "generate_claim_link_action" in content


@pytest.mark.django_db
class TestPersonAdminActionsHiddenFromNonSuperuser:
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

    def test_actions_are_present_in_the_changelist_for_a_superuser(self, admin_client):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "merge_person_action" in content
        assert "generate_claim_link_action" in content


def _community_manager(email="community-manager@example.com"):
    """Return a person holding the Community Manager role."""
    from django.contrib.auth.models import Group

    from fairdm.factories import PersonFactory
    from fairdm.portal_roles import PortalRoles

    PortalRoles.reconcile()
    manager = PersonFactory(email=email, is_active=True)
    manager.groups.add(Group.objects.get(name=PortalRoles.COMMUNITY_MANAGER.name))
    return manager


@pytest.mark.django_db
class TestPersonAdminFields:
    def test_a_community_manager_is_not_offered_the_account_escalation_fields(
        self, person
    ):
        model_admin = admin.site._registry[Person]
        request = RequestFactory().get("/")
        request.user = _community_manager()

        fieldsets = model_admin.get_fieldsets(request, person)
        form_class = model_admin.get_form(request, person)

        field_names = _fieldset_field_names(fieldsets)
        # `groups` grants the same rights by proxy, so it needs narrowing as well.
        assert not {"is_superuser", "is_staff", "password", "groups"} & field_names
        assert not {"is_superuser", "is_staff", "password", "groups"} & set(
            form_class.base_fields
        )

    def test_a_superuser_is_still_offered_all_three(self, person, superuser):
        model_admin = admin.site._registry[Person]
        request = RequestFactory().get("/")
        request.user = superuser

        fieldsets = model_admin.get_fieldsets(request, person)
        form_class = model_admin.get_form(request, person)

        field_names = _fieldset_field_names(fieldsets)
        assert {"is_superuser", "is_staff", "password", "groups"} <= field_names
        assert {"is_superuser", "is_staff", "groups"} <= set(form_class.base_fields)

    def test_posting_is_superuser_on_leaves_the_flag_unchanged_for_the_actor(self):
        model_admin = admin.site._registry[Person]
        manager = _community_manager()
        request = RequestFactory().get("/")
        request.user = manager

        form_class = model_admin.get_form(request, manager)
        form = form_class(
            data={
                "first_name": manager.first_name,
                "last_name": manager.last_name,
                "name": manager.name,
                "email": manager.email,
                "is_active": "on",
                "is_superuser": "on",
                "groups": [str(g.pk) for g in manager.groups.all()],
            },
            instance=manager,
        )

        assert form.is_valid(), form.errors
        saved = form.save()

        assert saved.is_superuser is False

    def test_posting_is_superuser_on_leaves_the_flag_unchanged_for_somebody_else(
        self, person
    ):
        model_admin = admin.site._registry[Person]
        manager = _community_manager()
        request = RequestFactory().get("/")
        request.user = manager

        form_class = model_admin.get_form(request, person)
        form = form_class(
            data={
                "first_name": person.first_name,
                "last_name": person.last_name,
                "name": person.name,
                "email": person.email,
                "is_active": "on",
                "is_superuser": "on",
            },
            instance=person,
        )

        assert form.is_valid(), form.errors
        saved = form.save()

        assert saved.is_superuser is False

    def test_posting_a_data_curator_group_id_leaves_membership_unchanged(self):
        from django.contrib.auth.models import Group

        from fairdm.portal_roles import PortalRoles

        model_admin = admin.site._registry[Person]
        manager = _community_manager()
        original_group_ids = set(manager.groups.values_list("pk", flat=True))
        data_curator = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)

        request = RequestFactory().get("/")
        request.user = manager

        form_class = model_admin.get_form(request, manager)
        form = form_class(
            data={
                "first_name": manager.first_name,
                "last_name": manager.last_name,
                "name": manager.name,
                "email": manager.email,
                "is_active": "on",
                "groups": [str(data_curator.pk)],
            },
            instance=manager,
        )

        assert form.is_valid(), form.errors
        saved = form.save()

        assert set(saved.groups.values_list("pk", flat=True)) == original_group_ids

    def test_a_portal_administrator_can_still_see_and_set_groups(self):
        from django.contrib.auth.models import Group

        from fairdm.factories import PersonFactory
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        portal_admin = PersonFactory(email="portal-admin@example.com", is_active=True)
        portal_admin.groups.add(
            Group.objects.get(name=PortalRoles.PORTAL_ADMINISTRATOR.name)
        )
        data_curator = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)

        model_admin = admin.site._registry[Person]
        request = RequestFactory().get("/")
        request.user = portal_admin

        fieldsets = model_admin.get_fieldsets(request, portal_admin)
        assert "groups" in _fieldset_field_names(fieldsets)

        form_class = model_admin.get_form(request, portal_admin)
        assert "groups" in form_class.base_fields

        form = form_class(
            data={
                "first_name": portal_admin.first_name,
                "last_name": portal_admin.last_name,
                "name": portal_admin.name,
                "email": portal_admin.email,
                "is_active": "on",
                "groups": [str(g.pk) for g in portal_admin.groups.all()]
                + [str(data_curator.pk)],
            },
            instance=portal_admin,
        )

        assert form.is_valid(), form.errors
        saved = form.save()

        assert data_curator in saved.groups.all()


class TestClaimingAuditLogAdminView:
    def test_changelist_view_returns_200(self, db, admin_client, audit_log_entry):
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_admin_has_no_add_permission(self, db, admin_client):
        from django.urls import reverse

        url = reverse("admin:contributors_claimingauditlog_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_admin_has_no_change_permission(self, db, admin_client, audit_log_entry):
        from django.urls import reverse

        url = reverse(
            "admin:contributors_claimingauditlog_change", args=[audit_log_entry.pk]
        )
        response = admin_client.get(url)
        assert response.status_code == 403


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
    def test_fieldsets_present_account_and_profile_fields_together(self):
        model_admin = admin.site._registry[Person]
        field_names = _fieldset_field_names(model_admin.fieldsets)

        account_fields = {"password", "is_active", "is_staff", "is_superuser"}
        profile_fields = {"name", "email", "profile", "image"}

        assert account_fields <= field_names
        assert profile_fields <= field_names

    def test_no_separate_account_model_is_registered(self):
        from fairdm.contrib.contributors.models import Contributor

        assert Person in admin.site._registry
        assert Contributor not in admin.site._registry

    def test_public_identifier_and_timestamps_are_readonly(self):
        model_admin = admin.site._registry[Person]
        assert "uuid" in model_admin.readonly_fields
        assert "added" in model_admin.readonly_fields
        assert "modified" in model_admin.readonly_fields
        assert {"uuid", "added", "modified"} <= _fieldset_field_names(
            model_admin.fieldsets
        )

    def test_search_fields_cover_name_email_and_public_identifier(self):
        model_admin = admin.site._registry[Person]
        assert set(model_admin.search_fields) == {"email", "name", "uuid"}

    def test_list_display_reports_account_state(self, person, unclaimed_person):
        model_admin = admin.site._registry[Person]
        assert "account_state" in model_admin.list_display
        assert str(model_admin.account_state(person)) == "Claimed"
        assert str(model_admin.account_state(unclaimed_person)) == "Ghost"


@pytest.mark.django_db
class TestContributorAdminSmoke:
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
