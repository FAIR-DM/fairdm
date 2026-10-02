"""Development data for the Statistics pages.

Adds one project whose datasets reach the states the dataset and project Statistics pages answer
for. The person and organization pages read the records ``seed_overviews`` and ``seed_profiles``
create, so run those first. It refuses outside development, and running it again replaces only
the project it created.

    DJANGO_ENV=development python manage.py seed_statistics
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from demo.factories import CustomSampleFactory, RockSampleFactory, XRFMeasurementFactory
from demo.seed.common import example_accounts, grant_team_rights, remove_own_projects
from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility

PROJECT = "Statistics page examples"
FULL = "Sandstone cores with field summaries of every kind"
UNPUBLISHED = "Second drilling season (not yet published)"
EMPTY = "Planned outcrop survey (empty)"
PRIVATE = "Working measurements (private)"


class Command(BaseCommand):
    help = "Seed every state of the dataset and project Statistics pages (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one."
            )
        random.seed(20261002)
        users = example_accounts()
        remove_own_projects([PROJECT], users)
        owner, _ = Organization.objects.get_or_create(
            name="Karlsruhe Institute of Technology"
        )
        project = Project.objects.create(
            name=PROJECT,
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
            created_by=users["super.user"],
        )
        project.add_contributor(users["super.user"], with_roles=["ProjectLeader"])
        now = timezone.now()
        start = now - timedelta(days=900)

        full = self.dataset(project, users, FULL, Visibility.PUBLIC, True)
        self.rocks(full, 240)
        self.customs(full, 60)
        self.xrf(full, 500)
        unpublished = self.dataset(
            project, users, UNPUBLISHED, Visibility.PUBLIC, False
        )
        self.rocks(unpublished, 40)
        empty = self.dataset(project, users, EMPTY, Visibility.PUBLIC, True)
        private = self.dataset(project, users, PRIVATE, Visibility.PRIVATE, False)
        self.rocks(private, 30)
        self.xrf(private, 80)
        # regular.user is on the team of the unpublished and the private dataset only.
        grant_team_rights(users["regular.user"], unpublished, private)
        for dataset in (full, unpublished, private):
            dataset.add_contributor(users["regular.user"], with_roles=["DataCollector"])

        datasets = [full, unpublished, empty, private]
        for index, dataset in enumerate(datasets):
            self.backdate(Sample.objects.filter(dataset=dataset), start, now)
            self.backdate(Measurement.objects.filter(dataset=dataset), start, now)
            Dataset.all_objects.filter(pk=dataset.pk).update(
                added=start + timedelta(days=200 * index)
            )
        self.earlier_seasons(project, users, owner, now)
        Project.objects.filter(pk=project.pk).update(
            added=now.replace(year=now.year - 6)
        )

        self.stdout.write(f"  project      {project.get_absolute_url()}statistics/")
        for label, dataset in zip(
            ("full", "unpublished", "empty", "private"), datasets, strict=True
        ):
            self.stdout.write(f"  {label:<12} {dataset.get_absolute_url()}statistics/")
        self.stdout.write(self.style.SUCCESS("Seeded the Statistics page states."))

    def earlier_seasons(self, project, users, owner, now):
        """Six small published datasets, one a year, so the yearly charts have years to show.

        ``regular.user`` is credited on all of them in changing roles, and the owner's current
        members on fewer of them each year back, so the count of active members varies.
        """
        members = [m.person for m in owner.get_current_memberships()][:5]
        roles = ["DataCollector", "DataCurator", "Researcher", "ContactPerson"]
        for back in range(6, 0, -1):
            added = now.replace(year=now.year - back)
            season = self.dataset(
                project, users, f"Field season {added.year}", Visibility.PUBLIC, True
            )
            self.rocks(season, 12)
            Sample.objects.filter(dataset=season).update(added=added)
            season.add_contributor(
                users["regular.user"], with_roles=[roles[back % len(roles)]]
            )
            for member in members[: max(1, 6 - back)]:
                season.add_contributor(member, with_roles=["DataCollector"])
            if back % 2:
                season.add_contributor(owner, with_roles=["HostingInstitution"])
            Dataset.all_objects.filter(pk=season.pk).update(added=added)

    def dataset(self, project, users, name, visibility, published):
        return Dataset.all_objects.create(
            name=name,
            project=project,
            visibility=visibility,
            published=published,
            created_by=users["super.user"],
        )

    def backdate(self, queryset, start, end):
        span = (end - start).days
        for pk in queryset.values_list("pk", flat=True):
            offset = int(span * random.random() ** 0.6)
            queryset.model.objects.filter(pk=pk).update(
                added=start + timedelta(days=offset)
            )

    def rocks(self, dataset, count):
        """Rock samples: a skewed weight, a date over six years and a text field a third lack."""
        for n in range(count):
            RockSampleFactory(
                dataset=dataset,
                name=f"SST-{dataset.pk}-{n:03d}",
                rock_type=random.choices(
                    ["sedimentary", "igneous", "metamorphic"], weights=[6, 3, 1]
                )[0],
                weight_grams=round(random.lognormvariate(5.5, 0.6), 1),
                hardness_mohs=Decimal(str(round(random.triangular(2, 9, 6.5), 1))),
                collection_date=date(2019, 1, 1)
                + timedelta(days=int(random.random() ** 0.7 * 2400)),
                mineral_content=""
                if random.random() < 0.33
                else random.choice(["Quartz, Feldspar, Mica", "Calcite, Dolomite"]),
            )

    def customs(self, dataset, count):
        """Samples of the all-field-types example: a yes/no field, and one field never filled."""
        for n in range(count):
            CustomSampleFactory(
                dataset=dataset,
                name=f"REF-{n:03d}",
                boolean_field=random.random() < 0.7,
                integer_field=None if random.random() < 0.15 else random.randint(1, 40),
                small_integer_field=7,
                big_integer_field=None,
                date_field=date(2024, 3, 1) + timedelta(days=random.randint(0, 20)),
            )

    def xrf(self, dataset, count):
        """XRF measurements: a detection limit on most, and two fields nobody filled in."""
        samples = list(Sample.objects.filter(dataset=dataset)[:200])
        elements = ["Si", "Al", "Fe", "Ca", "Mg", "K", "Na", "Ti", "Mn", "P"]
        for _ in range(count):
            XRFMeasurementFactory(
                sample=random.choice(samples),
                dataset=dataset,
                element=random.choices(elements, weights=range(10, 0, -1))[0],
                concentration_ppm=Decimal(str(round(random.lognormvariate(6, 1.4), 2))),
                detection_limit_ppm=None
                if random.random() < 0.4
                else Decimal(str(round(random.uniform(0.5, 5), 2))),
            )
