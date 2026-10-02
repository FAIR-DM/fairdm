"""Development data for the Contributors tab.

One command reaches every state the tab has to answer for on a project, a dataset, a sample and a
measurement, and signs them in through ``regular.user``, ``staff.user`` and ``super.user`` at
``example.com`` (password ``password``). It refuses outside development, and running it again
replaces only the records it created.

    DJANGO_ENV=development python manage.py seed_contributors
"""

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from demo.seed.contributors import ContributorSeed


class Command(BaseCommand):
    help = "Seed every state of the Contributors tab (development only)."

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
        ContributorSeed(stdout=self.stdout, stderr=self.stderr).handle(*args, **options)
