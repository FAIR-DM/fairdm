"""Tests for the contributor models."""

from datetime import date

import pytest
from django.apps import apps
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.formats import date_format

from fairdm.contrib.contributors.choices import AccountState, OrganizationType
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    Contributor,
    ContributorIdentifier,
    Organization,
    OrganizationMember,
    Person,
)
from fairdm.core.utils import assign_perm
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility


class TestContributorIdentity:
    @pytest.mark.django_db
    def test_person_identifier_carries_contributor_prefix(self):
        person = PersonFactory()
        assert person.uuid
        assert person.uuid.startswith("c")

    @pytest.mark.django_db
    def test_organization_identifier_carries_contributor_prefix(self):
        organization = OrganizationFactory()
        assert organization.uuid
        assert organization.uuid.startswith("c")

    @pytest.mark.django_db
    def test_identifier_unchanged_on_second_save(self):
        person = PersonFactory()
        original_uuid = person.uuid
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.uuid == original_uuid

    @pytest.mark.django_db
    def test_identifier_unique_across_both_concrete_types(self):
        person = PersonFactory()
        organization = OrganizationFactory()
        assert person.uuid != organization.uuid
        assert Contributor.objects.filter(uuid=person.uuid).count() == 1
        assert Contributor.objects.filter(uuid=organization.uuid).count() == 1

    @pytest.mark.django_db
    def test_identifier_uniqueness_enforced_across_types(self):
        person = PersonFactory()
        with pytest.raises(IntegrityError):
            OrganizationFactory(uuid=person.uuid)


class TestContributorProfileFields:
    @pytest.mark.django_db
    def test_preferred_name_is_required(self):
        organization = OrganizationFactory.build(name="")
        with pytest.raises(ValidationError):
            organization.full_clean()

    @pytest.mark.django_db
    def test_optional_profile_fields_round_trip(self):
        from fairdm.factories import PointFactory

        location = PointFactory()
        organization = OrganizationFactory(
            alternative_names=["Also Known As Inc."],
            profile="A description of the organization.",
            links=["https://example.org"],
            lang=["en", "fr"],
            location=location,
        )
        organization.refresh_from_db()

        assert organization.alternative_names == ["Also Known As Inc."]
        assert organization.profile == "A description of the organization."
        assert organization.links == ["https://example.org"]
        assert organization.lang == ["en", "fr"]
        assert organization.location == location

    @pytest.mark.django_db
    def test_optional_profile_fields_default_empty(self):
        organization = OrganizationFactory(
            alternative_names=None, links=None, lang=None, location=None
        )
        organization.full_clean()
        assert organization.location is None


class TestContributorTimestamps:
    @pytest.mark.django_db
    def test_created_timestamp_set_once(self):
        person = PersonFactory()
        original_added = person.added
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.added == original_added

    @pytest.mark.django_db
    def test_modified_timestamp_moves_on_later_save(self):
        person = PersonFactory()
        original_modified = person.modified
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.modified > original_modified


class TestContributorConfiguration:
    @pytest.mark.django_db
    def test_config_defaults_empty(self):
        person = PersonFactory()
        assert person.config == {}

    @pytest.mark.django_db
    def test_config_accepts_and_returns_arbitrary_json(self):
        person = PersonFactory()
        person.config = {"anything": ["the", "specification", "does", "not", "define"]}
        person.save()
        person.refresh_from_db()
        assert person.config == {
            "anything": ["the", "specification", "does", "not", "define"]
        }


class TestFieldMetadata:
    def _concrete_fields(self, model):
        return [f for f in model._meta.get_fields() if getattr(f, "concrete", False)]

    def test_every_field_has_verbose_name_and_help_text(self):
        from django.utils.functional import Promise

        models_to_check = [
            Contributor,
            Person,
            Organization,
            Affiliation,
            Contribution,
            ContributorIdentifier,
        ]
        exempt_fields = {
            "id",
            "polymorphic_ctype",
            "contributor_ptr",
            "password",
            "last_login",
            "first_name",
            "last_name",
            "date_joined",
            "order",
        }
        # Inherited from shared base classes (fairdm.db.models.Model imports gettext
        # eagerly; AbstractIdentifier is shared by every identifier model).
        exempt_by_model = {
            Affiliation: {"added", "modified"},
            ContributorIdentifier: {"type", "value"},
        }

        failures = []
        for model in models_to_check:
            model_exempt = exempt_fields | exempt_by_model.get(model, set())
            for field in self._concrete_fields(model):
                if field.name in model_exempt:
                    continue
                verbose_name = getattr(field, "verbose_name", None)
                help_text = getattr(field, "help_text", None)
                if not verbose_name or not isinstance(verbose_name, Promise):
                    failures.append(f"{model.__name__}.{field.name}: verbose_name")
                if not help_text or not isinstance(help_text, Promise):
                    failures.append(f"{model.__name__}.{field.name}: help_text")

        assert not failures, f"Missing or non-lazy verbose_name/help_text: {failures}"


class TestPersonIsTheAccount:
    def test_get_user_model_is_person(self):
        assert get_user_model() is Person
        assert get_user_model().__name__ == "Person"

    def test_no_separate_account_model_registered(self):
        username_field_models = [
            model for model in apps.get_models() if hasattr(model, "USERNAME_FIELD")
        ]
        assert username_field_models == [Person]

    def test_no_required_fields_beyond_the_username_field(self):
        assert Person.REQUIRED_FIELDS == []

    def test_username_field_is_removed_not_shadowed(self):
        assert Person.username is None


class TestAttributionOnlyPerson:
    @pytest.mark.django_db
    def test_attribution_only_person_has_no_usable_password(self, unclaimed_person):
        assert unclaimed_person.email is None
        assert unclaimed_person.has_usable_password() is False

    @pytest.mark.django_db
    def test_authenticate_fails_for_attribution_only_person(self, unclaimed_person):
        result = authenticate(
            request=None, email=unclaimed_person.email, password="whatever"
        )
        assert result is None


class TestPersonActivationEligibility:
    @pytest.mark.django_db
    def test_attribution_only_person_is_active(self, unclaimed_person):
        assert unclaimed_person.is_active is True

    @pytest.mark.django_db
    def test_invited_attribution_only_person_is_found_by_password_reset(
        self, unclaimed_person
    ):
        unclaimed_person.email = "invited@example.com"
        unclaimed_person.set_password("some-temporary-password")
        unclaimed_person.save()

        form = PasswordResetForm()
        found = list(form.get_users("invited@example.com"))

        assert unclaimed_person in found


class TestPersonEmailUniqueness:
    @pytest.mark.django_db
    def test_duplicate_email_refused_at_validation(self):
        PersonFactory(email="duplicate@example.com")
        second = PersonFactory.build(email="duplicate@example.com")

        with pytest.raises(ValidationError):
            second.full_clean()

    @pytest.mark.django_db
    def test_duplicate_email_refused_at_the_database(self):
        PersonFactory(email="duplicate@example.com")

        with pytest.raises(IntegrityError):
            Person.objects.create(
                email="duplicate@example.com", first_name="Second", last_name="Person"
            )

    @pytest.mark.django_db
    def test_multiple_people_may_have_no_email(self):
        first = Person.objects.create_unclaimed(first_name="A", last_name="One")
        second = Person.objects.create_unclaimed(first_name="B", last_name="Two")

        assert first.email is None
        assert second.email is None
        assert first.pk != second.pk

    @pytest.mark.django_db
    def test_duplicate_email_refused_case_insensitively(self):
        PersonFactory(email="Case@Example.com")
        second = PersonFactory.build(email="case@example.com")

        with pytest.raises(ValidationError):
            second.full_clean()

    @pytest.mark.django_db
    def test_duplicate_email_refused_case_insensitively_via_manager(self):
        Person.objects.create_user(email="Manager@Example.com", password="pw")

        with pytest.raises(IntegrityError):
            Person.objects.create(
                email="manager@example.com", first_name="Second", last_name="Person"
            )


class TestPersonClaimedUnclaimedSemantics:
    @pytest.mark.django_db
    def test_claimed_person_has_email_and_is_active(self, person):
        assert person.email is not None
        assert person.is_active is True
        assert person.is_claimed is True

    @pytest.mark.django_db
    def test_unclaimed_person_has_no_email(self, unclaimed_person):
        assert unclaimed_person.email is None
        assert unclaimed_person.is_active is True
        assert unclaimed_person.is_claimed is False

    @pytest.mark.django_db
    def test_create_unclaimed_via_manager(self, db):
        p = Person.objects.create_unclaimed(
            first_name="Test",
            last_name="Unclaimed",
        )
        assert p.pk is not None
        assert p.email is None
        assert p.is_active is True
        assert p.is_claimed is False
        assert not p.has_usable_password()
        assert p.name == "Test Unclaimed"

    @pytest.mark.django_db
    def test_person_auto_populates_name_from_first_last(self, db):
        p = PersonFactory(first_name="Jane", last_name="Smith", name="")
        assert p.name == "Jane Smith"

    @pytest.mark.django_db
    def test_person_is_claimed_requires_usable_password(self, db):
        p = Person.objects.create_unclaimed(first_name="No", last_name="Password")
        p.email = "test@example.com"
        p.is_active = True
        p.save()
        assert p.is_claimed is False

    @pytest.mark.django_db
    def test_person_clean_lowercases_email(self, db):
        p = PersonFactory(email="UPPER@Example.com")
        p.clean()
        assert p.email == "upper@example.com"

    @pytest.mark.django_db
    def test_person_polymorphic_query(self, db):
        p = PersonFactory()
        result = Contributor.objects.filter(pk=p.pk).first()
        assert isinstance(result, Person)

    @pytest.mark.django_db
    def test_backward_compatible_alias(self):
        assert OrganizationMember is Affiliation


class TestAccountState:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "member_name,expected_state",
        [
            ("ghost", AccountState.GHOST),
            ("invited", AccountState.INVITED),
            ("claimed", AccountState.CLAIMED),
            ("inactive", AccountState.INACTIVE),
        ],
    )
    def test_person_in_each_state_reports_that_state(
        self, contributor_population, member_name, expected_state
    ):
        person = getattr(contributor_population, member_name)
        assert person.account_state == expected_state

    @pytest.mark.django_db
    def test_no_person_reports_two_states(self, contributor_population):
        pop = contributor_population
        states = {
            pop.ghost.account_state,
            pop.invited.account_state,
            pop.claimed.account_state,
            pop.inactive.account_state,
        }
        assert states == {
            AccountState.GHOST,
            AccountState.INVITED,
            AccountState.CLAIMED,
            AccountState.INACTIVE,
        }


class TestAccountStatePrecedence:
    @pytest.mark.django_db
    def test_deactivated_and_claimed_reports_inactive(self, db):
        person = PersonFactory(
            email="deactivated-claimed@example.com", is_active=False, is_claimed=True
        )
        assert person.account_state == AccountState.INACTIVE

    @pytest.mark.django_db
    def test_deactivated_without_email_still_reports_inactive(self, db):
        person = PersonFactory(email=None, is_active=False, is_claimed=False)
        assert person.account_state == AccountState.INACTIVE


class TestClaimIsStoredOnce:
    def test_is_claimed_is_a_concrete_database_field(self):
        field = Person._meta.get_field("is_claimed")
        from django.db import models as django_models

        assert isinstance(field, django_models.BooleanField)

    def test_account_state_has_no_database_column(self):
        field_names = {f.name for f in Person._meta.get_fields()}
        assert "account_state" not in field_names

    def test_account_state_is_a_plain_property_not_stored_state(self):
        assert isinstance(Person.__dict__["account_state"], property)


class TestClaimedPersonEmailRemoval:
    @pytest.mark.django_db
    def test_claimed_person_cannot_remove_email(self):
        person = PersonFactory(
            email="claimed@example.com", is_active=True, is_claimed=True
        )
        person.set_password("testpass123")
        person.save()

        person.email = None
        with pytest.raises(ValidationError) as exc_info:
            person.full_clean()

        assert "email" in exc_info.value.message_dict

    @pytest.mark.django_db
    def test_unclaimed_person_with_usable_password_may_remove_email(self):
        person = PersonFactory(
            email="ghost-with-password@example.com", is_active=True, is_claimed=False
        )
        person.set_password("testpass123")
        person.save()

        person.email = None
        person.full_clean()

        assert person.email is None


class TestOrganizationCreationAndValidation:
    @pytest.mark.django_db
    def test_create_organization(self, organization):
        assert organization.pk is not None
        assert organization.name == "Test University"

    @pytest.mark.django_db
    def test_organization_is_polymorphic_contributor(self, organization):
        result = Contributor.objects.filter(pk=organization.pk).first()
        assert isinstance(result, Organization)

    @pytest.mark.django_db
    def test_organization_manage_permission_derived(self, db):
        perms = [p[0] for p in Organization._meta.permissions]
        assert "manage_organization" not in perms

        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.factories import PersonFactory

        org = OrganizationFactory(name="Test Org")
        person = PersonFactory(email="owner@example.com")

        assert not person.has_perm("manage_organization", org)

        Affiliation.objects.create(
            person=person,
            organization=org,
            type=Affiliation.MembershipType.OWNER,
        )

        assert person.has_perm("manage_organization", org)

    @pytest.mark.django_db
    def test_organization_parent_child(self, db):
        parent = OrganizationFactory(name="Parent Org")
        child = OrganizationFactory(name="Child Org", parent=parent)
        assert child.parent == parent
        assert parent.sub_organizations.count() == 1

    @pytest.mark.django_db
    def test_organization_owner(self, person, organization):
        AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        assert organization.owner() == person

    @pytest.mark.django_db
    def test_organization_owner_is_none_when_the_only_owner_affiliation_has_ended(
        self, person, organization
    ):
        AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            end_date="2019",
        )
        assert organization.owner() is None

    @pytest.mark.django_db
    def test_organization_get_location_display(self, db):
        org = OrganizationFactory(name="GFZ", city="Potsdam", country="DE")
        display = org.get_location_display()
        assert "Potsdam" in display
        assert "Germany" in display

    @pytest.mark.django_db
    def test_organization_default_identifier_is_ror(self):
        assert Organization.DEFAULT_IDENTIFIER == "ROR"


class TestOrganizationTypeValidation:
    @pytest.mark.django_db
    def test_type_outside_the_ror_set_is_refused(self, organization):
        organization.type = "museum"
        with pytest.raises(ValidationError):
            organization.full_clean()

    @pytest.mark.django_db
    def test_every_ror_type_is_accepted(self):
        for value in (
            OrganizationType.EDUCATION,
            OrganizationType.FUNDER,
            OrganizationType.HEALTHCARE,
            OrganizationType.COMPANY,
            OrganizationType.ARCHIVE,
            OrganizationType.NONPROFIT,
            OrganizationType.GOVERNMENT,
            OrganizationType.FACILITY,
            OrganizationType.OTHER,
        ):
            organization = OrganizationFactory(type=value)
            organization.full_clean()
            assert organization.type == value

    def test_type_field_is_indexed(self):
        assert Organization._meta.get_field("type").db_index is True


class TestOrganizationParentDeletion:
    @pytest.mark.django_db
    def test_deleting_the_parent_leaves_the_child_with_no_parent(self, person):
        university = OrganizationFactory(name="Test University")
        department = OrganizationFactory(name="Test Department", parent=university)
        AffiliationFactory(
            person=person,
            organization=department,
            type=Affiliation.MembershipType.MEMBER,
        )
        contribution = ContributionFactory(contributor=department)

        university.delete()

        department.refresh_from_db()
        assert department.parent is None
        assert department.affiliations.count() == 1
        assert department.contributions.count() == 1
        contribution.refresh_from_db()
        assert contribution.contributor_id == department.pk


class TestOrganizationLocation:
    @pytest.mark.django_db
    def test_city_and_country_are_optional(self):
        organization = OrganizationFactory(name="Unspecified Institute")
        organization.full_clean()
        assert not organization.city
        assert not organization.country

    @pytest.mark.django_db
    def test_city_and_country_round_trip(self):
        organization = OrganizationFactory(name="GFZ", city="Potsdam", country="DE")

        organization.refresh_from_db()

        assert organization.city == "Potsdam"
        assert organization.country == "DE"

    def test_city_and_country_are_indexed(self):
        assert Organization._meta.get_field("city").db_index is True
        assert Organization._meta.get_field("country").db_index is True


class TestOwnershipTransfer:
    @pytest.mark.django_db
    def test_transfer_demotes_incumbent_and_promotes_successor(
        self, organization, owner_affiliation
    ):
        incumbent = owner_affiliation.person
        successor = AffiliationFactory(
            person=PersonFactory(
                email="successor@example.com", is_active=True, is_claimed=True
            ),
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        ).person

        organization.transfer_ownership(successor)

        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.ADMIN
        assert organization.owner() == successor
        assert successor.has_perm("manage_organization", organization)
        assert not incumbent.has_perm("manage_organization", organization)

    @pytest.mark.django_db
    def test_transfer_refuses_a_person_who_is_not_a_member(
        self, organization, owner_affiliation
    ):
        stranger = PersonFactory(email="stranger@example.com")

        with pytest.raises(ValidationError):
            organization.transfer_ownership(stranger)

        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER
        assert not organization.affiliations.filter(person=stranger).exists()

    @pytest.mark.django_db
    def test_transfer_is_atomic(self, organization, owner_affiliation, monkeypatch):
        successor = AffiliationFactory(
            person=PersonFactory(
                email="atomic-successor@example.com", is_active=True, is_claimed=True
            ),
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        ).person

        def boom(self, *args, **kwargs):
            raise RuntimeError("simulated failure during promotion")

        monkeypatch.setattr(Affiliation, "save", boom, raising=True)

        with pytest.raises(RuntimeError):
            organization.transfer_ownership(successor)

        monkeypatch.undo()
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER
        assert (
            organization.affiliations.get(person=successor).type
            == Affiliation.MembershipType.MEMBER
        )

    @pytest.mark.django_db
    def test_transfer_leaves_an_already_ended_owner_affiliation_untouched(
        self, organization, person
    ):
        ended_owner_affiliation = AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            end_date="2019",
        )
        successor = PersonFactory(
            email="successor-past-owner@example.com", is_active=True, is_claimed=True
        )
        AffiliationFactory(
            person=successor,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        )

        organization.transfer_ownership(successor)

        ended_owner_affiliation.refresh_from_db()
        assert ended_owner_affiliation.type == Affiliation.MembershipType.OWNER
        assert ended_owner_affiliation.end_date is not None
        assert organization.owner() == successor


class TestTransferOwnershipRefusesInvalidTargets:
    @pytest.mark.django_db
    def test_refuses_a_pending_affiliate(self, organization, owner_affiliation):
        pending_person = PersonFactory(
            email="pending-affiliate@example.com", is_active=True, is_claimed=True
        )
        AffiliationFactory(
            person=pending_person,
            organization=organization,
            type=Affiliation.MembershipType.PENDING,
        )

        with pytest.raises(ValidationError) as exc_info:
            organization.transfer_ownership(pending_person)

        assert "pending verification" in str(exc_info.value)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER

    @pytest.mark.django_db
    def test_refuses_an_ended_affiliation(self, organization, owner_affiliation):
        ended_member = PersonFactory(
            email="ended-member@example.com", is_active=True, is_claimed=True
        )
        AffiliationFactory(
            person=ended_member,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
            end_date="2019",
        )

        with pytest.raises(ValidationError) as exc_info:
            organization.transfer_ownership(ended_member)

        assert "has ended" in str(exc_info.value)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER

    @pytest.mark.django_db
    def test_refuses_an_unclaimed_person(self, organization, owner_affiliation):
        unclaimed_member = PersonFactory(
            email="unclaimed-member@example.com", is_active=True, is_claimed=False
        )
        AffiliationFactory(
            person=unclaimed_member,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        )

        with pytest.raises(ValidationError) as exc_info:
            organization.transfer_ownership(unclaimed_member)

        assert "has not claimed" in str(exc_info.value)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER

    @pytest.mark.django_db
    def test_refuses_a_deactivated_person(self, organization, owner_affiliation):
        deactivated_member = PersonFactory(
            email="deactivated-member@example.com", is_active=False, is_claimed=True
        )
        AffiliationFactory(
            person=deactivated_member,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        )

        with pytest.raises(ValidationError) as exc_info:
            organization.transfer_ownership(deactivated_member)

        assert "deactivated" in str(exc_info.value)
        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER


class TestAffiliationSchema:
    def test_membership_type_is_indexed(self):
        field = Affiliation._meta.get_field("type")
        assert field.db_index is True

    def test_default_related_name_is_affiliations(self):
        assert Affiliation._meta.default_related_name == "affiliations"


class TestAffiliationUniqueConstraints:
    @pytest.mark.django_db
    def test_affiliation_unique_person_organization(self, person, organization):
        AffiliationFactory(person=person, organization=organization)
        with pytest.raises(IntegrityError):
            AffiliationFactory(person=person, organization=organization)

    @pytest.mark.django_db
    def test_affiliation_type_choices(self):
        types = Affiliation.MembershipType
        assert types.PENDING == 0
        assert types.MEMBER == 1
        assert types.ADMIN == 2
        assert types.OWNER == 3

    @pytest.mark.django_db
    def test_affiliation_start_end_dates(self, affiliation):
        affiliation.start_date = "2020"
        affiliation.end_date = "2024-06"
        affiliation.save()
        affiliation.refresh_from_db()
        assert str(affiliation.start_date) == "2020"
        assert str(affiliation.end_date) == "2024-06"

    @pytest.mark.django_db
    def test_only_one_primary_per_person(self, person):
        org1 = OrganizationFactory(name="Org A")
        org2 = OrganizationFactory(name="Org B")
        a1 = AffiliationFactory(person=person, organization=org1, is_primary=True)
        a2 = AffiliationFactory(person=person, organization=org2, is_primary=True)
        a1.refresh_from_db()
        assert a1.is_primary is False
        assert a2.is_primary is True

    @pytest.mark.django_db
    def test_affiliation_sync_ownership_permission(self, person, organization):
        aff = AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
        )
        aff.type = Affiliation.MembershipType.OWNER
        aff.save()
        assert person.has_perm("contributors.manage_organization", organization)

    @pytest.mark.django_db
    def test_affiliation_remove_ownership_permission(self, person, organization):
        aff = AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        aff.type = Affiliation.MembershipType.MEMBER
        aff.save()
        assert not person.has_perm("contributors.manage_organization", organization)

    @pytest.mark.django_db
    def test_string_representation(self, affiliation):
        result = str(affiliation)
        assert " - " in result


class TestAffiliationUniqueness:
    @pytest.mark.django_db
    def test_duplicate_membership_refused_at_validation_with_readable_message(
        self, person, organization
    ):
        AffiliationFactory(person=person, organization=organization)
        duplicate = Affiliation(person=person, organization=organization)

        with pytest.raises(ValidationError) as excinfo:
            duplicate.full_clean()

        assert "already a member" in str(excinfo.value)

    @pytest.mark.django_db
    def test_duplicate_membership_refused_at_database(self, person, organization):
        AffiliationFactory(person=person, organization=organization)

        with pytest.raises(IntegrityError):
            Affiliation.objects.create(person=person, organization=organization)


class TestContributionGFKRelationships:
    @pytest.mark.django_db
    def test_contribution_links_person_to_project(
        self, contribution, person, project_for_contributions
    ):
        assert contribution.contributor == person
        assert contribution.content_object == project_for_contributions

    @pytest.mark.django_db
    def test_contribution_unique_per_entity_contributor(self, person):
        project = ProjectFactory()
        ContributionFactory(contributor=person, content_object=project)
        with pytest.raises(IntegrityError):
            ContributionFactory(contributor=person, content_object=project)

    @pytest.mark.django_db
    def test_contribution_add_to_classmethod(self, person):
        project = ProjectFactory()
        contribution = person.add_to(project)
        assert contribution is not None
        assert contribution.content_object == project

    @pytest.mark.django_db
    def test_contribution_default_affiliation(self, person, organization):
        AffiliationFactory(
            person=person,
            organization=organization,
            is_primary=True,
        )
        project = ProjectFactory()
        c = person.add_to(project)
        assert c.affiliation == organization

    @pytest.mark.django_db
    def test_contribution_has_contribution_to(
        self, person, contribution, project_for_contributions
    ):
        assert person.has_contribution_to(project_for_contributions) is True

    @pytest.mark.django_db
    def test_contribution_projects_property(self, person, contribution):
        projects = person.projects
        assert projects.count() >= 1

    @pytest.mark.django_db
    def test_contribution_manager_for_entity(
        self, contribution, project_for_contributions
    ):
        qs = Contribution.objects.for_entity(project_for_contributions)
        assert qs.count() >= 1
        assert contribution in qs

    @pytest.mark.django_db
    def test_contribution_manager_by_contributor(self, person, contribution):
        qs = Contribution.objects.by_contributor(person)
        assert qs.count() >= 1


class TestContributionTargets:
    @pytest.mark.django_db
    def test_person_creditable_on_a_project(self, person, project_for_contributions):
        contribution = person.add_to(project_for_contributions)

        assert contribution.content_object == project_for_contributions

    @pytest.mark.django_db
    def test_person_creditable_on_a_dataset(self, person):
        dataset = DatasetFactory()

        contribution = person.add_to(dataset)

        assert contribution.content_object == dataset

    @pytest.mark.django_db
    def test_person_creditable_on_a_measurement(self, person):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        contribution = person.add_to(measurement)

        assert contribution.content_object == measurement

    @pytest.mark.django_db
    def test_organization_creditable_as_a_contributor(
        self, organization, project_for_contributions
    ):
        contribution = organization.add_to(project_for_contributions)

        assert contribution.content_object == project_for_contributions
        assert contribution.contributor == organization


class TestContributionUniqueness:
    @pytest.mark.django_db
    def test_second_contribution_for_the_same_pairing_is_refused(
        self, person, project_for_contributions
    ):
        ContributionFactory(
            contributor=person, content_object=project_for_contributions
        )
        with pytest.raises(IntegrityError):
            ContributionFactory(
                contributor=person, content_object=project_for_contributions
            )

    @pytest.mark.django_db
    def test_duplicate_pairing_raises_a_validation_error_with_a_clear_message(
        self, person, project_for_contributions
    ):
        ContributionFactory(
            contributor=person, content_object=project_for_contributions
        )
        duplicate = Contribution(
            contributor=person,
            content_type=ContentType.objects.get_for_model(project_for_contributions),
            object_id=project_for_contributions.pk,
        )
        with pytest.raises(ValidationError, match="already credited"):
            duplicate.full_clean(validate_unique=False, validate_constraints=False)

    @pytest.mark.django_db
    def test_crediting_again_under_a_new_role_accumulates_via_contributor_add_to(
        self, person, project_for_contributions
    ):
        person.add_to(project_for_contributions, roles=["DataCollector"])
        contribution = person.add_to(project_for_contributions, roles=["Researcher"])

        assert (
            Contribution.objects.filter(
                contributor=person, object_id=project_for_contributions.pk
            ).count()
            == 1
        )
        role_names = set(contribution.roles.values_list("name", flat=True))
        assert role_names == {"DataCollector", "Researcher"}

    @pytest.mark.django_db
    def test_crediting_again_under_a_new_role_accumulates_via_contribution_add_to(
        self, person, project_for_contributions
    ):
        Contribution.add_to(person, project_for_contributions, roles=["DataCollector"])
        contribution = Contribution.add_to(
            person, project_for_contributions, roles=["Researcher"]
        )

        assert (
            Contribution.objects.filter(
                contributor=person, object_id=project_for_contributions.pk
            ).count()
            == 1
        )
        role_names = set(contribution.roles.values_list("name", flat=True))
        assert role_names == {"DataCollector", "Researcher"}


class TestContributionRoles:
    @pytest.mark.django_db
    def test_role_from_the_roles_vocabulary_is_accepted(self, contribution):
        from research_vocabs.models import Concept

        role = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        contribution.roles.add(role)

        contribution.full_clean()

        assert role in contribution.roles.all()

    @pytest.mark.django_db
    def test_role_from_outside_the_roles_vocabulary_is_refused(
        self, contribution, off_vocabulary_role
    ):
        from django.db import transaction

        with (
            transaction.atomic(),
            pytest.raises(ValidationError, match="roles vocabulary"),
        ):
            contribution.roles.add(off_vocabulary_role)

        assert off_vocabulary_role not in contribution.roles.all()
        assert contribution.roles.count() == 0

    @pytest.mark.django_db
    def test_contribution_roles_fixture_has_real_concepts_to_attach(
        self, contribution, contribution_roles
    ):
        assert contribution_roles.count() > 1

        role = contribution_roles.get(name="Creator")
        contribution.roles.add(role)

        contribution.full_clean()

        assert role in contribution.roles.all()


class TestContributorCredits:
    @pytest.mark.django_db
    def test_reports_each_kind_of_credited_output(self, person):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory
        from fairdm.utils.choices import Visibility

        project = ProjectFactory()
        # Dataset.objects excludes PRIVATE datasets, the factory default.
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        person.add_to(project)
        person.add_to(dataset)
        person.add_to(sample)
        person.add_to(measurement)

        assert project in person.projects
        assert dataset in person.datasets
        assert sample in person.samples
        assert measurement in person.measurements

    @pytest.mark.django_db
    def test_reports_counts_by_kind(self, person):
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        person.add_to(ProjectFactory())
        person.add_to(DatasetFactory())
        person.add_to(DatasetFactory())

        counts = person.get_credit_counts()

        assert counts[Project._meta.verbose_name_plural] == 1
        assert counts[Dataset._meta.verbose_name_plural] == 2

    @pytest.mark.django_db
    def test_counts_by_kind_resolved_in_a_bounded_number_of_queries(
        self, person, django_assert_max_num_queries
    ):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        person.add_to(ProjectFactory())
        person.add_to(DatasetFactory())
        person.add_to(RockSampleFactory())
        person.add_to(ExampleMeasurementFactory(sample=RockSampleFactory()))

        with django_assert_max_num_queries(6):
            person.get_credit_counts()


class TestCollaborators:
    @pytest.mark.django_db
    def test_orders_collaborators_most_frequent_first(self, person):
        frequent = PersonFactory()
        occasional = PersonFactory()
        projects = ProjectFactory.create_batch(3)
        for project in projects:
            person.add_to(project)
            frequent.add_to(project)
        occasional.add_to(projects[0])

        collaborators = list(person.get_collaborators())

        assert collaborators[0] == frequent
        assert occasional in collaborators
        assert collaborators.index(frequent) < collaborators.index(occasional)

    @pytest.mark.django_db
    def test_excludes_the_contributor_credited_on_an_unrelated_object(self, person):
        shared_project = ProjectFactory()
        person.add_to(shared_project)
        collaborator = PersonFactory()
        collaborator.add_to(shared_project)

        stranger = PersonFactory()
        stranger.add_to(ProjectFactory())

        collaborators = list(person.get_collaborators())

        assert collaborator in collaborators
        assert stranger not in collaborators

    @pytest.mark.django_db
    def test_a_contributor_matching_content_type_and_object_id_separately_is_not_a_false_positive(
        self, person
    ):
        project = ProjectFactory()
        dataset = DatasetFactory()
        person.add_to(project)

        false_positive = PersonFactory()
        other_project = ProjectFactory()
        # Same content type as person's credit (Project), but a different object.
        Contribution.objects.create(
            contributor=false_positive,
            content_type=ContentType.objects.get_for_model(other_project),
            object_id=other_project.pk,
        )
        # Same object id as person's credit, but a different content type (Dataset).
        Contribution.objects.create(
            contributor=false_positive,
            content_type=ContentType.objects.get_for_model(dataset),
            object_id=str(project.pk),
        )

        collaborators = list(person.get_collaborators())

        assert false_positive not in collaborators


class TestContributorIdentifierUniqueness:
    @pytest.mark.django_db
    def test_create_orcid_identifier(self, orcid_identifier, person):
        assert orcid_identifier.pk is not None
        assert orcid_identifier.related == person

    @pytest.mark.django_db
    def test_create_ror_identifier(self, ror_identifier, organization):
        assert ror_identifier.pk is not None
        assert ror_identifier.related == organization

    @pytest.mark.django_db
    def test_person_default_identifier_is_orcid(self):
        assert Person.DEFAULT_IDENTIFIER == "ORCID"


class TestIdentifierUniquePerType:
    @pytest.mark.django_db
    def test_second_identifier_of_same_type_refused_at_the_database(
        self, orcid_identifier, person
    ):
        with pytest.raises(IntegrityError):
            ContributorIdentifier.objects.create(
                related=person, type="ORCID", value="0000-0001-9999-9999"
            )

    @pytest.mark.django_db
    def test_second_identifier_of_same_type_refused_at_clean(
        self, orcid_identifier, person
    ):
        duplicate = ContributorIdentifier(
            related=person, type="ORCID", value="0000-0001-9999-9999"
        )

        with pytest.raises(ValidationError) as excinfo:
            duplicate.clean()

        assert "ORCID" in str(excinfo.value)

    @pytest.mark.django_db
    def test_a_second_type_on_the_same_contributor_is_unaffected(
        self, orcid_identifier, person
    ):
        second = ContributorIdentifier(
            related=person, type="RESEARCHER_ID", value="A-1234-2020"
        )

        second.clean()
        second.save()

        assert person.identifiers.count() == 2


class TestIdentifierValueUniqueAcrossContributors:
    @pytest.mark.django_db
    def test_second_contributor_with_the_same_value_refused_at_the_database(
        self, orcid_identifier, organization
    ):
        with pytest.raises(IntegrityError):
            ContributorIdentifier.objects.create(
                related=organization, type="ROR", value=orcid_identifier.value
            )

    @pytest.mark.django_db
    def test_second_contributor_with_the_same_value_refused_at_clean(
        self, orcid_identifier, organization
    ):
        duplicate = ContributorIdentifier(
            related=organization, type="ROR", value=orcid_identifier.value
        )

        with pytest.raises(ValidationError):
            duplicate.clean()

    @pytest.mark.django_db
    def test_the_identifier_inline_form_refuses_it_as_an_ordinary_field_error(
        self, orcid_identifier, organization
    ):
        from django import forms

        form_class = forms.modelform_factory(
            ContributorIdentifier, fields=["type", "value"]
        )
        form = form_class(
            data={"type": "ROR", "value": orcid_identifier.value},
            instance=ContributorIdentifier(related=organization),
        )

        assert form.is_valid() is False
        assert "value" in form.errors


class TestDefaultIdentifier:
    @pytest.mark.django_db
    def test_person_default_identifier_is_its_orcid(self, orcid_identifier, person):
        assert person.get_default_identifier() == orcid_identifier

    @pytest.mark.django_db
    def test_organization_default_identifier_is_its_ror(
        self, ror_identifier, organization
    ):
        assert organization.get_default_identifier() == ror_identifier

    @pytest.mark.django_db
    def test_default_identifier_is_none_without_any_identifiers(self, person):
        assert person.get_default_identifier() is None


class TestContributorIdentifierVocabulary:
    def test_available_types_are_the_union_of_person_and_organization_types(self):
        assert set(ContributorIdentifier.VOCABULARY.values) == {
            "ORCID",
            "RESEARCHER_ID",
            "ROR",
            "WIKIDATA",
            "ISNI",
            "CROSSREF_FUNDER_ID",
        }

    def test_no_type_names_a_sample_or_project(self):
        assert set(ContributorIdentifier.VOCABULARY.values).isdisjoint(
            {"IGSN", "DOI", "GRANT_NUMBER", "PROPOSAL_ID"}
        )


class TestPersonNameInternationalization:
    @pytest.mark.django_db
    def test_person_name_chinese_script(self, db):
        person = PersonFactory(
            first_name="王",
            last_name="明",
            name="",
        )
        assert person.name == "王 明"
        assert person.first_name == "王"
        assert person.last_name == "明"

    @pytest.mark.django_db
    def test_person_name_arabic_script(self, db):
        person = PersonFactory(
            first_name="محمد",
            last_name="أحمد",
            name="",
        )
        assert person.name == "محمد أحمد"
        assert person.first_name == "محمد"
        assert person.last_name == "أحمد"

    @pytest.mark.django_db
    def test_person_name_cyrillic_script(self, db):
        person = PersonFactory(
            first_name="Иван",
            last_name="Петров",
            name="",
        )
        assert person.name == "Иван Петров"
        assert person.first_name == "Иван"
        assert person.last_name == "Петров"

    @pytest.mark.django_db
    def test_person_name_mixed_scripts(self, db):
        person = PersonFactory(
            first_name="José",
            last_name="García-López",
            name="",
        )
        assert person.name == "José García-López"
        assert "�" not in person.name

    @pytest.mark.django_db
    def test_person_name_emoji_and_special_chars(self, db):
        person = PersonFactory(
            first_name="Test",
            last_name="O'Brien-Smith",
            name="",
        )
        assert person.name == "Test O'Brien-Smith"
        assert "'" in person.last_name


class TestMultipleRolesPerContribution:
    @pytest.mark.django_db
    def test_contribution_multiple_roles(self, db):
        from research_vocabs.models import Concept

        project = ProjectFactory()
        person = PersonFactory()
        contribution = ContributionFactory(
            content_object=project,
            contributor=person,
        )

        roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")
        author_role = roles_qs.first()
        editor_role = roles_qs.last()

        contribution.roles.add(author_role, editor_role)

        assert contribution.roles.count() == 2
        assert author_role in contribution.roles.all()
        assert editor_role in contribution.roles.all()


class TestAffiliationTimeBounds:
    @pytest.mark.django_db
    def test_affiliation_active_no_end_date(self, db):
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            start_date="2020-01",
            end_date=None,
        )

        assert affiliation.end_date is None
        assert org.affiliations.filter(end_date__isnull=True).exists()

    @pytest.mark.django_db
    def test_affiliation_historical_has_end_date(self, db):
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            start_date="2015",
            end_date="2020-06",
        )

        assert affiliation.end_date is not None
        assert org.affiliations.filter(end_date__isnull=False).exists()

    @pytest.mark.django_db
    def test_multiple_affiliations_timeline(self, db):
        person = PersonFactory()
        org1 = OrganizationFactory(name="University A")
        org2 = OrganizationFactory(name="Institute B")

        past_aff = AffiliationFactory(
            person=person,
            organization=org1,
            start_date="2010",
            end_date="2015",
        )

        current_aff = AffiliationFactory(
            person=person,
            organization=org2,
            start_date="2015",
            end_date=None,
        )

        assert person.affiliations.count() == 2
        assert person.affiliations.filter(end_date__isnull=True).count() == 1
        assert person.affiliations.filter(end_date__isnull=False).count() == 1


class TestPartialDatePrecision:
    @pytest.mark.django_db
    def test_affiliation_year_only_precision(self, db):
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            start_date="2020",
            end_date=None,
        )

        assert affiliation.start_date == "2020"

    @pytest.mark.django_db
    def test_affiliation_year_month_precision(self, db):
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            start_date="2020-03",
            end_date="2023-12",
        )

        assert affiliation.start_date == "2020-03"
        assert affiliation.end_date == "2023-12"

    @pytest.mark.django_db
    def test_affiliation_full_date_precision(self, db):
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            start_date="2020-03-15",
            end_date="2023-12-31",
        )

        assert affiliation.start_date == "2020-03-15"
        assert affiliation.end_date == "2023-12-31"


class TestPrimaryAffiliationConstraint:
    @pytest.mark.django_db
    def test_single_primary_affiliation(self, db):
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            is_primary=True,
        )

        assert affiliation.is_primary is True
        assert person.affiliations.filter(is_primary=True).count() == 1

    @pytest.mark.django_db
    def test_setting_new_primary_unsetsolds(self, db):
        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")

        aff1 = AffiliationFactory(
            person=person,
            organization=org1,
            is_primary=True,
        )
        assert aff1.is_primary is True

        aff2 = AffiliationFactory(
            person=person,
            organization=org2,
            is_primary=True,
        )

        aff1.refresh_from_db()

        assert aff2.is_primary is True
        assert aff1.is_primary is False
        assert person.affiliations.filter(is_primary=True).count() == 1

    @pytest.mark.django_db
    def test_multiple_non_primary_affiliations_allowed(self, db):
        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        org3 = OrganizationFactory(name="Org 3")

        AffiliationFactory(person=person, organization=org1, is_primary=False)
        AffiliationFactory(person=person, organization=org2, is_primary=False)
        AffiliationFactory(person=person, organization=org3, is_primary=False)

        assert person.affiliations.filter(is_primary=False).count() == 3
        assert person.affiliations.filter(is_primary=True).count() == 0


class TestPrimaryAffiliationDemotionIsAtomic:
    @pytest.mark.django_db
    def test_demotion_and_save_roll_back_together_on_failure(self, person, monkeypatch):
        import django.db.models as django_db_models

        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        first = AffiliationFactory(person=person, organization=org1, is_primary=True)
        second = AffiliationFactory(person=person, organization=org2, is_primary=False)

        def failing_save(self, *args, **kwargs):
            raise IntegrityError("simulated failure during save")

        monkeypatch.setattr(django_db_models.Model, "save", failing_save)

        second.is_primary = True
        with pytest.raises(IntegrityError):
            second.save()

        first.refresh_from_db()
        assert first.is_primary is True


class TestPrimaryAffiliationDatabaseConstraint:
    @pytest.mark.django_db
    def test_database_refuses_two_primary_memberships_written_directly(self, person):
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        first = AffiliationFactory(person=person, organization=org1, is_primary=False)
        second = AffiliationFactory(person=person, organization=org2, is_primary=False)

        Affiliation.objects.filter(pk=first.pk).update(is_primary=True)

        with pytest.raises(IntegrityError):
            Affiliation.objects.filter(pk=second.pk).update(is_primary=True)


class TestClaimingAuditLogImmutability:
    def test_create_succeeds(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.ORCID,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        assert entry.pk is not None

    def test_update_raises_value_error(self, db, audit_log_entry):

        audit_log_entry.failure_reason = "tampered"
        with pytest.raises(ValueError, match="immutable"):
            audit_log_entry.save()

    def test_record_not_modified_on_failed_save(self, db, audit_log_entry):
        from fairdm.contrib.contributors.models import ClaimingAuditLog

        original_reason = audit_log_entry.failure_reason
        try:
            audit_log_entry.failure_reason = "tampered"
            audit_log_entry.save()
        except ValueError:
            pass
        fresh = ClaimingAuditLog.objects.get(pk=audit_log_entry.pk)
        assert fresh.failure_reason == original_reason


class TestClaimingAuditLogManager:
    def test_for_person_returns_related_entries(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.EMAIL,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        assert (
            ClaimingAuditLog.objects.for_person(person_a.pk)
            .filter(pk=entry.pk)
            .exists()
        )
        assert (
            ClaimingAuditLog.objects.for_person(person_b.pk)
            .filter(pk=entry.pk)
            .exists()
        )

    def test_for_person_excludes_unrelated_entries(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod
        from fairdm.factories import PersonFactory

        unrelated = PersonFactory()
        entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.EMAIL,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        assert (
            not ClaimingAuditLog.objects.for_person(unrelated.pk)
            .filter(pk=entry.pk)
            .exists()
        )

    def test_failures_filter(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        failed = ClaimingAuditLog.objects.create(
            method=ClaimMethod.TOKEN,
            source_person=person_a,
            target_person=person_b,
            success=False,
            failure_reason="expired",
        )
        succeeded = ClaimingAuditLog.objects.create(
            method=ClaimMethod.TOKEN,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        failures = ClaimingAuditLog.objects.failures()
        assert failures.filter(pk=failed.pk).exists()
        assert not failures.filter(pk=succeeded.pk).exists()

    def test_by_method_filter(self, db, person_a, person_b):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

        orcid_entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.ORCID,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        email_entry = ClaimingAuditLog.objects.create(
            method=ClaimMethod.EMAIL,
            source_person=person_a,
            target_person=person_b,
            success=True,
        )
        orcid_qs = ClaimingAuditLog.objects.by_method(ClaimMethod.ORCID)
        assert orcid_qs.filter(pk=orcid_entry.pk).exists()
        assert not orcid_qs.filter(pk=email_entry.pk).exists()


@pytest.mark.django_db
class TestContributorLinkValidation:
    def test_person_refuses_a_link_that_is_not_a_url(self, person):
        person.links = ["https://example.org", "not a url"]

        with pytest.raises(ValidationError) as excinfo:
            person.full_clean()

        assert "links" in excinfo.value.message_dict
        assert "not a url" in excinfo.value.message_dict["links"][0]

    def test_organization_refuses_a_link_that_is_not_a_url(self, organization):
        organization.links = ["ftp://not-a-web-address"]

        with pytest.raises(ValidationError) as excinfo:
            organization.full_clean()

        assert "links" in excinfo.value.message_dict
        assert "ftp://not-a-web-address" in excinfo.value.message_dict["links"][0]

    def test_a_valid_link_list_passes(self, person):
        person.links = ["https://example.org", "https://orcid.org/0000-0002-1825-0097"]

        person.full_clean()


@pytest.mark.django_db
class TestDefaultIdentifierReadsAPrefetch:
    def test_a_prefetched_person_finds_its_orcid_without_a_query(
        self, orcid_identifier, person, django_assert_num_queries
    ):
        prefetched = Person.objects.prefetch_related("identifiers").get(pk=person.pk)

        with django_assert_num_queries(0):
            assert prefetched.get_default_identifier() == orcid_identifier


@pytest.mark.django_db
class TestInitials:
    def test_a_person_uses_their_given_and_family_names(self):
        person = PersonFactory(first_name="ada", last_name="lovelace", name="The Countess")

        assert person.get_initials() == "AL"

    def test_a_person_without_given_or_family_names_uses_the_preferred_name(self):
        person = PersonFactory(first_name="", last_name="", name="Grace Hopper")

        assert person.get_initials() == "GH"

    def test_an_organization_starting_with_an_acronym_uses_the_acronym(self):
        organization = OrganizationFactory(name="GFZ Helmholtz Centre for Geosciences")

        assert organization.get_initials() == "GFZ"

    def test_an_organization_otherwise_uses_its_capitalised_words(self):
        organization = OrganizationFactory(name="University of Potsdam")

        assert organization.get_initials() == "UP"

    def test_a_contributor_without_a_name_has_no_initials(self):
        organization = OrganizationFactory()
        organization.name = ""

        assert organization.get_initials() == ""


@pytest.mark.django_db
class TestIsOrganization:
    def test_an_organization_is_an_organization(self):
        assert OrganizationFactory().is_organization is True

    def test_a_person_is_not_an_organization(self):
        assert PersonFactory().is_organization is False


@pytest.mark.django_db
class TestPrimaryOrganization:
    def test_a_person_is_shown_with_their_primary_affiliations_organization(self):
        person = PersonFactory()
        affiliation = AffiliationFactory(person=person, is_primary=True)
        AffiliationFactory(person=person, is_primary=False)

        assert person.primary_organization == affiliation.organization

    def test_a_person_without_a_primary_affiliation_has_none(self):
        person = PersonFactory()
        AffiliationFactory(person=person, is_primary=False)

        assert person.primary_organization is None

    def test_an_organization_has_none(self):
        assert OrganizationFactory().primary_organization is None

    def test_a_prefetched_person_needs_no_query(self, django_assert_num_queries):
        person = PersonFactory()
        AffiliationFactory(person=person, is_primary=True)
        prefetched = Person.objects.prefetch_related("affiliations__organization").get(
            pk=person.pk
        )

        with django_assert_num_queries(0):
            assert prefetched.primary_organization is not None


@pytest.mark.django_db
class TestPortalRoles:
    def test_a_person_holds_their_portal_roles_in_declaration_order(self):
        from django.contrib.auth.models import Group

        from fairdm.portal_roles import PortalRoles

        person = PersonFactory()
        person.groups.add(
            Group.objects.get(name=PortalRoles.DEVELOPER.name),
            Group.objects.get(name=PortalRoles.PORTAL_ADMINISTRATOR.name),
        )

        assert [str(label) for label in person.portal_roles] == [
            str(PortalRoles.PORTAL_ADMINISTRATOR.label),
            str(PortalRoles.DEVELOPER.label),
        ]

    def test_a_group_the_portal_created_itself_is_not_a_portal_role(self):
        from django.contrib.auth.models import Group

        person = PersonFactory()
        person.groups.add(Group.objects.create(name="Reading club"))

        assert person.portal_roles == []

    def test_an_inactive_person_holds_none(self):
        from django.contrib.auth.models import Group

        from fairdm.portal_roles import PortalRoles

        person = PersonFactory(is_active=False)
        person.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))

        assert person.portal_roles == []


@pytest.mark.django_db
class TestOrganizationSummary:
    def test_the_summary_joins_the_type_and_the_place(self):
        organization = OrganizationFactory(
            type=OrganizationType.EDUCATION, city="Potsdam", country="DE"
        )

        assert organization.summary == (
            f"{OrganizationType.EDUCATION.label} · {organization.get_location_display()}"
        )

    def test_an_organization_with_neither_has_an_empty_summary(self):
        organization = OrganizationFactory(type=None, city=None, country=None)

        assert organization.summary == ""


@pytest.mark.django_db
class TestOrcidIsAuthenticated:
    def test_a_person_who_signed_in_with_orcid_is_authenticated(self):
        from allauth.socialaccount.models import SocialAccount

        person = PersonFactory()
        SocialAccount.objects.create(user=person, provider="orcid", uid="0000-0001-0000-0001")

        assert person.orcid_is_authenticated is True

    def test_another_provider_does_not_count(self):
        from allauth.socialaccount.models import SocialAccount

        person = PersonFactory()
        SocialAccount.objects.create(user=person, provider="github", uid="42")

        assert person.orcid_is_authenticated is False


def _credited(*records):
    """What a credit on each record looks like in the visible contributions."""
    kinds = {
        "project": "project.Project",
        "dataset": "dataset.Dataset",
        "sample": "sample.Sample",
        "measurement": "measurement.Measurement",
    }
    return {
        (
            next(
                kind
                for kind, label in kinds.items()
                if isinstance(record, apps.get_model(label))
            ),
            str(record.pk),
        )
        for record in records
    }


def _records(contributions):
    """The kind and id of each record the contributions are on."""
    return {(c.kind, str(c.object_id)) for c in contributions}


@pytest.mark.django_db
class TestGetVisibleContributions:
    def test_a_visitor_gets_the_public_records_only(self, credited_world):
        world = credited_world

        contributions = world.person.get_visible_contributions(AnonymousUser())

        assert _records(contributions) == _credited(
            world.public_project,
            world.public_dataset,
            world.public_sample,
            world.public_measurement,
        )

    def test_the_person_gets_what_a_visitor_gets(self, credited_world):
        world = credited_world

        contributions = world.person.get_visible_contributions(world.person)

        assert _records(contributions) == _records(
            world.person.get_visible_contributions(AnonymousUser())
        )

    def test_a_member_of_a_private_project_does_not_get_it_listed(
        self, credited_world
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        assign_perm("view_project", member, world.private_project)

        contributions = world.person.get_visible_contributions(member)

        assert _credited(world.private_project).isdisjoint(_records(contributions))

    def test_a_public_dataset_inside_a_private_project_is_left_out(
        self, credited_world
    ):
        world = credited_world

        contributions = world.person.get_visible_contributions(AnonymousUser())

        assert _credited(world.dataset_in_private_project).isdisjoint(
            _records(contributions)
        )

    def test_a_sample_and_a_measurement_inside_a_private_project_are_left_out_for_its_team(
        self, credited_world
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        assign_perm("view_project", member, world.private_project)
        assign_perm("view_dataset", member, world.dataset_in_private_project)

        records = _records(world.person.get_visible_contributions(member))

        assert _credited(
            world.sample_in_private_project, world.measurement_in_private_project
        ).isdisjoint(records)

    def test_a_sample_in_a_private_dataset_follows_who_may_open_the_dataset(
        self, credited_world
    ):
        world = credited_world
        world.person.add_to(world.private_sample)
        team = PersonFactory(is_active=True)
        assign_perm("view_dataset", team, world.private_dataset)

        assert _credited(world.private_sample).isdisjoint(
            _records(world.person.get_visible_contributions(AnonymousUser()))
        )
        assert _credited(world.private_sample) <= _records(
            world.person.get_visible_contributions(team)
        )

    def test_each_contribution_says_which_kind_of_record_it_is(self, credited_world):
        world = credited_world

        kinds = {
            contribution.kind
            for contribution in world.person.get_visible_contributions(
                AnonymousUser()
            )
        }

        assert kinds == {"project", "dataset", "sample", "measurement"}


@pytest.mark.django_db
class TestPublicRecordSources:
    def test_the_public_projects_are_the_credited_projects_that_are_public(
        self, credited_world
    ):
        world = credited_world

        assert set(world.person.get_public_projects()) == {world.public_project}

    def test_the_public_datasets_leave_out_private_ones_and_those_in_private_projects(
        self, credited_world
    ):
        world = credited_world

        assert set(world.person.get_public_datasets()) == {world.public_dataset}

    def test_they_equal_the_projects_and_datasets_among_the_public_credits(
        self, credited_world
    ):
        world = credited_world
        contributions = world.person.get_visible_contributions(AnonymousUser())

        projects = {c.record for c in contributions if c.kind == "project"}
        datasets = {c.record for c in contributions if c.kind == "dataset"}

        assert projects == set(world.person.get_public_projects())
        assert datasets == set(world.person.get_public_datasets())

    def test_a_dataset_with_no_project_is_public_when_it_is_public(self, db):
        person = PersonFactory()
        dataset = DatasetFactory(project=None, visibility=Visibility.PUBLIC)
        person.add_to(dataset)

        assert set(person.get_public_datasets()) == {dataset}


@pytest.mark.django_db
class TestVisibleRoleCounts:
    def test_a_role_held_only_on_a_private_record_is_not_counted(self, credited_world):
        world = credited_world
        contributions = world.person.get_visible_contributions(AnonymousUser())

        counts = world.person.get_role_counts(contributions)

        assert set(counts) == {"Creator", "Data Collector", "Researcher", "Support"}

    def test_each_role_counts_the_records_it_is_held_on(self, credited_world):
        world = credited_world
        world.person.add_to(world.public_dataset, roles=["Creator"])
        contributions = world.person.get_visible_contributions(AnonymousUser())

        counts = world.person.get_role_counts(contributions)

        assert counts["Creator"] == 2


@pytest.mark.django_db
class TestVisibleCollaborators:
    def test_a_collaborator_known_only_through_a_private_record_is_absent(
        self, credited_world
    ):
        world = credited_world
        contributions = world.person.get_visible_contributions(AnonymousUser())

        collaborators = list(world.person.get_collaborators(contributions=contributions))

        assert world.private_mate not in collaborators
        assert world.private_dataset_mate not in collaborators

    def test_the_most_frequent_collaborator_comes_first(self, credited_world):
        world = credited_world
        contributions = world.person.get_visible_contributions(AnonymousUser())

        collaborators = list(world.person.get_collaborators(contributions=contributions))

        assert collaborators == [world.open_mate, world.sample_mate]
        assert collaborators[0].collaboration_count == 2

    def test_collaborators_with_the_same_count_are_ordered_by_name(self, db):
        person = PersonFactory()
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        later = PersonFactory(name="Zed")
        earlier = PersonFactory(name="Abe")
        for contributor in (person, later, earlier):
            contributor.add_to(project)
        contributions = person.get_visible_contributions(AnonymousUser())

        collaborators = list(person.get_collaborators(contributions=contributions))

        assert collaborators == [earlier, later]

    def test_a_collaborator_may_be_an_organization(self, db):
        person = PersonFactory()
        organization = OrganizationFactory()
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        person.add_to(project)
        organization.add_to(project)
        contributions = person.get_visible_contributions(AnonymousUser())

        collaborators = list(person.get_collaborators(contributions=contributions))

        assert collaborators == [organization]

    def test_no_visible_credit_means_no_collaborators(self, db):
        person = PersonFactory()
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        person.add_to(project)
        PersonFactory().add_to(project)
        contributions = person.get_visible_contributions(AnonymousUser())

        assert list(person.get_collaborators(contributions=contributions)) == []


@pytest.mark.django_db
class TestPersonAffiliationHistory:
    def test_the_primary_affiliation_leads_and_the_rest_follow_by_name(self, db):
        person = PersonFactory()
        primary = AffiliationFactory(
            person=person, organization=OrganizationFactory(name="Zeta"), is_primary=True
        )
        beta = AffiliationFactory(person=person, organization=OrganizationFactory(name="Beta"))
        alpha = AffiliationFactory(person=person, organization=OrganizationFactory(name="Alpha"))

        history = person.get_affiliation_history()

        assert history["current"] == [primary, alpha, beta]

    def test_past_affiliations_come_with_the_most_recently_ended_first(self, db):
        person = PersonFactory()
        older = AffiliationFactory(person=person, start_date="2010", end_date="2014")
        newer = AffiliationFactory(person=person, start_date="2015", end_date="2020-05")

        history = person.get_affiliation_history()

        assert history["past"] == [newer, older]
        assert history["current"] == []

    def test_a_pending_affiliation_is_left_out(self, db):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            type=Affiliation.MembershipType.PENDING,
            is_primary=True,
        )

        history = person.get_affiliation_history()

        assert history == {"current": [], "past": []}


@pytest.mark.django_db
class TestPersonMemberSince:
    @pytest.mark.parametrize(
        ("member_name", "has_date"),
        [("ghost", False), ("invited", False), ("claimed", True), ("inactive", True)],
    )
    def test_the_date_is_given_for_a_profile_with_an_account_only(
        self, contributor_population, member_name, has_date
    ):
        person = getattr(contributor_population, member_name)

        assert (person.member_since is not None) is has_date

    def test_the_date_is_when_the_account_was_created(self, contributor_population):
        person = contributor_population.claimed

        assert person.member_since == person.date_joined


@pytest.mark.django_db
class TestAffiliationDisplay:
    @pytest.mark.parametrize(
        ("recorded", "expected"),
        [
            ("2020", "2020"),
            ("2020-03", date_format(date(2020, 3, 1), "YEAR_MONTH_FORMAT")),
            ("2020-03-14", date_format(date(2020, 3, 14), "SHORT_DATE_FORMAT")),
        ],
    )
    def test_a_date_is_shown_as_precisely_as_it_was_recorded(
        self, recorded, expected
    ):
        affiliation = AffiliationFactory(start_date=recorded, end_date=recorded)

        affiliation.refresh_from_db()

        assert affiliation.start_display == expected
        assert affiliation.end_display == expected

    def test_a_date_that_was_not_recorded_is_an_empty_string(self):
        affiliation = AffiliationFactory(start_date=None, end_date=None)

        assert affiliation.start_display == ""
        assert affiliation.end_display == ""


@pytest.mark.django_db
class TestPublicSchemaOrg:
    def test_the_email_address_is_not_carried(self):
        person = PersonFactory(email="private@example.org")

        assert "email" not in person.to_public_schema_org()
        assert "private@example.org" not in str(person.to_public_schema_org())

    def test_the_verified_current_primary_affiliation_is_carried(self):
        person = PersonFactory()
        organization = OrganizationFactory(name="Current Institute")
        AffiliationFactory(person=person, organization=organization, is_primary=True)

        data = person.to_public_schema_org()

        assert data["affiliation"]["name"] == "Current Institute"

    def test_a_pending_primary_affiliation_is_not_carried(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(name="Pending Institute"),
            type=Affiliation.MembershipType.PENDING,
            is_primary=True,
        )

        assert "affiliation" not in person.to_public_schema_org()
        assert "Pending Institute" not in str(person.to_public_schema_org())

    def test_an_ended_primary_affiliation_is_not_carried(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(name="Former Institute"),
            is_primary=True,
            start_date="2010",
            end_date="2015",
        )

        assert "affiliation" not in person.to_public_schema_org()

    def test_an_organization_carries_no_email_either(self):
        organization = OrganizationFactory()

        assert "email" not in organization.to_public_schema_org()


@pytest.mark.django_db
class TestContributorLinks:
    def test_each_link_is_named_by_its_site(self):
        person = PersonFactory(links=["https://www.github.com/someone", "https://x.test/a"])

        assert person.get_links_display() == [
            {"url": "https://www.github.com/someone", "host": "github.com"},
            {"url": "https://x.test/a", "host": "x.test"},
        ]

    def test_no_links_gives_an_empty_list(self):
        assert PersonFactory(links=[]).get_links_display() == []


@pytest.mark.django_db
class TestIdentifierResolverUrl:
    def test_a_type_with_a_resolver_links_to_it(self):
        identifier = ContributorIdentifier.objects.create(
            related=PersonFactory(), type="ORCID", value="0000-0001-2345-6789"
        )

        assert identifier.resolver_url == "https://orcid.org/0000-0001-2345-6789"

    def test_a_type_with_no_resolver_has_no_link(self):
        identifier = ContributorIdentifier.objects.create(
            related=PersonFactory(), type="RESEARCHER_ID", value="A-1234-2020"
        )

        assert identifier.resolver_url is None


@pytest.mark.django_db
class TestOrganizationMemberships:
    @staticmethod
    def _join(organization, name, type=Affiliation.MembershipType.MEMBER, **kwargs):
        return AffiliationFactory(
            organization=organization,
            person=PersonFactory(name=name, is_active=True),
            type=type,
            **kwargs,
        )

    def test_only_current_verified_members_are_listed(self):
        organization = OrganizationFactory()
        current = self._join(organization, "Current")
        self._join(organization, "Pending", type=Affiliation.MembershipType.PENDING)
        self._join(organization, "Former", start_date="2010", end_date="2014")
        self._join(OrganizationFactory(), "Elsewhere")

        assert organization.get_current_memberships() == [current]

    def test_the_owner_comes_first_then_administrators_then_members_each_by_name(self):
        organization = OrganizationFactory()
        member_b = self._join(organization, "Beta")
        member_a = self._join(organization, "Alpha")
        admin_b = self._join(organization, "Yara", Affiliation.MembershipType.ADMIN)
        admin_a = self._join(organization, "Xavier", Affiliation.MembershipType.ADMIN)
        owner = self._join(organization, "Zed", Affiliation.MembershipType.OWNER)

        assert organization.get_current_memberships() == [
            owner,
            admin_a,
            admin_b,
            member_a,
            member_b,
        ]

    def test_an_organization_with_no_members_lists_none(self):
        assert OrganizationFactory().get_current_memberships() == []


@pytest.mark.django_db
class TestOrganizationHasMember:
    @pytest.mark.parametrize(
        "type",
        [
            Affiliation.MembershipType.MEMBER,
            Affiliation.MembershipType.ADMIN,
            Affiliation.MembershipType.OWNER,
        ],
    )
    def test_a_current_verified_affiliation_of_any_kind_counts(self, type):
        affiliation = AffiliationFactory(type=type)

        assert affiliation.organization.has_member(affiliation.person) is True

    def test_a_pending_affiliation_does_not_count(self):
        affiliation = AffiliationFactory(type=Affiliation.MembershipType.PENDING)

        assert affiliation.organization.has_member(affiliation.person) is False

    def test_an_ended_affiliation_does_not_count(self):
        affiliation = AffiliationFactory(start_date="2010", end_date="2014")

        assert affiliation.organization.has_member(affiliation.person) is False

    def test_an_affiliation_to_another_organization_does_not_count(self):
        affiliation = AffiliationFactory()

        assert OrganizationFactory().has_member(affiliation.person) is False

    def test_a_visitor_is_not_a_member(self):
        assert OrganizationFactory().has_member(AnonymousUser()) is False


@pytest.mark.django_db
class TestOrganizationIsManagedBy:
    @pytest.mark.parametrize(
        ("type", "managed"),
        [
            (Affiliation.MembershipType.OWNER, True),
            (Affiliation.MembershipType.ADMIN, True),
            (Affiliation.MembershipType.MEMBER, False),
            (Affiliation.MembershipType.PENDING, False),
        ],
    )
    def test_only_the_owner_and_administrators_keep_the_record(self, type, managed):
        affiliation = AffiliationFactory(type=type)

        assert affiliation.organization.is_managed_by(affiliation.person) is managed

    @pytest.mark.parametrize(
        "type", [Affiliation.MembershipType.OWNER, Affiliation.MembershipType.ADMIN]
    )
    def test_an_ended_affiliation_does_not_count(self, type):
        affiliation = AffiliationFactory(
            type=type, start_date="2010", end_date="2014"
        )

        assert affiliation.organization.is_managed_by(affiliation.person) is False

    def test_a_portal_role_does_not_count(self):
        organization = OrganizationFactory()
        staff = PersonFactory(is_active=True, is_staff=True, is_superuser=True)

        assert organization.is_managed_by(staff) is False

    def test_a_visitor_does_not_keep_any_record(self):
        assert OrganizationFactory().is_managed_by(AnonymousUser()) is False


@pytest.mark.django_db
class TestOrganizationHierarchy:
    def test_it_gives_the_parent_the_siblings_with_this_one_among_them_and_the_children(
        self,
    ):
        parent = OrganizationFactory(name="Parent")
        organization = OrganizationFactory(name="Middle", parent=parent)
        before = OrganizationFactory(name="Before", parent=parent)
        after = OrganizationFactory(name="Zulu", parent=parent)
        child_b = OrganizationFactory(name="Child B", parent=organization)
        child_a = OrganizationFactory(name="Child A", parent=organization)
        OrganizationFactory(name="Grandchild", parent=child_a)

        hierarchy = organization.get_hierarchy()

        assert hierarchy["parent"] == parent
        assert hierarchy["siblings"] == [before, organization, after]
        assert hierarchy["children"] == [child_a, child_b]

    def test_without_a_parent_there_are_no_siblings(self):
        organization = OrganizationFactory()
        OrganizationFactory()
        child = OrganizationFactory(parent=organization)

        hierarchy = organization.get_hierarchy()

        assert hierarchy["parent"] is None
        assert hierarchy["siblings"] == []
        assert hierarchy["children"] == [child]

    def test_with_neither_a_parent_nor_children_it_is_empty(self):
        hierarchy = OrganizationFactory().get_hierarchy()

        assert hierarchy == {"parent": None, "siblings": [], "children": []}
