"""Development data for the Contributors tab on projects, datasets, samples and measurements."""

from django.core.management.base import BaseCommand
from django.db import transaction
from research_vocabs.models import Concept

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Affiliation, Organization, Person
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility

from .common import example_accounts, remove_own_projects

PROJECT = "Contributors tab examples"

#: A dataset credited to this many people, to show search on a long list.
SOLO = "Dataset with one manager and no project"

CROWD = 36

FIRST_NAMES = [
    "Aiko",
    "Bruno",
    "Carmen",
    "Dmitri",
    "Elif",
    "Farid",
    "Greta",
    "Hugo",
    "Ines",
]
LAST_NAMES = ["Albrecht", "Bianchi", "Costa", "Dubois"]


class ContributorSeed(BaseCommand):
    help = "Seed every state of the Contributors tab (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("keep_records"):
            self.affiliate()
            self.stdout.write("Added affiliations to the records already seeded.")
            return
        users = example_accounts()
        remove_own_projects([PROJECT], users)
        Dataset.all_objects.filter(name=SOLO, created_by=users["super.user"]).delete()
        regular, staff, creator = (
            users["regular.user"],
            users["staff.user"],
            users["super.user"],
        )

        anna = self.person("Anna", "Keller")
        lea = self.person("Lea", "Brandt")
        yusuf = self.person("Yusuf", "Demir")
        mei = self.person("Mei", "Tanaka")
        visitor = self.person("Noor", "Haddad")
        long_name = self.person(
            "Maximilian-Alexander", "von Hohenzollern-Sigmaringen-Wolfenbüttel"
        )
        no_account = self.person("Ingrid", "Solberg", account=False)
        institute = self.organization("Karlsruhe Institute of Technology")
        survey = self.organization("Landesamt für Geologie, Rohstoffe und Bergbau")

        project = Project.objects.create(
            name=PROJECT,
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            created_by=creator,
        )
        self.credit(
            project, regular, ["Creator", "ProjectLeader"], ContributionLevel.MANAGE
        )
        self.credit(project, anna, ["ProjectMember"], ContributionLevel.EDIT)
        self.credit(project, mei, ["ProjectMember"], ContributionLevel.VIEW)
        self.credit(project, institute, [])

        team = self.dataset(
            project, "Private dataset with a full team", Visibility.PRIVATE, creator
        )
        self.credit(
            team, regular, ["Creator", "ContactPerson"], ContributionLevel.MANAGE
        )
        self.credit(team, lea, ["Creator", "DataCollector"], ContributionLevel.MANAGE)
        self.credit(team, staff, ["DataCurator"], ContributionLevel.EDIT)
        self.credit(team, yusuf, ["DataCollector"], ContributionLevel.VIEW)
        self.credit(team, mei, ["Researcher"], ContributionLevel.EDIT)
        self.credit(team, visitor, [], ContributionLevel.VIEW)
        self.credit(team, no_account, ["Supervisor"], ContributionLevel.EDIT)
        self.credit(
            team,
            long_name,
            ["RightsHolder", "Editor", "Producer"],
            ContributionLevel.VIEW,
        )
        self.credit(team, institute, ["Other"])
        self.credit(team, survey, [])

        solo = self.dataset(None, SOLO, Visibility.PRIVATE, creator)
        self.credit(solo, staff, ["Creator"], ContributionLevel.MANAGE)
        self.credit(solo, yusuf, ["DataCollector"], ContributionLevel.VIEW)

        self.dataset(
            project, "Dataset nobody is credited on yet", Visibility.PRIVATE, creator
        )

        crowd = self.dataset(
            project,
            "Public dataset with a long author list",
            Visibility.PUBLIC,
            creator,
        )
        self.credit(crowd, regular, ["Creator"], ContributionLevel.MANAGE)
        for n in range(CROWD):
            person = self.person(
                FIRST_NAMES[n % len(FIRST_NAMES)], LAST_NAMES[n % len(LAST_NAMES)]
            )
            self.credit(
                crowd,
                person,
                ["Creator"] if n < 8 else ["DataCollector"],
                ContributionLevel.VIEW,
            )

        sample = RockSampleFactory(dataset=team, name="Core GPK-3, 2210 m")
        self.credit(sample, yusuf, ["Collection"], ContributionLevel.VIEW)
        self.credit(sample, lea, ["Preparation"], None)
        measurement = XRFMeasurementFactory(
            sample=sample, dataset=team, name="Fe, fused bead, run 88"
        )
        self.credit(measurement, lea, ["MeasurementCollection"], None)
        self.credit(measurement, institute, ["Support"])

        self.affiliate()

        from fairdm.contrib.plugins import reverse

        for label, record in (
            ("Project, public", project),
            ("Dataset, private, every kind of contributor", team),
            ("Dataset with one manager and no project (sign in as staff.user)", solo),
            (
                "Dataset with nobody credited",
                Dataset.all_objects.get(
                    name="Dataset nobody is credited on yet", project=project
                ),
            ),
            ("Dataset with a long list", crowd),
            ("Sample", sample),
            ("Measurement", measurement),
        ):
            self.stdout.write(f"{label}: {reverse(record, 'contribution-list')}")

    def affiliate(self):
        """Give the example people affiliations, and credit some of them from one.

        Safe to run again, and changes no address: it only adds to the records already seeded.

        - Lea Brandt moved from Karlsruhe to Tübingen, which is her primary affiliation today. The
          private dataset dates from Karlsruhe and credits her from there.
        - Regular User is credited from Karlsruhe too, so that organization is on the dataset
          through two people and cannot be removed.
        - Yusuf Demir is credited from Tübingen, which is listed through him alone.
        - Mei Tanaka has an affiliation and is credited from none. Noor Haddad has none at all.
        - Anna Keller, who is not on the dataset, has a current and an earlier affiliation to
          choose between when she is added.
        - Landesamt für Geologie is credited in its own right and can be removed.
        """
        team = Dataset.all_objects.get(name="Private dataset with a full team")
        karlsruhe = self.organization("Karlsruhe Institute of Technology")
        tuebingen = self.organization("Universität Tübingen")
        potsdam = self.organization("GFZ Helmholtz Centre for Geosciences")
        people = {
            name: Person.objects.get(name=name)
            for name in (
                "Lea Brandt",
                "Regular User",
                "Yusuf Demir",
                "Mei Tanaka",
                "Anna Keller",
            )
        }
        held = [
            ("Lea Brandt", tuebingen, True, "2023", None),
            ("Lea Brandt", karlsruhe, False, "2017", "2023"),
            ("Regular User", karlsruhe, True, "2015", None),
            ("Yusuf Demir", tuebingen, True, "2020", None),
            ("Mei Tanaka", karlsruhe, True, "2021", None),
            ("Anna Keller", potsdam, True, "2024", None),
            ("Anna Keller", karlsruhe, False, "2018", "2024"),
            ("Anna Keller", tuebingen, False, "2012", "2018"),
        ]
        for name, organization, primary, start, end in held:
            Affiliation.objects.update_or_create(
                person=people[name],
                organization=organization,
                defaults={
                    "is_primary": primary,
                    "type": Affiliation.MembershipType.MEMBER,
                    "start_date": start,
                    "end_date": end,
                },
            )
        credited_from = {
            "Lea Brandt": karlsruhe,
            "Regular User": karlsruhe,
            "Yusuf Demir": tuebingen,
        }
        crediting = Crediting(team)
        for name, organization in credited_from.items():
            contribution = team.contributors.get(contributor=people[name])
            crediting.update(
                contribution,
                roles=list(contribution.roles.all()),
                organization=organization,
            )

    def person(self, first, last, account=True):
        email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.org"
        person = Person.objects.filter(name=f"{first} {last}").first()
        if person is None and account:
            person = Person.objects.create_user(
                email=email, first_name=first, last_name=last
            )
        elif person is None:
            person = Person(first_name=first, last_name=last, email=None)
            person.set_unusable_password()
        person.name = f"{first} {last}"
        person.is_claimed = account
        person.save()
        return person

    def organization(self, name):
        organization, _ = Organization.objects.get_or_create(name=name)
        return organization

    def dataset(self, project, name, visibility, creator):
        return Dataset.all_objects.create(
            name=name, project=project, visibility=visibility, created_by=creator
        )

    def credit(self, record, contributor, roles, level=None):
        crediting = Crediting(record)
        contribution = crediting.add(contributor)
        crediting.update(
            contribution,
            roles=Concept.objects.filter(
                vocabulary__name="fairdm-roles", name__in=roles
            ),
            level=level,
        )
        if level is None and not contributor.is_organization:
            contribution.level = None
            contribution.save(update_fields=["level"])
