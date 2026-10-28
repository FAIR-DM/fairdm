"""Development data for the record search fields.

    DJANGO_ENV=development python manage.py seed_record_search

Pass ``--large`` to add a public dataset of 100,000 samples as well. It refuses outside
development, and running it again adds only what is missing.
"""

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from demo.seed.record_search import LARGE_SAMPLE_COUNT, RecordSearchSeed


class Command(BaseCommand):
    help = (
        "Seed the records the search fields are walked through with (development only)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--large",
            action="store_true",
            help=f"Also seed a public dataset of {LARGE_SAMPLE_COUNT:,} samples.",
        )

    def handle(self, *args, **options):
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one. The data signs in through accounts whose password is "
                "written down."
            )
        call_command("sync_vocabularies", verbosity=0)
        RecordSearchSeed(stdout=self.stdout).handle(large=options["large"])
        self.stdout.write(self.style.SUCCESS("Seeded the record search records."))
