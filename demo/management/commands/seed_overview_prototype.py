"""Development data for the redesigned overview pages (prototype).

Runs on top of ``seed_overviews``. It gives the Upper Rhine Graben project's samples realistic
locations so the coverage maps have something to show, replaces placeholder measurement names
with lab-style ones, puts ``regular.user`` on that project's team, and creates ``regular.user2``
with one empty project and one empty dataset of their own, so the first visit can be judged.

    DJANGO_ENV=development python manage.py seed_overview_prototype
"""

import random

from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.core.management.base import BaseCommand

from demo.seed.common import create_accounts, grant_team_rights
from fairdm.core.models import Dataset, Measurement, Project, Sample

PROJECT_NAME = "Thermal regime and groundwater flow of the Upper Rhine Graben"

# Where each dataset's samples were taken: a centre (lon, lat), a spread in degrees and an
# elevation range in metres.
SITES = {
    "Thermal conductivity of Buntsandstein sandstones": ((8.55, 49.02), 0.18, (140, 420)),
    "Shallow soil gas survey, Bruchsal": ((8.60, 49.12), 0.05, (110, 180)),
    "Core samples from the Soultz-sous-Forêts boreholes": ((7.865, 48.935), 0.02, (150, 160)),
    "Deep groundwater chemistry, Rittershoffen and Landau": ((8.03, 49.04), 0.16, (120, 190)),
    "Borehole temperature logs (quality-controlled)": ((8.25, 49.30), 0.25, (95, 160)),
    "Spring water sampling campaign 2026": ((8.35, 48.75), 0.30, (120, 600)),
}

ELEMENTS = ["Fe", "Ca", "Mg", "Na", "K", "Ti", "Mn", "Si", "Al", "P"]
ANALYTES = ["Li", "Sr", "Ba", "Rb", "Cs", "B", "U"]


class Command(BaseCommand):
    help = "Seed the redesigned overview pages (development only, prototype)."

    def handle(self, *args, **options):
        rng = random.Random(42)
        users = create_accounts(
            [
                ("regular.user@example.com", "Regular", "User", False, False),
                ("regular.user2@example.com", "Second", "User", False, False),
            ]
        )
        project = Project.objects.filter(name=PROJECT_NAME).first()
        if project is None:
            call_command("seed_overviews")
            project = Project.objects.get(name=PROJECT_NAME)

        grant_team_rights(users["regular.user"], project)

        located = 0
        for dataset in Dataset.all_objects.filter(project=project):
            site = SITES.get(dataset.name)
            if site is None:
                (lon, lat), spread, elevation = (8.3, 49.0), 0.3, (100, 400)
            else:
                (lon, lat), spread, elevation = site
            for i, sample in enumerate(Sample.objects.filter(dataset=dataset).order_by("pk")):
                # One in eight samples keeps no location, so the "without one" count shows.
                if i % 8 == 7:
                    continue
                sample.location = Point(
                    lon + rng.uniform(-spread, spread) * 1.4, lat + rng.uniform(-spread, spread), srid=4326
                )
                sample.location_elevation = round(rng.uniform(*elevation))
                sample.location_uncertainty = rng.choice([5, 10, 25, 50])
                sample.save(update_fields=["location", "location_elevation", "location_uncertainty"])
                located += 1

        renamed = 0
        for measurement in Measurement.objects.filter(dataset__project__name__in=[PROJECT_NAME, "Sample page examples"]):
            name = measurement.name or ""
            if " " in name or "," in name or len(name) > 12:
                continue
            kind = type(measurement).__name__
            if kind == "XRFMeasurement":
                element = getattr(measurement, "element", None) or rng.choice(ELEMENTS)
                measurement.name = f"{element}, fused bead, run {rng.randint(100, 520)}"
            elif "ICP" in kind.upper():
                measurement.name = f"{rng.choice(ANALYTES)}, solution ICP-MS, run {rng.randint(10, 90)}"
            else:
                measurement.name = f"{type(measurement)._meta.verbose_name.capitalize()} {rng.randint(1, 400)}"
            measurement.save(update_fields=["name"])
            renamed += 1

        second = users["regular.user2"]
        empty, _ = Project.objects.get_or_create(
            name="Karst spring monitoring, Swabian Jura",
            defaults={"owner": None},
        )
        grant_team_rights(second, empty)
        empty_dataset = Dataset.all_objects.filter(project=empty).first()
        if empty_dataset is None:
            empty_dataset = Dataset.all_objects.create(name="Spring discharge 2027 (planned)", project=empty)
        grant_team_rights(second, empty_dataset)

        self.stdout.write(f"Located {located} samples and renamed {renamed} measurements.")
        self.stdout.write(f"Rich project: {project.get_absolute_url()} (regular.user is on its team)")
        self.stdout.write(f"Empty project: {empty.get_absolute_url()} and dataset {empty_dataset.get_absolute_url()} (regular.user2)")
