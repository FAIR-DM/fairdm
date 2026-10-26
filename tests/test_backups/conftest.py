"""Shared fixtures for tests/test_backups."""

import os
import subprocess
from types import SimpleNamespace

import gnupg
import pytest
from dbbackup import settings as dbbackup_settings
from dbbackup import utils
from dbbackup.storage import get_storage
from django.core.files.base import ContentFile

KEEP = 2


@pytest.fixture
def backup_storage(monkeypatch, settings, tmp_path):
    """Point django-dbbackup at a temporary directory and give media one file.

    django-dbbackup reads its settings once, at import, so ``override_settings`` does not
    reach it: the attributes of ``dbbackup.settings`` are patched instead.

    Returns:
        The ``dbbackup.storage.Storage`` the backup commands write to.
    """
    monkeypatch.setattr(
        dbbackup_settings, "STORAGE", "django.core.files.storage.FileSystemStorage"
    )
    monkeypatch.setattr(
        dbbackup_settings, "STORAGE_OPTIONS", {"location": str(tmp_path / "backups")}
    )
    monkeypatch.setattr(dbbackup_settings, "CLEANUP_KEEP", KEEP)
    monkeypatch.setattr(dbbackup_settings, "CLEANUP_KEEP_MEDIA", KEEP)

    media = tmp_path / "media"
    media.mkdir()
    (media / "photo.txt").write_text("a file of the portal's media")
    settings.MEDIA_ROOT = str(media)

    return get_storage()


@pytest.fixture
def seed_backups(backup_storage):
    """Return a function writing earlier backups of one kind into the backup storage."""

    def seed(content_type, count):
        """Write ``count`` backups dated 2020, oldest first, and return their names.

        django-dbbackup 5 names a dump after the database alias, ``default``.

        Args:
            content_type: ``"db"`` or ``"media"``.
            count: How many backups to write.

        Returns:
            The file names written, oldest first.
        """
        extension = "psql.bin" if content_type == "db" else "tar.gz"
        names = []
        for day in range(1, count + 1):
            name = utils.filename_generate(
                extension,
                database_name="default",
                content_type=content_type,
                wildcard=f"2020-01-0{day}-000000",
            )
            backup_storage.write_file(ContentFile(b"an earlier backup"), name)
            names.append(name)
        return names

    return seed


def generate_key(home, **options):
    """Generate a key with no passphrase in the keyring at ``home``.

    Args:
        home: The directory to use as the keyring.
        **options: Extra key parameters for ``gen_key_input``.

    Returns:
        A namespace of the keyring, ``fingerprint``, armoured ``public`` and ``private`` keys.
    """
    gpg = gnupg.GPG(gnupghome=str(home))
    parameters = gpg.gen_key_input(
        key_type="RSA",
        key_length=2048,
        name_email="backups@example.org",
        no_protection=True,
        **options,
    )
    fingerprint = gpg.gen_key(parameters).fingerprint
    return SimpleNamespace(
        home=str(home),
        fingerprint=fingerprint,
        public=gpg.export_keys(fingerprint),
        private=gpg.export_keys(fingerprint, secret=True, passphrase=""),
    )


@pytest.fixture(scope="session")
def key_pair(tmp_path_factory):
    """An RSA 2048 key pair with no passphrase, in a keyring of its own.

    That keyring trusts its own key ultimately, so a test that encrypts through it proves
    nothing about trust. Encrypt through ``BackupKey.keyring()`` and decrypt here.
    """
    return generate_key(tmp_path_factory.mktemp("gpg"))


@pytest.fixture(scope="session")
def sign_only_key(tmp_path_factory):
    """A key that can sign but not encrypt."""
    return generate_key(tmp_path_factory.mktemp("gpg-sign"), key_usage="sign")


@pytest.fixture
def backup_tmp_dir(monkeypatch, tmp_path):
    """Keep what django-dbbackup and ``BackupKey`` write while working in ``tmp_path``.

    Returns:
        The directory they write to.
    """
    directory = tmp_path / "work"
    directory.mkdir()
    monkeypatch.setattr(dbbackup_settings, "TMP_DIR", str(directory))
    return directory


def generate_expired_key(home):
    """Generate an encrypt-capable key in ``home`` whose one-day lifetime ended in 2020.

    Args:
        home: The directory to use as the keyring.

    Returns:
        A namespace holding the armoured ``public`` key.
    """
    home.chmod(0o700)
    environment = {**os.environ, "GNUPGHOME": str(home)}
    subprocess.run(
        [  # noqa: S607
            "gpg",
            "--batch",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            "",
            "--faked-system-time",
            "20200101T000000",
            "--quick-generate-key",
            "expired@example.org",
            "rsa2048",
            "sign,encr",
            "1d",
        ],
        env=environment,
        check=True,
        capture_output=True,
    )
    exported = subprocess.run(
        ["gpg", "--armor", "--export", "expired@example.org"],  # noqa: S607
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return SimpleNamespace(public=exported.stdout)


@pytest.fixture(scope="session")
def expired_key(tmp_path_factory):
    """An encrypt-capable public key that expired in 2020."""
    return generate_expired_key(tmp_path_factory.mktemp("gpg-expired"))
