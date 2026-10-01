"""Development data for the person and organization overview pages.

Builds on the records ``seed_overviews`` creates and reaches every state the two pages answer for:
a complete profile, your own incomplete profile, an unclaimed profile, an inactive account, a
person credited on nothing, a name in a non-Latin script and a very long one; an organization
with a logo, ROR ID, map, parent, sub-organizations, members, former members and projects, one
you own with an administrator, a member and a former administrator, and one with nothing
recorded. It refuses outside development, and running it again
replaces what it created.

    DJANGO_ENV=development python manage.py seed_profiles
"""

import io
import random
from datetime import UTC, datetime

from allauth.socialaccount.models import SocialAccount
from django.apps import apps
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from demo.seed.common import example_accounts, profile_accounts
from demo.seed.projects import SHOWCASE
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.contrib.location.models import Point
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

SEED = "profiles"

ANNA_PROFILE = (
    "I work on the thermal structure of the Upper Rhine Graben, combining borehole temperature "
    "logs with laboratory measurements of thermal conductivity and radiogenic heat production "
    "on core samples.\n\n"
    "Most of my recent work is about **uncertainty**: how much of the scatter in published heat "
    "flow values comes from the rocks, and how much from the way the samples were prepared and "
    "measured. I coordinate the core sampling campaigns in Soultz-sous-Forêts and curate the "
    "project's rock property datasets."
)

KIT_PROFILE = (
    "The Karlsruhe Institute of Technology is a public research university and a member of the "
    "Helmholtz Association. Its geoscience institutes work on geothermal energy, groundwater and "
    "the structure of the upper crust, with a long record of fieldwork in the Upper Rhine Graben."
)

MEMBER, ADMIN, OWNER = (
    Affiliation.MembershipType.MEMBER,
    Affiliation.MembershipType.ADMIN,
    Affiliation.MembershipType.OWNER,
)

PALETTE = [
    ((236, 214, 196), (122, 84, 60)),
    ((205, 222, 238), (52, 84, 122)),
    ((226, 236, 208), (78, 104, 52)),
    ((240, 214, 222), (120, 56, 78)),
]


def portrait(seed):
    """A stand-in photo: head and shoulders on a soft background."""
    background, figure = random.Random(seed).choice(PALETTE)
    image = Image.new("RGB", (400, 400), background)
    draw = ImageDraw.Draw(image)
    draw.ellipse((40, 250, 360, 560), fill=figure)
    draw.ellipse((125, 70, 275, 240), fill=tuple(min(c + 40, 255) for c in figure))
    return png(image)


def logo(shape, seed):
    """A stand-in logo: a mark and a wordmark, square or wide."""
    _, colour = random.Random(seed).choice(PALETTE)
    size = (600, 200) if shape == "wide" else (400, 400)
    image = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    if shape == "wide":
        draw.rounded_rectangle((10, 30, 150, 170), radius=28, fill=colour)
        for row, width in enumerate((400, 300)):
            draw.rounded_rectangle(
                (180, 60 + row * 55, 180 + width, 95 + row * 55), radius=8, fill=colour
            )
    else:
        draw.ellipse((60, 60, 340, 340), outline=colour, width=28)
        draw.polygon([(200, 110), (290, 280), (110, 280)], fill=colour)
    return png(image)


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Seed every state of the person and organization overview pages (development only)."

    def handle(self, *args, **options):
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one."
            )
        if not Project.objects.filter(name=SHOWCASE).exists():
            call_command("seed_overviews")
        with transaction.atomic():
            self.showcase = Project.objects.filter(name=SHOWCASE).latest("pk")
            self.datasets = list(
                Dataset.all_objects.filter(project=self.showcase).order_by("pk")
            )
            self.clear()
            orgs = self.organizations()
            people = self.people(orgs)
        for label, obj in [*orgs.items(), *people.items()]:
            self.stdout.write(f"  {label:<12} /contributor/{obj.uuid}/")
        self.stdout.write(self.style.SUCCESS("Seeded the profile page states."))

    # ------------------------------------------------------------------ helpers

    def person(self, first, last):
        email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.org"
        return Person.objects.get(email=email)

    def mark(self, contributor):
        contributor.config = {**(contributor.config or {}), "seed": SEED}
        return contributor

    def clear(self):
        # People and organizations `seed_overviews` made keep their credits; crediting them again
        # adds to the same credit rather than a second one.
        touched = Contributor.objects.filter(config__seed=SEED)
        Contribution.objects.filter(
            contributor__in=touched.filter(config__created=True)
        ).delete()
        Affiliation.objects.filter(organization__in=touched).delete()
        Affiliation.objects.filter(person__in=touched).delete()
        # A credit records the affiliation it was made under, and protects that organization.
        Contribution.objects.filter(
            affiliation__in=touched.filter(config__created=True)
        ).update(affiliation=None)
        SocialAccount.objects.filter(user__config__seed=SEED).delete()
        ContributorIdentifier.objects.filter(related__in=touched).delete()
        created = touched.filter(config__created=True)
        for contributor in created:
            contributor.delete()

    def samples(self, n, offset=0):
        dataset_ids = [d.pk for d in self.datasets]
        return list(
            Sample.objects.filter(dataset_id__in=dataset_ids).order_by("pk")[
                offset : offset + n
            ]
        )

    def measurements(self, n, offset=0):
        dataset_ids = [d.pk for d in self.datasets]
        return list(
            Measurement.objects.filter(dataset_id__in=dataset_ids).order_by("pk")[
                offset : offset + n
            ]
        )

    def new(self, model, **fields):
        obj = model(config={"seed": SEED, "created": True}, **fields)
        return obj

    # ------------------------------------------------------------- organizations

    def organizations(self):
        helmholtz = self.new(
            Organization,
            name="Helmholtz Association of German Research Centres",
            type="nonprofit",
            city="Berlin",
            country="DE",
            alternative_names=["Helmholtz Association", "HGF"],
            links=["https://www.helmholtz.de/en/"],
            profile="Germany's largest scientific organisation, made up of eighteen research centres.",
        )
        helmholtz.save()
        ContributorIdentifier.objects.create(
            related=helmholtz, type="ROR", value="0281dp749"
        )

        kit, _ = Organization.objects.get_or_create(
            name="Karlsruhe Institute of Technology"
        )
        self.mark(kit)
        kit.type = "education"
        kit.city, kit.country = "Karlsruhe", "DE"
        kit.parent = helmholtz
        kit.alternative_names = ["KIT", "Karlsruher Institut für Technologie"]
        kit.links = [
            "https://www.kit.edu/english/",
            "https://en.wikipedia.org/wiki/Karlsruhe_Institute_of_Technology",
        ]
        kit.lang = ["de", "en"]
        kit.profile = KIT_PROFILE
        kit.location, _ = Point.objects.get_or_create(x=8.4115, y=49.0094)
        kit.synced_data = {"id": "https://ror.org/04t3en479", "name": kit.name}
        kit.image.save("kit.png", ContentFile(logo("wide", 1)), save=False)
        kit.save()
        ContributorIdentifier.objects.create(related=kit, type="ROR", value="04t3en479")

        agw = self.new(
            Organization,
            name="Institute of Applied Geosciences",
            type="education",
            city="Karlsruhe",
            country="DE",
            parent=kit,
        )
        agw.image.save("agw.png", ContentFile(logo("square", 2)), save=False)
        agw.save()
        gpi = self.new(Organization, name="Geophysical Institute", parent=kit)
        gpi.save()
        empty = self.new(Organization, name="Rhine Graben Geothermal Working Group")
        empty.save()

        tuebingen, _ = Organization.objects.get_or_create(name="Universität Tübingen")
        self.mark(tuebingen)
        tuebingen.save()

        # The organizations' own credits.
        kit.add_to(self.showcase, ["HostingInstitution"])
        if self.datasets:
            helmholtz.add_to(self.datasets[0], ["Sponsor"])
            kit.add_to(self.datasets[0], ["HostingInstitution"])
        return {
            "helmholtz": helmholtz,
            "kit": kit,
            "agw": agw,
            "gpi": gpi,
            "tuebingen": tuebingen,
            "empty-org": empty,
        }

    # ------------------------------------------------------------------ people

    def people(self, orgs):
        users = example_accounts()
        roles_group = {g.name: g for g in Group.objects.all()}

        # A complete profile.
        anna = self.mark(self.person("Anna", "Keller"))
        anna.profile = ANNA_PROFILE
        anna.links = [
            "https://www.researchgate.net/profile/Anna-Keller",
            "https://github.com/akeller-geo",
            "https://scholar.google.com/citations?user=akeller",
        ]
        anna.alternative_names = ["A. M. Keller", "Anna Maria Keller"]
        anna.lang = ["de", "en", "fr"]
        anna.is_claimed = True
        anna.date_joined = datetime(2023, 3, 14, tzinfo=UTC)
        anna.synced_data = {"orcid-identifier": {"path": "0000-0002-1825-0097"}}
        anna.image.save("anna.png", ContentFile(portrait(3)), save=False)
        anna.save()
        ContributorIdentifier.objects.create(
            related=anna, type="ORCID", value="0000-0002-1825-0097"
        )
        SocialAccount.objects.create(
            user=anna, provider="orcid", uid="0000-0002-1825-0097"
        )
        if "Data Curator" in roles_group:
            anna.groups.add(roles_group["Data Curator"])
        Affiliation.objects.create(
            person=anna,
            organization=orgs["agw"],
            type=MEMBER,
            is_primary=True,
            start_date="2020-04",
        )
        Affiliation.objects.create(
            person=anna, organization=orgs["kit"], type=ADMIN, start_date="2019"
        )
        Affiliation.objects.create(
            person=anna,
            organization=orgs["tuebingen"],
            type=MEMBER,
            start_date="2014-10",
            end_date="2019-03",
        )
        for sample in self.samples(9):
            anna.add_to(sample, ["Collection"])
        for sample in self.samples(3, offset=9):
            anna.add_to(sample, ["Preparation"])
        for measurement in self.measurements(6):
            anna.add_to(measurement, ["MeasurementCollection"])
        for dataset in self.datasets[:3]:
            anna.add_to(dataset, ["DataCurator"])

        # An ORCID iD nobody has confirmed, and the owner of the university's record.
        tomas = self.mark(self.person("Tomás", "Oliveira"))
        tomas.save()
        ContributorIdentifier.objects.create(
            related=tomas, type="ORCID", value="0000-0001-5109-3700"
        )
        Affiliation.objects.create(
            person=tomas,
            organization=orgs["kit"],
            type=OWNER,
            is_primary=True,
            start_date="2012",
        )
        for measurement in self.measurements(4, offset=6):
            tomas.add_to(measurement, ["MeasurementCollection"])

        # The rest of the project team fill the university's member list.
        team = [
            ("Lea", "Brandt", "gpi"),
            ("Yusuf", "Demir", "agw"),
            ("Chloé", "Martin", "kit"),
            ("Jonas", "Weber", "agw"),
            ("Mei", "Tanaka", "gpi"),
            ("Pieter", "de Vries", "kit"),
            ("Sofia", "Rossi", "kit"),
            ("Lukas", "Hofmann", "agw"),
            ("Ingrid", "Lund", "kit"),
        ]
        for index, (first, last, key) in enumerate(team):
            person = self.mark(self.person(first, last))
            if index % 2 == 0:
                person.image.save(
                    f"team{index}.png", ContentFile(portrait(10 + index)), save=False
                )
            person.save()
            Affiliation.objects.create(
                person=person,
                organization=orgs[key],
                type=MEMBER,
                is_primary=True,
                start_date=str(2015 + index),
            )
            if key != "kit":
                Affiliation.objects.create(
                    person=person,
                    organization=orgs["kit"],
                    type=MEMBER,
                    start_date=str(2015 + index),
                )
            for sample in self.samples(2, offset=12 + 2 * index):
                person.add_to(sample, ["Collection"])

        # Your own profile, missing most things, and the owner of an institute's record.
        me = self.mark(users["regular.user"])
        me.is_claimed = True
        me.save()
        Affiliation.objects.create(
            person=me,
            organization=orgs["agw"],
            type=OWNER,
            is_primary=True,
            start_date="2024-09",
        )
        if len(self.datasets) > 1:
            me.add_to(self.datasets[1], ["DataCollector"])
        for sample in self.samples(2, offset=40):
            me.add_to(sample, ["Collection"])

        # The people around the institute's record: an administrator, an ordinary member and an
        # administrator whose affiliation has ended.
        keepers = profile_accounts()
        for key, membership, end_date in [
            ("admin.user", ADMIN, None),
            ("member.user", MEMBER, None),
            ("former-admin.user", ADMIN, "2023-08"),
        ]:
            person = self.mark(keepers[key])
            person.is_claimed = True
            person.save()
            Affiliation.objects.create(
                person=person,
                organization=orgs["agw"],
                type=membership,
                start_date="2022-01",
                end_date=end_date,
            )

        # Unclaimed, with a very long name.
        ghost = self.new(
            Person,
            first_name="Wilhelmina Adaeze",
            last_name="Oyelaran-Castellanos de la Fuente",
            name="Wilhelmina Adaeze Oyelaran-Castellanos de la Fuente",
        )
        ghost.set_unusable_password()
        ghost.save()
        for sample in self.samples(3, offset=30):
            ghost.add_to(sample, ["Collection", "Storage"])

        # An account that has been closed, with a former affiliation.
        inactive = self.new(
            Person,
            first_name="Georg",
            last_name="Lindemann",
            name="Georg Lindemann",
            email="georg.lindemann@example.org",
            is_claimed=True,
            is_active=False,
            date_joined=datetime(2021, 5, 2, tzinfo=UTC),
        )
        inactive.set_unusable_password()
        inactive.save()
        Affiliation.objects.create(
            person=inactive,
            organization=orgs["kit"],
            type=MEMBER,
            start_date="2016",
            end_date="2022-06",
        )
        if self.datasets:
            inactive.add_to(self.datasets[0], ["DataCollector"])

        # A name in a non-Latin script, with an unconfirmed ORCID iD.
        wang = self.new(Person, first_name="晓明", last_name="王", name="王晓明")
        wang.set_unusable_password()
        wang.save()
        ContributorIdentifier.objects.create(
            related=wang, type="ORCID", value="0000-0003-1415-9269"
        )
        for measurement in self.measurements(2, offset=12):
            wang.add_to(measurement, ["MeasurementPreparation"])

        # Credited on nothing and affiliated nowhere.
        nobody = self.new(
            Person,
            first_name="Mireille",
            last_name="Dufresne",
            name="Mireille Dufresne",
        )
        nobody.set_unusable_password()
        nobody.save()

        return {
            "anna": anna,
            "tomas": tomas,
            "me": me,
            "ghost": ghost,
            "inactive": inactive,
            "wang": wang,
            "nobody": nobody,
        }
