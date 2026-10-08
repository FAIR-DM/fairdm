"""Tests for contributor-related factories (Person, Organization, Contribution)."""

import pytest

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.factories import (
    AffiliationFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.factories.contributors import (
    ContributionFactory,
    ContributorFactory,
    ContributorIdentifierFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestContributorFactories:
    def test_person_factory_creates_valid_person(self):
        person = PersonFactory()

        assert isinstance(person, Person)
        assert person.pk is not None
        assert person.name is not None

    def test_organization_factory_creates_valid_organization(self):
        organization = OrganizationFactory()

        assert isinstance(organization, Organization)
        assert organization.pk is not None
        assert organization.name is not None

    def test_contribution_factory_creates_valid_contribution(self):
        contribution = ContributionFactory()

        assert isinstance(contribution, Contribution)
        assert contribution.pk is not None
        assert contribution.contributor is not None


@pytest.mark.django_db
class TestContributorFactoryCreation:
    def test_person_factory_creates_person(self):
        person = PersonFactory()

        assert isinstance(person, Person)
        assert person.pk is not None
        assert person.name
        assert person.first_name
        assert person.last_name
        assert person.email
        assert "@" in person.email
        assert person.profile

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

    def test_organization_factory_creates_organization(self):
        org = OrganizationFactory()

        assert isinstance(org, Organization)
        assert org.pk is not None
        assert org.name
        assert org.profile

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
class TestAffiliationFactory:
    def test_default_type_is_member(self):
        affiliation = AffiliationFactory()

        assert affiliation.type == Affiliation.MembershipType.MEMBER

    def test_default_period_is_current(self):
        affiliation = AffiliationFactory()

        assert affiliation.start_date is not None
        assert affiliation.end_date is None
        assert affiliation in Affiliation.objects.current()


@pytest.mark.django_db
class TestContributionFactory:
    def test_contribution_factory_with_project(self):
        person = PersonFactory()
        project = ProjectFactory()

        contribution = ContributionFactory(content_object=project, contributor=person)

        assert isinstance(contribution, Contribution)
        assert contribution.pk is not None
        assert contribution.contributor == person
        assert contribution.content_object == project

    def test_contribution_factory_with_dataset(self):
        org = OrganizationFactory()
        dataset = DatasetFactory()

        contribution = ContributionFactory(content_object=dataset, contributor=org)

        assert isinstance(contribution, Contribution)
        assert contribution.pk is not None
        assert contribution.contributor == org
        assert contribution.content_object == dataset


@pytest.mark.django_db
class TestContributorIdentifierFactory:
    def test_default_type_is_a_contributor_identifier_vocabulary_member(self):
        person = PersonFactory()

        identifier = ContributorIdentifierFactory(related=person)

        assert identifier.type in ContributorIdentifier.VOCABULARY.values

    def test_identifier_values_are_unique_across_instances(self):
        first = ContributorIdentifierFactory(related=PersonFactory())
        second = ContributorIdentifierFactory(related=PersonFactory())

        assert first.value != second.value


@pytest.mark.django_db
class TestFactoryIntegration:
    def test_complete_research_workflow(self):
        principal_investigator = PersonFactory(first_name="Dr. Jane", last_name="Smith")
        research_institution = OrganizationFactory(name="University Research Center")

        project = ProjectFactory(name="Climate Change Research Project")

        ContributionFactory(contributor=principal_investigator, content_object=project)
        ContributionFactory(contributor=research_institution, content_object=project)

        dataset = DatasetFactory(
            project=project, name="Temperature Measurements Dataset"
        )

        samples = RockSampleFactory.create_batch(3, dataset=dataset)

        measurements = []
        for sample in samples:
            measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
            measurements.append(measurement)

        assert project.name == "Climate Change Research Project"
        assert dataset.project == project
        assert len(samples) == 3
        assert len(measurements) == 3

        project_contributions = Contribution.objects.filter(
            content_type__model="project", object_id=project.pk
        )
        assert project_contributions.count() == 2

        for sample in samples:
            assert sample.dataset == dataset

        for measurement in measurements:
            assert measurement.sample in samples
            assert measurement.dataset == dataset

    def test_project_with_multiple_datasets_and_samples(self):
        project = ProjectFactory()

        datasets = DatasetFactory.create_batch(2, project=project)

        all_samples = []
        for dataset in datasets:
            samples = RockSampleFactory.create_batch(2, dataset=dataset)
            all_samples.extend(samples)

        all_measurements = []
        for sample in all_samples:
            measurements = ExampleMeasurementFactory.create_batch(
                2, dataset=sample.dataset, sample=sample
            )
            all_measurements.extend(measurements)

        assert len(datasets) == 2
        assert len(all_samples) == 4  # 2 datasets x 2 samples each
        assert len(all_measurements) == 8  # 4 samples x 2 measurements each

        for dataset in datasets:
            assert dataset.project == project

        for sample in all_samples:
            assert sample.dataset in datasets

        for measurement in all_measurements:
            assert measurement.sample in all_samples
            assert measurement.dataset == measurement.sample.dataset

    def test_contributor_project_relationships(self):
        person = PersonFactory()
        organization = OrganizationFactory()
        contributor_as_person = ContributorFactory()

        project = ProjectFactory()

        contributions = [
            ContributionFactory(contributor=person, content_object=project),
            ContributionFactory(contributor=organization, content_object=project),
            ContributionFactory(
                contributor=contributor_as_person, content_object=project
            ),
        ]

        for contribution in contributions:
            assert contribution.content_object == project

        project_contributions = Contribution.objects.filter(
            content_type__model="project", object_id=project.pk
        )
        assert project_contributions.count() == 3

    def test_sample_measurement_contributor_workflow(self):
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        sample_collector = PersonFactory(first_name="Field", last_name="Collector")
        lab_analyst = PersonFactory(first_name="Lab", last_name="Analyst")

        sample_contribution = ContributionFactory(
            contributor=sample_collector, content_object=sample
        )
        measurement_contribution = ContributionFactory(
            contributor=lab_analyst, content_object=measurement
        )

        assert sample_contribution.content_object == sample
        assert measurement_contribution.content_object == measurement

        assert sample_collector != lab_analyst

    def test_factory_build_vs_create(self):
        project_built = ProjectFactory.build()
        person_built = PersonFactory.build()

        project_created = ProjectFactory()
        person_created = PersonFactory()

        assert project_built.pk is None
        assert person_built.pk is None

        assert project_created.pk is not None
        assert person_created.pk is not None

    def test_factory_custom_parameters(self):
        custom_project = ProjectFactory(
            name="Custom Project Name",
            funding=[{"funderName": "Custom Agency"}],
        )

        custom_person = PersonFactory(
            first_name="John", last_name="Doe", email="john.doe@example.org"
        )

        assert custom_project.name == "Custom Project Name"
        assert custom_project.funding[0]["funderName"] == "Custom Agency"
        assert custom_person.first_name == "John"
        assert custom_person.email == "john.doe@example.org"

    def test_related_factory_relationships(self):
        project = ProjectFactory(descriptions=2, dates=1)

        assert project.descriptions.exists()
        assert project.dates.exists()

        assert project.descriptions.count() == 2
        assert project.dates.count() == 1

    def test_factory_batch_creation_performance(self):
        projects = ProjectFactory.create_batch(5, descriptions=2, dates=1)

        for project in projects:
            assert project.descriptions.exists()
            assert project.dates.exists()

        dataset = DatasetFactory()
        samples = RockSampleFactory.create_batch(10, dataset=dataset)

        for sample in samples:
            assert sample.dataset == dataset

    def test_polymorphic_contributor_behavior(self):
        person = PersonFactory()
        organization = OrganizationFactory()

        from fairdm.contrib.contributors.models import Contributor

        assert isinstance(person, Contributor)
        assert isinstance(organization, Contributor)
        assert isinstance(person, Person)
        assert isinstance(organization, Organization)

        assert person.polymorphic_ctype != organization.polymorphic_ctype


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
