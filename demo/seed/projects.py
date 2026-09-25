"""Seed the development database with projects that exercise every state of the project
overview page.

Development only. Creates the standard sign-in accounts and three projects:

- a fully described, active project with datasets, samples and measurements spread over
  three years, a large team, funding and identifiers;
- a brand-new private project with nothing but a name, owned by ``regular.user``;
- a sparse public project with a very long title, one dataset and one contributor.

Safe to run twice: it removes the projects it created before creating them again.
"""

import random
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand

from fairdm.management.commands.create_dev_accounts import EXAMPLE_ACCOUNTS as ACCOUNTS
from django.db import transaction
from django.utils import timezone
from guardian.shortcuts import assign_perm
from licensing.models import License
from partial_date import PartialDate
from literature.models import LiteratureItem
from research_vocabs.models import Concept, Vocabulary

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
    WaterSampleFactory,
    XRFMeasurementFactory,
)
from fairdm.contrib.contributors.models import Organization, Person
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
    DatasetLiteratureRelation,
)
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import (
    Project,
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility

SHOWCASE = "Thermal regime and groundwater flow of the Upper Rhine Graben"
EMPTY = "Soil carbon pilot"
SPARSE = (
    "A long-running intercomparison of low-temperature thermochronology laboratories "
    "across central Europe, and what their disagreements tell us about sample preparation"
)
SEEDED_NAMES = [SHOWCASE, EMPTY, SPARSE]


PROJECT_PERMISSIONS = [
    "view_project",
    "change_project",
    "delete_project",
    "change_project_metadata",
    "change_project_settings",
]

KEYWORDS = [
    ("geothermal-energy", "Geothermal energy"),
    ("groundwater", "Groundwater"),
    ("heat-flow", "Heat flow"),
    ("hydrogeology", "Hydrogeology"),
    ("rift-basins", "Rift basins"),
    ("geochemistry", "Geochemistry"),
]

ABSTRACT = (
    "The Upper Rhine Graben is one of the most promising regions in Europe for deep "
    "geothermal energy, yet the way heat moves through it is still poorly constrained. "
    "This project combines borehole temperature logs, rock and water geochemistry and "
    "numerical models to map where heat is carried by conduction and where groundwater "
    "flow redistributes it.\n\n"
    "All samples, measurements and derived temperature models are published openly as "
    "they are quality-checked, so that operators, regulators and other research groups "
    "can build on them."
)
OBJECTIVES = (
    "1. Compile a consistent, quality-controlled database of subsurface temperatures.\n"
    "2. Measure thermal conductivity and radiogenic heat production on core samples.\n"
    "3. Characterise deep groundwater chemistry to trace flow paths.\n"
    "4. Build and publish a 3D thermal model of the graben."
)
BACKGROUND = (
    "Earlier temperature compilations for the region mix measurement types of very "
    "different quality, and few of them are openly available. Several operators have "
    "since released borehole data, which makes a consistent reassessment possible."
)
EXPECTED_OUTPUT = (
    "Open datasets of rock properties and water chemistry, a harmonised temperature "
    "database, and a 3D thermal model with documented uncertainties."
)

PEOPLE = [
    ("Anna", "Keller", ["Creator", "ProjectLeader"]),
    ("Tomás", "Oliveira", ["Creator", "ProjectManager", "ContactPerson"]),
    ("Lea", "Brandt", ["Creator", "ProjectMember"]),
    ("Yusuf", "Demir", ["ProjectMember"]),
    ("Chloé", "Martin", ["ProjectMember"]),
    ("Jonas", "Weber", ["ProjectMember"]),
    ("Mei", "Tanaka", ["ProjectMember"]),
    ("Pieter", "de Vries", ["ProjectMember"]),
    ("Sofia", "Rossi", ["ProjectMember"]),
    ("Lukas", "Hofmann", ["ProjectMember"]),
    ("Ingrid", "Lund", ["ProjectMember"]),
    ("Omar", "Haddad", ["Other"]),
]

DATASETS = [
    # name, visibility, published, sample factory, measurement factories
    ("Core samples from the Soultz-sous-Forêts boreholes", Visibility.PUBLIC, True,
     RockSampleFactory, [XRFMeasurementFactory]),
    ("Thermal conductivity of Buntsandstein sandstones", Visibility.PUBLIC, True,
     RockSampleFactory, [XRFMeasurementFactory]),
    ("Deep groundwater chemistry, Rittershoffen and Landau", Visibility.PUBLIC, True,
     WaterSampleFactory, [ICP_MS_MeasurementFactory]),
    ("Shallow soil gas survey, Bruchsal", Visibility.PUBLIC, False,
     SoilSampleFactory, [ICP_MS_MeasurementFactory]),
    ("Borehole temperature logs (quality-controlled)", Visibility.PRIVATE, False,
     RockSampleFactory, []),
    ("Spring water sampling campaign 2026", Visibility.PRIVATE, False,
     WaterSampleFactory, [ICP_MS_MeasurementFactory]),
]


class ProjectSeed(BaseCommand):
    help = "Seed projects that exercise every state of the project overview page (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(20260924)
        call_command("seed_licenses", verbosity=0)
        users = self.accounts()
        # Datasets first: a project with public datasets refuses to be deleted.
        Dataset.all_objects.filter(project__name__in=SEEDED_NAMES).delete()
        Project.objects.filter(name__in=SEEDED_NAMES).delete()
        keywords = self.keywords()
        self.showcase(users, keywords)
        self.empty(users)
        self.sparse(users)
        self.dataset_metadata(users, keywords)
        self.stdout.write(self.style.SUCCESS("Seeded the project and dataset overview states."))

    def accounts(self):
        users = {}
        for email, first, last, staff, superuser in ACCOUNTS:
            user = Person.objects.filter(email=email).first()
            if user is None:
                user = Person.objects.create_user(
                    email=email, password="password", first_name=first, last_name=last
                )
            user.first_name, user.last_name = first, last
            user.name = f"{first} {last}"
            user.is_staff, user.is_superuser = staff, superuser
            user.set_password("password")
            user.save()
            users[email.split("@")[0]] = user
        return users

    def keywords(self):
        vocabulary, _ = Vocabulary.objects.get_or_create(
            name="demo-research-topics",
            defaults={
                "label": "Research topics",
                "uri": "https://www.fairdm.org/vocabularies/demo-research-topics",
            },
        )
        concepts = []
        for name, label in KEYWORDS:
            concept, _ = Concept.objects.get_or_create(
                vocabulary=vocabulary,
                name=name,
                defaults={"label": label, "uri": f"{vocabulary.uri}/{name}"},
            )
            concepts.append(concept)
        return concepts

    def person(self, first, last):
        email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.org"
        person = Person.objects.filter(email=email).first()
        if person is None:
            person = Person.objects.create_user(
                email=email, first_name=first, last_name=last
            )
            person.name = f"{first} {last}"
            person.save()
        return person

    def organization(self, name):
        organization, _ = Organization.objects.get_or_create(name=name)
        return organization

    def backdate(self, queryset, start, end):
        span = (end - start).days
        for pk in queryset.values_list("pk", flat=True):
            # Weighted towards the later part of the project, as collection ramps up.
            offset = int(span * random.random() ** 0.6)
            queryset.model.objects.filter(pk=pk).update(added=start + timedelta(days=offset))

    def showcase(self, users, keywords):
        owner = self.organization("Karlsruhe Institute of Technology")
        project = Project.objects.create(
            name=SHOWCASE,
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
            created_by=users["super.user"],
            funding=[
                {
                    "funderName": "Deutsche Forschungsgemeinschaft",
                    "funderIdentifier": "https://ror.org/018mejw64",
                    "funderIdentifierType": "ROR",
                    "awardNumber": "461295877",
                    "awardTitle": "Heat transport in the Upper Rhine Graben",
                    "awardURI": "https://gepris.dfg.de/gepris/projekt/461295877",
                },
                {
                    "funderName": "European Commission",
                    "funderIdentifier": "https://ror.org/00k4n6c32",
                    "funderIdentifierType": "ROR",
                    "awardNumber": "101084623",
                    "awardTitle": "Horizon Europe — Geothermal resource characterisation",
                },
            ],
        )
        project.keywords.set(keywords)
        for type_, value in [
            ("Abstract", ABSTRACT),
            ("Objectives", OBJECTIVES),
            ("Background", BACKGROUND),
            ("ExpectedOutput", EXPECTED_OUTPUT),
        ]:
            ProjectDescription.objects.create(related=project, type=type_, value=value)
        ProjectDate.objects.create(related=project, type="Start", value=PartialDate("2024-03-01"))
        ProjectDate.objects.create(related=project, type="End", value=PartialDate("2028-02-29"))
        ProjectIdentifier.objects.create(related=project, type="DOI", value="10.5880/fairdm.2024.001")
        ProjectIdentifier.objects.create(related=project, type="GRANT_NUMBER", value="DFG 461295877")

        for first, last, roles in PEOPLE:
            project.add_contributor(self.person(first, last), with_roles=roles)
        project.add_contributor(owner, with_roles=["Other"])
        project.add_contributor(users["super.user"], with_roles=["ProjectManager"])
        for permission in PROJECT_PERMISSIONS:
            assign_perm(f"project.{permission}", users["staff.user"], project)

        start = timezone.now() - timedelta(days=int(365 * 2.5))
        now = timezone.now()
        licenses = list(License.objects.all())
        for index, (name, visibility, published, sample_factory, measurement_factories) in enumerate(DATASETS):
            dataset = Dataset.all_objects.create(
                name=name,
                project=project,
                visibility=visibility,
                published=published,
                license=licenses[index % len(licenses)] if licenses else None,
                created_by=users["super.user"],
            )
            samples = [
                sample_factory(dataset=dataset, name=f"{name.split()[0]}-{n:03d}")
                for n in range(random.randint(12, 40))
            ]
            for sample in samples:
                for factory in measurement_factories:
                    for _ in range(random.randint(1, 3)):
                        factory(sample=sample, dataset=dataset)
            self.backdate(Sample.objects.filter(dataset=dataset), start, now)
            self.backdate(Measurement.objects.filter(dataset=dataset), start + timedelta(days=60), now)
            Dataset.all_objects.filter(pk=dataset.pk).update(
                added=start + timedelta(days=90 * index),
                modified=now - timedelta(days=random.randint(1, 120)),
            )
        Project.objects.filter(pk=project.pk).update(added=start, modified=now - timedelta(days=2))

    def empty(self, users):
        project = Project.objects.create(
            name=EMPTY,
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            created_by=users["regular.user"],
        )
        project.add_contributor(users["regular.user"], with_roles=["Creator"])
        for permission in PROJECT_PERMISSIONS:
            assign_perm(f"project.{permission}", users["regular.user"], project)

    def sparse(self, users):
        project = Project.objects.create(
            name=SPARSE,
            status=ProjectStatus.SEARCHING_FOR_COLLABORATORS,
            visibility=Visibility.PUBLIC,
            owner=self.organization("Universität Tübingen"),
            created_by=users["super.user"],
        )
        ProjectDescription.objects.create(
            related=project,
            type="Abstract",
            value=(
                "We are looking for laboratories willing to date a shared set of apatite "
                "and zircon reference samples, so that inter-laboratory differences can be "
                "traced to specific preparation steps."
            ),
        )
        person = self.person("Hannah", "Vogel")
        project.add_contributor(person, with_roles=["Creator", "ProjectLeader", "ContactPerson"])
        dataset = Dataset.all_objects.create(
            name="Round 1 reference ages", project=project, visibility=Visibility.PUBLIC
        )
        for n in range(3):
            RockSampleFactory(dataset=dataset, name=f"REF-{n + 1:02d}")
        Dataset.all_objects.create(
            name="Round 2 reference ages (draft)",
            project=project,
            visibility=Visibility.PRIVATE,
            license=None,
            created_by=users["super.user"],
        )

    def literature(self, key, title, year, doi, kind="article-journal"):
        item, _ = LiteratureItem.objects.get_or_create(
            citation_key=key,
            defaults={
                "item": {
                    "type": kind,
                    "title": title,
                    "DOI": doi,
                    "issued": {"date-parts": [[year]]},
                }
            },
        )
        return item

    def dataset_metadata(self, users, keywords):
        """Dataset-level metadata for the showcase's datasets, so each access state has a fully
        described example: the Soultz cores (published), the Bruchsal soil gas survey (public,
        data not released) and the borehole logs (private)."""
        showcase = Project.objects.get(name=SHOWCASE)
        people = {p.last_name: p for p in Person.objects.filter(email__endswith="@example.org")}
        for dataset in Dataset.all_objects.filter(project=showcase):
            for permission in ("view_dataset", "change_dataset", "delete_dataset"):
                assign_perm(f"dataset.{permission}", users["staff.user"], dataset)

        cores = Dataset.all_objects.get(project=showcase, name__startswith="Core samples")
        cores.keywords.set(keywords[:3] + keywords[5:])
        DatasetDescription.objects.create(
            related=cores,
            type="Abstract",
            value=(
                "Rock cores recovered from the GPK and EPS boreholes at Soultz-sous-Forêts, "
                "between 1.4 and 5 km depth, with their X-ray fluorescence major and trace "
                "element geochemistry. The cores span the sedimentary cover and the granite "
                "basement and were sampled to constrain radiogenic heat production."
            ),
        )
        DatasetDescription.objects.create(
            related=cores,
            type="Methods",
            value=(
                "Core sections were cut at roughly 25 m intervals, crushed and milled to below "
                "63 µm. Fused beads were measured on a wavelength-dispersive XRF spectrometer; "
                "values below the detection limit are reported as the limit itself and flagged."
            ),
        )
        DatasetDescription.objects.create(
            related=cores,
            type="TechnicalInfo",
            value="Concentrations are in ppm by mass. Depths are measured depth along hole.",
        )
        for type_, value in [
            ("CollectionStart", "2024-05-02"),
            ("CollectionEnd", "2025-10-17"),
            ("Submitted", "2026-01-20"),
            ("Published", "2026-03-04"),
            ("Available", "2026-03-04"),
        ]:
            DatasetDate.objects.create(related=cores, type=type_, value=PartialDate(value))
        DatasetIdentifier.objects.create(related=cores, type="DOI", value="10.5880/fairdm.2026.014")
        cores.add_contributor(people["Keller"], with_roles=["Creator", "Supervisor"])
        cores.add_contributor(people["Brandt"], with_roles=["Creator", "DataCollector"])
        cores.add_contributor(people["Demir"], with_roles=["Creator", "Researcher"])
        cores.add_contributor(people["Oliveira"], with_roles=["ContactPerson", "DataManager"])
        cores.add_contributor(people["Tanaka"], with_roles=["DataCurator"])
        cores.add_contributor(people["Weber"], with_roles=["DataCollector"])
        for key, title, year, doi, relation in [
            (
                "brandt2026heat",
                "Radiogenic heat production of the Soultz granite from 3.5 km of core",
                2026,
                "10.1016/j.geothermics.2026.103112",
                "IsDescribedBy",
            ),
            (
                "keller2025graben",
                "Conductive and advective heat transport in the Upper Rhine Graben",
                2025,
                "10.1029/2025JB031442",
                "IsCitedBy",
            ),
            (
                "genter2010soultz",
                "Contribution of the exploration of deep crystalline fractured reservoir of "
                "Soultz to the knowledge of enhanced geothermal systems",
                2010,
                "10.1016/j.crte.2010.01.006",
                "Cites",
            ),
        ]:
            DatasetLiteratureRelation.objects.create(
                dataset=cores,
                literature_item=self.literature(key, title, year, doi),
                relationship_type=relation,
            )

        soil = Dataset.all_objects.get(project=showcase, name__startswith="Shallow soil gas")
        DatasetDescription.objects.create(
            related=soil,
            type="Abstract",
            value=(
                "Soil gas and soil chemistry along two transects across the eastern "
                "boundary fault near Bruchsal, to test whether fluid pathways reach the surface."
            ),
        )
        DatasetDate.objects.create(related=soil, type="CollectionStart", value=PartialDate("2025-06"))
        soil.add_contributor(people["Martin"], with_roles=["Creator", "ContactPerson"])
        soil.add_contributor(people["Hofmann"], with_roles=["DataCollector"])
