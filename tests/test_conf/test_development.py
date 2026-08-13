"""
Tests for ``fairdm/conf/development.py`` — FairDM's shipped override module
for ``DJANGO_ENV=development`` (FR-004, FR-009).
"""

import os


class TestDevelopmentDefaults:
    """``development.py`` supplies a clearly-marked development-only secret
    key and a ``localhost`` allowed-hosts list, and neither value exists in
    the production baseline (FR-004, FR-009)."""

    def test_development_secret_key_is_clearly_marked_and_not_empty(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        assert module.SECRET_KEY != ""
        assert "insecure" in module.SECRET_KEY.lower()
        assert "dev" in module.SECRET_KEY.lower()

    def test_development_secret_key_not_in_production_baseline(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module()

        assert module.SECRET_KEY == ""

    def test_development_allowed_hosts_is_localhost(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        assert "localhost" in module.ALLOWED_HOSTS
        assert "*" not in module.ALLOWED_HOSTS

    def test_development_allowed_hosts_not_in_production_baseline(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert "localhost" not in module.ALLOWED_HOSTS
        assert module.ALLOWED_HOSTS == []
