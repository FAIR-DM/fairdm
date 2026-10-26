"""An in-memory stand-in for an S3 bucket, so no test reaches the network."""

from django.core.files.base import ContentFile
from storages.backends.s3 import S3Boto3Storage
from storages.utils import clean_name


class InMemoryS3Storage(S3Boto3Storage):
    """An ``S3Boto3Storage`` whose buckets are dicts of key to bytes in ``buckets``.

    It keeps the real class's ``bucket_name``, ``location`` and key handling, so code that
    reads those behaves as it does against S3. Reset ``buckets`` between tests.
    """

    buckets: dict[str, dict[str, bytes]] = {}

    @property
    def objects(self):
        """The keys of this storage's bucket."""
        return self.buckets.setdefault(self.bucket_name, {})

    def save(self, name, content, max_length=None):
        """Store ``content`` under ``name`` in this storage's location."""
        self.objects[self._normalize_name(clean_name(name))] = content.read()
        return name

    def open(self, name, mode="rb"):
        """Return the stored bytes of ``name`` as a file."""
        return ContentFile(self.objects[self._normalize_name(clean_name(name))], name)

    def exists(self, name):
        """Return whether ``name`` is stored in this storage's location."""
        return self._normalize_name(clean_name(name)) in self.objects

    def delete(self, name):
        """Remove ``name`` from this storage's location."""
        self.objects.pop(self._normalize_name(clean_name(name)), None)

    def listdir(self, name):
        """List the directories and files directly under ``name``, as S3 does."""
        prefix = self._normalize_name(clean_name(name))
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        directories, files = set(), []
        for key in self.objects:
            if not key.startswith(prefix):
                continue
            head, separator, _ = key[len(prefix) :].partition("/")
            if separator:
                directories.add(head)
            else:
                files.append(head)
        return sorted(directories), files
