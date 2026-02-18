"""Fixtures for contributor system tests.

Provides factories and commonly-used instances for testing:
- Person (claimed and unclaimed)
- Organization
- Affiliation
- Contribution
- ContributorIdentifier
"""

import pytest

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

# ── Person Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def person(db):
    """A claimed person (has email, is_active=True)."""
    return PersonFactory(email="claimed@example.com", is_active=True)


@pytest.fixture
def unclaimed_person(db):
    """An unclaimed person (no email, is_active=False)."""
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
