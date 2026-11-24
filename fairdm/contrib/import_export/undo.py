"""What an import keeps so that it can be told apart from later edits."""

import hashlib
import json


class ImportUndo:
    """The undoing of one import.

    Attributes:
        job: The import the undo is about.
    """

    def __init__(self, job):
        """Keep the import.

        Args:
            job: The import job.
        """
        self.job = job

    def digest(self, record):
        """Describe a record's stored values in one short text.

        Every concrete field's value is written with ``field.value_to_string`` and the
        values are hashed as canonical JSON. ``modified`` is one of them, so a save
        that changes nothing still changes the digest. Read the record fresh from the
        database before calling this, so the digest describes what the database holds.

        Args:
            record: The sample or measurement, as read from the database.

        Returns:
            The SHA-256 of the values, as 64 hexadecimal characters.
        """
        values = {
            field.attname: field.value_to_string(record)
            for field in record._meta.concrete_fields
        }
        canonical = json.dumps(values, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
