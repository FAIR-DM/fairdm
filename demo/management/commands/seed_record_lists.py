"""Development data for the Samples and Measurements tabs (specification 023).

DJANGO_ENV=development python manage.py seed_record_lists
"""

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from demo.seed.record_lists import RecordListSeed


class Command(BaseCommand):
    help = "Seed every state of the Samples and Measurements tabs (development only)."

    def handle(self, *args, **options):
        from fairdm.conf.environment import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one."
            )
        call_command("sync_vocabularies", verbosity=0)
        RecordListSeed(stdout=self.stdout, stderr=self.stderr).handle(*args, **options)
