"""Development data for the contributor display components.

Seeds people and organizations that reach every state the ``c-contributor.*`` components have to
answer for: with and without a photo or logo, a wide logo, authenticated, unauthenticated and
missing ORCID iDs, a ROR ID or none, an affiliation or none, a very long name, a name in a
non-Latin script, every account state, one portal role or several, and records credited to one, a handful and many contributors. It refuses outside
development, and running it again replaces only the records it created.

    DJANGO_ENV=development python manage.py seed_contributors

The gallery at ``/dev/contributors/`` draws every component against this data.
"""

import io
import random

from allauth.socialaccount.models import SocialAccount
from django.apps import apps
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from fairdm.contrib.contributors.models import (
    Affiliation,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

SEED = "contributor-components"

PROFILE = (
    "Works on the thermal structure of the continental lithosphere, combining borehole "
    "temperature logs with thermal conductivity measurements on core samples to estimate "
    "surface heat flow and its uncertainty."
)

# first, last, preferred name override, photo, orcid state, organization keys (first is primary)
PEOPLE = [
    ("Ana Sofía", "Martínez-Ortega", "", True, "authenticated", ["gfz"]),
    ("Ben", "Wu", "", False, "unauthenticated", ["potsdam"]),
    ("", "", "李辰", False, None, ["igg"]),
    ("Maximiliane Theodora", "von Hohenzollern-Sigmaringen", "", True, None, ["potsdam", "gfz"]),
    ("Tomás", "Oliveira", "", True, "authenticated", []),
    ("Priya", "Raghunathan", "", False, None, []),
    ("Kwame", "Mensah", "", True, "unauthenticated", ["gfz"]),
    ("Sarah", "O'Connor", "", False, "authenticated", ["potsdam"]),
    ("Jonas", "Keller", "", True, None, ["gfz"]),
    ("Leila", "Haddad", "", True, "authenticated", ["igg"]),
    ("Mateo", "Rossi", "", False, None, ["gfz"]),
    ("Yuki", "Tanaka", "", True, None, []),
    ("Emre", "Demir", "", False, "unauthenticated", ["potsdam"]),
    ("Freya", "Lindqvist", "", True, None, ["gfz"]),
    ("Oluwaseun", "Adeyemi", "", True, "authenticated", []),
    ("Hannah", "Brandt", "", False, None, ["gfz"]),
    ("Diego", "Fernández", "", True, None, ["potsdam"]),
    ("Ingrid", "Solberg", "", False, None, []),
    ("Arjun", "Mehta", "", True, None, ["igg"]),
    ("Clara", "Weber", "", False, None, ["gfz"]),
    ("Nikolai", "Petrov", "", True, None, []),
    ("Amara", "Okafor", "", False, None, ["potsdam"]),
]

# index into PEOPLE: account state, portal roles held. Everyone else is a ghost profile.
ACCOUNTS = {
    0: ("claimed", ["Portal Administrator"]),
    1: ("claimed", ["Data Curator", "Community Manager"]),
    2: ("invited", []),
    3: ("claimed", []),
    4: ("claimed", ["Developer"]),
    5: ("inactive", []),
    6: ("claimed", ["Data Curator"]),
    7: ("invited", []),
}

# key: name, type, city, country, ror, logo shape (None, "square", "wide")
ORGANIZATIONS = {
    "gfz": ("GFZ Helmholtz Centre for Geosciences", "facility", "Potsdam", "DE", "04z8jg394", "wide"),
    "potsdam": ("University of Potsdam", "education", "Potsdam", "DE", "03bnmw459", "square"),
    "dfg": ("Deutsche Forschungsgemeinschaft", "funder", "Bonn", "DE", "018mejw64", None),
    "igg": (
        "Institute of Geology and Geophysics, Chinese Academy of Sciences",
        "education",
        "Beijing",
        "CN",
        "",
        "square",
    ),
    "ihfc": ("International Heat Flow Commission", "", "", "", "", None),
}

PALETTE = [
    ((236, 214, 196), (122, 84, 60)),
    ((205, 222, 238), (52, 84, 122)),
    ((226, 236, 208), (78, 104, 52)),
    ((240, 214, 222), (120, 56, 78)),
    ((222, 214, 240), (78, 62, 122)),
    ((244, 230, 200), (130, 96, 40)),
]


def portrait(seed):
    """A stand-in photo: head and shoulders on a soft background, different per person."""
    rng = random.Random(seed)
    background, figure = rng.choice(PALETTE)
    image = Image.new("RGB", (400, 400), background)
    draw = ImageDraw.Draw(image)
    draw.ellipse((40, 250, 360, 560), fill=figure)
    draw.ellipse((125, 70, 275, 240), fill=tuple(min(c + 40, 255) for c in figure))
    return png(image)


def logo(name, shape, seed):
    """A stand-in logo: a mark and a wordmark, square or wide."""
    rng = random.Random(seed)
    _, colour = rng.choice(PALETTE)
    size = (600, 200) if shape == "wide" else (400, 400)
    image = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    if shape == "wide":
        draw.rounded_rectangle((10, 30, 150, 170), radius=28, fill=colour)
        for row, width in enumerate((400, 300)):
            draw.rounded_rectangle((180, 60 + row * 55, 180 + width, 95 + row * 55), radius=8, fill=colour)
    else:
        draw.ellipse((60, 60, 340, 340), outline=colour, width=28)
        draw.polygon([(200, 110), (290, 280), (110, 280)], fill=colour)
    return png(image)


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def orcid_for(index):
    """A syntactically valid ORCID iD, including its ISO 7064 check character."""
    base = f"000000021{index:06d}"
    total = 0
    for digit in base:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    digits = base + ("X" if check == 10 else str(check))
    return "-".join(digits[i : i + 4] for i in range(0, 16, 4))


class Command(BaseCommand):
    help = "Seed every state of the contributor display components (development only)."

    def handle(self, *args, **options):
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one."
            )
        call_command("preload", verbosity=0)
        with transaction.atomic():
            self.clear()
            organizations = self.organizations()
            people = self.people(organizations)
            self.credits(people, organizations)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(people)} people and {len(organizations)} organizations."))

    def clear(self):
        # A project holding a public dataset refuses deletion, so the datasets go first.
        Dataset.objects.filter(name__startswith="[Contributors] ").delete()
        Project.objects.filter(name__startswith="[Contributors] ").delete()
        SocialAccount.objects.filter(user__config__seed=SEED).delete()
        Contributor.objects.filter(config__seed=SEED).delete()

    def organizations(self):
        created = {}
        for index, (key, (name, kind, city, country, ror, shape)) in enumerate(ORGANIZATIONS.items()):
            org = Organization(
                name=name,
                type=kind or None,
                city=city or None,
                country=country or None,
                config={"seed": SEED},
                profile=f"{name} is credited on research in this portal." if kind else "",
            )
            if shape:
                org.image.save(f"{key}.png", ContentFile(logo(name, shape, index)), save=False)
            org.save()
            if ror:
                ContributorIdentifier.objects.create(related=org, type="ROR", value=ror)
            created[key] = org
        return created

    def people(self, organizations):
        created = []
        for index, (first, last, preferred, photo, orcid, affiliations) in enumerate(PEOPLE):
            state, roles = ACCOUNTS.get(index, ("ghost", []))
            person = Person(
                first_name=first,
                last_name=last,
                name=preferred,
                email=f"seed.person{index}@example.com" if state != "ghost" else None,
                is_claimed=state == "claimed",
                is_active=state != "inactive",
                config={"seed": SEED},
                profile=PROFILE if index % 3 != 2 else "",
            )
            if photo:
                person.image.save(f"p{index}.png", ContentFile(portrait(index)), save=False)
            person.save()
            if orcid:
                value = orcid_for(index)
                ContributorIdentifier.objects.create(related=person, type="ORCID", value=value)
                if orcid == "authenticated":
                    SocialAccount.objects.create(user=person, provider="orcid", uid=value)
            for position, key in enumerate(affiliations):
                Affiliation.objects.create(
                    person=person,
                    organization=organizations[key],
                    type=Affiliation.MembershipType.MEMBER,
                    is_primary=position == 0,
                )
            if roles:
                person.groups.add(*Group.objects.filter(name__in=roles))
            created.append(person)
        return created

    def credits(self, people, organizations):
        many = Project.objects.create(name="[Contributors] Many contributors", visibility=Visibility.PUBLIC)
        roles = [
            ["ProjectLeader", "ContactPerson"],
            ["ProjectLeader"],
            ["DataCollector"],
            ["DataCurator", "DataManager"],
            ["Researcher"],
        ]
        for index, person in enumerate(people):
            many.add_contributor(person, with_roles=roles[index % len(roles)])
        many.add_contributor(organizations["gfz"], with_roles=["HostingInstitution"])
        many.add_contributor(organizations["dfg"], with_roles=["Sponsor"])

        few = Project.objects.create(name="[Contributors] Three contributors", visibility=Visibility.PUBLIC)
        for person, role in zip(people[:3], (["ProjectLeader"], ["DataCollector"], ["ContactPerson"])):
            few.add_contributor(person, with_roles=role)

        one = Project.objects.create(name="[Contributors] One contributor", visibility=Visibility.PUBLIC)
        one.add_contributor(people[3], with_roles=["ProjectLeader", "ContactPerson", "ProjectMember"])

        Project.objects.create(name="[Contributors] Nobody credited", visibility=Visibility.PUBLIC)

        dataset = Dataset.objects.create(name="[Contributors] Borehole temperatures", project=few, visibility=Visibility.PUBLIC)
        for person in people[:6]:
            dataset.add_contributor(person, with_roles=["Creator"])
