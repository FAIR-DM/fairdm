"""
Tests for ``fairdm/conf/settings/logging.py`` — the baseline logging and
Sentry configuration, using the shared ``Env`` declaration with no
environment branching (FR-002, FR-003).
"""

import importlib.util
import os
from pathlib import Path
from unittest import mock


class TestLogging:
    def test_uses_the_shared_env_instance_not_its_own(self):
        """Contract: fairdm/conf/settings/*.py must not construct its own
        ``environ.Env()`` (contracts/settings-sections.md).

        Read as source text, not imported — the module relies on ``env``
        being injected into its scope by ``split_settings.include()``, so a
        bare import raises ``KeyError`` outside that machinery.
        """
        spec = importlib.util.find_spec("fairdm.conf.settings.logging")
        source = Path(spec.origin).read_text()

        assert "environ.Env(" not in source
        assert "Env(" not in source

    def test_sentry_initializes_when_dsn_present(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands
        os.environ["SENTRY_DSN"] = "https://fake@sentry.io/123456"

        with mock.patch("sentry_sdk.init") as mock_init:
            settings_module()

        assert mock_init.called
        assert mock_init.call_args.kwargs["dsn"] == "https://fake@sentry.io/123456"

    def test_sentry_not_initialized_when_dsn_absent(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        with mock.patch("sentry_sdk.init") as mock_init:
            settings_module()

        assert not mock_init.called

    def test_sentry_initializes_regardless_of_debug(self, isolated_env, settings_module):
        """The baseline never branches on DEBUG (FR-003) — Sentry
        initialization no longer depends on it."""
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["SENTRY_DSN"] = "https://fake@sentry.io/123456"
        os.environ["DJANGO_DEBUG"] = "True"

        with mock.patch("sentry_sdk.init") as mock_init:
            settings_module()

        assert mock_init.called

    def test_reading_unconfigured_logging_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
