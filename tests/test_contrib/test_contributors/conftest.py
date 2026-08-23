"""Fixtures for contributor system tests.

Provides factories and commonly-used instances for testing:
- Person (claimed and unclaimed)
- Organization
- Affiliation
- Contribution
- ContributorIdentifier
"""

from types import SimpleNamespace

import pytest
from guardian.utils import get_anonymous_user

from fairdm.contrib.contributors.models import (
    Affiliation,
    ContributorIdentifier,
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

# ── Roles Vocabulary Fixture ─────────────────────────────────────────────────


@pytest.fixture
def contribution_roles(db):
    """The framework's controlled roles vocabulary (``fairdm-roles``,
    ``fairdm.core.vocabularies.FairDMRoles``), as a plain queryset of its
    concepts, so credit tests have real concepts to attach without repeating
    the vocabulary name.

    The concepts themselves are already seeded once per session by
    ``Concept.preload()`` (``tests/conftest.py``); this fixture only names
    that queryset for tests in this module.
    """
    from research_vocabs.models import Concept

    return Concept.objects.filter(vocabulary__name="fairdm-roles")


@pytest.fixture
def off_vocabulary_role(db):
    """A concept from a vocabulary that is not ``fairdm-roles`` (FR-032) - the shape a
    credit's roles must always refuse, whichever write path attaches it."""
    from research_vocabs.models import Concept, Vocabulary

    vocabulary = Vocabulary.objects.create(
        name="not-fairdm-roles",
        label="Not FairDM Roles",
        uri="https://example.com/vocabularies/not-fairdm-roles",
    )
    return Concept.objects.create(
        vocabulary=vocabulary,
        uri="https://example.com/vocabularies/not-fairdm-roles#outsider",
        name="Outsider",
        label="Outsider",
    )


# ── Person Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def person(db):
    """A claimed person (has email, is_active=True, is_claimed=True)."""
    p = PersonFactory(email="claimed@example.com", is_active=True, is_claimed=True)
    p.set_password("testpass123")
    p.save()
    return p


@pytest.fixture
def unclaimed_person(db):
    """An unclaimed person (no email, is_active=True, is_claimed=False)."""
    return Person.objects.create_unclaimed(
        first_name="Jane",
        last_name="Doe",
    )


@pytest.fixture
def superuser(db):
    """A superuser for admin tests."""
    return UserFactory(
        email="admin@example.com",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


@pytest.fixture
def admin_client(client, superuser):
    """An authenticated client with superuser privileges."""
    client.force_login(superuser)
    return client


# ── Organization Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def organization(db):
    """A basic organization."""
    return OrganizationFactory(name="Test University")


@pytest.fixture
def organization_with_members(db, organization, person, unclaimed_person):
    """An organization with two members: one claimed, one unclaimed."""
    AffiliationFactory(
        person=person,
        organization=organization,
        type=Affiliation.MembershipType.MEMBER,
        is_primary=True,
    )
    AffiliationFactory(
        person=unclaimed_person,
        organization=organization,
        type=Affiliation.MembershipType.PENDING,
    )
    return organization


# ── Affiliation Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def affiliation(db, person, organization):
    """A standard member affiliation."""
    return AffiliationFactory(
        person=person,
        organization=organization,
        type=Affiliation.MembershipType.MEMBER,
    )


@pytest.fixture
def owner_affiliation(db, person, organization):
    """An owner-level affiliation."""
    return AffiliationFactory(
        person=person,
        organization=organization,
        type=Affiliation.MembershipType.OWNER,
        is_primary=True,
    )


# ── Contribution Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def project_for_contributions(db):
    """A project to use for contribution tests."""
    return ProjectFactory()


@pytest.fixture
def contribution(db, person, project_for_contributions):
    """A contribution linking a person to a project."""
    return ContributionFactory(
        contributor=person,
        content_object=project_for_contributions,
    )


# ── Identifier Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def orcid_identifier(db, person):
    """A person with an ORCID identifier."""
    return ContributorIdentifier.objects.create(
        related=person,
        type="ORCID",
        value="0000-0001-2345-6789",
    )


@pytest.fixture
def ror_identifier(db, organization):
    """An organization with a ROR identifier."""
    return ContributorIdentifier.objects.create(
        related=organization,
        type="ROR",
        value="https://ror.org/02nr0ka47",
    )


# ── Claiming Audit Log Fixtures ──────────────────────────────────────────────


@pytest.fixture
def person_a(db):
    from fairdm.factories import PersonFactory

    return PersonFactory()


@pytest.fixture
def person_b(db):
    from fairdm.factories import PersonFactory

    return PersonFactory()


@pytest.fixture
def audit_log_entry(db, person_a, person_b):
    from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod

    return ClaimingAuditLog.objects.create(
        method=ClaimMethod.TOKEN,
        source_person=person_a,
        target_person=person_b,
        success=True,
    )


# ── Contributor Population Fixture (US9) ─────────────────────────────────────


@pytest.fixture
def contributor_population(db):
    """One population covering every case FR-041 and FR-042 distinguish.

    A superuser and the django-guardian anonymous placeholder alongside a
    real person in each of the four account states (ghost, invited, claimed,
    inactive), an organisation with one current and one ended membership,
    and credits under two different roles (SC-014).
    """
    from research_vocabs.models import Concept

    superuser = UserFactory(
        email="population-superuser@example.com",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    anonymous = get_anonymous_user()

    ghost = Person.objects.create_unclaimed(
        first_name="Ghost", last_name="Population"
    )

    invited = PersonFactory(
        email="population-invited@example.com",
        is_active=True,
        is_claimed=False,
    )

    claimed = PersonFactory(
        email="population-claimed@example.com",
        is_active=True,
        is_claimed=True,
    )
    claimed.set_password("testpass123")
    claimed.save()

    inactive = PersonFactory(
        email="population-inactive@example.com",
        is_active=False,
        is_claimed=True,
    )

    organization = OrganizationFactory(name="Population Organization")
    current_membership = AffiliationFactory(
        person=claimed,
        organization=organization,
        end_date=None,
    )
    ended_membership = AffiliationFactory(
        person=invited,
        organization=organization,
        end_date="2020",
    )

    # Two of the FairDMRoles vocabulary's own concepts, so no new Concept row
    # has to invent a URI (Concept.uri is unique with no default).
    creator_role = Concept.objects.get(vocabulary__name="fairdm-roles", name="Creator")
    contributor_role = Concept.objects.get(
        vocabulary__name="fairdm-roles", name="Contributor"
    )

    project = ProjectFactory()
    creator_credit = ContributionFactory(contributor=claimed, content_object=project)
    creator_credit.roles.add(creator_role)
    contributor_credit = ContributionFactory(
        contributor=invited, content_object=project
    )
    contributor_credit.roles.add(contributor_role)

    return SimpleNamespace(
        superuser=superuser,
        anonymous=anonymous,
        ghost=ghost,
        invited=invited,
        claimed=claimed,
        inactive=inactive,
        organization=organization,
        current_membership=current_membership,
        ended_membership=ended_membership,
        creator_role=creator_role,
        contributor_role=contributor_role,
        creator_credit=creator_credit,
        contributor_credit=contributor_credit,
    )
