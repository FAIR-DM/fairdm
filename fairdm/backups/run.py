"""Run one backup of the database or the media."""

from typing import Literal

from django.core.management import call_command


def run_backup(kind: Literal["database", "media"]) -> None:
    """Write one backup and remove the oldest beyond the count to keep.

    Any failure propagates, so a scheduled run fails rather than reporting a backup it did
    not make.

    Args:
        kind: ``"database"`` for a dump of the database, ``"media"`` for an archive of the
            media files.

    Raises:
        Exception: Whatever the backup raises, such as a failed dump.
    """
    if kind == "database":
        # The custom dump format is already compressed.
        call_command("dbbackup", clean=True, compress=False)
    else:
        call_command("mediabackup", clean=True, compress=True)
