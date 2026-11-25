"""Prototype: seed the records the Contributors page prototype is judged on.

``regular.user`` manages a project, a dataset and a sample with a full set of people and
organizations. ``regular.user2`` manages a new dataset with nobody else on it, and can only view
the project. Run again to start over: the seeded records are replaced.
"""

from controlled_vocabularies.models import Record
from django.core.management.base import BaseCommand
from django.db import transaction

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Affiliation, Contribution, Organization, Person
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

TAG = "[contributors prototype]"

ORGANIZATIONS = [
    ("University of Oslo", "Oslo", "NO"),
    ("Norwegian Polar Institute", "Tromsø", "NO"),
    ("GFZ Helmholtz Centre for Geosciences", "Potsdam", "DE"),
    ("Alfred Wegener Institute, Helmholtz Centre for Polar and Marine Research", "Bremerhaven", "DE"),
    ("University Centre in Svalbard", "Longyearbyen", "NO"),
    ("ETH Zurich", "Zürich", "CH"),
    ("Research Council of Norway", "Oslo", "NO"),
]

# (given, family, [(organization, current?)], affiliation on the record, roles)
PEOPLE = [
    ("Ingrid", "Halvorsen", [("University of Oslo", True)], "University of Oslo", ["Project Leader", "Creator"]),
    ("Tomasz", "Wiśniewski", [("Norwegian Polar Institute", False), ("GFZ Helmholtz Centre for Geosciences", True)], "Norwegian Polar Institute", ["Project Member", "Creator"]),
    ("Amara", "Okonkwo-Lindqvist", [("Alfred Wegener Institute, Helmholtz Centre for Polar and Marine Research", True)], "Alfred Wegener Institute, Helmholtz Centre for Polar and Marine Research", ["Project Member"]),
    ("Lukas", "Brunner", [("ETH Zurich", True)], "ETH Zurich", ["Contact Person", "Project Manager"]),
    ("Sigrid", "Nakamura", [("University Centre in Svalbard", True), ("University of Oslo", False)], "University Centre in Svalbard", ["Project Member"]),
    ("Mateo", "Alvarez", [], None, ["Other"]),
]

DATASET_PEOPLE = [
    ("Ingrid", "Halvorsen", "University of Oslo", ["Creator", "Supervisor"]),
    ("Tomasz", "Wiśniewski", "Norwegian Polar Institute", ["Data Collector", "Creator"]),
    ("Sigrid", "Nakamura", "University Centre in Svalbard", ["Data Collector"]),
    ("Lukas", "Brunner", "ETH Zurich", ["Data Curator", "Contact Person"]),
]


class Command(BaseCommand):
    """Seed the Contributors page prototype."""

    help = "Seed the records the Contributors page prototype is judged on."

    def roles(self, record, labels):
        """The offered role concepts of a record named by their labels."""
        offered = {str(role): role for role in Crediting(record).offered_roles()}
        return [offered[label] for label in labels if label in offered]

    def record(self, model, name, **fields):
        """The seeded record of that name, kept between runs so its address stays, with nobody on it."""
        manager = getattr(model, "all_objects", model.objects)
        record = manager.filter(name=name).first()
        if record is None:
            return model.objects.create(name=name, **fields)
        Contribution.objects.filter(object_id=record.pk).delete()
        for field, value in fields.items():
            setattr(record, field, value)
        record.save()
        return record

    @transaction.atomic
    def handle(self, *args, **options):
        """Build the records."""
        user = Person.objects.get(email="regular.user@example.com")
        user2 = Person.objects.get(email="regular.user2@example.com")

        # Leftovers from trying the page out.
        Organization.objects.filter(name__startswith="Svalbard Science Forum").delete()
        Organization.objects.filter(name="ETH Zürich").delete()
        Person.objects.filter(last_name="Haddad", is_claimed=False).delete()

        organizations = {}
        for name, city, country in ORGANIZATIONS:
            organizations[name], _ = Organization.objects.get_or_create(
                name=name, defaults={"city": city, "country": country}
            )

        people = {}
        for given, family, affiliations, _on_record, _roles in PEOPLE:
            person = Person.objects.filter(first_name=given, last_name=family).first()
            if person is None:
                person = Person.objects.create_unclaimed(given, family)
            for org_name, current in affiliations:
                Affiliation.objects.get_or_create(
                    person=person,
                    organization=organizations[org_name],
                    defaults={"end_date": None if current else "2023", "start_date": "2019" if not current else "2023"},
                )
            people[(given, family)] = person

        project = self.record(Project, f"Glacier meltwater chemistry on Svalbard, 2023–2025 {TAG}", visibility=Visibility.PUBLIC)
        crediting = Crediting(project)
        crediting.make_creator(user)
        mine = project.contributors.get(contributor=user)
        crediting.update(mine, roles=self.roles(project, ["Project Manager"]), organization=organizations["GFZ Helmholtz Centre for Geosciences"])
        for given, family, _affiliations, on_record, roles in PEOPLE:
            credit = crediting.add(people[(given, family)], organization=organizations.get(on_record))
            crediting.update(credit, roles=self.roles(project, roles))
        funder = crediting.add(organizations["Research Council of Norway"])
        crediting.update(funder, roles=self.roles(project, ["Other"]))
        uni = project.contributors.get(contributor=organizations["University of Oslo"])
        crediting.update(uni, roles=self.roles(project, ["Project Leader"]))
        viewer = crediting.add(user2)
        crediting.update(viewer, roles=self.roles(project, ["Project Member"]))

        dataset = self.record(Dataset, f"Proglacial river water samples, summer 2024 {TAG}", project=project, visibility=Visibility.PUBLIC)
        crediting = Crediting(dataset)
        crediting.make_creator(user)
        for given, family, on_record, roles in DATASET_PEOPLE:
            credit = crediting.add(people[(given, family)], organization=organizations.get(on_record))
            crediting.update(credit, roles=self.roles(dataset, roles))
        rights = crediting.add(organizations["University of Oslo"]) if not dataset.contributors.filter(contributor=organizations["University of Oslo"]).exists() else dataset.contributors.get(contributor=organizations["University of Oslo"])
        crediting.update(rights, roles=self.roles(dataset, ["Rights Holder"]))

        empty = self.record(Dataset, f"Pilot survey {TAG}", project=project, visibility=Visibility.PRIVATE)
        Crediting(empty).make_creator(user2)

        self.stdout.write(f"project {project.get_absolute_url()}contributors/")
        self.stdout.write(f"dataset {dataset.get_absolute_url()}contributors/")
        self.stdout.write(f"empty   {empty.get_absolute_url()}contributors/")
        _ = (ContributionLevel, Record)
