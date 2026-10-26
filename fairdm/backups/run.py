"""Run one backup of the database or the media."""

from contextlib import nullcontext
from typing import Literal

from django.conf import settings
from django.core.management import call_command

from fairdm.backups.keys import BackupKey
from fairdm.backups.media import SkippingMediaBackup


def run_backup(kind: Literal["database", "media"]) -> None:
    """Write one backup and remove the oldest beyond the count to keep.

    The backup is encrypted to ``BACKUP_PUBLIC_KEY`` when it is set. Any failure propagates, so a
    scheduled run fails rather than reporting a backup it did not make.

    Args:
        kind: ``"database"`` for a dump of the database, ``"media"`` for an archive of the
            media files.

    Raises:
        Exception: Whatever the backup raises, such as a failed dump or a key that cannot
            encrypt.
    """
    armored = getattr(settings, "BACKUP_PUBLIC_KEY", "")
    keyring = BackupKey(armored).keyring() if armored else nullcontext()
    with keyring:
        if kind == "database":
            # The custom dump format is already compressed.
            call_command("dbbackup", clean=True, compress=False, encrypt=bool(armored))
        else:
            call_command(
                SkippingMediaBackup(),
                clean=True,
                compress=True,
                encrypt=bool(armored),
            )
