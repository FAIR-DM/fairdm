"""Seed the development database with records that exercise every state of the map of sample
locations.

Development only. Creates one project and six datasets, and:

- an outcrop survey whose samples are mostly on the map, some sharing a location, some with no
  location and one whose coordinates are not a latitude and longitude;
- a private dataset in the same project, which only its team sees on the project's map;
- a dataset where no sample has a location, and one with no samples at all;
- a dataset with a single located sample, and a large one, to judge the map when it is crowded;
- a person and an organization credited on the public and the private dataset, and a person
  credited on the project alone, whose map is empty.

Safe to run twice: it removes what it created before creating it again.
"""

import random

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from licensing.models import License

from demo.factories import RockSampleFactory, SoilSampleFactory, WaterSampleFactory
from demo.seed.common import example_accounts, grant_team_rights, remove_own_projects
from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.location.models import Point
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

PROJECT = "Map examples: Upper Rhine Graben field survey"
ORGANIZATION = "Rhine Valley Geological Survey"

# Outcrops between Basel and Karlsruhe, as (longitude, latitude).
OUTCROPS = [
    (7.59, 47.56), (7.62, 47.71), (7.66, 47.83), (7.85, 47.99), (7.71, 48.05),
    (7.75, 48.21), (7.82, 48.33), (7.95, 48.47), (7.79, 48.58), (8.05, 48.62),
    (8.11, 48.76), (8.24, 48.89), (8.4, 49.01), (8.35, 49.12), (8.47, 49.24),
]  # fmt: skip
LARGE = 1200


class SampleMapSeed(BaseCommand):
    help = "Seed records that exercise every state of the map of sample locations (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(20261002)
        call_command("seed_licenses", verbosity=0)
        users = example_accounts()
        remove_own_projects([PROJECT], users)

        project = Project.objects.create(
            name=PROJECT,
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            created_by=users["super.user"],
        )
        licence = License.objects.first()
        survey = self.dataset(project, "Outcrop survey, 2025", licence)
        private = self.dataset(
            project, "Borehole cuttings, 2026 (private)", licence, public=False
        )
        unlocated = self.dataset(project, "Archive hand specimens, unlocated", licence)
        empty = self.dataset(
            project, "Spring water chemistry (no samples yet)", licence
        )
        single = self.dataset(project, "Kaiserstuhl type section", licence)
        large = self.dataset(project, "Regional soil grid", licence)
        grant_team_rights(users["staff.user"], project, private)

        on_map = self.survey(survey)
        for lon, lat in [(8.62, 48.41), (8.71, 48.44), (8.66, 48.52)]:
            RockSampleFactory(
                dataset=private,
                name=f"Cuttings, {lat:.2f} N",
                location=self.point(lon, lat),
            )
        nowhere = [
            RockSampleFactory(
                dataset=unlocated, name=f"Hand specimen {n}", location=None
            )
            for n in range(1, 5)
        ]
        RockSampleFactory(
            dataset=single,
            name="Limberg tephrite, type section",
            location=self.point(7.6, 48.15),
        )
        for n in range(LARGE):
            SoilSampleFactory(
                dataset=large,
                name=f"Soil grid {n + 1:04d}",
                location=self.point(
                    round(random.uniform(7.5, 8.6), 4),
                    round(random.uniform(47.6, 49.3), 4),
                ),
            )

        clara = self.person("Clara", "Vogt")
        felix = self.person("Felix", "Arnold")
        survey_org, _ = Organization.objects.get_or_create(name=ORGANIZATION)
        for contributor in (clara, survey_org):
            survey.add_contributor(contributor, with_roles=["DataCollector"])
            private.add_contributor(contributor, with_roles=["DataCollector"])
        project.add_contributor(felix, with_roles=["ProjectMember"])

        for label, url in [
            ("Dataset, most samples on the map", self.map_url(survey)),
            ("Dataset, private", self.map_url(private)),
            ("Dataset, no sample has a location", self.map_url(unlocated)),
            ("Dataset, no samples", self.map_url(empty)),
            ("Dataset, one sample", self.map_url(single)),
            (f"Dataset, {LARGE} samples", self.map_url(large)),
            ("Project", self.map_url(project)),
            ("Sample with a location", self.map_url(on_map)),
            ("Sample without a location", self.map_url(nowhere[0])),
            ("Person credited on a public and a private dataset", self.map_url(clara)),
            ("Organization credited on the same two", self.map_url(survey_org)),
            ("Person credited on the project only", self.map_url(felix)),
        ]:
            self.stdout.write(f"{label}: {url}")

    def survey(self, dataset):
        """Fill the outcrop survey: one or several samples per outcrop, and some that can't be placed."""
        first = None
        for index, (lon, lat) in enumerate(OUTCROPS):
            point = self.point(lon, lat)
            sample = RockSampleFactory(
                dataset=dataset, name=f"Outcrop {index + 1:02d}, rock", location=point
            )
            first = first or sample
            if index % 3 == 0:
                SoilSampleFactory(
                    dataset=dataset,
                    name=f"Outcrop {index + 1:02d}, soil cover",
                    location=point,
                )
            if index == 4:
                for letter in "ABCDEFGH":
                    WaterSampleFactory(
                        dataset=dataset,
                        name=f"Outcrop 05, seep water {letter}",
                        location=point,
                    )
        for n in range(1, 6):
            RockSampleFactory(
                dataset=dataset, name=f"Float block {n}, no position", location=None
            )
        # Stored as metres on a projected grid by mistake, so not a latitude and longitude.
        RockSampleFactory(
            dataset=dataset,
            name="Outcrop 16, projected coordinates",
            location=self.point(412.5, 95.25),
        )
        return first

    def point(self, lon, lat):
        return Point.objects.get_or_create(x=lon, y=lat)[0]

    def dataset(self, project, name, licence, public=True):
        return Dataset.all_objects.create(
            name=name,
            project=project,
            visibility=Visibility.PUBLIC if public else Visibility.PRIVATE,
            published=public,
            license=licence,
        )

    def person(self, first, last):
        email = f"{first.lower()}.{last.lower()}@example.org"
        person = Person.objects.filter(email=email).first()
        if person is None:
            person = Person.objects.create_user(
                email=email, first_name=first, last_name=last
            )
            person.name = f"{first} {last}"
            person.save()
        return person

    def map_url(self, record):
        from fairdm.contrib.plugins import reverse

        return reverse(record, "map")
