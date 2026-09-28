"""Tests for ``fairdm/conf/settings/logging.py``."""

import importlib.util
import os
from pathlib import Path
from unittest import mock


class TestLogging:
    def test_uses_the_shared_env_instance_not_its_own(self):
        # Read as source text: the module relies on `env` being injected by split_settings.include(),
        # so importing it directly fails.
        spec = importlib.util.find_spec("fairdm.conf.settings.logging")
        source = Path(spec.origin).read_text()

        assert "environ.Env(" not in source
        assert "Env(" not in source

    def test_sentry_initializes_when_dsn_present(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["SENTRY_DSN"] = "https://fake@sentry.io/123456"

        with mock.patch("sentry_sdk.init") as mock_init:
            settings_module()

        assert mock_init.called
        assert mock_init.call_args.kwargs["dsn"] == "https://fake@sentry.io/123456"

    def test_sentry_not_initialized_when_dsn_absent(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        with mock.patch("sentry_sdk.init") as mock_init:
            settings_module()

        assert not mock_init.called

    def test_sentry_initializes_regardless_of_debug(
        self, isolated_env, settings_module
    ):
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

        settings_module()
