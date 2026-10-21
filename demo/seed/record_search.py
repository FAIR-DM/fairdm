"""Development data for the record search fields.

Seeds what a walkthrough of the search fields needs: organizations with ROR identifiers, people with
ORCIDs and two nobody has claimed, a private project and two private datasets that
``regular.user@example.com`` manages, public datasets, rock samples with local IDs and IGSNs,
publications with DOIs, and tags. ``--large`` adds a public dataset of 100,000 samples, to see how
fast the sample field answers on a portal that size.
"""

import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from literature.models import LiteratureItem

from demo.models import RockSample
from demo.seed.common import example_accounts, grant_team_rights
from fairdm.contrib.contributors.models import (
    Affiliation,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample, SampleIdentifier
from fairdm.utils.choices import Visibility

LARGE_SAMPLE_COUNT = 100_000
LARGE_DATASET = "Large sample collection"
BATCH_SIZE = 5_000

ORGANIZATIONS = [
    ("GFZ Helmholtz Centre for Geosciences", "Potsdam", "DE", "04z8jg394"),
    ("University of Potsdam", "Potsdam", "DE", "03bnmw459"),
    ("Freie Universität Berlin", "Berlin", "DE", "046ak2485"),
    ("Technische Universität Berlin", "Berlin", "DE", "03v4gjf40"),
    ("Alfred Wegener Institute", "Bremerhaven", "DE", "032e6b942"),
    ("British Geological Survey", "Keyworth", "GB", "04a7gbp98"),
    ("University of Leeds", "Leeds", "GB", "024mrxd33"),
    ("ETH Zurich", "Zurich", "CH", "05a28rw58"),
    ("University of Bern", "Bern", "CH", "02k7v4d05"),
    ("Geological Survey of Norway", "Trondheim", "NO", "01kwkqc60"),
    ("Utrecht University", "Utrecht", "NL", "04pp8hn57"),
    ("Institut de Physique du Globe de Paris", "Paris", "FR", "004gzqz66"),
]

PEOPLE = [
    ("Amara", "Okafor", "0000-0002-1825-0097", "GFZ Helmholtz Centre for Geosciences"),
    ("Jonas", "Weber", "0000-0001-5109-3700", "University of Potsdam"),
    ("Lena", "Fischer", "", "Freie Universität Berlin"),
    ("Mateo", "Rossi", "0000-0003-1419-2405", "ETH Zurich"),
    ("Ingrid", "Halvorsen", "", "Geological Survey of Norway"),
    ("Priya", "Raman", "0000-0002-9079-593X", "University of Leeds"),
]

UNCLAIMED = [("Heinrich", "Albrecht"), ("Margarethe", "Lindqvist-Bergström")]

PUBLICATIONS = [
    (
        "Alpine spring chemistry across three seasons",
        ["Okafor", "Weber", "Fischer"],
        2024,
        "10.5880/gfz.2024.011",
    ),
    (
        "Groundwater residence times in fractured granite",
        ["Rossi"],
        2023,
        "10.1029/2023wr034512",
    ),
    (
        "A global database of heat flow measurements",
        ["Raman", "Halvorsen"],
        2021,
        "10.5880/fidgeo.2021.014",
    ),
    (
        "Isotopic tracers of meltwater in high mountain catchments",
        ["Weber", "Okafor"],
        2022,
        "10.1016/j.jhydrol.2022.127845",
    ),
    (
        "Hydrochemical survey of the Bernese Oberland",
        ["Rossi", "Fischer"],
        2020,
        "10.5194/hess-24-1234-2020",
    ),
]

PRIVATE_PROJECT = "Alpine groundwater survey"
PUBLIC_PROJECT = "Alpine groundwater atlas"
PRIVATE_DATASETS = [
    "Alpine springs 2025 field season",
    "Alpine springs 2025 lab results",
]
PUBLIC_DATASETS = [
    ("Alpine springs 2024", True),
    ("Alpine springs 2023", True),
    ("Alpine springs isotopes", False),
]


class RecordSearchSeed:
    """Seed the records the search fields are walked through with.

    Every record is found by name before it is made, so running the seed twice adds nothing.

    Args:
        stdout: Where to report progress.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    @transaction.atomic
    def handle(self, large=False):
        """Seed the walkthrough records, and the large dataset when asked.

        Args:
            large: Whether to add a public dataset of 100,000 samples.
        """
        regular = example_accounts()["regular.user"]
        organizations = self.organizations()
        self.affiliate(regular, organizations)
        people = self.people(organizations)
        datasets = self.projects_and_datasets(regular, people)
        self.samples(datasets[PRIVATE_DATASETS[0]])
        self.publications()
        datasets[PRIVATE_DATASETS[0]].tags.add(
            "groundwater", "springs", "hydrochemistry"
        )
        datasets[PUBLIC_DATASETS[0][0]].tags.add(
            "groundwater", "isotopes", "glacial meltwater"
        )
        if large:
            self.large_dataset()

    def organizations(self):
        """Return the organizations by name, each with its ROR identifier."""
        made = {}
        for name, city, country, ror in ORGANIZATIONS:
            organization = Organization.objects.filter(name=name).first()
            if organization is None:
                organization = Organization.objects.create(
                    name=name, city=city, country=country
                )
            ContributorIdentifier.objects.get_or_create(
                related=organization, type="ROR", defaults={"value": ror}
            )
            made[name] = organization
        return made

    def affiliate(self, person, organizations):
        """Make a person a member of two organizations, the first of them primary."""
        for name, is_primary in (
            ("GFZ Helmholtz Centre for Geosciences", True),
            ("University of Potsdam", False),
        ):
            Affiliation.objects.get_or_create(
                person=person,
                organization=organizations[name],
                defaults={
                    "is_primary": is_primary,
                    "type": Affiliation.MembershipType.MEMBER,
                },
            )

    def people(self, organizations):
        """Return the claimed people, and create the two nobody has claimed."""
        people = []
        for first, last, orcid, organization in PEOPLE:
            person = Person.objects.filter(first_name=first, last_name=last).first()
            if person is None:
                person = Person.objects.create_unclaimed(first, last)
                person.is_claimed = True
                person.save()
            Affiliation.objects.get_or_create(
                person=person,
                organization=organizations[organization],
                defaults={
                    "is_primary": True,
                    "type": Affiliation.MembershipType.MEMBER,
                },
            )
            if orcid:
                ContributorIdentifier.objects.get_or_create(
                    related=person, type="ORCID", defaults={"value": orcid}
                )
            people.append(person)
        for first, last in UNCLAIMED:
            if not Person.objects.filter(first_name=first, last_name=last).exists():
                Person.objects.create_unclaimed(first, last)
        return people

    def projects_and_datasets(self, regular, people):
        """Return the datasets by name: two private ones the regular user manages and public ones."""
        private, _ = Project.objects.get_or_create(
            name=PRIVATE_PROJECT, defaults={"visibility": Visibility.PRIVATE}
        )
        public, _ = Project.objects.get_or_create(
            name=PUBLIC_PROJECT, defaults={"visibility": Visibility.PUBLIC}
        )
        grant_team_rights(regular, private)
        for person in people[:3]:
            person.add_to(private)
            person.add_to(public)
        datasets = {}
        wanted = [
            (name, private, Visibility.PRIVATE, False) for name in PRIVATE_DATASETS
        ]
        wanted += [
            (name, public, Visibility.PUBLIC, published)
            for name, published in PUBLIC_DATASETS
        ]
        for name, project, visibility, published in wanted:
            dataset, _ = Dataset.all_objects.get_or_create(
                name=name,
                defaults={
                    "project": project,
                    "visibility": visibility,
                    "published": published,
                },
            )
            datasets[name] = dataset
        grant_team_rights(regular, *(datasets[name] for name in PRIVATE_DATASETS))
        return datasets

    def samples(self, dataset):
        """Add twelve rock samples with local IDs to a dataset, the first three with an IGSN."""
        for number in range(1, 13):
            name = f"Spring AS-{number:03d}"
            sample = RockSample.objects.filter(name=name, dataset=dataset).first()
            if sample is None:
                sample = RockSample.objects.create(
                    name=name,
                    dataset=dataset,
                    local_id=f"AS25-{number:03d}",
                    rock_type="granite",
                    collection_date=datetime.date(2025, 7, number),
                )
            if number <= 3:
                SampleIdentifier.objects.get_or_create(
                    related=sample,
                    type="IGSN",
                    defaults={"value": f"10.58052/IEAS25{number:04d}"},
                )

    def publications(self):
        """Add the publications, each with authors, a year and a DOI."""
        for title, authors, year, doi in PUBLICATIONS:
            if LiteratureItem.objects.filter(title=title).exists():
                continue
            LiteratureItem.objects.create(
                type="article-journal",
                title=title,
                item={
                    "type": "article-journal",
                    "title": title,
                    "author": [{"family": author, "given": ""} for author in authors],
                    "issued": {"date-parts": [[year]]},
                    "DOI": doi,
                },
            )

    def large_dataset(self, count=LARGE_SAMPLE_COUNT):
        """Add a public dataset holding ``count`` rock samples, written in batches.

        The samples are inserted in bulk, as a base row and a rock row each, because creating
        a hundred thousand through the model takes minutes. A second run adds only what is missing.

        Args:
            count: How many samples the dataset should hold.

        Returns:
            The dataset.
        """
        project, _ = Project.objects.get_or_create(
            name=PUBLIC_PROJECT, defaults={"visibility": Visibility.PUBLIC}
        )
        dataset, _ = Dataset.all_objects.get_or_create(
            name=LARGE_DATASET,
            defaults={
                "project": project,
                "visibility": Visibility.PUBLIC,
                "published": True,
            },
        )
        rock_type = ContentType.objects.get_for_model(RockSample)
        held = Sample.objects.filter(dataset=dataset).count()
        for start in range(held + 1, count + 1, BATCH_SIZE):
            stop = min(start + BATCH_SIZE, count + 1)
            created = Sample.objects.bulk_create(
                [
                    Sample(
                        name=f"Core sample {number:06d}",
                        local_id=f"LC-{number:06d}",
                        dataset=dataset,
                        polymorphic_ctype=rock_type,
                    )
                    for number in range(start, stop)
                ]
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {RockSample._meta.db_table} "
                    "(sample_ptr_id, rock_type, mineral_content, collection_date) "
                    "SELECT unnest(%s::bigint[]), 'granite', '', %s",
                    [[sample.pk for sample in created], datetime.date(2025, 7, 1)],
                )
            self.stdout.write(f"  {stop - 1:,} of {count:,} samples")
        return dataset
