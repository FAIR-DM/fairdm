"""Seed the development database with samples that exercise every state of the sample overview
page.

Development only. Creates the standard sign-in accounts, one project and three datasets, and:

- a rock core with a full history, an IGSN, a location, measurements (some of them recorded in
  another team's dataset) and three subsamples — the rock sample type has its own overview
  template, so this shows the extended page;
- a water sample that has been destroyed — a type with no template of its own, so this shows the
  generic page alone;
- a soil sample with nothing but a name;
- a rock sample in an unpublished dataset, which only the dataset's team can open.

Safe to run twice: it removes what it created before creating it again.
"""

import random
from datetime import date

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from guardian.shortcuts import assign_perm
from licensing.models import License
from partial_date import PartialDate

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
    WaterSampleFactory,
    XRFMeasurementFactory,
)
from fairdm.contrib.contributors.models import Person
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import SampleDate, SampleDescription, SampleIdentifier, SampleRelation
from fairdm.utils.choices import Visibility

PROJECT = "Sample page examples"

ACCOUNTS = [
    ("regular.user@example.com", "Regular", "User", False, False),
    ("staff.user@example.com", "Staff", "User", True, False),
    ("super.user@example.com", "Super", "User", True, True),
]


class Command(BaseCommand):
    help = "Seed samples that exercise every state of the sample overview page (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(20260924)
        call_command("seed_licenses", verbosity=0)
        users = self.accounts()
        # Datasets first: a project with public datasets refuses to be deleted.
        Dataset.all_objects.filter(project__name=PROJECT).delete()
        Project.objects.filter(name=PROJECT).delete()

        project = Project.objects.create(
            name=PROJECT, status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC
        )
        licence = License.objects.first()
        cores = self.dataset(project, "Soultz cores, 2025 campaign", licence, published=True)
        lab = self.dataset(project, "Partner laboratory ICP-MS runs", licence, published=True)
        pending = self.dataset(project, "Soultz cores, 2026 campaign (in progress)", licence, published=False)
        for dataset in (cores, lab, pending):
            for permission in ("view_dataset", "change_dataset"):
                assign_perm(f"dataset.{permission}", users["staff.user"], dataset)

        core = self.core(cores, lab)
        water = self.destroyed_water(cores)
        soil = SoilSampleFactory(dataset=cores, name="Bruchsal soil, transect B, point 7")
        hidden = RockSampleFactory(dataset=pending, name="EPS-1 core, 1840 m")

        for label, sample in [
            ("Rock core, full history (extended page)", core),
            ("Water sample, destroyed (generic page)", water),
            ("Soil sample, nothing recorded", soil),
            ("Rock sample in an unpublished dataset", hidden),
        ]:
            self.stdout.write(f"{label}: {sample.get_absolute_url()}")

    def accounts(self):
        users = {}
        for email, first, last, staff, superuser in ACCOUNTS:
            user = Person.objects.filter(email=email).first() or Person.objects.create_user(
                email=email, password="password"
            )
            user.first_name, user.last_name, user.name = first, last, f"{first} {last}"
            user.is_staff, user.is_superuser = staff, superuser
            user.set_password("password")
            user.save()
            users[email.split("@")[0]] = user
        return users

    def person(self, first, last):
        email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.org"
        person = Person.objects.filter(email=email).first()
        if person is None:
            person = Person.objects.create_user(email=email, first_name=first, last_name=last)
            person.name = f"{first} {last}"
            person.save()
        return person

    def dataset(self, project, name, licence, published):
        return Dataset.all_objects.create(
            name=name,
            project=project,
            visibility=Visibility.PUBLIC,
            published=published,
            license=licence,
        )

    def core(self, cores, lab):
        Point = apps.get_model("fairdm_location", "Point")
        core = RockSampleFactory(
            dataset=cores,
            name="GPK-2 core, 3512 m",
            local_id="GPK2-C14-3512",
            status="stored",
            rock_type="igneous",
            collection_date=date(2025, 4, 3),
            mineral_content="K-feldspar, quartz, plagioclase, biotite; altered to illite along fractures.",
            location=Point.objects.get_or_create(x=7.8656, y=48.9353, defaults={"crs": "EPSG:4326"})[0],
        )
        SampleIdentifier.objects.create(related=core, type="IGSN", value="10.60510/FDM.GPK2C143512")
        for type_, value in [("Collected", "2025-04-03"), ("Prepared", "2025-05-19"), ("Archival", "2025-07-01")]:
            SampleDate.objects.create(related=core, type=type_, value=PartialDate(value))
        for type_, value in [
            ("SampleCollection", "Recovered by wireline coring from the GPK-2 well. Orientation marked on recovery."),
            ("SamplePreparation", "Slabbed along the long axis; one half crushed and milled below 63 µm for XRF."),
            ("SampleStorage", "Archive half held at the BGR core repository, Berlin-Spandau, box 2025-117."),
            ("Other", "Fracture zone at 3509–3514 m. The core is partly altered, which shows in the potassium values."),
        ]:
            SampleDescription.objects.create(related=core, type=type_, value=value)
        core.add_contributor(self.person("Lea", "Brandt"), with_roles=["Collection"])
        core.add_contributor(self.person("Jonas", "Weber"), with_roles=["Collection", "Preparation"])
        core.add_contributor(self.person("Mei", "Tanaka"), with_roles=["Storage"])

        for _ in range(8):
            XRFMeasurementFactory(sample=core, dataset=cores)
        for _ in range(3):
            ICP_MS_MeasurementFactory(sample=core, dataset=lab)
        for letter in "ABC":
            split = RockSampleFactory(dataset=cores, name=f"GPK-2 core, 3512 m, split {letter}", status="in_use")
            SampleRelation.objects.create(source=split, target=core, type="child_of")
        return core

    def destroyed_water(self, cores):
        water = WaterSampleFactory(dataset=cores, name="Rittershoffen brine, GRT-1, sample 4", status="destroyed")
        for type_, value in [("Collected", "2025-08-12"), ("Destroyed", "2025-09-30")]:
            SampleDate.objects.create(related=water, type=type_, value=PartialDate(value))
        SampleDescription.objects.create(
            related=water,
            type="SampleDestruction",
            value="Consumed entirely by the isotope analysis.",
        )
        water.add_contributor(self.person("Yusuf", "Demir"), with_roles=["Collection", "Destruction"])
        for _ in range(2):
            ICP_MS_MeasurementFactory(sample=water, dataset=cores)
        return water
