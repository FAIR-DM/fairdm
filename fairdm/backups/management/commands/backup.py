"""Back up the database and the media now, in the foreground.

Writes the same backups the scheduled tasks write, to the same place, and removes the oldest
beyond ``BACKUP_KEEP``. A failure ends the command with an error.

Usage::

    python manage.py backup
    python manage.py backup --database-only
    python manage.py backup --media-only
"""

from django.core.management.base import BaseCommand

from fairdm.backups.run import run_backup


class Command(BaseCommand):
    """Write a database backup, a media backup, or both."""

    help = "Back up the database and the media now."

    def add_arguments(self, parser):
        """Add the options that limit the backup to one kind."""
        only = parser.add_mutually_exclusive_group()
        only.add_argument(
            "--database-only", action="store_true", help="Back up the database only."
        )
        only.add_argument(
            "--media-only", action="store_true", help="Back up the media only."
        )

    def handle(self, *args, **options):
        """Run each requested backup."""
        if not options["media_only"]:
            run_backup("database")
            self.stdout.write("Database backed up.")
        if not options["database_only"]:
            run_backup("media")
            self.stdout.write("Media backed up.")
