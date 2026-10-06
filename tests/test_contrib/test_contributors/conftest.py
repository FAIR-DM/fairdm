"""Fixtures for contributor system tests."""

from io import BytesIO
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from guardian.utils import get_anonymous_user
from PIL import Image

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.models import (
    Affiliation,
    ContributorIdentifier,
    Person,
)
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility


@pytest.fixture
def contribution_roles(db):
    from research_vocabs.models import Concept

    return Concept.objects.filter(vocabulary__name="fairdm-roles")


@pytest.fixture
def off_vocabulary_role(db):
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


@pytest.fixture
def person(db):
    p = PersonFactory(email="claimed@example.com", is_active=True, is_claimed=True)
    p.set_password("testpass123")
    p.save()
    return p


@pytest.fixture
def unclaimed_person(db):
    return Person.objects.create_unclaimed(
        first_name="Jane",
        last_name="Doe",
    )


@pytest.fixture
def community_manager(db):
    """A person with an active account who holds the Community Manager role."""
    manager = PersonFactory(is_active=True, is_claimed=True, password="x")
    manager.groups.add(Group.objects.get(name=PortalRoles.COMMUNITY_MANAGER.name))
    return manager


@pytest.fixture
def superuser(db):
    return UserFactory(
        email="admin@example.com",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


@pytest.fixture
def admin_client(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def organization(db):
    return OrganizationFactory(name="Test University")


@pytest.fixture
def organization_with_members(db, organization, person, unclaimed_person):
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


@pytest.fixture
def affiliation(db, person, organization):
    return AffiliationFactory(
        person=person,
        organization=organization,
        type=Affiliation.MembershipType.MEMBER,
    )


@pytest.fixture
def owner_affiliation(db, person, organization):
    return AffiliationFactory(
        person=person,
        organization=organization,
        type=Affiliation.MembershipType.OWNER,
        is_primary=True,
    )


@pytest.fixture
def project_for_contributions(db):
    return ProjectFactory()


@pytest.fixture
def contribution(db, person, project_for_contributions):
    return ContributionFactory(
        contributor=person,
        content_object=project_for_contributions,
    )


@pytest.fixture
def orcid_identifier(db, person):
    return ContributorIdentifier.objects.create(
        related=person,
        type="ORCID",
        value="0000-0001-2345-6789",
    )


@pytest.fixture
def ror_identifier(db, organization):
    return ContributorIdentifier.objects.create(
        related=organization,
        type="ROR",
        value="https://ror.org/02nr0ka47",
    )


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


@pytest.fixture
def contributor_population(db):
    from research_vocabs.models import Concept

    superuser = UserFactory(
        email="population-superuser@example.com",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    anonymous = get_anonymous_user()

    ghost = Person.objects.create_unclaimed(first_name="Ghost", last_name="Population")

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


@pytest.fixture
def credited_world(db):
    """A person credited on public and private records of every kind.

    Each private record has its own mate, credited there under a role held nowhere else, so a
    test can tell a role or a collaborator that is known only through a private record.
    """
    person = PersonFactory(
        email="credited@example.com",
        is_active=True,
        is_claimed=True,
        password="testpass123",
    )
    public_project = ProjectFactory(visibility=Visibility.PUBLIC)
    private_project = ProjectFactory(visibility=Visibility.PRIVATE)
    public_dataset = DatasetFactory(
        project=public_project, visibility=Visibility.PUBLIC, published=True
    )
    private_dataset = DatasetFactory(
        project=public_project, visibility=Visibility.PRIVATE, published=False
    )
    dataset_in_private_project = DatasetFactory(
        project=private_project, visibility=Visibility.PUBLIC, published=True
    )
    public_sample = RockSampleFactory(dataset=public_dataset)
    private_sample = RockSampleFactory(dataset=private_dataset)
    sample_in_private_project = RockSampleFactory(dataset=dataset_in_private_project)
    public_measurement = ExampleMeasurementFactory(
        dataset=public_dataset, sample=public_sample
    )
    measurement_in_private_project = ExampleMeasurementFactory(
        dataset=dataset_in_private_project, sample=sample_in_private_project
    )

    open_mate = PersonFactory(email="open-mate@example.com")
    sample_mate = PersonFactory(email="sample-mate@example.com")
    private_mate = PersonFactory(email="private-mate@example.com")
    private_dataset_mate = PersonFactory(email="private-dataset-mate@example.com")

    for record, roles in [
        (public_project, ["Creator"]),
        (private_project, ["Supervisor"]),
        (public_dataset, ["DataCollector"]),
        (private_dataset, ["Editor"]),
        (dataset_in_private_project, ["Producer"]),
        (public_sample, ["Researcher"]),
        (sample_in_private_project, ["Sponsor"]),
        (public_measurement, ["Support"]),
        (measurement_in_private_project, ["Other"]),
    ]:
        person.add_to(record, roles=roles)
    for record in (public_project, public_dataset):
        open_mate.add_to(record)
    sample_mate.add_to(public_sample)
    for record in (private_project, dataset_in_private_project, sample_in_private_project):
        private_mate.add_to(record)
    private_dataset_mate.add_to(private_dataset)
    private_dataset_mate.add_to(private_sample)

    return SimpleNamespace(
        person=person,
        public_project=public_project,
        private_project=private_project,
        public_dataset=public_dataset,
        private_dataset=private_dataset,
        dataset_in_private_project=dataset_in_private_project,
        public_sample=public_sample,
        private_sample=private_sample,
        sample_in_private_project=sample_in_private_project,
        public_measurement=public_measurement,
        measurement_in_private_project=measurement_in_private_project,
        open_mate=open_mate,
        sample_mate=sample_mate,
        private_mate=private_mate,
        private_dataset_mate=private_dataset_mate,
    )


@pytest.fixture
def image_upload():
    """Build a small valid image upload."""

    def build(name="photo.png"):
        buffer = BytesIO()
        Image.new("RGB", (20, 20), "blue").save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    return build


@pytest.fixture
def profile_data():
    """Every field of a person's profile form, filled in with valid values."""
    return {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "name": "Dr. Ada Lovelace",
        "alternative_names": "A. Lovelace\nAugusta Ada King",
        "profile": "Mathematician and writer.",
        "links": "https://example.org/ada\nhttp://example.org/notes",
        "lang": ["en", "fr"],
    }


@pytest.fixture
def organization_profile_data():
    """Every field of an organization's profile form, filled in with valid values."""
    return {
        "name": "Potsdam Research Institute",
        "alternative_names": "PRI\nInstitut Potsdam",
        "type": "education",
        "parent": "",
        "city": "Potsdam",
        "country": "DE",
        "profile": "Studies the Earth system.",
        "website": "https://example.org",
        "links": "https://example.net/wiki\nhttps://example.org/news",
    }
