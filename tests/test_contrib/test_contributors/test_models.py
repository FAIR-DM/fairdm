"""Tests for the contributor models."""

import json
from datetime import date

import pytest
from django.apps import apps
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point as GEOSPoint
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import resolve
from django.utils import timezone
from django.utils.formats import date_format

from fairdm.contrib.contributors.choices import (
    AccountState,
    ContributionLevel,
    OrganizationType,
)
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, IDENTIFIER_TYPES
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility


class TestContributorIdentity:
    @pytest.mark.django_db
    def test_person_identifier_carries_contributor_prefix(self):
        person = PersonFactory()
        assert person.uuid
        assert person.uuid.startswith("c")

    @pytest.mark.django_db
    def test_identifier_unchanged_on_second_save(self):
        person = PersonFactory()
        original_uuid = person.uuid
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.uuid == original_uuid


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
    def test_no_separate_account_model_registered(self):
        username_field_models = [
            model for model in apps.get_models() if hasattr(model, "USERNAME_FIELD")
        ]
        assert username_field_models == [Person]


class TestAttributionOnlyPerson:
    @pytest.mark.django_db
    def test_authenticate_fails_for_attribution_only_person(self, unclaimed_person):
        result = authenticate(
            request=None, email=unclaimed_person.email, password="whatever"
        )
        assert result is None


class TestPersonActivationEligibility:
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
    def test_person_auto_populates_name_from_first_last(self, db):
        p = PersonFactory(first_name="Jane", last_name="Smith", name="")
        assert p.name == "Jane Smith"

    @pytest.mark.django_db
    def test_person_clean_lowercases_email(self, db):
        p = PersonFactory(email="UPPER@Example.com")
        p.clean()
        assert p.email == "upper@example.com"


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
class TestOrganizationFromRor:
    def test_creates_the_organization_from_its_ror_record(
        self, registry_network, recorded
    ):
        registry_network.answer(
            "https://api.ror.org/v2/organizations/04z8jg394", recorded("ror-record")
        )

        organization = Organization.from_ror("https://ror.org/04z8jg394")

        organization.refresh_from_db()
        assert organization.name == "GFZ Helmholtz Centre for Geosciences"
        assert organization.city == "Potsdam"
        assert organization.country.code == "DE"
        assert (
            organization.identifiers.get(type_id=f"{IDENTIFIER_TYPES}/ror").value
            == "04z8jg394"
        )

    def test_a_new_ror_identifier_is_synced_once_the_transaction_commits(
        self, registry_network, recorded, django_capture_on_commit_callbacks
    ):
        registry_network.answer(
            "https://api.ror.org/v2/organizations/04z8jg394", recorded("ror-record")
        )
        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            Organization.from_ror("04z8jg394")
        fetched_before_commit = len(registry_network.calls)

        for callback in callbacks:
            callback()

        assert len(registry_network.calls) == fetched_before_commit + 1


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


class TestContributionGFKRelationships:
    @pytest.mark.django_db
    def test_a_credit_is_not_given_the_primary_affiliation(self, person, organization):
        AffiliationFactory(
            person=person,
            organization=organization,
            is_primary=True,
        )
        project = ProjectFactory()
        c = person.add_to(project)
        assert c.affiliation is None

    @pytest.mark.django_db
    def test_contribution_has_contribution_to(
        self, person, contribution, project_for_contributions
    ):
        assert person.has_contribution_to(project_for_contributions) is True

    @pytest.mark.django_db
    def test_contribution_projects_property(self, person, contribution):
        assert list(person.projects) == [contribution.content_object]

    @pytest.mark.django_db
    def test_contribution_manager_by_contributor(self, person, contribution):
        qs = Contribution.objects.by_contributor(person)

        assert contribution in qs
        assert not qs.exclude(contributor=person).exists()


class TestContributionTargets:
    @pytest.mark.django_db
    def test_person_creditable_on_a_project(self, person, project_for_contributions):
        contribution = person.add_to(project_for_contributions)

        assert contribution.content_object == project_for_contributions

    @pytest.mark.django_db
    def test_person_creditable_on_a_measurement(self, person):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        contribution = person.add_to(measurement)

        assert contribution.content_object == measurement


class TestContributionUniqueness:
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
    def test_crediting_again_under_a_new_role_accumulates_via_contribution_add_to(
        self, person, project_for_contributions
    ):
        Contribution.add_to(
            person,
            project_for_contributions,
            roles=[f"{CONTRIBUTOR_ROLES}/data-collector"],
        )
        contribution = Contribution.add_to(
            person, project_for_contributions, roles=[f"{CONTRIBUTOR_ROLES}/researcher"]
        )

        assert (
            Contribution.objects.filter(
                contributor=person, object_id=project_for_contributions.pk
            ).count()
            == 1
        )
        role_names = set(contribution.roles.values_list("uri", flat=True))
        assert role_names == {
            f"{CONTRIBUTOR_ROLES}/data-collector",
            f"{CONTRIBUTOR_ROLES}/researcher",
        }


class TestContributionRoles:
    @pytest.mark.django_db
    def test_role_from_the_roles_vocabulary_is_accepted(self, contribution):
        from controlled_vocabularies.models import Record

        role = Record.objects.filter(
            scheme__uri=CONTRIBUTOR_ROLES, type=Record.Type.CONCEPT
        ).first()
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
    def test_counts_by_kind_cost_the_same_queries_for_one_credit_or_three(self, person):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        def credit_every_kind():
            person.add_to(ProjectFactory())
            person.add_to(DatasetFactory())
            person.add_to(RockSampleFactory())
            person.add_to(ExampleMeasurementFactory(sample=RockSampleFactory()))

        def queries_for_the_counts():
            with CaptureQueriesContext(connection) as captured:
                person.get_credit_counts()
            return len(captured)

        credit_every_kind()
        queries_for_the_counts()
        with_one_of_each = queries_for_the_counts()
        credit_every_kind()
        credit_every_kind()

        assert queries_for_the_counts() == with_one_of_each


class TestCollaborators:
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


class TestIdentifierUniquePerType:
    @pytest.mark.django_db
    def test_second_identifier_of_same_type_refused_at_clean(
        self, orcid_identifier, person
    ):
        duplicate = ContributorIdentifier(
            related=person,
            type_id=f"{IDENTIFIER_TYPES}/orcid",
            value="0000-0001-9999-9999",
        )

        with pytest.raises(ValidationError) as excinfo:
            duplicate.clean()

        assert "ORCID" in str(excinfo.value)

    @pytest.mark.django_db
    def test_a_second_type_on_the_same_contributor_is_unaffected(
        self, orcid_identifier, person
    ):
        second = ContributorIdentifier(
            related=person,
            type_id=f"{IDENTIFIER_TYPES}/researcher-id",
            value="A-1234-2020",
        )

        second.clean()
        second.save()

        assert person.identifiers.count() == 2


class TestIdentifierValueUniqueAcrossContributors:
    @pytest.mark.django_db
    def test_second_contributor_with_the_same_value_refused_at_clean(
        self, orcid_identifier, organization
    ):
        duplicate = ContributorIdentifier(
            related=organization,
            type_id=f"{IDENTIFIER_TYPES}/ror",
            value=orcid_identifier.value,
        )

        with pytest.raises(ValidationError) as excinfo:
            duplicate.clean()

        assert "value" in excinfo.value.message_dict


class TestDefaultIdentifier:
    @pytest.mark.django_db
    def test_person_default_identifier_is_its_orcid(self, orcid_identifier, person):
        assert person.get_default_identifier() == orcid_identifier

    @pytest.mark.django_db
    def test_default_identifier_is_none_without_any_identifiers(self, person):
        assert person.get_default_identifier() is None


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


class TestPrimaryAffiliationConstraint:
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
    def test_update_raises_value_error(self, db, audit_log_entry):

        from fairdm.contrib.contributors.models import ClaimingAuditLog

        original_reason = audit_log_entry.failure_reason
        audit_log_entry.failure_reason = "tampered"
        with pytest.raises(ValueError, match="immutable"):
            audit_log_entry.save()

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
        assert not ClaimingAuditLog.objects.for_person(PersonFactory().pk).exists()

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
        person = PersonFactory(
            first_name="ada", last_name="lovelace", name="The Countess"
        )

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

    def test_a_pending_primary_affiliation_gives_none(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            is_primary=True,
            type=Affiliation.MembershipType.PENDING,
        )

        assert person.primary_affiliation() is None
        assert person.primary_organization is None

    def test_an_ended_primary_affiliation_gives_none(self):
        person = PersonFactory()
        AffiliationFactory(person=person, is_primary=True, end_date="2023")

        assert person.primary_affiliation() is None
        assert person.primary_organization is None

    def test_an_organization_has_none(self):
        assert OrganizationFactory().primary_organization is None

    def test_a_prefetched_person_needs_no_query(self, django_assert_num_queries):
        person = PersonFactory()
        affiliation = AffiliationFactory(person=person, is_primary=True)
        prefetched = Person.objects.prefetch_related("affiliations__organization").get(
            pk=person.pk
        )

        with django_assert_num_queries(0):
            assert prefetched.primary_organization == affiliation.organization


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
        SocialAccount.objects.create(
            user=person, provider="orcid", uid="0000-0001-0000-0001"
        )

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

    def test_a_member_of_a_private_project_does_not_get_it_listed(self, credited_world):
        world = credited_world
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=world.private_project,
            contributor=member,
            level=ContributionLevel.VIEW,
        )

        contributions = world.person.get_visible_contributions(member)

        assert _credited(world.private_project).isdisjoint(_records(contributions))

    def test_a_sample_and_a_measurement_inside_a_private_project_are_left_out_for_its_team(
        self, credited_world
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=world.private_project,
            contributor=member,
            level=ContributionLevel.VIEW,
        )
        ContributionFactory(
            content_object=world.dataset_in_private_project,
            contributor=member,
            level=ContributionLevel.VIEW,
        )

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
        ContributionFactory(
            content_object=world.private_dataset,
            contributor=team,
            level=ContributionLevel.VIEW,
        )

        assert _credited(world.private_sample).isdisjoint(
            _records(world.person.get_visible_contributions(AnonymousUser()))
        )
        assert _credited(world.private_sample) <= _records(
            world.person.get_visible_contributions(team)
        )


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
        world.person.add_to(
            world.public_dataset, roles=[f"{CONTRIBUTOR_ROLES}/creator"]
        )
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

        collaborators = list(
            world.person.get_collaborators(contributions=contributions)
        )

        assert world.private_mate not in collaborators
        assert world.private_dataset_mate not in collaborators

    def test_the_most_frequent_collaborator_comes_first(self, credited_world):
        world = credited_world
        contributions = world.person.get_visible_contributions(AnonymousUser())

        collaborators = list(
            world.person.get_collaborators(contributions=contributions)
        )

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
            person=person,
            organization=OrganizationFactory(name="Zeta"),
            is_primary=True,
        )
        beta = AffiliationFactory(
            person=person, organization=OrganizationFactory(name="Beta")
        )
        alpha = AffiliationFactory(
            person=person, organization=OrganizationFactory(name="Alpha")
        )

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
    def test_the_date_is_when_the_account_was_created(self):
        person = PersonFactory(is_claimed=True)

        assert person.member_since == person.date_joined

    def test_a_profile_nobody_claimed_has_no_date(self):
        person = PersonFactory(is_claimed=False, email=None)

        assert person.member_since is None


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
    def test_a_date_is_shown_as_precisely_as_it_was_recorded(self, recorded, expected):
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
        person = PersonFactory(
            links=["https://www.github.com/someone", "https://x.test/a"]
        )

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
            related=PersonFactory(),
            type_id=f"{IDENTIFIER_TYPES}/orcid",
            value="0000-0001-2345-6789",
        )

        assert identifier.resolver_url == "https://orcid.org/0000-0001-2345-6789"

    def test_a_type_with_no_resolver_has_no_link(self):
        identifier = ContributorIdentifier.objects.create(
            related=PersonFactory(),
            type_id=f"{IDENTIFIER_TYPES}/researcher-id",
            value="A-1234-2020",
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
    def test_a_current_verified_affiliation_counts(self):
        affiliation = AffiliationFactory(type=Affiliation.MembershipType.MEMBER)

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
            (Affiliation.MembershipType.ADMIN, True),
            (Affiliation.MembershipType.MEMBER, False),
        ],
    )
    def test_only_the_owner_and_administrators_keep_the_record(self, type, managed):
        affiliation = AffiliationFactory(type=type)

        assert affiliation.organization.is_managed_by(affiliation.person) is managed

    def test_an_ended_affiliation_does_not_count(self):
        affiliation = AffiliationFactory(
            type=Affiliation.MembershipType.ADMIN, start_date="2010", end_date="2014"
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


@pytest.mark.django_db
class TestOrganizationPublicRecordSources:
    def test_the_projects_are_the_public_ones_it_owns_and_those_it_is_credited_on(self):
        organization = OrganizationFactory()
        owned = ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        credited = ProjectFactory(visibility=Visibility.PUBLIC)
        organization.add_to(credited)
        ProjectFactory(owner=organization, visibility=Visibility.PRIVATE)
        private_credit = ProjectFactory(visibility=Visibility.PRIVATE)
        organization.add_to(private_credit)
        ProjectFactory(visibility=Visibility.PUBLIC)

        assert set(organization.get_public_projects()) == {owned, credited}

    def test_a_project_it_owns_and_is_credited_on_is_listed_once(self):
        organization = OrganizationFactory()
        project = ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        organization.add_to(project)

        assert list(organization.get_public_projects()) == [project]

    def test_the_datasets_are_those_it_is_credited_on_and_those_in_its_projects(self):
        organization = OrganizationFactory()
        owned = ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        inside = DatasetFactory(project=owned, visibility=Visibility.PUBLIC)
        inside_credited = DatasetFactory(project=owned, visibility=Visibility.PUBLIC)
        organization.add_to(inside_credited)
        credited = DatasetFactory(project=None, visibility=Visibility.PUBLIC)
        organization.add_to(credited)
        DatasetFactory(project=owned, visibility=Visibility.PRIVATE)
        DatasetFactory(visibility=Visibility.PUBLIC)

        datasets = organization.get_public_datasets()

        assert set(datasets) == {inside, inside_credited, credited}
        assert len(datasets) == 3

    def test_a_dataset_in_a_private_project_is_left_out_even_when_it_owns_the_project(
        self,
    ):
        organization = OrganizationFactory()
        private = ProjectFactory(owner=organization, visibility=Visibility.PRIVATE)
        DatasetFactory(project=private, visibility=Visibility.PUBLIC)

        assert list(organization.get_public_datasets()) == []

    def test_what_its_members_are_credited_on_is_not_its_own(self):
        organization = OrganizationFactory()
        member = AffiliationFactory(organization=organization).person
        member.add_to(ProjectFactory(visibility=Visibility.PUBLIC))
        member.add_to(DatasetFactory(project=None, visibility=Visibility.PUBLIC))

        assert list(organization.get_public_projects()) == []
        assert list(organization.get_public_datasets()) == []

    def test_the_credits_it_returns_are_for_records_it_is_credited_on_only(self):
        organization = OrganizationFactory()
        ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        credited = ProjectFactory(visibility=Visibility.PUBLIC)
        organization.add_to(credited)

        contributions = organization.get_visible_contributions(AnonymousUser())

        assert [c.record for c in contributions] == [credited]


@pytest.mark.django_db
class TestPersonProfileCompleteness:
    def test_a_bare_profile_has_none_of_the_items(self):
        person = PersonFactory(profile="", links=[])

        assert person.get_profile_completeness() == {
            "image": False,
            "orcid": False,
            "profile": False,
            "primary_affiliation": False,
            "links": False,
        }

    def test_a_filled_in_profile_has_every_item(self):
        from allauth.socialaccount.models import SocialAccount

        person = PersonFactory(
            with_image=True, profile="A biography.", links=["https://example.org/me"]
        )
        SocialAccount.objects.create(user=person, provider="orcid", uid="0000-0001")
        AffiliationFactory(person=person, is_primary=True)

        assert all(person.get_profile_completeness().values())

    def test_an_orcid_id_typed_in_is_not_connected(self):
        person = PersonFactory()
        ContributorIdentifier.objects.create(
            related=person,
            type_id=f"{IDENTIFIER_TYPES}/orcid",
            value="0000-0001-2345-6789",
        )

        assert person.get_profile_completeness()["orcid"] is False

    def test_signing_in_with_orcid_is_connected(self):
        from allauth.socialaccount.models import SocialAccount

        person = PersonFactory()
        SocialAccount.objects.create(user=person, provider="orcid", uid="0000-0001")

        assert person.get_profile_completeness()["orcid"] is True

    def test_an_affiliation_that_is_not_primary_does_not_count(self):
        person = PersonFactory()
        AffiliationFactory(person=person, is_primary=False)

        assert person.get_profile_completeness()["primary_affiliation"] is False

    def test_a_current_verified_primary_affiliation_counts(self):
        person = PersonFactory()
        AffiliationFactory(person=person, is_primary=True)

        assert person.get_profile_completeness()["primary_affiliation"] is True

    def test_an_ended_primary_affiliation_does_not_count(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person, is_primary=True, start_date="2010", end_date="2014"
        )

        assert person.get_profile_completeness()["primary_affiliation"] is False

    def test_a_pending_primary_affiliation_does_not_count(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            is_primary=True,
            type=Affiliation.MembershipType.PENDING,
        )

        assert person.get_profile_completeness()["primary_affiliation"] is False


@pytest.mark.django_db
class TestOrganizationRecordCompleteness:
    def test_a_bare_record_has_none_of_the_items(self):
        organization = OrganizationFactory(
            profile="", type="", city="", country="", links=[]
        )

        assert not any(organization.get_record_completeness().values())

    def test_a_filled_in_record_has_every_item(self):
        organization = OrganizationFactory(
            with_image=True,
            profile="A description.",
            type=OrganizationType.EDUCATION,
            city="Potsdam",
            country="DE",
            links=["https://example.org"],
        )
        ContributorIdentifier.objects.create(
            related=organization,
            type_id=f"{IDENTIFIER_TYPES}/ror",
            value="https://ror.org/02nr0ka47",
        )

        assert all(organization.get_record_completeness().values())

    def test_only_a_ror_identifier_counts_as_the_ror_item(self):
        organization = OrganizationFactory()
        ContributorIdentifier.objects.create(
            related=organization,
            type_id=f"{IDENTIFIER_TYPES}/isni",
            value="0000000121032683",
        )

        assert organization.get_record_completeness()["ror"] is False

        ContributorIdentifier.objects.create(
            related=organization,
            type_id=f"{IDENTIFIER_TYPES}/ror",
            value="https://ror.org/02nr0ka47",
        )

        assert organization.get_record_completeness()["ror"] is True

    @pytest.mark.parametrize(
        ("kwargs", "complete"),
        [
            ({"city": "Potsdam", "country": "DE"}, True),
            ({"city": "Potsdam", "country": ""}, False),
            ({"city": "", "country": "DE"}, False),
        ],
    )
    def test_the_location_needs_both_the_city_and_the_country(self, kwargs, complete):
        organization = OrganizationFactory(**kwargs)

        assert organization.get_record_completeness()["location"] is complete


@pytest.mark.django_db
class TestPersonLocationDisplay:
    def test_it_is_the_city_and_country_of_the_current_verified_primary_affiliation(
        self,
    ):
        person = PersonFactory()
        organization = OrganizationFactory(city="Potsdam", country="DE")
        AffiliationFactory(person=person, organization=organization, is_primary=True)

        assert person.get_location_display() == "Potsdam, Germany"

    def test_it_reads_a_prefetch_of_the_affiliations(self, django_assert_num_queries):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(city="Potsdam", country="DE"),
            is_primary=True,
        )
        person = Person.objects.prefetch_related("affiliations__organization").get(
            pk=person.pk
        )

        with django_assert_num_queries(0):
            person.get_location_display()


@pytest.mark.django_db
class TestPersonPlacedOnAMap:
    def test_a_person_is_placed_at_the_point_of_their_primary_affiliation_only(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(
                location=GEOSPoint(2.35, 48.85, srid=4326)
            ),
            is_primary=False,
        )
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(
                location=GEOSPoint(13.06566, 52.39886, srid=4326)
            ),
            is_primary=True,
        )

        feature = json.loads(person.as_geojson())

        assert feature["geometry"]["coordinates"] == [13.06566, 52.39886]

    def test_a_person_whose_organization_has_no_point_is_not_placed(self):
        person = PersonFactory()
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(location=None),
            is_primary=True,
        )

        assert person.as_geojson() is None


class TestProfileSafety:
    @pytest.mark.django_db
    def test_a_link_that_is_not_a_web_address_is_left_out(self):
        person = PersonFactory()
        Person.objects.filter(pk=person.pk).update(
            links=["javascript:alert(1)", "https://example.org/me"]
        )
        person.refresh_from_db()

        assert [link["url"] for link in person.get_links_display()] == [
            "https://example.org/me"
        ]


@pytest.mark.django_db
class TestPersonIsEditableBy:
    def test_a_person_may_edit_their_own_profile(self, person):
        assert person.is_editable_by(person) is True

    def test_another_signed_in_person_may_not_edit_it(self, person):
        stranger = PersonFactory(is_active=True, password="x")

        assert person.is_editable_by(stranger) is False

    def test_a_visitor_may_not_edit_it(self, person):
        assert person.is_editable_by(AnonymousUser()) is False

    def test_a_community_manager_may_edit_an_unclaimed_person(self, community_manager):
        person = PersonFactory(is_active=True, is_claimed=False)

        assert person.is_editable_by(community_manager) is True

    def test_a_community_manager_may_edit_a_person_whose_account_is_inactive(
        self, community_manager
    ):
        person = PersonFactory(is_active=False, is_claimed=True, password="x")

        assert person.is_editable_by(community_manager) is True

    def test_a_community_manager_may_not_edit_a_person_with_an_active_account(
        self, community_manager
    ):
        person = PersonFactory(is_active=True, is_claimed=True, password="x")

        assert person.is_editable_by(community_manager) is False

    def test_a_person_removed_from_the_role_may_no_longer_edit_it(
        self, community_manager
    ):
        person = PersonFactory(is_active=True, is_claimed=False)
        community_manager.groups.clear()

        assert person.is_editable_by(community_manager) is False

    def test_a_data_curator_may_not_edit_an_unclaimed_person(self):
        curator = PersonFactory(is_active=True, password="x")
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        person = PersonFactory(is_active=True, is_claimed=False)

        assert person.is_editable_by(curator) is False


@pytest.mark.django_db
class TestOrganizationRorIdentifier:
    @pytest.mark.parametrize("value", ["02nr0ka47", "https://ror.org/02nr0ka47"])
    def test_a_ror_stored_as_the_bare_identifier_or_the_full_address_validates(
        self, value
    ):
        organization = OrganizationFactory()
        ContributorIdentifier.objects.create(
            related=organization, type_id=f"{IDENTIFIER_TYPES}/ror", value=value
        )

        organization.full_clean()

    @pytest.mark.parametrize(
        "value",
        [
            "not-a-ror",
            "https://example.org/02nr0ka47",
            "12nr0ka47",
        ],
    )
    def test_a_malformed_ror_still_fails_on_the_identifiers_field(self, value):
        organization = OrganizationFactory()
        ContributorIdentifier.objects.create(
            related=organization, type_id=f"{IDENTIFIER_TYPES}/ror", value=value
        )

        with pytest.raises(ValidationError) as error:
            organization.full_clean()

        assert "identifiers" in error.value.message_dict


@pytest.mark.django_db
class TestOrganizationDescendantIds:
    def test_an_organization_with_no_sub_organizations_has_none(self):
        organization = OrganizationFactory()

        assert organization.get_descendant_ids() == set()

    def test_the_grandchildren_are_included(self):
        organization = OrganizationFactory()
        child = OrganizationFactory(parent=organization)
        grandchild = OrganizationFactory(parent=child)
        great_grandchild = OrganizationFactory(parent=grandchild)

        assert organization.get_descendant_ids() == {
            child.pk,
            grandchild.pk,
            great_grandchild.pk,
        }

    def test_the_parent_and_the_siblings_are_not_included(self):
        parent = OrganizationFactory()
        organization = OrganizationFactory(parent=parent)
        OrganizationFactory(parent=parent)

        assert organization.get_descendant_ids() == set()

    def test_a_loop_already_stored_does_not_run_forever(self):
        first = OrganizationFactory()
        second = OrganizationFactory(parent=first)
        Organization.objects.filter(pk=first.pk).update(parent=second)
        first.refresh_from_db()

        assert first.get_descendant_ids() == {first.pk, second.pk}


@pytest.mark.django_db
class TestOrganizationParentLoop:
    def test_the_organization_itself_is_refused_as_its_parent(self):
        organization = OrganizationFactory()
        organization.parent = organization

        with pytest.raises(ValidationError) as refused:
            organization.full_clean()

        assert set(refused.value.message_dict) == {"parent"}

    def test_an_organization_beneath_it_is_refused_as_its_parent(self):
        organization = OrganizationFactory()
        child = OrganizationFactory(parent=organization)
        grandchild = OrganizationFactory(parent=child)

        for beneath in (child, grandchild):
            organization.parent = beneath
            with pytest.raises(ValidationError) as refused:
                organization.full_clean()

            assert set(refused.value.message_dict) == {"parent"}

    def test_an_unrelated_organization_is_accepted(self):
        organization = OrganizationFactory()
        organization.parent = OrganizationFactory()

        organization.full_clean()

    def test_an_organization_not_saved_yet_may_have_any_parent(self):
        organization = OrganizationFactory.build(parent=OrganizationFactory())

        organization.full_clean(exclude=["uuid"])


@pytest.mark.django_db
class TestOrganizationIsEditableBy:
    @pytest.fixture
    def organization(self):
        return OrganizationFactory()

    def _joined(self, organization, type, **kwargs):
        person = PersonFactory(is_active=True, password="x")
        AffiliationFactory(
            person=person, organization=organization, type=type, **kwargs
        )
        return person

    def test_a_person_who_keeps_the_record_may_edit_it(self, organization):
        keeper = self._joined(organization, Affiliation.MembershipType.ADMIN)

        assert organization.is_editable_by(keeper) is True

    def test_a_stranger_may_not_edit_it(self, organization):
        stranger = PersonFactory(is_active=True, password="x")

        assert organization.is_editable_by(stranger) is False

    def test_a_deactivated_administrator_may_not_edit_it(self, organization):
        keeper = self._joined(organization, Affiliation.MembershipType.ADMIN)
        keeper.is_active = False
        keeper.save()

        assert organization.is_editable_by(keeper) is False

    def test_a_community_manager_may_edit_it(self, organization, community_manager):
        assert organization.is_editable_by(community_manager) is True

    def test_a_person_removed_from_the_role_may_no_longer_edit_it(
        self, organization, community_manager
    ):
        community_manager.groups.clear()

        assert organization.is_editable_by(community_manager) is False

    def test_a_deactivated_community_manager_may_not_edit_it(
        self, organization, community_manager
    ):
        community_manager.is_active = False
        community_manager.save()

        assert organization.is_editable_by(community_manager) is False


class TestContributorUpdateUrl:
    @pytest.mark.django_db
    def test_the_address_is_the_editing_page_of_the_overview(self):
        contributor = PersonFactory()

        match = resolve(contributor.get_update_url())

        assert match.view_name == "contributor:overview-update"
        assert match.kwargs == {"uuid": contributor.uuid}


@pytest.mark.django_db
class TestPersonCanSignIn:
    def test_an_active_claimed_person_can(self):
        person = PersonFactory(is_active=True, is_claimed=True, password="x")

        assert person.can_sign_in() is True

    def test_an_active_person_who_signed_in_without_being_marked_claimed_can(self):
        person = PersonFactory(is_active=True, is_claimed=False, password="x")
        person.last_login = timezone.now()
        person.save()

        assert person.can_sign_in() is True

    def test_a_person_who_never_signed_in_and_never_claimed_cannot(self):
        person = PersonFactory(is_active=True, is_claimed=False, password="x")

        assert person.can_sign_in() is False

    def test_an_inactive_person_cannot(self):
        person = PersonFactory(is_active=False, is_claimed=True, password="x")

        assert person.can_sign_in() is False


@pytest.mark.django_db
class TestACreditStartsAtTheViewLevel:
    @pytest.fixture
    def credit(self, project_for_contributions):
        def make(contributor):
            return Contribution.add_to(contributor, project_for_contributions)

        return make

    def test_a_person_starts_at_the_view_level(self, credit):
        person = PersonFactory(is_active=True)

        assert credit(person).level == ContributionLevel.VIEW

    def test_an_organization_holds_no_level(self, credit):
        assert credit(OrganizationFactory()).level is None

    def test_crediting_again_leaves_the_level_alone(self, credit):
        person = PersonFactory(is_active=True)
        contribution = credit(person)
        contribution.level = ContributionLevel.MANAGE
        contribution.save(update_fields=["level"])

        assert credit(person).level == ContributionLevel.MANAGE
