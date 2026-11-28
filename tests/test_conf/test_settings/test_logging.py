"""Tests for ``fairdm/conf/settings/logging.py``."""

import os
from unittest import mock


class TestLogging:
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
