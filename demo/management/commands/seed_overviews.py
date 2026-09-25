"""Development data for the four overview pages.

One command reaches every state the project, dataset, sample and measurement overview pages have
to answer for, and signs them in through ``regular.user``, ``staff.user`` and ``super.user`` at
``example.com`` (password ``password``). It refuses outside development, and running it again
replaces only the records it created.

    DJANGO_ENV=development python manage.py seed_overviews

See documentation: [Overview pages](docs/portal-development/overview-pages.md).
"""

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from demo.seed.measurements import MeasurementSeed
from demo.seed.projects import ProjectSeed
from demo.seed.samples import SampleSeed


class Command(BaseCommand):
    help = "Seed every state of the project, dataset, sample and measurement overview pages (development only)."

    def handle(self, *args, **options):
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        environment = apps.get_app_config("fairdm").resolved_environment()
        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to seed development data: the resolved environment {environment!r} "
                "is not a development one. The data signs in through accounts whose password is "
                "written down."
            )
        for seed in (ProjectSeed, SampleSeed, MeasurementSeed):
            seed(stdout=self.stdout, stderr=self.stderr).handle(*args, **options)
