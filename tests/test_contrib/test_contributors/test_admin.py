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
class TestPersonAdminClaimFilter:
    def test_the_changelist_is_narrowed_by_the_claim_filter(
        self, admin_client, person, unclaimed_person
    ):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url, {"is_claimed": "unclaimed"})

        listed = {listed.pk for listed in response.context["cl"].result_list}
        assert unclaimed_person.pk in listed
        assert person.pk not in listed


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
class TestOrganizationAdminRORSync:
    def test_the_sync_action_stores_the_record_of_each_selected_organization(
        self, admin_client, organization, ror_identifier, registry_network, recorded
    ):
        registry_network.answer(
            "https://api.ror.org/v2/organizations/02nr0ka47", recorded("ror-record")
        )

        response = admin_client.post(
            reverse("admin:contributors_organization_changelist"),
            {"action": "sync_from_ror", "_selected_action": [organization.pk]},
            follow=True,
        )

        assert response.status_code == 200
        organization.refresh_from_db()
        assert organization.synced_data == recorded("ror-record")


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
    def test_list_display_reports_account_state(self, person, unclaimed_person):
        model_admin = admin.site._registry[Person]
        assert "account_state" in model_admin.list_display
        assert str(model_admin.account_state(person)) == "Claimed"
        assert str(model_admin.account_state(unclaimed_person)) == "Ghost"


@pytest.mark.django_db
class TestContributorAdminSmoke:
    #: The status each registered model's changelist, add page and change page answer
    #: with.
    EXPECTED = {
        "person": (200, 200, 200),
        "organization": (200, 200, 200),
        "affiliation": (200, 200, 200),
        "claimingauditlog": (200, 403, 403),
    }

    def test_every_registered_page_answers_as_expected(
        self, admin_client, person, organization, affiliation, audit_log_entry
    ):
        from django.apps import apps

        instances = {
            "person": person,
            "organization": organization,
            "affiliation": affiliation,
            "claimingauditlog": audit_log_entry,
        }
        app_models = set(apps.get_app_config("contributors").get_models())
        registered = [model for model in admin.site._registry if model in app_models]

        failures = []
        if {model._meta.model_name for model in registered} != set(self.EXPECTED):
            failures.append(
                f"registered models {sorted(m._meta.model_name for m in registered)}"
                f" differ from {sorted(self.EXPECTED)}"
            )
        for model in registered:
            opts = model._meta
            expected = self.EXPECTED.get(opts.model_name)
            if expected is None:
                continue
            obj = instances[opts.model_name]
            pages = {
                "changelist": ("changelist", [], expected[0]),
                "add": ("add", [], expected[1]),
                "change": ("change", [obj.pk], expected[2]),
            }
            for label, (view, args, status) in pages.items():
                url = reverse(
                    f"admin:{opts.app_label}_{opts.model_name}_{view}", args=args
                )
                got = admin_client.get(url).status_code
                if got != status:
                    failures.append(
                        f"{model.__name__} {label}: {got}, expected {status}"
                    )
        assert not failures, failures


def _admitted_holder_of(role, email):
    """Return a person holding a shipped role, which admits them to the administration."""
    from django.contrib.auth.models import Group

    from fairdm.factories import PersonFactory
    from fairdm.portal_roles import PortalRoles

    PortalRoles.reconcile()
    holder = PersonFactory(email=email, is_active=True)
    holder.groups.add(Group.objects.get(name=role.name))
    return holder


@pytest.mark.django_db
class TestPersonImportAndExportPermissions:
    def test_a_role_without_the_permission_to_add_people_cannot_open_the_import(
        self, client
    ):
        from fairdm.portal_roles import PortalRoles

        for role in (
            PortalRoles.PORTAL_ADMINISTRATOR,
            PortalRoles.DATA_CURATOR,
            PortalRoles.COMMUNITY_MANAGER,
        ):
            client.force_login(_admitted_holder_of(role, f"{role.name}@example.com"))

            response = client.get(reverse("admin:contributors_person_import"))

            assert response.status_code == 403, role.name

    def test_a_role_without_the_permission_to_add_people_cannot_run_an_import(
        self, client
    ):
        from fairdm.portal_roles import PortalRoles

        manager = _admitted_holder_of(
            PortalRoles.COMMUNITY_MANAGER, "import-manager@example.com"
        )
        client.force_login(manager)

        response = client.post(reverse("admin:contributors_person_process_import"))

        assert response.status_code == 403

    def test_the_import_button_is_withheld_from_someone_who_cannot_add_people(
        self, client
    ):
        from fairdm.portal_roles import PortalRoles

        manager = _admitted_holder_of(
            PortalRoles.COMMUNITY_MANAGER, "button-manager@example.com"
        )
        client.force_login(manager)

        response = client.get(reverse("admin:contributors_person_changelist"))

        assert response.status_code == 200
        assert response.context["has_import_permission"] is False
        assert response.context["has_export_permission"] is True

    def test_someone_granted_the_permission_to_add_people_can_open_the_import(
        self, client
    ):
        from fairdm.factories import PersonFactory

        staff = PersonFactory(
            email="adds-people@example.com", is_staff=True, is_active=True
        )
        _grant(staff, Person, "add_person")
        client.force_login(staff)

        response = client.get(reverse("admin:contributors_person_import"))

        assert response.status_code == 200

    def test_a_role_that_can_view_people_can_export_them(self, client):
        from fairdm.portal_roles import PortalRoles

        for role in (PortalRoles.PORTAL_ADMINISTRATOR, PortalRoles.COMMUNITY_MANAGER):
            client.force_login(
                _admitted_holder_of(role, f"export-{role.name}@example.com")
            )

            response = client.get(reverse("admin:contributors_person_export"))

            assert response.status_code == 200, role.name

    def test_a_role_that_cannot_view_people_cannot_export_them(self, client):
        from fairdm.portal_roles import PortalRoles

        curator = _admitted_holder_of(
            PortalRoles.DATA_CURATOR, "export-curator@example.com"
        )
        client.force_login(curator)

        response = client.get(reverse("admin:contributors_person_export"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestPossibleDuplicatesPanel:
    def test_the_similarity_is_shown_as_a_percentage_of_the_score(self, admin_client):
        from fairdm.factories import PersonFactory

        # Scores 94.1, so a fraction rounded to no places shows as 1%.
        person = PersonFactory(name="Margaret Hamilton")
        PersonFactory(name="Margaret Hamiltom")

        response = admin_client.get(
            reverse("admin:contributors_person_change", args=[person.pk])
        )

        assert "<td>94%</td>" in response.content.decode()


@pytest.mark.django_db
class TestMergePagePreselection:
    def _merge_url(self, person, merge_into):
        url = reverse("admin:contributors_person_merge", args=[person.pk])
        return f"{url}?merge_into={merge_into}"

    def test_the_person_named_in_the_query_is_chosen(
        self, admin_client, unclaimed_person
    ):
        from fairdm.factories import PersonFactory

        target = PersonFactory()

        response = admin_client.get(self._merge_url(unclaimed_person, target.pk))

        assert response.context["form"]["merge_into"].value() == target.pk

    def test_the_merge_page_carries_the_scripts_of_the_target_field(
        self, admin_client, unclaimed_person
    ):
        response = admin_client.get(
            reverse("admin:contributors_person_merge", args=[unclaimed_person.pk])
        )

        media = str(response.context["form"].media)
        assert media
        assert media in response.content.decode()

    def test_the_chosen_person_is_drawn_in_the_field(
        self, admin_client, unclaimed_person
    ):
        from fairdm.factories import PersonFactory

        target = PersonFactory(name="Margaret Hamilton")

        response = admin_client.get(self._merge_url(unclaimed_person, target.pk))

        assert target.name in response.content.decode()

    def test_a_query_that_cannot_name_a_choice_chooses_nothing(
        self, admin_client, unclaimed_person, admin_user
    ):
        for merge_into in (
            "not-a-number",
            "99999999",
            "",
            unclaimed_person.pk,
            admin_user.pk,
        ):
            response = admin_client.get(self._merge_url(unclaimed_person, merge_into))

            assert response.status_code == 200, merge_into
            assert response.context["form"]["merge_into"].value() is None, merge_into
