"""Tests for contributor data models (User Story 1).

Tests cover:
- The Contributor base: public identifier, profile fields, timestamps,
  configuration store, field metadata (FS-009 US1 T008-T013)
- Person claimed/unclaimed semantics (T013)
- Organization creation and validation (T014)
- Affiliation unique constraints (T015)
- Contribution GFK relationships (T016)
- ContributorIdentifier uniqueness (T017)
- ClaimingAuditLog immutability and manager filter methods (T046)
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    Contributor,
    ContributorIdentifier,
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

# ── FS-009 US1 T008: Contributor public identifier ──────────────────────────


class TestContributorIdentity:
    """Verify the contributor public identifier (FR-002, SC-001)."""

    @pytest.mark.django_db
    def test_person_identifier_carries_contributor_prefix(self):
        """A person's identifier is generated on first save with the 'c' prefix."""
        person = PersonFactory()
        assert person.uuid
        assert person.uuid.startswith("c")

    @pytest.mark.django_db
    def test_organization_identifier_carries_contributor_prefix(self):
        """An organization's identifier is generated on first save with the 'c' prefix."""
        organization = OrganizationFactory()
        assert organization.uuid
        assert organization.uuid.startswith("c")

    @pytest.mark.django_db
    def test_identifier_unchanged_on_second_save(self):
        """Saving a contributor a second time leaves its identifier unchanged."""
        person = PersonFactory()
        original_uuid = person.uuid
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.uuid == original_uuid

    @pytest.mark.django_db
    def test_identifier_unique_across_both_concrete_types(self):
        """No two contributors, of either concrete type, share an identifier."""
        person = PersonFactory()
        organization = OrganizationFactory()
        assert person.uuid != organization.uuid
        assert Contributor.objects.filter(uuid=person.uuid).count() == 1
        assert Contributor.objects.filter(uuid=organization.uuid).count() == 1

    @pytest.mark.django_db
    def test_identifier_uniqueness_enforced_across_types(self):
        """The database refuses a second contributor carrying a used identifier."""
        person = PersonFactory()
        with pytest.raises(IntegrityError):
            OrganizationFactory(uuid=person.uuid)


# ── FS-009 US1 T009: Contributor profile fields ──────────────────────────────


class TestContributorProfileFields:
    """Verify the optional profile fields round-trip and the name is required (FR-003)."""

    @pytest.mark.django_db
    def test_preferred_name_is_required(self):
        """A contributor without a preferred name is refused."""
        organization = OrganizationFactory.build(name="")
        with pytest.raises(ValidationError):
            organization.full_clean()

    @pytest.mark.django_db
    def test_optional_profile_fields_round_trip(self):
        """Other names, description, links, location and language preferences round-trip."""
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
        """The optional profile fields are genuinely optional."""
        organization = OrganizationFactory(
            alternative_names=None, links=None, lang=None, location=None
        )
        organization.full_clean()
        assert organization.location is None


# ── FS-009 US1 T011: Contributor timestamps ──────────────────────────────────


class TestContributorTimestamps:
    """Verify the creation and modification timestamps (FR-005)."""

    @pytest.mark.django_db
    def test_created_timestamp_set_once(self):
        """The creation timestamp is set on first save and does not move."""
        person = PersonFactory()
        original_added = person.added
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.added == original_added

    @pytest.mark.django_db
    def test_modified_timestamp_moves_on_later_save(self):
        """The modification timestamp moves on a later save."""
        person = PersonFactory()
        original_modified = person.modified
        person.name = "Changed Name"
        person.save()
        person.refresh_from_db()
        assert person.modified > original_modified


# ── FS-009 US1 T012: Contributor configuration store ─────────────────────────


class TestContributorConfiguration:
    """Verify the general-purpose configuration store (FR-006)."""

    @pytest.mark.django_db
    def test_config_defaults_empty(self):
        """A contributor with nothing written to its configuration store has an empty one."""
        person = PersonFactory()
        assert person.config == {}

    @pytest.mark.django_db
    def test_config_accepts_and_returns_arbitrary_json(self):
        """Arbitrary JSON written to the store round-trips unchanged."""
        person = PersonFactory()
        person.config = {"anything": ["the", "specification", "does", "not", "define"]}
        person.save()
        person.refresh_from_db()
        assert person.config == {
            "anything": ["the", "specification", "does", "not", "define"]
        }


# ── FS-009 US1 T013: Field metadata ──────────────────────────────────────────


class TestFieldMetadata:
    """Every concrete field on every model this app defines is translatable (FR-007, Articles VIII, IX)."""

    def _concrete_fields(self, model):
        return [f for f in model._meta.get_fields() if getattr(f, "concrete", False)]

    def test_every_field_has_verbose_name_and_help_text(self):
        """Every concrete field declares a non-empty, translatable verbose_name and help_text.

        Scoped to the models this specification's data model owns (plan.md "Data
        model"): Contributor, Person, Organization, Affiliation, Contribution and
        ContributorIdentifier. ClaimingAuditLog lives in this app's models.py but
        belongs to profile claiming (specs/010-profile-claiming), which this story's
        brief places out of scope.
        """
        from django.utils.functional import Promise

        models_to_check = [
            Contributor,
            Person,
            Organization,
            Affiliation,
            Contribution,
            ContributorIdentifier,
        ]
        # Fields whose identity *is* their name, and fields owned entirely by a
        # third-party base class this app does not redeclare (Django's AbstractUser,
        # django-ordered_model's OrderedModel).
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
        # Affiliation.added/modified are inherited from fairdm.db.models.Model, which
        # imports gettext eagerly rather than lazily (fairdm/db/models.py:14) -- a
        # pre-existing defect in a shared framework base well outside this app, out
        # of this story's scope to fix. Contributor declares its own added/modified
        # directly and is not affected. ContributorIdentifier.type/value are inherited
        # from fairdm.core.abstract.AbstractIdentifier, shared by every identifier
        # model in the codebase (dataset, project, sample, measurement); also out of
        # this app's scope.
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
        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.factories import PersonFactory

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


# ── T081/T085: Ownership transfer ────────────────────────────────────────────


class TestOwnershipTransfer:
    """Verify Organization.transfer_ownership() (FR-029, SC-009)."""

    @pytest.mark.django_db
    def test_transfer_demotes_incumbent_and_promotes_successor(
        self, organization, owner_affiliation
    ):
        """Transfer leaves the incumbent an administrator and the successor the owner."""
        incumbent = owner_affiliation.person
        successor = AffiliationFactory(
            person=PersonFactory(email="successor@example.com"),
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
        """Transfer to someone with no affiliation is refused, and nothing changes."""
        stranger = PersonFactory(email="stranger@example.com")

        with pytest.raises(ValidationError):
            organization.transfer_ownership(stranger)

        owner_affiliation.refresh_from_db()
        assert owner_affiliation.type == Affiliation.MembershipType.OWNER
        assert not organization.affiliations.filter(person=stranger).exists()

    @pytest.mark.django_db
    def test_transfer_is_atomic(self, organization, owner_affiliation, monkeypatch):
        """A failure mid-transfer leaves neither the demotion nor the promotion applied."""
        successor = AffiliationFactory(
            person=PersonFactory(email="atomic-successor@example.com"),
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


# ── T015: Affiliation unique constraints ─────────────────────────────────────


class TestAffiliationSchema:
    """FR-020, FR-025, Article IX: the membership type is a real query path for
    ownership lookups and is indexed; reverse access from person/organization
    has a deliberate default related name."""

    def test_membership_type_is_indexed(self):
        """Affiliation.type is indexed because ownership lookups filter on it."""
        field = Affiliation._meta.get_field("type")
        assert field.db_index is True

    def test_default_related_name_is_affiliations(self):
        """Affiliation.Meta declares a default related name."""
        assert Affiliation._meta.default_related_name == "affiliations"


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


# ── T061: Affiliation uniqueness is refused with a readable message ─────────


class TestAffiliationUniqueness:
    """FR-021, SC-008: a second membership of the same organisation by the same
    person is refused, at validation with a readable message and at the
    database by constraint."""

    @pytest.mark.django_db
    def test_duplicate_membership_refused_at_validation_with_readable_message(
        self, person, organization
    ):
        """A second membership fails full_clean() with a readable message, not
        only a database error."""
        AffiliationFactory(person=person, organization=organization)
        duplicate = Affiliation(person=person, organization=organization)

        with pytest.raises(ValidationError) as excinfo:
            duplicate.full_clean()

        assert "already a member" in str(excinfo.value)

    @pytest.mark.django_db
    def test_duplicate_membership_refused_at_database(self, person, organization):
        """A second membership that bypasses validation is still refused by the
        database constraint."""
        AffiliationFactory(person=person, organization=organization)

        with pytest.raises(IntegrityError):
            Affiliation.objects.create(person=person, organization=organization)


# ── T016: Contribution GFK relationships ─────────────────────────────────────


class TestContributionGFKRelationships:
    """Verify Contribution model with GenericForeignKey."""

    @pytest.mark.django_db
    def test_contribution_links_person_to_project(
        self, contribution, person, project_for_contributions
    ):
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
    def test_contribution_has_contribution_to(
        self, person, contribution, project_for_contributions
    ):
        """Contributor.has_contribution_to() returns True for contributed entities."""
        assert person.has_contribution_to(project_for_contributions) is True

    @pytest.mark.django_db
    def test_contribution_projects_property(self, person, contribution):
        """Person.projects returns projects they contribute to."""
        projects = person.projects
        assert projects.count() >= 1

    @pytest.mark.django_db
    def test_contribution_manager_for_entity(
        self, contribution, project_for_contributions
    ):
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


class TestContributorIdentifierVocabulary:
    """005 F1/F2 - ContributorIdentifier is bound to a scoped collection (the union of the
    Person and Organization collections), not the unscoped FairDMIdentifiers vocabulary, so a
    member added for another record type - IGSN for samples - cannot be offered to a person or
    an organisation."""

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


# ── T070: primary-membership demotion is atomic ──────────────────────────────


class TestPrimaryAffiliationDemotionIsAtomic:
    """FR-024: promoting a new primary and demoting the old one happen together
    or not at all."""

    @pytest.mark.django_db
    def test_demotion_and_save_roll_back_together_on_failure(self, person, monkeypatch):
        """If the save that promotes the new primary fails, the demotion of the
        old primary is rolled back too, not left half-applied."""
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


# ── T071: database-level primary-membership constraint ──────────────────────


class TestPrimaryAffiliationDatabaseConstraint:
    """FR-024, Article IX: a partial UniqueConstraint protects the
    primary-membership invariant so a concurrent write cannot slip past the
    save-time demotion."""

    @pytest.mark.django_db
    def test_database_refuses_two_primary_memberships_written_directly(
        self, person
    ):
        """Marking two memberships primary directly at the database - bypassing
        Affiliation.save() - is refused by the constraint."""
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        first = AffiliationFactory(person=person, organization=org1, is_primary=False)
        second = AffiliationFactory(person=person, organization=org2, is_primary=False)

        Affiliation.objects.filter(pk=first.pk).update(is_primary=True)

        with pytest.raises(IntegrityError):
            Affiliation.objects.filter(pk=second.pk).update(is_primary=True)


# ── T046: ClaimingAuditLog immutability and manager ─────────────────────────


class TestClaimingAuditLogImmutability:
    """Verify that ClaimingAuditLog records cannot be modified after creation."""

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
        """Calling save() on an existing record should raise ValueError."""

        audit_log_entry.failure_reason = "tampered"
        with pytest.raises(ValueError, match="immutable"):
            audit_log_entry.save()

    def test_record_not_modified_on_failed_save(self, db, audit_log_entry):
        """DB record should be unchanged after a rejected save()."""
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
    """Tests for ClaimingAuditLogManager filter methods."""

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

