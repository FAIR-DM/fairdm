"""A media backup that does not archive the backups themselves."""

import os
from collections.abc import Iterator

from dbbackup.management.commands.mediabackup import Command
from storages.backends.s3boto3 import S3Boto3Storage


class SkippingMediaBackup(Command):
    """``mediabackup`` that leaves the backup location out of the archive.

    When the backups and the media are in one S3 bucket, with the backups under the media
    storage's location, an archive of the media would otherwise contain every earlier
    backup. The choice is made from the two storages' configured bucket and location, so
    the bucket is never listed to decide it.
    """

    def skipped_prefix(self) -> str:
        """Return the media path that holds the backups, or an empty string.

        Returns:
            The path of the backup location relative to the media storage, such as
            ``backups``. Empty unless both storages are S3 storages in one bucket and the
            backup location is inside the media location.
        """
        media, backup = self.media_storage, self.storage.storage
        if not (
            isinstance(media, S3Boto3Storage)
            and isinstance(backup, S3Boto3Storage)
            and media.bucket_name == backup.bucket_name
        ):
            return ""
        media_location = str(media.location).replace("\\", "/").strip("/")
        backup_location = str(backup.location).replace("\\", "/").strip("/")
        if not media_location:
            return backup_location
        if backup_location.startswith(f"{media_location}/"):
            return backup_location[len(media_location) + 1 :]
        return ""

    def _explore_storage(self) -> Iterator[str]:
        """Yield the media files, without descending into the backup location."""
        skipped = self.skipped_prefix()
        dirs = [""]
        while dirs:
            path = dirs.pop()
            subdirs, files = self.media_storage.listdir(path)
            for media_filename in files:
                yield os.path.join(path, media_filename)
            dirs.extend(
                os.path.join(path, subdir)
                for subdir in subdirs
                if os.path.join(path, subdir) != skipped
            )
