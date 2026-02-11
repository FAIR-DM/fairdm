"""
Management command to generate fake data for development purposes.

This command creates a complete hierarchy of fake data including projects, datasets,
samples, and measurements. It uses polymorphic Sample and Measurement subclasses
configured via the FAIRDM_FACTORIES setting.

Configuration:
    Add your custom factory classes to settings.py:

    FAIRDM_FACTORIES = {
        "myapp.CustomSample": "myapp.factories.CustomSampleFactory",
        "myapp.SpecialMeasurement": "myapp.factories.SpecialMeasurementFactory",
    }

    The command will randomly use these factories to create polymorphic instances.
    If no factories are configured, it falls back to base Sample/Measurement factories.

Usage:
    poetry run python manage.py generate_fake_data
    poetry run python manage.py generate_fake_data --projects 5 --datasets 3
    poetry run python manage.py generate_fake_data --clear
"""

import random
from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from research_vocabs.models import Concept

from fairdm.contrib.contributors.models import Contribution, Organization, Person
from fairdm.core.dataset.models import DatasetDate, DatasetDescription
from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
from fairdm.core.models import Dataset, Measurement, Project, Sample
from fairdm.core.project.models import ProjectDate, ProjectDescription
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.factories import (
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)


class Command(BaseCommand):
    """Generate fake data for development."""

    help = "Generate fake data for development purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--projects",
            type=int,
            default=3,
            help="Number of projects to create (default: 3)",
        )
        parser.add_argument(
            "--min-datasets",
            type=int,
            default=2,
            help="Minimum datasets per project (default: 2)",
        )
        parser.add_argument(
            "--max-datasets",
            type=int,
            default=4,
            help="Maximum datasets per project (default: 4)",
        )
        parser.add_argument(
            "--min-samples",
            type=int,
            default=5,
            help="Minimum samples per dataset (default: 5)",
        )
        parser.add_argument(
            "--max-samples",
            type=int,
            default=15,
            help="Maximum samples per dataset (default: 15)",
        )
        parser.add_argument(
            "--min-measurements",
            type=int,
            default=10,
            help="Minimum measurements per dataset (default: 10)",
        )
        parser.add_argument(
            "--max-measurements",
            type=int,
            default=30,
            help="Maximum measurements per dataset (default: 30)",
        )
        parser.add_argument(
            "--people",
            type=int,
            default=12,
            help="Number of personal contributors to create (default: 12)",
        )
        parser.add_argument(
            "--organizations",
            type=int,
            default=5,
            help="Number of organizational contributors to create (default: 5)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before generating new data",
        )

    def _load_factories_from_settings(self):
        """Load factory classes from FAIRDM_FACTORIES setting.

        Returns:
            dict: Dictionary with 'sample_factories' and 'measurement_factories' lists,
                  where each item is a tuple of (factory_class, model_class).
        """
        from fairdm.core.models import Measurement, Sample

        factories_config = getattr(settings, "FAIRDM_FACTORIES", {})
        sample_factories = []
        measurement_factories = []

        for _, factory_path in factories_config.items():
            try:
                # Import the factory class
                module_path, class_name = factory_path.rsplit(".", 1)
                module = import_module(module_path)
                factory_class = getattr(module, class_name)

                # Get the model class from the factory's Meta
                model_class = factory_class._meta.model

                # Categorize by base type
                if issubclass(model_class, Sample):
                    sample_factories.append((factory_class, model_class))
                    self.stdout.write(f"  ✓ Loaded Sample factory: {class_name} for {model_class.__name__}")
                elif issubclass(model_class, Measurement):
                    measurement_factories.append((factory_class, model_class))
                    self.stdout.write(f"  ✓ Loaded Measurement factory: {class_name} for {model_class.__name__}")
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Skipping {factory_path}: {model_class.__name__} is not a Sample or Measurement"
                        )
                    )
            except (ImportError, AttributeError) as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Could not load factory {factory_path}: {e}"))

        # Warn if no factories configured - we should never create base Sample/Measurement instances
        if not sample_factories:
            self.stdout.write(
                self.style.WARNING("  ⚠ No Sample factories configured in FAIRDM_FACTORIES. Samples will be skipped.")
            )

        if not measurement_factories:
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠ No Measurement factories configured in FAIRDM_FACTORIES. Measurements will be skipped."
                )
            )

        return {
            "sample_factories": sample_factories,
            "measurement_factories": measurement_factories,
        }

    def handle(self, *args, **options):
        """Execute the command."""
        num_projects = options["projects"]
        min_datasets = options["min_datasets"]
        max_datasets = options["max_datasets"]
        min_samples = options["min_samples"]
        max_samples = options["max_samples"]
        min_measurements = options["min_measurements"]
        max_measurements = options["max_measurements"]
        num_people = options["people"]
        num_organizations = options["organizations"]
        clear_data = options["clear"]

        if clear_data:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            with transaction.atomic():
                Measurement.objects.all().delete()
                Sample.objects.all().delete()
                Dataset.objects.all().delete()
                Project.objects.all().delete()
                Contribution.objects.all().delete()
                Person.objects.all().delete()
                Organization.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Data cleared"))

        self.stdout.write(self.style.WARNING("Loading configured factories..."))
        factories = self._load_factories_from_settings()

        self.stdout.write(self.style.WARNING("\nGenerating fake data..."))

        with transaction.atomic():
            # Create contributors first
            people = self._create_people(num_people)
            organizations = self._create_organizations(num_organizations)
            all_contributors = people + organizations

            # Create projects with datasets, samples, and measurements
            projects = []
            for i in range(num_projects):
                project = self._create_project(
                    i + 1,
                    all_contributors,
                    factories,
                    min_datasets,
                    max_datasets,
                    min_samples,
                    max_samples,
                    min_measurements,
                    max_measurements,
                )
                projects.append(project)

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("✓ Fake data generation complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Contributors: {len(all_contributors)} ({num_people} people, {num_organizations} orgs)")
        self.stdout.write(f"  Projects: {len(projects)}")

        total_datasets = Dataset.objects.count()
        total_samples = Sample.objects.count()
        total_measurements = Measurement.objects.count()
        total_contributions = Contribution.objects.count()

        self.stdout.write(f"  Datasets: {total_datasets}")
        self.stdout.write(f"  Samples: {total_samples}")
        self.stdout.write(f"  Measurements: {total_measurements}")
        self.stdout.write(f"  Contributions: {total_contributions}")
        self.stdout.write(self.style.SUCCESS("=" * 50 + "\n"))

    def _create_people(self, count):
        """Create personal contributors."""
        self.stdout.write(f"Creating {count} personal contributors...")
        people = []
        for _ in range(count):
            person = PersonFactory.create()
            people.append(person)
            self.stdout.write(f"  ✓ Created person: {person.name}")
        return people

    def _create_organizations(self, count):
        """Create organizational contributors."""
        self.stdout.write(f"\nCreating {count} organizational contributors...")
        organizations = []
        for _ in range(count):
            org = OrganizationFactory.create()
            organizations.append(org)
            self.stdout.write(f"  ✓ Created organization: {org.name}")
        return organizations

    def _create_project(
        self,
        project_num,
        all_contributors,
        factories,
        min_datasets,
        max_datasets,
        min_samples,
        max_samples,
        min_measurements,
        max_measurements,
    ):
        """Create a project with datasets, samples, and measurements."""
        self.stdout.write(f"\nCreating Project #{project_num}...")

        # Create project
        project = ProjectFactory()

        # Add descriptions and dates
        self._add_descriptions(project, ProjectDescription, random.randint(2, 4))
        self._add_dates(project, ProjectDate, random.randint(1, 3))

        # Add contributors with varied roles
        num_contributors = random.randint(3, 6)
        project_contributors = random.sample(all_contributors, min(num_contributors, len(all_contributors)))
        self._add_contributors(project, project_contributors, is_project=True)

        # Set a project owner (must be an Organization)
        for contributor in project_contributors:
            if isinstance(contributor, Organization):
                project.owner = contributor
                project.save()
                break

        self.stdout.write(f"  ✓ Created project: {project.name}")

        # Create datasets for this project
        num_datasets = random.randint(min_datasets, max_datasets)
        for _ in range(num_datasets):
            self._create_dataset(
                project,
                random.randint(1, num_datasets),
                all_contributors,
                factories,
                min_samples,
                max_samples,
                min_measurements,
                max_measurements,
            )

        return project

    def _create_dataset(
        self,
        project,
        dataset_num,
        all_contributors,
        factories,
        min_samples,
        max_samples,
        min_measurements,
        max_measurements,
    ):
        """Create a dataset with samples and measurements."""
        # Create dataset
        dataset = DatasetFactory(project=project)

        # Add descriptions and dates
        self._add_descriptions(dataset, DatasetDescription, random.randint(2, 5))
        self._add_dates(dataset, DatasetDate, random.randint(1, 2))

        # Add contributors
        num_contributors = random.randint(2, 5)
        dataset_contributors = random.sample(all_contributors, min(num_contributors, len(all_contributors)))
        self._add_contributors(dataset, dataset_contributors, is_project=False)

        self.stdout.write(f"    ✓ Created dataset: {dataset.name}")

        # Create samples for this dataset using configured factories
        num_samples = random.randint(min_samples, max_samples)
        samples = []

        if factories["sample_factories"]:
            for _ in range(num_samples):
                sample = self._create_sample(dataset, factories["sample_factories"])
                samples.append(sample)
        else:
            self.stdout.write(self.style.WARNING("      ⚠ Skipping sample creation (no Sample factories configured)"))

        # Create measurements for this dataset using configured factories
        num_measurements = random.randint(min_measurements, max_measurements)

        if factories["measurement_factories"]:
            for _ in range(num_measurements):
                # Randomly associate measurements with samples in this dataset
                related_sample = random.choice(samples) if samples else None
                self._create_measurement(dataset, related_sample, factories["measurement_factories"])
        else:
            self.stdout.write(
                self.style.WARNING("      ⚠ Skipping measurement creation (no Measurement factories configured)")
            )

        return dataset

    def _create_sample(self, dataset, sample_factories):
        """Create a sample using a random factory from configured sample factories.

        Args:
            dataset: The dataset to associate the sample with
            sample_factories: List of (factory_class, model_class) tuples
        """
        # Randomly select a factory from the available sample factories
        factory_class, _model_class = random.choice(sample_factories)

        # Create sample instance using the selected factory
        sample = factory_class(dataset=dataset)

        # Add descriptions and dates
        self._add_descriptions(sample, SampleDescription, random.randint(1, 3))
        self._add_dates(sample, SampleDate, random.randint(1, 2))

        return sample

    def _create_measurement(self, dataset, sample, measurement_factories):
        """Create a measurement using a random factory from configured measurement factories.

        Args:
            dataset: The dataset to associate the measurement with
            sample: The sample to associate the measurement with
            measurement_factories: List of (factory_class, model_class) tuples
        """
        # Randomly select a factory from the available measurement factories
        factory_class, _model_class = random.choice(measurement_factories)

        # Create measurement instance using the selected factory
        measurement = factory_class(dataset=dataset, sample=sample)

        # Add descriptions and dates
        self._add_descriptions(measurement, MeasurementDescription, random.randint(1, 2))
        self._add_dates(measurement, MeasurementDate, random.randint(1, 2))

        return measurement

    def _add_descriptions(self, obj, description_model, count):
        """Add description objects to a model instance."""
        description_types = [
            "Abstract",
            "Methods",
            "Technical Info",
            "Table of Contents",
        ]
        # Use sample to avoid duplicates (UniqueConstraint on related+type)
        selected_types = random.sample(description_types, min(count, len(description_types)))
        for desc_type in selected_types:
            description_model.objects.create(
                related=obj,
                type=desc_type,
                value=f"This is a {desc_type.lower()} description for {obj.name}.",
            )

    def _add_dates(self, obj, date_model, count):
        """Add date objects to a model instance."""
        date_types = [
            "Created",
            "Updated",
            "Issued",
            "Submitted",
            "Accepted",
            "Available",
        ]
        # Use sample to avoid duplicates (UniqueConstraint on related+type)
        selected_types = random.sample(date_types, min(count, len(date_types)))
        for date_type in selected_types:
            date_model.objects.create(
                related=obj,
                type=date_type,
                value="2024",  # Using partial date
            )

    def _add_contributors(self, obj, contributors, is_project=False):
        """Add contributors with varied roles to an object."""
        # Define available roles based on object type
        if is_project:
            available_roles = [
                "Creator",
                "ProjectLeader",
                "ProjectManager",
                "Researcher",
                "ContactPerson",
            ]
        else:
            available_roles = [
                "Creator",
                "Contributor",
                "DataCollector",
                "DataCurator",
                "DataManager",
                "Editor",
                "Researcher",
                "ContactPerson",
            ]

        # Get the fairdm-roles vocabulary concepts
        roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")

        for contributor in contributors:
            # Randomly assign 1-3 roles to each contributor
            num_roles = random.randint(1, 3)
            selected_roles = random.sample(available_roles, min(num_roles, len(available_roles)))

            # Create contribution
            contribution = Contribution.objects.create(
                contributor=contributor,
                content_object=obj,
            )

            # Add roles using concept queryset filtered by name
            if selected_roles:
                contribution.roles.set(roles_qs.filter(name__in=selected_roles))
