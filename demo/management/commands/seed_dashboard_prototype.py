"""Seed what the dashboard prototype is looked at with.

``regular.user`` gets a full history: an ORCID iD, an organization they run with people asking
to join, imports waiting on them, and a year of other people opening and downloading the
portal's public datasets. ``regular.user2`` is stripped back to a new account that holds
nothing. The portal-role accounts each get something to do. Records' and people's dates are
spread over the last year, so the monthly figures read like a portal in use.

Safe to run again: everything it adds is found or replaced, never added twice.
"""

import csv
import io
import random
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contribution,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.contrib.dashboard.models import DashboardState, RecentRecord, RecordUse
from fairdm.contrib.import_export.definitions import get_definition
from fairdm.contrib.import_export.matching import HeadingMatcher
from fairdm.contrib.import_export.models import ImportJob
from fairdm.contrib.import_export.runner import ImportRun
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import ORCID
from fairdm.utils.choices import Visibility

USER = "regular.user@example.com"
NEW_USER = "regular.user2@example.com"
DEVELOPER = "portal.developer@example.com"
WEEKS = 16
SEED_FILES = ("dashboard-rocks-to-fix.csv", "dashboard-rocks-ready.csv")


class Command(BaseCommand):
    help = "Seed the accounts and history the dashboard prototype is looked at with."

    def handle(self, *args, **options):
        call_command("create_dev_accounts", stdout=io.StringIO())
        self.rng = random.Random(2026)
        with transaction.atomic():
            self.spread_dates()
            user = Person.objects.get(email=USER)
            self.empty_new_user()
            self.give_orcid(user)
            self.organization_to_run(user)
            self.private_ready_dataset(user)
            self.record_use()
            self.developer_token()
            self.possible_duplicate()
            self.portal_identity()
            DashboardState.objects.filter(person__email__in=[USER, NEW_USER]).delete()
        self.imports(user)
        self.recent_pages(user)
        self.stdout.write(self.style.SUCCESS("Dashboard prototype data seeded."))

    # ------------------------------------------------------------------------------- dates

    def spread_dates(self):
        """Spread when records were added and people joined over the last year, newest densest."""
        now = timezone.now()

        def when(i, n):
            # A square root puts more of the dates near now, as a growing portal has.
            share = ((i + 1) / n) ** 0.5
            return now - timedelta(days=365 * (1 - share) + self.rng.uniform(0, 6))

        for model in (Project, Dataset):
            rows = list(model.all_objects.order_by("pk").values_list("pk", flat=True)) if model is Dataset else list(model.objects.order_by("pk").values_list("pk", flat=True))
            manager = model.all_objects if model is Dataset else model.objects
            for i, pk in enumerate(rows):
                manager.filter(pk=pk).update(added=when(i, len(rows)))
        for model in (Sample, Measurement):
            rows = list(model.objects.order_by("pk").values_list("pk", "dataset__added"))
            for pk, dataset_added in rows:
                start = dataset_added or now - timedelta(days=200)
                days = max((now - start).days, 1)
                model.objects.filter(pk=pk).update(added=start + timedelta(days=self.rng.uniform(0, days)))
        people = list(Person.objects.filter(is_claimed=True).order_by("pk").values_list("pk", flat=True))
        for i, pk in enumerate(people):
            Person.objects.filter(pk=pk).update(date_joined=when(i, len(people)))
        # The new account joined this week.
        Person.objects.filter(email=NEW_USER).update(date_joined=now - timedelta(days=2))
        Person.objects.filter(email=USER).update(date_joined=now - timedelta(days=330))

    # -------------------------------------------------------------------------- the people

    def empty_new_user(self):
        """Leave regular.user2 an account with nothing: no credit, no organization, no iD."""
        person = Person.objects.get(email=NEW_USER)
        Contribution.objects.filter(contributor_id=person.pk).delete()
        Affiliation.objects.filter(person=person).delete()
        ContributorIdentifier.objects.filter(related=person).delete()
        ImportJob.objects.filter(created_by=person).delete()

    def give_orcid(self, user):
        ContributorIdentifier.objects.update_or_create(
            related=user, type_id=ORCID, defaults={"value": "0000-0003-4821-7658"}
        )

    def organization_to_run(self, user):
        """Make regular.user the owner of their primary organization, with people asking to join."""
        affiliation = (
            Affiliation.objects.filter(person=user, end_date__isnull=True)
            .order_by("-is_primary", "pk")
            .first()
        )
        if affiliation is None:
            organization = Organization.objects.order_by("pk").first()
            affiliation = Affiliation.objects.create(person=user, organization=organization)
        Affiliation.objects.filter(person=user).update(is_primary=False)
        affiliation.is_primary = True
        affiliation.type = Affiliation.MembershipType.OWNER
        affiliation.save()
        organization = affiliation.organization
        Affiliation.objects.filter(organization=organization, type=Affiliation.MembershipType.PENDING).delete()
        members = Affiliation.objects.filter(organization=organization).values("person")
        askers = (
            Person.objects.filter(is_claimed=True, is_active=True)
            .exclude(pk__in=members)
            .exclude(email__in=[USER, NEW_USER])
            .order_by("-date_joined")[:3]
        )
        for person in askers:
            Affiliation.objects.create(
                person=person, organization=organization, type=Affiliation.MembershipType.PENDING
            )

    def private_ready_dataset(self, user):
        """Make sure one of regular.user's managed datasets is private, so 'Make it public' shows."""
        from fairdm.contrib.dashboard.panels import readiness

        from fairdm.core.dataset.models import DatasetDate, DatasetDescription
        from fairdm.core.vocabularies import ABSTRACT, CREATOR, DESCRIPTION_TYPES

        managed = Dataset.all_objects.with_level(user, ContributionLevel.MANAGE).filter(published=False)
        with_data = managed.filter(samples__isnull=False).distinct().order_by("pk")
        dataset = next((d for d in managed if not readiness(d)["required_missing"]), None) or with_data.first()
        if dataset is None:
            return
        # Fill in what a reuser needs, so only its visibility is left.
        for type_id, text in (
            (ABSTRACT, "Water chemistry of twelve alpine springs sampled monthly through the 2025 thaw."),
            (f"{DESCRIPTION_TYPES}/methods", "Field filtration at 0.45 µm, cations by ICP-MS, anions by ion chromatography."),
        ):
            DatasetDescription.objects.get_or_create(related=dataset, type_id=type_id, defaults={"value": text})
        if not DatasetDate.objects.filter(related=dataset, type_id=DatasetDate.START_TYPE).exists():
            DatasetDate.objects.create(related=dataset, type_id=DatasetDate.START_TYPE, value="2025-04")
        if dataset.license_id is None:
            licensed = Dataset.all_objects.exclude(license=None).values_list("license_id", flat=True).first()
            Dataset.all_objects.filter(pk=dataset.pk).update(license_id=licensed)
        credit = Contribution.objects.filter(dataset=dataset, contributor_id=user.pk).first()
        if credit and not credit.roles.filter(uri=CREATOR).exists():
            credit.roles.add(credit.roles.model.objects.get(uri=CREATOR))
        Dataset.all_objects.filter(pk=dataset.pk).update(visibility=Visibility.PRIVATE, modified=timezone.now())
        dataset.refresh_from_db()
        self.stdout.write(f"Ready but private: {dataset.name}, still missing {[m['label'] for m in readiness(dataset)['required_missing']]}")

    def developer_token(self):
        from knox.models import get_token_model

        person = Person.objects.get(email=DEVELOPER)
        model = get_token_model()
        if not model.objects.filter(user=person).exists():
            for _ in range(2):
                model.objects.create(user=person, expiry=timedelta(days=90))

    def possible_duplicate(self):
        """Add an unclaimed profile sharing a name with a claimed one, as imports often leave."""
        original = Person.objects.filter(is_claimed=True).exclude(last_name="").exclude(email__in=[USER, NEW_USER]).order_by("pk").first()
        if original and not Person.objects.filter(first_name__iexact=original.first_name, last_name__iexact=original.last_name, is_claimed=False).exists():
            Person.objects.create(first_name=original.first_name, last_name=original.last_name, is_claimed=False)

    def portal_identity(self):
        """Fill in part of the portal's own description, so the administrator has some left to do."""
        from fairdm.contrib.identity.models import Authority, Identity

        identity = Identity.get_solo()
        identity.set_current_language("en")
        identity.name = "FairDM Demo"
        identity.description = "Geothermal and hydrochemical field data from the Upper Rhine Graben and the Alps."
        identity.save()
        authority = Authority.get_solo()
        authority.set_current_language("en")
        authority.name = "FairDM Demo Consortium"
        authority.save()

    # ----------------------------------------------------------------------------- record use

    def record_use(self):
        """Opens and downloads of every public dataset by people outside its team, per day."""
        dataset_type = ContentType.objects.get_for_model(Dataset)
        RecordUse.objects.filter(content_type=dataset_type).delete()
        today = timezone.localdate()
        rows = []
        for dataset in Dataset.objects.filter(visibility=Visibility.PUBLIC).order_by("pk"):
            appeal = self.rng.choice([0.3, 0.6, 1, 1, 2, 4])
            for day in range(WEEKS * 7):
                date = today - timedelta(days=day)
                growth = 1 + (WEEKS * 7 - day) / (WEEKS * 7)  # busier lately
                weekday = 0.45 if date.weekday() >= 5 else 1
                views = int(self.rng.expovariate(1 / (appeal * growth * weekday)))
                if not views:
                    continue
                exports = sum(1 for _ in range(views) if self.rng.random() < 0.18)
                rows.append(RecordUse(content_type=dataset_type, object_id=dataset.pk, day=date, views=views, exports=exports))
        RecordUse.objects.bulk_create(rows)

    # -------------------------------------------------------------------------------- imports

    def recent_pages(self, user):
        """Leave regular.user four records they had open lately, each on a different page."""
        from django.contrib.contenttypes.models import ContentType
        from django.urls import reverse

        from fairdm.contrib.contributors.choices import ContributionLevel

        RecentRecord.objects.filter(person__email__in=[USER, NEW_USER]).delete()
        datasets = list(Dataset.all_objects.with_level(user, ContributionLevel.EDIT).order_by("-modified")[:3])
        project = Project.objects.with_level(user, ContributionLevel.EDIT).order_by("-modified").first()
        now = timezone.now()
        visits = [
            (datasets[0], "descriptions", "Descriptions", timedelta(minutes=25)),
            (datasets[1], "samples", "Samples", timedelta(hours=3)),
            (project, "overview", "Overview", timedelta(days=1, hours=2)),
            (datasets[2], "imports", "Imports", timedelta(days=4)),
        ]
        for record, page, label, ago in visits:
            if record is None:
                continue
            kind = "dataset" if isinstance(record, Dataset) else "project"
            RecentRecord.objects.create(
                person=user,
                content_type=ContentType.objects.get_for_model(type(record)),
                object_id=record.pk,
                page=label,
                path=reverse(f"{kind}:{page}", kwargs={"uuid": record.uuid}),
                seen=now - ago,
            )

    def imports(self, user):
        """Upload two real files as regular.user and check them: one with rows to fix, one ready."""
        ImportJob.objects.filter(created_by=user, filename__in=SEED_FILES).delete()
        editable = Dataset.all_objects.with_level(user, ContributionLevel.EDIT).order_by("-modified")
        targets = list(editable[:2])
        if not targets:
            return
        definition = get_definition("rocksample")
        schema = definition.table_schema()
        names = [c.name for c in schema.columns]
        for filename, dataset, broken in (
            (SEED_FILES[0], targets[0], True),
            (SEED_FILES[-1], targets[-1], False),
        ):
            raw = self.rock_file(names, broken)
            headings = names
            matcher = HeadingMatcher(schema)
            job = ImportJob(
                dataset=dataset,
                definition_name=definition.name,
                created_by=user,
                filename=filename,
                file_format="csv",
                file_size=len(raw),
                headers=headings,
                samples={},
                column_map=matcher.match_columns(headings),
                row_count=12,
                status=ImportJob.Status.CHECKING,
            )
            job.file.save(filename, ContentFile(raw), save=False)
            job.save()
            ImportRun(job).check()
            job.refresh_from_db()
            ImportJob.objects.filter(pk=job.pk).update(created=timezone.now() - timedelta(hours=3 if broken else 26))
            self.stdout.write(f"{filename}: {job.status}")

    def rock_file(self, names, broken):
        values = {
            "name": lambda i: f"DB-{i:03d}",
            "rock_type": lambda i: self.rng.choice(["granite", "basalt", "gneiss", "schist"]),
            "mineral_content": lambda i: "quartz, feldspar, mica",
            "weight_grams": lambda i: f"{self.rng.uniform(80, 900):.1f}",
            "collection_date": lambda i: f"2026-0{self.rng.randint(1, 9)}-1{self.rng.randint(0, 9)}",
            "hardness_mohs": lambda i: f"{self.rng.uniform(3, 7):.1f}",
        }
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(names)
        for i in range(1, 13):
            row = [values.get(name, lambda i: "")(i) for name in names]
            if broken and i in (4, 9):
                row[names.index("weight_grams")] = "heavy" if "weight_grams" in names else ""
            if broken and i == 7 and "collection_date" in names:
                row[names.index("collection_date")] = "31/02/2026"
            writer.writerow(row)
        return out.getvalue().encode()
