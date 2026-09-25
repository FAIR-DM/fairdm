"""Seed the development database with measurements that exercise every state of the measurement
overview page.

Development only. Creates the standard sign-in accounts, one project, three datasets and a rock
sample, then:

- an XRF measurement with its setup, conditions and take-down recorded, a DOI and three people
  credited — XRF has its own overview template, so this shows the extended page;
- an ICP-MS measurement made on the same sample but recorded in a partner laboratory's dataset —
  a type with no template of its own, so this shows the generic page alone;
- a bare XRF measurement below its detection limit, with nothing else recorded;
- a measurement in an unpublished dataset, which only that dataset's team can open.

Safe to run twice: it removes what it created before creating it again.
"""

from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand

from fairdm.management.commands.create_dev_accounts import EXAMPLE_ACCOUNTS as ACCOUNTS
from django.db import transaction
from guardian.shortcuts import assign_perm
from licensing.models import License
from partial_date import PartialDate

from demo.factories import ICP_MS_MeasurementFactory, RockSampleFactory, XRFMeasurementFactory
from fairdm.contrib.contributors.models import Person
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

PROJECT = "Measurement page examples"



class MeasurementSeed(BaseCommand):
    help = "Seed measurements that exercise every state of the measurement overview page (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_licenses", verbosity=0)
        users = self.accounts()
        # Datasets first: a project with public datasets refuses to be deleted.
        Dataset.all_objects.filter(project__name=PROJECT).delete()
        Project.objects.filter(name=PROJECT).delete()
        MeasurementIdentifier.objects.filter(value="10.60510/FDM.XRF.2025.0412").delete()

        project = Project.objects.create(
            name=PROJECT, status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC
        )
        licence = License.objects.first()
        cores = self.dataset(project, "Soultz cores, XRF geochemistry", licence, published=True)
        lab = self.dataset(project, "Partner laboratory ICP-MS runs", licence, published=True)
        pending = self.dataset(project, "Soultz cores, 2026 reruns (in progress)", licence, published=False)
        for dataset in (cores, lab, pending):
            for permission in ("view_dataset", "change_dataset"):
                assign_perm(f"dataset.{permission}", users["staff.user"], dataset)

        sample = RockSampleFactory(dataset=cores, name="GPK-2 core, 3512 m", local_id="GPK2-C14-3512")

        full = XRFMeasurementFactory(
            sample=sample,
            dataset=cores,
            name="Fe, fused bead, run 412",
            local_id="XRF-2025-0412",
            element="Fe",
            concentration_ppm=Decimal("38214.50"),
            detection_limit_ppm=Decimal("12.00"),
            instrument_model="Bruker S8 Tiger",
            measurement_conditions="Rh tube, 50 kV, 50 mA, vacuum, LiF200 crystal.",
        )
        for type_, value in [("Setup", "2025-06-10"), ("TearDown", "2025-06-11")]:
            MeasurementDate.objects.create(related=full, type=type_, value=PartialDate(value))
        for type_, value in [
            ("MeasurementSetup", "Calibrated against GA and GS-N reference materials the same morning."),
            ("MeasurementConditions", "Fused bead of 0.6 g sample with 6 g lithium borate; loss on ignition determined separately."),
            ("MeasurementTearDown", "Bead archived with the sample; drift check on GA at the end of the run was within 0.8 %."),
            ("Other", "The core is partly altered at this depth, which raises Fe relative to fresh granite."),
        ]:
            MeasurementDescription.objects.create(related=full, type=type_, value=value)
        MeasurementIdentifier.objects.create(related=full, type="DOI", value="10.60510/FDM.XRF.2025.0412")
        full.add_contributor(self.person("Jonas", "Weber"), with_roles=["MeasurementPreparation"])
        full.add_contributor(self.person("Lea", "Brandt"), with_roles=["MeasurementCollection"])
        full.add_contributor(self.person("Mei", "Tanaka"), with_roles=["Support"])

        for element in ("Si", "Al", "Ca", "K", "Mg", "Ti", "Mn", "Na", "P"):
            XRFMeasurementFactory(sample=sample, dataset=cores, name=f"{element}, fused bead, run 412", element=element)
        other_lab = ICP_MS_MeasurementFactory(sample=sample, dataset=lab, name="206Pb/238U, spot 3")
        other_lab.add_contributor(self.person("Pieter", "de Vries"), with_roles=["MeasurementCollection"])
        bare = XRFMeasurementFactory(
            sample=sample,
            dataset=cores,
            name="Cr, fused bead, run 412",
            element="Cr",
            concentration_ppm=Decimal("9.10"),
            detection_limit_ppm=Decimal("10.00"),
        )
        hidden = XRFMeasurementFactory(sample=sample, dataset=pending, name="Fe, fused bead, rerun 17", element="Fe")

        for label, measurement in [
            ("XRF, fully described (extended page)", full),
            ("ICP-MS in a partner dataset (generic page)", other_lab),
            ("XRF, below detection limit, nothing else recorded", bare),
            ("XRF in an unpublished dataset", hidden),
        ]:
            self.stdout.write(f"{label}: {measurement.get_absolute_url()}")

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
            name=name, project=project, visibility=Visibility.PUBLIC, published=published, license=licence
        )
