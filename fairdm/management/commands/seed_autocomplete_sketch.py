"""SKETCH ONLY. Seed the records the autocomplete sketch needs, for the dev server.

Idempotent: every record is found by name before it is made. Removed before the build merges.

    python manage.py seed_autocomplete_sketch
"""

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.core.models import Dataset, Project
from fairdm.core.sample.models import SampleIdentifier
from fairdm.utils.choices import Visibility

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

GHOSTS = [("Heinrich", "Albrecht"), ("Margarethe", "Lindqvist-Bergström")]

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


class Command(BaseCommand):
    help = "Seed the records the autocomplete sketch needs."

    @transaction.atomic
    def handle(self, *args, **options):
        regular = Person.objects.get(email="regular.user@example.com")

        orgs = {}
        for name, city, country, ror in ORGANIZATIONS:
            org, _ = Organization.objects.get_or_create(
                name=name, defaults={"city": city, "country": country}
            )
            orgs[name] = org
            ContributorIdentifier.objects.get_or_create(
                related=org, type="ROR", defaults={"value": ror}
            )

        Affiliation.objects.get_or_create(
            person=regular,
            organization=orgs["GFZ Helmholtz Centre for Geosciences"],
            defaults={"is_primary": True, "type": Affiliation.MembershipType.MEMBER},
        )
        Affiliation.objects.get_or_create(
            person=regular,
            organization=orgs["University of Potsdam"],
            defaults={"type": Affiliation.MembershipType.MEMBER},
        )

        people = []
        for first, last, orcid, org_name in PEOPLE:
            person = Person.objects.filter(first_name=first, last_name=last).first()
            if person is None:
                person = Person.objects.create_unclaimed(first, last)
                person.is_claimed = True
                person.save()
            Affiliation.objects.get_or_create(
                person=person,
                organization=orgs[org_name],
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
        for first, last in GHOSTS:
            if not Person.objects.filter(first_name=first, last_name=last).exists():
                Person.objects.create_unclaimed(first, last)

        # Regular user's own records, with names close to public ones.
        internal, _ = Project.objects.get_or_create(
            name="Alpine groundwater survey",
            defaults={"visibility": Visibility.PRIVATE},
        )
        public_project, _ = Project.objects.get_or_create(
            name="Alpine groundwater atlas", defaults={"visibility": Visibility.PUBLIC}
        )
        Contribution.add_to(regular, internal)
        Contribution.objects.filter(
            contributor=regular, object_id=str(internal.pk)
        ).update(level=ContributionLevel.MANAGE)
        for person in people[:3]:
            Contribution.add_to(person, internal)
            Contribution.add_to(person, public_project)

        datasets = [
            ("Alpine springs 2025 field season", internal, Visibility.PRIVATE, False),
            ("Alpine springs 2025 lab results", internal, Visibility.PRIVATE, False),
            ("Alpine springs 2024", public_project, Visibility.PUBLIC, True),
            ("Alpine springs 2023", public_project, Visibility.PUBLIC, True),
            ("Alpine springs isotopes", public_project, Visibility.PUBLIC, False),
        ]
        for i in range(1, 26):
            datasets.append(
                (
                    f"Borehole temperature log {i:02d}",
                    public_project,
                    Visibility.PUBLIC,
                    True,
                )
            )
        made = {}
        for name, project, visibility, published in datasets:
            ds, _ = Dataset.all_objects.get_or_create(
                name=name,
                defaults={
                    "project": project,
                    "visibility": visibility,
                    "published": published,
                },
            )
            made[name] = ds

        # A long name, to see truncation.
        Dataset.all_objects.get_or_create(
            name="Hydrochemistry of high alpine springs in the Bernese Oberland and the "
            "Valais, including repeat sampling after the 2024 glacial outburst event",
            defaults={
                "project": public_project,
                "visibility": Visibility.PUBLIC,
                "published": True,
            },
        )

        # Samples with local IDs and IGSNs in the regular user's dataset.
        from fairdm.registry import registry

        sample_model = next(
            (m for m in registry.samples if m._meta.model_name == "rocksample"), None
        )
        if sample_model is not None:
            target = made["Alpine springs 2025 field season"]
            for i in range(1, 13):
                name = f"Spring AS-{i:03d}"
                sample = sample_model.objects.filter(name=name).first()
                if sample is None:
                    sample = sample_model.objects.create(
                        name=name,
                        dataset=target,
                        local_id=f"AS25-{i:03d}",
                        rock_type="granite",
                        collection_date=datetime.date(2025, 7, i),
                    )
                if i <= 3:
                    SampleIdentifier.objects.get_or_create(
                        related=sample,
                        type="IGSN",
                        defaults={"value": f"10.58052/IEAS25{i:04d}"},
                    )

        made["Alpine springs 2025 field season"].tags.add(
            "groundwater", "springs", "hydrochemistry"
        )
        made["Alpine springs 2024"].tags.add(
            "groundwater", "isotopes", "glacial meltwater"
        )

        from literature.models import LiteratureItem

        for title, authors, year, doi in PUBLICATIONS:
            if LiteratureItem.objects.filter(title=title).exists():
                continue
            LiteratureItem.objects.create(
                type="article-journal",
                title=title,
                item={
                    "type": "article-journal",
                    "title": title,
                    "author": [{"family": a, "given": ""} for a in authors],
                    "issued": {"date-parts": [[year]]},
                    "DOI": doi,
                },
            )

        self.stdout.write(self.style.SUCCESS("Seeded the autocomplete sketch records."))
