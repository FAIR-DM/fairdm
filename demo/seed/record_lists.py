"""Seed every state of the Samples and Measurements tabs of specification 023.

Development only. Signs in through ``regular.user`` and ``staff.user`` at ``example.com``, password
``password``. Safe to run twice: it removes what it created before creating it again.

- A public project owned by an organization, with a published dataset holding two sample types
  and two measurement types (enough rows to page), an unpublished public dataset, a private
  dataset, an empty dataset, and a partner dataset whose measurements were made on the first
  dataset's samples and on a private sample.
- A private project with a public, published dataset, which a private project hides.
- A public project whose only dataset is public and unpublished.
- ``regular.user`` credited on the partner dataset, on one sample of the published dataset, on the
  unpublished and the private dataset, and on the dataset in the private project.
- ``staff.user`` on the team of everything.
"""

import random


from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from licensing.models import License

from demo.factories import (
    ICP_MS_MeasurementFactory,
    OrganizationFactory,
    RockSampleFactory,
    SoilSampleFactory,
    WaterSampleFactory,
    XRFMeasurementFactory,
)
from demo.seed.common import example_accounts, grant_team_rights, remove_own_projects
from fairdm.contrib.contributors.models import Organization
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

MAIN = "Record list examples"
HIDDEN = "Record list examples, private project"
WAITING = "Record list examples, nothing published yet"
ORGANIZATION = "Record List Laboratory"


def near(lon, lat):
    """Return a point a short way from ``lon``, ``lat``, so each sample has a place of its own."""
    return Point(
        round(lon + random.uniform(-0.02, 0.02), 5),
        round(lat + random.uniform(-0.02, 0.02), 5),
        srid=4326,
    )


class RecordListSeed(BaseCommand):
    help = "Seed every state of the Samples and Measurements tabs (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(20261103)
        call_command("seed_licenses", verbosity=0)
        users = example_accounts()
        remove_own_projects([MAIN, HIDDEN, WAITING], users)
        Organization.objects.filter(name=ORGANIZATION).delete()
        self.licence = License.objects.first()
        regular, staff = users["regular.user"], users["staff.user"]

        lab = OrganizationFactory(name=ORGANIZATION, location=Point(13.06, 52.38, srid=4326))
        main = self.project(MAIN, Visibility.PUBLIC, users, owner=lab)
        published = self.dataset(main, "Borehole cores, published", published=True)
        unpublished = self.dataset(main, "Borehole cores, 2026 (not published yet)")
        private = self.dataset(
            main, "Pilot soil survey (private)", visibility=Visibility.PRIVATE
        )
        empty = self.dataset(main, "Planned campaign (no records yet)", published=True)
        partner = self.dataset(main, "Partner laboratory ICP-MS runs", published=True)

        rocks = [
            RockSampleFactory(
                dataset=published,
                name=f"BH-1 core, {100 + 12 * i} m",
                location=near(7.86, 48.93),
            )
            for i in range(60)
        ]
        for i in range(8):
            WaterSampleFactory(
                dataset=published,
                name=f"BH-1 pore water {i + 1}",
                location=near(7.86, 48.93),
            )
        for rock in rocks[:40]:
            XRFMeasurementFactory(dataset=published, sample=rock, name=f"XRF {rock.name}")
        for rock in rocks[:12]:
            ICP_MS_MeasurementFactory(
                dataset=published, sample=rock, name=f"ICP-MS {rock.name}"
            )
        waiting = [
            RockSampleFactory(
                dataset=unpublished,
                name=f"BH-2 core, {200 + 10 * i} m",
                location=near(7.91, 48.95),
            )
            for i in range(5)
        ]
        for rock in waiting:
            XRFMeasurementFactory(dataset=unpublished, sample=rock, name=f"XRF {rock.name}")
        soils = [
            SoilSampleFactory(
                dataset=private, name=f"Pilot soil {i + 1}", location=near(8.1, 49.0)
            ) for i in range(4)
        ]
        for rock in rocks[:6]:
            ICP_MS_MeasurementFactory(
                dataset=partner, sample=rock, name=f"Partner ICP-MS {rock.name}"
            )
        for i, soil in enumerate(soils[:2]):
            ICP_MS_MeasurementFactory(
                dataset=partner, sample=soil, name=f"Partner ICP-MS run {i + 1}"
            )

        hidden_project = self.project(HIDDEN, Visibility.PRIVATE, users)
        hidden = self.dataset(hidden_project, "Hidden cores", published=True)
        for i in range(3):
            RockSampleFactory(dataset=hidden, name=f"Hidden core {i + 1}")

        waiting_project = self.project(WAITING, Visibility.PUBLIC, users)
        waiting_dataset = self.dataset(waiting_project, "First campaign (not published yet)")
        for i in range(3):
            RockSampleFactory(dataset=waiting_dataset, name=f"First campaign core {i + 1}")

        grant_team_rights(
            staff,
            main,
            hidden_project,
            waiting_project,
            published,
            unpublished,
            private,
            empty,
            partner,
            hidden,
            waiting_dataset,
        )
        for record in (partner, rocks[0], unpublished, private, hidden):
            Crediting(record).add(regular)

        self.stdout.write(f"Dataset, two types each: {published.get_absolute_url()}")
        self.stdout.write(f"Dataset, not published: {unpublished.get_absolute_url()}")
        self.stdout.write(f"Dataset, private: {private.get_absolute_url()}")
        self.stdout.write(f"Dataset, empty: {empty.get_absolute_url()}")
        self.stdout.write(f"Dataset, other team's samples: {partner.get_absolute_url()}")
        self.stdout.write(f"Project, mixed: {main.get_absolute_url()}")
        self.stdout.write(f"Project, nothing published: {waiting_project.get_absolute_url()}")
        self.stdout.write(f"Person: {regular.get_absolute_url()}")
        self.stdout.write(f"Organization: {lab.get_absolute_url()}")

    def project(self, name, visibility, users, owner=None):
        return Project.objects.create(
            name=name,
            status=ProjectStatus.IN_PROGRESS,
            visibility=visibility,
            created_by=users["super.user"],
            owner=owner,
        )

    def dataset(self, project, name, published=False, visibility=Visibility.PUBLIC):
        return Dataset.all_objects.create(
            name=name,
            project=project,
            visibility=visibility,
            published=published,
            license=self.licence,
        )
