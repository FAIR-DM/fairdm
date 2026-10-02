"""Development data for the map of sample locations.

One command reaches every state the map has to answer for on a project, a dataset, a sample, a
person and an organization. Sign in as ``staff.user@example.com`` (password ``password``) to see
the private dataset as its team does. It refuses outside development, and running it again
replaces only the records it created.

    DJANGO_ENV=development python manage.py seed_sample_map
"""

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from demo.seed.sample_map import SampleMapSeed


class Command(BaseCommand):
    help = "Seed every state of the map of sample locations (development only)."

    def handle(self, *args, **options):
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one. The data signs in through accounts whose password is "
                "written down."
            )
        call_command("preload", verbosity=0)
        SampleMapSeed(stdout=self.stdout, stderr=self.stderr).handle(*args, **options)
