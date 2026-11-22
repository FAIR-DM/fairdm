"""Development data for the import and export prototype.

    DJANGO_ENV=development python manage.py seed_import_export_prototype

- ``regular.user`` manages "Black Forest soil survey 2024", filled by imports: soil samples, rock
  samples and XRF measurements, with a history that reaches every state of an import (imported,
  imported and no longer undoable, undone, needing changes, ready to import).
- ``regular.user2`` manages "Lake cores 2025", which holds nothing yet.
- Example files to try are written to ``tabular/static/tabular/examples/``.

Running it again replaces what it created.
"""

from __future__ import annotations

import csv
import io
import random
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from demo.models import RockSample, SoilSample, WaterSample, XRFMeasurement
from demo.seed.common import create_accounts, example_accounts, grant_team_rights, remove_own_projects
from fairdm.contrib.tabular import engine
from fairdm.contrib.tabular.models import ImportJob
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

PROJECTS = ["Import and export walkthrough", "Lake cores (nothing recorded)"]
EXAMPLES = Path(__file__).resolve().parents[2] / "static" / "tabular" / "examples"

SOIL_TYPES = ["loam", "clay", "sandy loam", "silt loam", "peat"]
TEXTURES = ["fine", "medium", "coarse"]
ROCKS = ["granite", "gneiss", "sandstone", "limestone", "basalt"]
ELEMENTS = ["Fe", "Ca", "Ti", "K", "Mn"]


def csv_bytes(headers, rows):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(headers)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def xlsx_bytes(headers, rows):
    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


SOIL_HEADERS = ["local_id", "name", "soil_type", "ph_level", "depth_cm", "organic_matter_percent", "moisture_content", "texture", "latitude", "longitude", "location_elevation"]


def soil_row(rng, n, prefix="BF-S"):
    return [
        f"{prefix}-{n:03d}",
        f"Plot {(n - 1) // 4 + 1}, pit {(n - 1) % 4 + 1}",
        rng.choice(SOIL_TYPES),
        f"{rng.uniform(4.2, 7.6):.2f}",
        rng.choice([10, 20, 30, 50, 80]),
        f"{rng.uniform(1.5, 14):.1f}",
        f"{rng.uniform(12, 48):.1f}",
        rng.choice(TEXTURES),
        f"{48.0 + rng.uniform(-0.08, 0.08):.5f}",
        f"{8.1 + rng.uniform(-0.12, 0.12):.5f}",
        f"{rng.uniform(640, 1100):.0f}",
    ]


class Command(BaseCommand):
    help = "Seed the import and export prototype (development only)."

    def handle(self, *args, **options):
        rng = random.Random(42)
        users = example_accounts()
        regular = users["regular.user"]
        regular2 = create_accounts([("regular.user2@example.com", "Regular", "User Two", False, False)])["regular.user2"]

        old = Dataset.all_objects.filter(project__name__in=PROJECTS, project__created_by=users["super.user"])
        ImportJob.objects.filter(dataset__in=old).delete()
        for dataset in old:
            XRFMeasurement.objects.filter(dataset=dataset).delete()
        remove_own_projects(PROJECTS, users)

        project = Project.objects.create(
            name=PROJECTS[0], status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, created_by=users["super.user"]
        )
        dataset = Dataset.all_objects.create(
            name="Black Forest soil survey 2024", project=project, visibility=Visibility.PUBLIC, published=False
        )
        grant_team_rights(regular, project, dataset)

        empty_project = Project.objects.create(
            name=PROJECTS[1], status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, created_by=users["super.user"]
        )
        empty = Dataset.all_objects.create(
            name="Lake cores 2025", project=empty_project, visibility=Visibility.PUBLIC, published=False
        )
        grant_team_rights(regular2, empty_project, empty)

        now = timezone.now()

        def run(model, name, raw, when_days, finish=True, mode="both", empty_cells="keep", mapping=None):
            upload = SimpleUploadedFile(name, raw)
            job = engine.start_job(dataset, model, upload, regular, mode, empty_cells)
            if mapping:
                job.column_map.update(mapping)
                job.save()
            engine.check(job)
            job.refresh_from_db()
            if finish and job.status == ImportJob.Status.CHECKED:
                engine.perform(job, regular)
                job.refresh_from_db()
            ImportJob.objects.filter(pk=job.pk).update(created=now - timedelta(days=when_days))
            return job

        # 1. The spring soil campaign: 40 new soil samples, three weeks ago.
        spring = [soil_row(rng, n) for n in range(1, 41)]
        job1 = run(SoilSample, "soil-samples-spring.csv", csv_bytes(SOIL_HEADERS, spring), 21)
        ImportJob.objects.filter(pk=job1.pk).update(imported_at=now - timedelta(days=21))

        # 2. Rock samples from the field sheet, two weeks ago.
        rock_headers = ["local_id", "name", "rock_type", "collection_date", "weight_grams", "hardness_mohs", "latitude", "longitude"]
        rocks = [
            [f"BF-R-{n:03d}", f"Outcrop {n}", rng.choice(ROCKS), f"2024-0{rng.randint(4, 9)}-{rng.randint(10, 28)}",
             f"{rng.uniform(120, 950):.1f}", f"{rng.uniform(3, 7.5):.1f}", f"{48.0 + rng.uniform(-0.1, 0.1):.5f}", f"{8.1 + rng.uniform(-0.1, 0.1):.5f}"]
            for n in range(1, 16)
        ]
        job2 = run(RockSample, "rock-samples-field-sheet.csv", csv_bytes(rock_headers, rocks), 14)
        ImportJob.objects.filter(pk=job2.pk).update(imported_at=now - timedelta(days=14))

        # 3. XRF results on the rock samples, by Local ID, ten days ago.
        xrf_headers = ["local_id", "name", "sample", "element", "concentration_ppm", "detection_limit_ppm", "instrument_model"]
        xrf = []
        n = 0
        for r in range(1, 16):
            for element in rng.sample(ELEMENTS, 3):
                n += 1
                xrf.append([f"BF-X-{n:03d}", f"{element} in BF-R-{r:03d}", f"BF-R-{r:03d}", element,
                            f"{rng.uniform(50, 9000):.2f}", f"{rng.uniform(1, 12):.2f}", "Bruker S1 TITAN"])
        job3 = run(XRFMeasurement, "xrf-batch-1.csv", csv_bytes(xrf_headers, xrf), 10)
        ImportJob.objects.filter(pk=job3.pk).update(imported_at=now - timedelta(days=10))

        # 4. A trial water-sample file, imported and undone a week ago.
        water_headers = ["local_id", "name", "water_source", "temperature_celsius", "ph_level"]
        water = [[f"BF-W-{i:02d}", f"Spring {i}", "spring", f"{rng.uniform(6, 11):.1f}", f"{rng.uniform(6.2, 7.8):.2f}"] for i in range(1, 6)]
        job4 = run(WaterSample, "water-test.csv", csv_bytes(water_headers, water), 7)
        engine.undo(job4, regular)
        ImportJob.objects.filter(pk=job4.pk).update(imported_at=now - timedelta(days=7), undone_at=now - timedelta(days=7))

        # 5. pH corrections from the lab, as an edited export: yesterday, still undoable.
        corrections = []
        for sample in SoilSample.objects.filter(dataset=dataset).order_by("local_id")[:6]:
            corrections.append([sample.uuid, sample.local_id, f"{float(sample.ph_level) + rng.choice([-0.4, -0.2, 0.3, 0.5]):.2f}"])
        job5 = run(SoilSample, "soil-ph-corrections.xlsx", xlsx_bytes(["portal_id", "local_id", "ph_level"], corrections), 1)

        # 6. A second XRF batch with mistakes: waiting for a corrected file.
        bad = [
            ["BF-X-101", "Fe in BF-R-001 (repeat)", "BF-R-001", "Fe", "4210.5", "3.1", "Bruker S1 TITAN"],
            ["BF-X-102", "Ca in BF-R-002", "BF-R-002", "Ca", "1830,2", "2.4", "Bruker S1 TITAN"],
            ["BF-X-103", "Ti in BF-R-099", "BF-R-099", "Ti", "612.0", "1.9", "Bruker S1 TITAN"],
            ["BF-X-104", "K in BF-R-003", "BF-R-003", "K", "2104.7", "2.2", "Bruker S1 TITAN"],
            ["BF-X-104", "Mn in BF-R-003", "BF-R-003", "Mn", "388.4", "1.5", "Bruker S1 TITAN"],
            ["BF-X-106", "", "BF-R-004", "Fe", "5120.0", "", "Bruker S1 TITAN"],
            ["BF-X-107", "Ca in BF-R-005", "", "Ca", "990.0", "2.0", "Bruker S1 TITAN"],
        ] + [
            [f"BF-X-{i:03d}", f"Fe in BF-R-{(i % 15) + 1:03d}", f"BF-R-{(i % 15) + 1:03d}", "Fe", f"{rng.uniform(800, 7000):.2f}", "2.0", "Bruker S1 TITAN"]
            for i in range(108, 130)
        ]
        run(XRFMeasurement, "xrf-batch-2.csv", csv_bytes(xrf_headers, bad), 0, finish=False)

        # 7. The autumn soil campaign: checked, waiting for the go-ahead.
        autumn = [soil_row(rng, n) for n in range(41, 53)]
        existing = list(SoilSample.objects.filter(dataset=dataset).order_by("local_id")[6:14])
        for i, sample in enumerate(existing):
            row = [sample.local_id, sample.name, sample.soil_type, f"{sample.ph_level}", sample.depth_cm,
                   f"{sample.organic_matter_percent}", f"{sample.moisture_content}", sample.texture,
                   f"{sample.location.y:.5f}", f"{sample.location.x:.5f}", f"{sample.location_elevation:.0f}"]
            if i < 3:
                row[7] = "coarse" if sample.texture != "coarse" else "fine"
                row[5] = f"{float(sample.organic_matter_percent) + 1.5:.1f}"
            autumn.append(row)
        run(SoilSample, "soil-samples-autumn.csv", csv_bytes(SOIL_HEADERS, autumn), 0, finish=False)

        self.write_examples(rng, dataset)

        self.stdout.write("Seeded the import and export prototype.")
        self.stdout.write(f"regular.user's dataset: {dataset.get_absolute_url()}")
        self.stdout.write(f"regular.user2's empty dataset: {empty.get_absolute_url()}")

    def write_examples(self, rng, dataset):
        EXAMPLES.mkdir(parents=True, exist_ok=True)
        (EXAMPLES / "soil-samples-new.csv").write_bytes(
            csv_bytes(SOIL_HEADERS, [soil_row(rng, n, prefix="BF-S") for n in range(101, 109)])
        )
        field_headers = ["Sample code", "Name", "Soil class", "pH", "Depth (cm)", "Lat", "Lon", "Comments", "Collected by"]
        field_rows = [
            [f"LK-{n:02d}", f"Lake shore pit {n}", rng.choice(SOIL_TYPES), round(rng.uniform(5, 7.5), 2), rng.choice([10, 25, 40]),
             round(47.6 + rng.uniform(-0.05, 0.05), 5), round(9.2 + rng.uniform(-0.05, 0.05), 5), rng.choice(["wet", "", "roots", "stony"]), "J. Weber"]
            for n in range(1, 7)
        ]
        (EXAMPLES / "soil-samples-field-headings.xlsx").write_bytes(xlsx_bytes(field_headers, field_rows))
        xrf_headers = ["local_id", "name", "sample", "element", "concentration_ppm", "detection_limit_ppm", "instrument_model"]
        problem_rows = [
            ["BF-X-201", "Fe in BF-R-006", "BF-R-006", "Fe", "4021.3", "2.1", "Bruker S1 TITAN"],
            ["BF-X-202", "Ca in BF-R-007", "BF-R-007", "Ca", "1290,5", "2.0", "Bruker S1 TITAN"],
            ["BF-X-203", "Ti in BF-R-404", "BF-R-404", "Ti", "411.0", "1.2", "Bruker S1 TITAN"],
            ["BF-X-204", "K in BF-R-008", "BF-R-008", "K", "2210.0", "abc", "Bruker S1 TITAN"],
        ]
        (EXAMPLES / "xrf-with-problems.csv").write_bytes(csv_bytes(xrf_headers, problem_rows))
