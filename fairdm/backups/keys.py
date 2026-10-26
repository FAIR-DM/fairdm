"""The public key a portal's backups are encrypted to."""

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

import gnupg
from dbbackup import settings as dbbackup_settings


class BackupKey:
    """An armoured OpenPGP public key that backups are encrypted to.

    One class serves the production checks and ``run_backup``, so what the checks accept is
    exactly what a backup is encrypted with.

    Args:
        armored: The key as armoured text, such as the value of ``BACKUP_PUBLIC_KEY``.
    """

    PRIVATE_ARMOUR = "PRIVATE KEY BLOCK"

    def __init__(self, armored: str):
        self.armored = armored

    @contextmanager
    def home(self) -> Iterator[str]:
        """Yield a new, empty keyring directory and remove it on exit.

        Yields:
            The path of the directory, under django-dbbackup's temporary directory.
        """
        directory = tempfile.mkdtemp(dir=dbbackup_settings.TMP_DIR)
        try:
            yield directory
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def import_into(self, home: str) -> str | None:
        """Import the key into the keyring at ``home``.

        Args:
            home: The keyring directory.

        Returns:
            The fingerprint of a key that can encrypt, or ``None`` when the text holds no such
            key, or holds secret key material.

        Raises:
            OSError: gpg is not installed.
        """
        if self.PRIVATE_ARMOUR in self.armored:
            return None
        gpg = gnupg.GPG(gnupghome=home)
        gpg.import_keys(self.armored)
        for key in gpg.list_keys():
            if "e" in key["cap"].lower():
                return str(key["fingerprint"])
        return None

    @property
    def fingerprint(self) -> str | None:
        """The fingerprint of a key that can encrypt, or ``None``.

        It is ``None`` when the text is not an armoured public key, the key cannot encrypt, or
        the text holds a secret key, so the portal never holds the key that decrypts its backups.

        Raises:
            OSError: gpg is not installed.
        """
        with self.home() as home:
            return self.import_into(home)

    @contextmanager
    def keyring(self) -> Iterator[None]:
        """Make django-dbbackup encrypt to this key for the length of the block.

        The key is imported into a new keyring that is removed on exit. django-dbbackup
        overwrites its trust setting when it is imported, and gpg refuses a recipient whose
        trust is unknown, so trust is set here. The keyring, recipient and trust are restored on
        exit, also after an exception.

        Yields:
            Nothing.

        Raises:
            ValueError: The text is not a public key that can encrypt.
            OSError: gpg is not installed.
        """
        with self.home() as home:
            fingerprint = self.import_into(home)
            if fingerprint is None:
                msg = "BACKUP_PUBLIC_KEY is not a public key that can encrypt."
                raise ValueError(msg)
            previous = (
                dbbackup_settings.GPG_RECIPIENT,
                dbbackup_settings.GPG_ALWAYS_TRUST,
                os.environ.get("GNUPGHOME"),
            )
            dbbackup_settings.GPG_RECIPIENT = fingerprint
            dbbackup_settings.GPG_ALWAYS_TRUST = True
            os.environ["GNUPGHOME"] = home
            try:
                yield
            finally:
                dbbackup_settings.GPG_RECIPIENT, dbbackup_settings.GPG_ALWAYS_TRUST = (
                    previous[:2]
                )
                if previous[2] is None:
                    os.environ.pop("GNUPGHOME", None)
                else:
                    os.environ["GNUPGHOME"] = previous[2]
