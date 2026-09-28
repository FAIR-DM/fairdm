"""Tests for the shared ``django-environ`` ``Env()`` declaration (FR-004, FR-006, research R6)."""

import os

from fairdm.conf.environment import env


class TestEnv:
    def test_secret_key_has_no_working_default(self, isolated_env):
        assert env("DJANGO_SECRET_KEY") == ""

    def test_site_domain_has_no_working_default(self, isolated_env):
        assert env("DJANGO_SITE_DOMAIN") == ""

    def test_superuser_password_has_no_working_default(self, isolated_env):
        assert env("DJANGO_SUPERUSER_PASSWORD") == ""

    def test_allowed_hosts_has_no_working_default(self, isolated_env):
        assert env("DJANGO_ALLOWED_HOSTS") == []

    def test_database_url_has_no_working_default(self, isolated_env):
        assert env("DATABASE_URL") == ""

    def test_redis_url_has_no_working_default(self, isolated_env):
        assert env("REDIS_URL") == ""

    def test_reading_unset_security_critical_variables_never_raises(self, isolated_env):
        # The read never refuses a boot. The production-critical checks do.
        env("DJANGO_SECRET_KEY")
        env("DJANGO_SITE_DOMAIN")
        env("DJANGO_SUPERUSER_PASSWORD")
        env("DJANGO_ALLOWED_HOSTS")
        env("DATABASE_URL")
        env("REDIS_URL")


class TestNoSecurityDefaults:
    # The literal secret key FairDM's source once published as a default must never reappear as a resolved value.
    FORMERLY_PUBLISHED_SECRET_KEY = (
        "django-insecure-qQN1YqvsY7dQ1xtdhLavAeXn1mUEAI0Wu8vkDbodEqRKkJbHyMEQS5F"
    )

    def test_secret_key_resolves_to_nothing_published_or_insecure(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.SECRET_KEY != self.FORMERLY_PUBLISHED_SECRET_KEY
        assert not module.SECRET_KEY.startswith("django-insecure-")
        assert module.SECRET_KEY == ""

    def test_site_domain_resolves_to_nothing_localhost(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.SITE_DOMAIN != "localhost:8000"
        assert module.SITE_DOMAIN == ""

    def test_superuser_password_resolves_to_nothing_admin(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert env("DJANGO_SUPERUSER_PASSWORD") != "admin"
        assert env("DJANGO_SUPERUSER_PASSWORD") == ""

    def test_settings_import_still_succeeds_with_everything_unset(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()
