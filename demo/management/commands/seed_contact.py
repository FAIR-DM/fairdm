"""Development data for the Contact and Report a problem screens.

Builds on ``seed_overviews`` and ``seed_profiles``, which must have run first. It refuses outside
development, and running it again replaces only what it created.

    DJANGO_ENV=development python manage.py seed_contact
"""

from datetime import timedelta

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm

from fairdm.contrib.contact.models import ContactMessage, ProblemReport
from fairdm.contrib.contributors.models import Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample

PASSWORD = "password"  # noqa: S105 - the published development password


class Command(BaseCommand):
    help = "Seed every state of the Contact and Report a problem screens (development only)."

    def handle(self, *args, **options):
        from allauth.account.models import EmailAddress

        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError("Refusing to seed development data outside development.")

        def account(email, first, last, verified=True):
            person, _ = Person.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "name": f"{first} {last}",
                },
            )
            person.is_active = True
            person.is_claimed = True
            person.set_password(PASSWORD)
            person.save()
            EmailAddress.objects.update_or_create(
                user=person,
                email=email,
                defaults={"verified": verified, "primary": True},
            )
            return person

        regular = account("regular.user@example.com", "Regular", "User")
        staff = account("staff.user@example.com", "Staff", "User")
        account("super.user@example.com", "Super", "User")
        account("regular.user2@example.com", "Unverified", "User", verified=False)
        limited = account("regular.user3@example.com", "Limited", "User")
        # The named contact of the showcase dataset, and the portal's data curator, can receive mail.
        for email in ("tomás.oliveira@example.org", "anna.keller@example.org"):
            Person.objects.filter(email=email).update(is_claimed=True, is_active=True)

        ContactMessage.objects.all().delete()
        ProblemReport.objects.all().delete()

        showcase = Dataset.all_objects.get(
            name__startswith="Core samples from the Soultz"
        )
        no_contact = Dataset.all_objects.get(
            name__startswith="Deep groundwater chemistry"
        )
        orphan = Dataset.all_objects.filter(
            name__startswith="Partner laboratory ICP-MS runs"
        ).first()
        quiet = Dataset.all_objects.get(
            name__startswith="Thermal conductivity of Buntsandstein"
        )

        assign_perm("dataset.change_dataset", staff, showcase)
        assign_perm("dataset.change_dataset", staff, no_contact)
        assign_perm("dataset.change_dataset", staff, quiet)
        # Nobody on this dataset's team has an account, so its messages fall to the data curators.
        for codename in ("change_dataset", "view_dataset", "delete_dataset"):
            remove_perm(f"dataset.{codename}", staff, orphan)

        # One account already at the day's limit.
        dataset_type = ContentType.objects.get_for_model(Dataset)
        for _ in range(10):
            ContactMessage.objects.create(
                sender=limited, content_type=dataset_type, object_id=showcase.pk
            )

        samples = list(Sample.objects.filter(dataset=showcase).order_by("pk")[:3])
        measurements = list(
            Measurement.objects.filter(dataset=showcase).order_by("pk")[:2]
        )
        now = timezone.now()

        def report(record, reporter, text, age, resolved_by=None, note=""):
            made = ProblemReport.objects.create(
                reporter=reporter,
                content_type=ContentType.objects.get_for_model(record),
                object_id=record.pk,
                dataset=record if isinstance(record, Dataset) else record.dataset,
                description=text,
                state="resolved" if resolved_by else "open",
                resolved_by=resolved_by,
                resolved=now - age / 2 if resolved_by else None,
                note=note,
            )
            ProblemReport.objects.filter(pk=made.pk).update(created=now - age)
            return made

        anna = Person.objects.get(email="anna.keller@example.org")
        report(
            showcase,
            regular,
            "The methods section says the cores were logged at 0.5 m intervals, but the depth column "
            "steps by 1 m throughout. Either the description or the depths look wrong.\n\n"
            "I noticed it when trying to line these up against the 2025 campaign, where the same "
            "boreholes are logged at 0.5 m.",
            timedelta(hours=3),
        )
        report(
            samples[0],
            limited,
            "Collection depth is given as 14200 m. The borehole is about 5 km deep, so this is "
            "probably 1420 m with an extra zero.",
            timedelta(days=2),
        )
        report(
            measurements[0],
            anna,
            "Unit looks wrong: 2400 W/mK for a sandstone. Expected something near 2.4.",
            timedelta(days=6),
        )
        report(
            samples[1],
            regular,
            "The IGSN on this sample resolves to a different specimen.",
            timedelta(days=20),
            resolved_by=staff,
            note="Thanks. Two digits were swapped when the identifier was typed in. It now "
            "resolves to this core.",
        )
        report(
            measurements[1],
            regular,
            "Duplicate of the measurement above it?",
            timedelta(days=41),
            resolved_by=staff,
        )
        # A sample whose own list has exactly one report, and one whose list is empty.
        self.stdout.write("Seeded the Contact and Report a problem states.")
        for label, record in (
            ("dataset with a named contact, and reports", showcase),
            ("dataset with no contact (goes to its maintainers)", no_contact),
            ("dataset whose team has no accounts (goes to data curators)", orphan),
            ("dataset with no reports (empty list)", quiet),
            ("sample with one open report", samples[0]),
            ("sample with one resolved report", samples[1]),
            ("sample with no reports", samples[2]),
            ("measurement with one open report", measurements[0]),
        ):
            self.stdout.write(f"  {label}: {record.get_absolute_url()}")
