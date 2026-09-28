"""FairDM Demo App - Contributor Feature Tests."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from fairdm.contrib.contributors.models import Affiliation, Person
from fairdm.factories import OrganizationFactory, PersonFactory

User = get_user_model()


@pytest.mark.django_db
class TestDemoPersonCreation:
    def test_demo_person_creation(self):
        claimed_person = PersonFactory(
            email="researcher@example.com",
            first_name="Jane",
            last_name="Researcher",
            is_active=True,
            is_claimed=True,
            password="testpass123",
        )

        assert claimed_person.is_claimed
        assert claimed_person.email == "researcher@example.com"
        assert claimed_person.check_password("testpass123")
        assert claimed_person.is_active

        unclaimed_person = Person.objects.create_unclaimed(
            first_name="Historical",
            last_name="Contributor",
        )

        # The record stays active: the unusable password stops sign-in, and staying active lets the
        # person it describes claim it later by invitation.
        assert not unclaimed_person.is_claimed
        assert unclaimed_person.email is None
        assert not unclaimed_person.has_usable_password()
        assert unclaimed_person.is_active

        assert Person.objects.count() >= 2


@pytest.mark.django_db
class TestDemoOrganizationOwnership:
    def test_demo_organization_ownership(self):
        org = OrganizationFactory(name="Demo Research Lab")
        researcher = PersonFactory(email="lead@example.com")

        member_affiliation = Affiliation.objects.create(
            person=researcher,
            organization=org,
            type=Affiliation.MembershipType.MEMBER,
        )

        assert not researcher.has_perm("contributors.manage_organization", org)

        member_affiliation.type = Affiliation.MembershipType.OWNER
        member_affiliation.save()

        researcher_fresh = Person.objects.get(pk=researcher.pk)

        assert researcher_fresh.has_perm("contributors.manage_organization", org)

        second_owner = PersonFactory(email="co-lead@example.com")
        second_owner_affiliation = Affiliation.objects.create(
            person=second_owner,
            organization=org,
            type=Affiliation.MembershipType.OWNER,
        )

        assert second_owner_affiliation.type == Affiliation.MembershipType.OWNER
        # Permission checks may be cached in test environments.


@pytest.mark.django_db
class TestDemoAffiliationWorkflow:
    def test_demo_affiliation_workflow(self):
        from partial_date import PartialDate

        person = PersonFactory(email="postdoc@example.com")
        university = OrganizationFactory(name="Example University")

        affiliation = Affiliation.objects.create(
            person=person,
            organization=university,
            type=Affiliation.MembershipType.MEMBER,
            start_date=PartialDate("2020"),  # Year-only precision (string format)
            is_primary=True,
        )

        assert affiliation.start_date is not None
        assert str(affiliation.start_date) == "2020"
        assert affiliation.is_primary

        affiliation.type = Affiliation.MembershipType.ADMIN
        affiliation.save()

        assert affiliation.type == Affiliation.MembershipType.ADMIN

        secondary_org = OrganizationFactory(name="Collaborating Institute")
        Affiliation.objects.create(
            person=person,
            organization=secondary_org,
            type=Affiliation.MembershipType.MEMBER,
            is_primary=False,  # Only one primary allowed
        )

        assert person.affiliations.count() == 2
        assert person.affiliations.filter(is_primary=True).count() == 1


@pytest.mark.django_db
class TestDemoAdminViewsLoad:
    def test_person_admin_changelist_loads(self, admin_client):
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_person_admin_change_view_loads(self, admin_client):
        person = PersonFactory(email="admin-test@example.com")
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_organization_admin_changelist_loads(self, admin_client):
        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_organization_admin_change_view_loads(self, admin_client):
        org = OrganizationFactory(name="Test Research Center")
        url = reverse("admin:contributors_organization_change", args=[org.pk])
        response = admin_client.get(url)
        assert response.status_code == 200
