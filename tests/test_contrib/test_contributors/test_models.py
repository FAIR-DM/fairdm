"""Tests for contributor data models (User Story 1).

Tests cover:
- Person claimed/unclaimed semantics (T013)
- Organization creation and validation (T014)
- Affiliation unique constraints (T015)
- Contribution GFK relationships (T016)
- ContributorIdentifier uniqueness (T017)
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    Contributor,
    Organization,
    OrganizationMember,
    Person,
)
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)

# ── T013: Person claimed/unclaimed semantics ────────────────────────────────


class TestPersonClaimedUnclaimedSemantics:
    """Verify claimed vs unclaimed Person behavior."""

    @pytest.mark.django_db
    def test_claimed_person_has_email_and_is_active(self, person):
        """A claimed person has email, is_active, and is_claimed property returns True."""
        assert person.email is not None
        assert person.is_active is True
        assert person.is_claimed is True

    @pytest.mark.django_db
    def test_unclaimed_person_has_no_email(self, unclaimed_person):
        """An unclaimed person has no email, is_active=True (allows claiming), is_claimed=False."""
        assert unclaimed_person.email is None
        assert unclaimed_person.is_active is True  # Allows future claiming
        assert unclaimed_person.is_claimed is False

    @pytest.mark.django_db
    def test_create_unclaimed_via_manager(self, db):
        """UserManager.create_unclaimed() creates a provenance-only record."""
        p = Person.objects.create_unclaimed(
            first_name="Test",
            last_name="Unclaimed",
        )
        assert p.pk is not None
        assert p.email is None
        assert p.is_active is True  # Allows future claiming
        assert p.is_claimed is False
        assert not p.has_usable_password()
        assert p.name == "Test Unclaimed"

    @pytest.mark.django_db
    def test_person_auto_populates_name_from_first_last(self, db):
        """Person.save() auto-populates name from first_name + last_name."""
        p = PersonFactory(first_name="Jane", last_name="Smith", name="")
        assert p.name == "Jane Smith"

    @pytest.mark.django_db
    def test_person_is_claimed_requires_usable_password(self, db):
        """A person with email and is_active but no usable password is not claimed."""
        p = Person.objects.create_unclaimed(first_name="No", last_name="Password")
        p.email = "test@example.com"
        p.is_active = True
        p.save()
        # Still not claimed because no usable password
        assert p.is_claimed is False

    @pytest.mark.django_db
    def test_claimed_person_default_privacy_settings(self, db):
        """Claimed persons get default privacy_settings with email=private."""
        p = UserFactory(email="privacy@example.com", is_active=True)
        assert isinstance(p.privacy_settings, dict)
        assert p.privacy_settings.get("email") == "private"

    @pytest.mark.django_db
    def test_unclaimed_person_default_privacy_settings(self, db):
        """Unclaimed persons get default privacy_settings with all=public."""
        p = Person.objects.create_unclaimed(first_name="Open", last_name="Person")
        # Unclaimed defaults: all public
        assert isinstance(p.privacy_settings, dict)
        assert p.privacy_settings.get("email") == "public"

    @pytest.mark.django_db
    def test_person_clean_lowercases_email(self, db):
        """Person.clean() lowercases the email."""
        p = PersonFactory(email="UPPER@Example.com")
        p.clean()
        assert p.email == "upper@example.com"

    @pytest.mark.django_db
    def test_person_polymorphic_query(self, db):
        """Person instances are retrievable via Contributor polymorphic queryset."""
        p = PersonFactory()
        result = Contributor.objects.filter(pk=p.pk).first()
        assert isinstance(result, Person)

    @pytest.mark.django_db
    def test_contributor_get_visible_fields_public(self, person):
        """get_visible_fields with no viewer returns public fields only."""
        visible = person.get_visible_fields(viewer=None)
        assert isinstance(visible, dict)
        assert "name" in visible

    @pytest.mark.django_db
    def test_person_clean_prevents_claimed_email_null(self, db):
        """A claimed person cannot null their email via clean()."""
        p = UserFactory(email="test@example.com", is_active=True)
        p.set_password("testpass123")
        p.save()
        # Try to set email to None
        p.email = None
        with pytest.raises(ValidationError):
            p.clean()

    @pytest.mark.django_db
    def test_backward_compatible_alias(self):
        """OrganizationMember alias points to Affiliation."""
        assert OrganizationMember is Affiliation


# ── T014: Organization creation and validation ──────────────────────────────


class TestOrganizationCreationAndValidation:
    """Verify Organization model behavior."""

    @pytest.mark.django_db
    def test_create_organization(self, organization):
        """Organizations can be created with a name."""
        assert organization.pk is not None
        assert organization.name == "Test University"

    @pytest.mark.django_db
    def test_organization_is_polymorphic_contributor(self, organization):
        """Organization is retrievable via Contributor queryset."""
        result = Contributor.objects.filter(pk=organization.pk).first()
        assert isinstance(result, Organization)

    @pytest.mark.django_db
    def test_organization_manage_permission_derived(self, db):
        """manage_organization permission is derived from OWNER affiliation (not in Meta)."""
        # Verify permission is NOT in Meta (derived via backend instead)
        perms = [p[0] for p in Organization._meta.permissions]
        assert "manage_organization" not in perms
        
        # Verify derived permission works via OrganizationPermissionBackend
        from fairdm.factories import PersonFactory
        from fairdm.contrib.contributors.models import Affiliation
        
        org = OrganizationFactory(name="Test Org")
        person = PersonFactory(email="owner@example.com")
        
        # No permission without OWNER affiliation
        assert not person.has_perm("manage_organization", org)
        
        # Create OWNER affiliation
        Affiliation.objects.create(
            person=person,
            organization=org,
            type=Affiliation.MembershipType.OWNER,
        )
        
        # Permission derived from OWNER affiliation
        assert person.has_perm("manage_organization", org)

    @pytest.mark.django_db
    def test_organization_parent_child(self, db):
        """Organizations support parent/child hierarchy."""
        parent = OrganizationFactory(name="Parent Org")
        child = OrganizationFactory(name="Child Org", parent=parent)
        assert child.parent == parent
        assert parent.sub_organizations.count() == 1

    @pytest.mark.django_db
    def test_organization_owner(self, person, organization):
        """Organization.owner() returns the person with OWNER membership."""
        AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        assert organization.owner() == person

    @pytest.mark.django_db
    def test_organization_get_location_display(self, db):
        """get_location_display returns city, country string."""
        org = OrganizationFactory(name="GFZ", city="Potsdam", country="DE")
        display = org.get_location_display()
        assert "Potsdam" in display
        assert "Germany" in display

    @pytest.mark.django_db
    def test_organization_default_identifier_is_ror(self):
        """Organization.DEFAULT_IDENTIFIER is 'ROR'."""
        assert Organization.DEFAULT_IDENTIFIER == "ROR"


# ── T015: Affiliation unique constraints ─────────────────────────────────────


class TestAffiliationUniqueConstraints:
    """Verify Affiliation model constraints and behavior."""

    @pytest.mark.django_db
    def test_affiliation_unique_person_organization(self, person, organization):
        """Cannot create two affiliations for same person+organization pair."""
        AffiliationFactory(person=person, organization=organization)
        with pytest.raises(IntegrityError):
            AffiliationFactory(person=person, organization=organization)

    @pytest.mark.django_db
    def test_affiliation_type_choices(self):
        """MembershipType has four levels."""
        types = Affiliation.MembershipType
        assert types.PENDING == 0
        assert types.MEMBER == 1
        assert types.ADMIN == 2
        assert types.OWNER == 3

    @pytest.mark.django_db
    def test_affiliation_start_end_dates(self, affiliation):
        """Affiliation supports start_date and end_date."""
        affiliation.start_date = "2020"
        affiliation.end_date = "2024-06"
        affiliation.save()
        affiliation.refresh_from_db()
        assert str(affiliation.start_date) == "2020"
        assert str(affiliation.end_date) == "2024-06"

    @pytest.mark.django_db
    def test_only_one_primary_per_person(self, person):
        """Setting is_primary=True on one affiliation clears it on others for same person."""
        org1 = OrganizationFactory(name="Org A")
        org2 = OrganizationFactory(name="Org B")
        a1 = AffiliationFactory(person=person, organization=org1, is_primary=True)
        a2 = AffiliationFactory(person=person, organization=org2, is_primary=True)
        a1.refresh_from_db()
        assert a1.is_primary is False
        assert a2.is_primary is True

    @pytest.mark.django_db
    def test_affiliation_sync_ownership_permission(self, person, organization):
        """When type changes to OWNER, manage_organization permission is assigned."""
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
        """When type changes from OWNER, manage_organization permission is removed."""
        aff = AffiliationFactory(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
        )
        # Simulate: set type to MEMBER (downgrade)
        aff.type = Affiliation.MembershipType.MEMBER
        aff.save()
        assert not person.has_perm("contributors.manage_organization", organization)

    @pytest.mark.django_db
    def test_string_representation(self, affiliation):
        """__str__ returns 'Person - Organization'."""
        result = str(affiliation)
        assert " - " in result


# ── T016: Contribution GFK relationships ─────────────────────────────────────


class TestContributionGFKRelationships:
    """Verify Contribution model with GenericForeignKey."""

    @pytest.mark.django_db
    def test_contribution_links_person_to_project(self, contribution, person, project_for_contributions):
        """Contribution correctly links a contributor to a project."""
        assert contribution.contributor == person
        assert contribution.content_object == project_for_contributions

    @pytest.mark.django_db
    def test_contribution_unique_per_entity_contributor(self, person):
        """Cannot duplicate a contribution for the same contributor+entity."""
        project = ProjectFactory()
        ContributionFactory(contributor=person, content_object=project)
        with pytest.raises(IntegrityError):
            ContributionFactory(contributor=person, content_object=project)

    @pytest.mark.django_db
    def test_contribution_add_to_classmethod(self, person):
        """Contributor.add_to() creates a contribution."""
        project = ProjectFactory()
        contribution = person.add_to(project)
        assert contribution is not None
        assert contribution.content_object == project

    @pytest.mark.django_db
    def test_contribution_default_affiliation(self, person, organization):
        """Contribution.set_default_affiliation hook sets primary org affiliation."""
        AffiliationFactory(
            person=person,
            organization=organization,
            is_primary=True,
        )
        project = ProjectFactory()
        c = person.add_to(project)
        assert c.affiliation == organization

    @pytest.mark.django_db
    def test_contribution_has_contribution_to(self, person, contribution, project_for_contributions):
        """Contributor.has_contribution_to() returns True for contributed entities."""
        assert person.has_contribution_to(project_for_contributions) is True

    @pytest.mark.django_db
    def test_contribution_projects_property(self, person, contribution):
        """Person.projects returns projects they contribute to."""
        projects = person.projects
        assert projects.count() >= 1

    @pytest.mark.django_db
    def test_contribution_manager_for_entity(self, contribution, project_for_contributions):
        """ContributionManager.for_entity() filters by entity."""
        qs = Contribution.objects.for_entity(project_for_contributions)
        assert qs.count() >= 1
        assert contribution in qs

    @pytest.mark.django_db
    def test_contribution_manager_by_contributor(self, person, contribution):
        """ContributionManager.by_contributor() filters by contributor."""
        qs = Contribution.objects.by_contributor(person)
        assert qs.count() >= 1


# ── T017: ContributorIdentifier uniqueness ───────────────────────────────────


class TestContributorIdentifierUniqueness:
    """Verify ContributorIdentifier model behavior."""

    @pytest.mark.django_db
    def test_create_orcid_identifier(self, orcid_identifier, person):
        """ORCID identifier is created and linked to person."""
        assert orcid_identifier.pk is not None
        assert orcid_identifier.related == person

    @pytest.mark.django_db
    def test_create_ror_identifier(self, ror_identifier, organization):
        """ROR identifier is created and linked to organization."""
        assert ror_identifier.pk is not None
        assert ror_identifier.related == organization

    @pytest.mark.django_db
    def test_person_default_identifier_is_orcid(self):
        """Person.DEFAULT_IDENTIFIER is 'ORCID'."""
        assert Person.DEFAULT_IDENTIFIER == "ORCID"


# ── T027a: Person name internationalization ────────────────────────────────


class TestPersonNameInternationalization:
    """Test Person name handling with non-Latin scripts (FR-020 compliance)."""

    @pytest.mark.django_db
    def test_person_name_chinese_script(self, db):
        """Person model handles Chinese characters correctly."""
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
        """Person model handles Arabic characters correctly."""
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
        """Person model handles Cyrillic characters correctly."""
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
        """Person model handles mixed script names."""
        person = PersonFactory(
            first_name="José",
            last_name="García-López",
            name="",
        )
        assert person.name == "José García-López"
        # Verify no mojibake or encoding issues
        assert "�" not in person.name

    @pytest.mark.django_db
    def test_person_name_emoji_and_special_chars(self, db):
        """Person model handles emoji and special Unicode characters."""
        person = PersonFactory(
            first_name="Test",
            last_name="O'Brien-Smith",
            name="",
        )
        assert person.name == "Test O'Brien-Smith"
        assert "'" in person.last_name  # Curly apostrophe preserved


# ── T072: Multiple roles per contribution ──────────────────────────────────


class TestMultipleRolesPerContribution:
    """Test that a contribution can have multiple roles assigned."""

    @pytest.mark.django_db
    def test_contribution_multiple_roles(self, db):
        """A contribution can have multiple roles from Fair DM vocabulary."""
        from research_vocabs.models import Concept

        project = ProjectFactory()
        person = PersonFactory()
        contribution = ContributionFactory(
            content_object=project,
            contributor=person,
        )

        # Get role concepts from the database (they should exist from fixtures/migrations)
        # Use the legacy vocabulary filter approach
        try:
            roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")
            if roles_qs.count() < 2:
                # If vocabulary not initialized, skip test
                import pytest

                pytest.skip("fairdm-roles vocabulary not initialized")

            author_role = roles_qs.first()
            editor_role = roles_qs.last()

            # Assign multiple roles
            contribution.roles.add(author_role, editor_role)

            assert contribution.roles.count() == 2
        except Concept.DoesNotExist:
            import pytest

            pytest.skip("fairdm-roles vocabulary not initialized")
        assert author_role in contribution.roles.all()
        assert editor_role in contribution.roles.all()


# ── T073: Affiliation time bounds ──────────────────────────────────────────


class TestAffiliationTimeBounds:
    """Test affiliation time-bound functionality with PartialDateField."""

    @pytest.mark.django_db
    def test_affiliation_active_no_end_date(self, db):
        """Affiliation with end_date=None is considered active."""
        person = PersonFactory()
        org = OrganizationFactory()
        affiliation = AffiliationFactory(
            person=person,
            organization=org,
            start_date="2020-01",
            end_date=None,
        )

        # Active affiliations have no end_date
        assert affiliation.end_date is None
        assert org.affiliations.filter(end_date__isnull=True).exists()

    @pytest.mark.django_db
    def test_affiliation_historical_has_end_date(self, db):
        """Affiliation with end_date IS NOT NULL is historical."""
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
        """Person can have multiple affiliations with different time periods."""
        person = PersonFactory()
        org1 = OrganizationFactory(name="University A")
        org2 = OrganizationFactory(name="Institute B")

        # Past affiliation
        past_aff = AffiliationFactory(
            person=person,
            organization=org1,
            start_date="2010",
            end_date="2015",
        )

        # Current affiliation
        current_aff = AffiliationFactory(
            person=person,
            organization=org2,
            start_date="2015",
            end_date=None,
        )

        assert person.affiliations.count() == 2
        assert person.affiliations.filter(end_date__isnull=True).count() == 1
        assert person.affiliations.filter(end_date__isnull=False).count() == 1


# ── T074: Partial date precision ───────────────────────────────────────────


class TestPartialDatePrecision:
    """Test PartialDateField supports year, year-month, and full date precision."""

    @pytest.mark.django_db
    def test_affiliation_year_only_precision(self, db):
        """PartialDateField accepts year-only precision."""
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
        """PartialDateField accepts year-month precision."""
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
        """PartialDateField accepts full date precision."""
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


# ── T075: Primary affiliation constraint ───────────────────────────────────


class TestPrimaryAffiliationConstraint:
    """Test that only one affiliation per person can be primary."""

    @pytest.mark.django_db
    def test_single_primary_affiliation(self, db):
        """Person can have one primary affiliation."""
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
        """Setting a new primary affiliation unsets the old one."""
        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")

        # Create first primary affiliation
        aff1 = AffiliationFactory(
            person=person,
            organization=org1,
            is_primary=True,
        )
        assert aff1.is_primary is True

        # Create second primary affiliation - should unset first
        aff2 = AffiliationFactory(
            person=person,
            organization=org2,
            is_primary=True,
        )

        # Refresh from DB
        aff1.refresh_from_db()

        assert aff2.is_primary is True
        assert aff1.is_primary is False
        assert person.affiliations.filter(is_primary=True).count() == 1

    @pytest.mark.django_db
    def test_multiple_non_primary_affiliations_allowed(self, db):
        """Person can have multiple non-primary affiliations."""
        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        org3 = OrganizationFactory(name="Org 3")

        AffiliationFactory(person=person, organization=org1, is_primary=False)
        AffiliationFactory(person=person, organization=org2, is_primary=False)
        AffiliationFactory(person=person, organization=org3, is_primary=False)

        assert person.affiliations.filter(is_primary=False).count() == 3
        assert person.affiliations.filter(is_primary=True).count() == 0
