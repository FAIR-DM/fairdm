"""Tests for ``fairdm/backups/keys.py``."""

import os

import pytest
from dbbackup import settings as dbbackup_settings
from fairdm.backups.keys import BackupKey

NOT_KEYS = ["", "not a key", "-----BEGIN PGP PUBLIC KEY BLOCK-----\nnot base64\n"]


class TestBackupKeyFingerprint:
    def test_a_public_key_gives_its_fingerprint(self, key_pair, backup_tmp_dir):
        assert BackupKey(key_pair.public).fingerprint == key_pair.fingerprint

    @pytest.mark.parametrize("text", NOT_KEYS)
    def test_text_that_is_not_a_key_gives_none(self, text, backup_tmp_dir):
        assert BackupKey(text).fingerprint is None

    def test_a_key_that_cannot_encrypt_gives_none(self, sign_only_key, backup_tmp_dir):
        assert BackupKey(sign_only_key.public).fingerprint is None

    def test_a_private_key_gives_none(self, key_pair, backup_tmp_dir):
        assert "PRIVATE KEY BLOCK" in key_pair.private
        assert BackupKey(key_pair.private).fingerprint is None

    def test_reading_a_key_leaves_nothing_in_the_working_directory(
        self, key_pair, backup_tmp_dir
    ):
        BackupKey(key_pair.public).fingerprint  # noqa: B018

        assert list(backup_tmp_dir.iterdir()) == []


class TestBackupKeyKeyring:
    def test_inside_the_recipient_is_the_key_and_trust_is_given(
        self, key_pair, backup_tmp_dir
    ):
        with BackupKey(key_pair.public).keyring():
            assert key_pair.fingerprint == dbbackup_settings.GPG_RECIPIENT
            assert dbbackup_settings.GPG_ALWAYS_TRUST is True
            assert os.environ["GNUPGHOME"].startswith(str(backup_tmp_dir))

    def test_after_the_settings_and_keyring_are_as_they_were(
        self, key_pair, backup_tmp_dir, monkeypatch
    ):
        monkeypatch.setattr(dbbackup_settings, "GPG_RECIPIENT", "someone")
        monkeypatch.setattr(dbbackup_settings, "GPG_ALWAYS_TRUST", False)
        monkeypatch.setenv("GNUPGHOME", "/a/keyring")

        with BackupKey(key_pair.public).keyring():
            pass

        assert dbbackup_settings.GPG_RECIPIENT == "someone"
        assert dbbackup_settings.GPG_ALWAYS_TRUST is False
        assert os.environ["GNUPGHOME"] == "/a/keyring"
        assert list(backup_tmp_dir.iterdir()) == []

    def test_after_a_failure_inside_everything_is_restored(
        self, key_pair, backup_tmp_dir, monkeypatch
    ):
        monkeypatch.setattr(dbbackup_settings, "GPG_RECIPIENT", None)
        monkeypatch.setattr(dbbackup_settings, "GPG_ALWAYS_TRUST", None)
        monkeypatch.delenv("GNUPGHOME", raising=False)

        with pytest.raises(RuntimeError), BackupKey(key_pair.public).keyring():
            raise RuntimeError

        assert dbbackup_settings.GPG_RECIPIENT is None
        assert dbbackup_settings.GPG_ALWAYS_TRUST is None
        assert "GNUPGHOME" not in os.environ
        assert list(backup_tmp_dir.iterdir()) == []

    def test_a_text_that_is_not_a_usable_key_is_refused(self, backup_tmp_dir):
        with pytest.raises(ValueError, match="public key"), BackupKey("x").keyring():
            pass
