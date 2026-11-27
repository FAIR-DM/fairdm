"""Tests for contributor-related factories (Person, Organization, Contribution)."""

import pytest

from fairdm.contrib.contributors.models import (
    ContributorIdentifier,
    Person,
)
from fairdm.factories import (
    AffiliationFactory,
    OrganizationFactory,
    PersonFactory,
)
from fairdm.factories.contributors import (
    ContributionFactory,
    ContributorFactory,
    ContributorIdentifierFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestContributorFactoryCreation:

    def test_person_factory_unique_emails(self):
        person1 = PersonFactory()
        person2 = PersonFactory()

        assert person1.email != person2.email

    def test_person_factory_get_or_create_by_email(self):
        email = "test@example.com"
        person1 = PersonFactory(email=email)
        person2 = PersonFactory(email=email)

        assert person1.pk == person2.pk
        assert Person.objects.filter(email=email).count() == 1

    def test_person_factory_defaults_to_unusable_password_and_unclaimed(self):
        # A contributor added for attribution alone is the common case (#227).
        person = PersonFactory()

        assert person.has_usable_password() is False
        assert person.is_claimed is False
        assert person.is_active is True

    def test_person_factory_accepts_an_explicit_password(self):
        person = PersonFactory(password="s3cret-pass")

        assert person.has_usable_password() is True
        assert person.check_password("s3cret-pass") is True


    def test_person_factory_no_auto_image(self):
        # A default factory sets no image. Generating one on every call left files under MEDIA_ROOT (#323).
        person = PersonFactory()

        assert not person.image

    def test_organization_factory_no_auto_image(self):
        org = OrganizationFactory()

        assert not org.image

    def test_person_factory_with_image_generates_one(self):
        person = PersonFactory(with_image=True)

        assert person.image


@pytest.mark.django_db
class TestContributorIdentifierFactory:
    def test_default_type_is_a_contributor_identifier_vocabulary_member(self):
        person = PersonFactory()

        identifier = ContributorIdentifierFactory(related=person)

        assert identifier.type_id in [
            concept.uri for concept in ContributorIdentifier.get_type_concepts()
        ]

    def test_identifier_values_are_unique_across_instances(self):
        first = ContributorIdentifierFactory(related=PersonFactory())
        second = ContributorIdentifierFactory(related=PersonFactory())

        assert first.value != second.value


@pytest.mark.django_db
class TestContributorFactoriesPassFullClean:
    def test_user_factory_instance_passes_full_clean(self):
        UserFactory().full_clean()

    def test_contributor_factory_instance_passes_full_clean(self):
        ContributorFactory().full_clean()

    def test_person_factory_instance_passes_full_clean(self):
        PersonFactory().full_clean()

    def test_organization_factory_instance_passes_full_clean(self):
        OrganizationFactory().full_clean()

    def test_affiliation_factory_instance_passes_full_clean(self):
        AffiliationFactory().full_clean()

    def test_contribution_factory_instance_passes_full_clean(self):
        ContributionFactory().full_clean()


@pytest.mark.django_db
class TestContributorFactoryBatchUniqueness:
    def test_user_factory_batch_has_unique_emails_and_rows(self):
        users = UserFactory.create_batch(5)

        assert len({u.pk for u in users}) == 5
        assert len({u.email for u in users}) == 5

    def test_person_factory_batch_has_unique_emails_and_rows(self):
        people = PersonFactory.create_batch(5)

        assert len({p.pk for p in people}) == 5
        assert len({p.email for p in people}) == 5

    def test_two_people_with_the_same_name_are_different_people(self):
        first = PersonFactory(first_name="Robert", last_name="Brown")
        second = PersonFactory(first_name="Robert", last_name="Brown")

        assert first.pk != second.pk
        assert first.email != second.email

    def test_one_organization_takes_two_same_named_members(self):
        organization = OrganizationFactory()
        for _ in range(2):
            AffiliationFactory(
                organization=organization,
                person=PersonFactory(first_name="Robert", last_name="Brown"),
            )

        assert organization.affiliations.count() == 2
