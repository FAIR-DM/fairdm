"""
Tests for the shared ``django-environ`` ``Env()`` declaration (FR-004, FR-006,
research R6).
"""

import os

from fairdm.conf.environment import env


class TestEnv:
    """No security-critical variable in the shared ``Env`` carries a *working*
    default — each resolves to an explicitly unusable sentinel when the
    corresponding environment variable is unset, and the read itself never
    raises (FR-004, FR-006, research R6)."""

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
        """The read is never what refuses a boot — the production-critical
        checks are (research R6). All six resolve without an exception even
        though none of them carries a usable value."""
        env("DJANGO_SECRET_KEY")
        env("DJANGO_SITE_DOMAIN")
        env("DJANGO_SUPERUSER_PASSWORD")
        env("DJANGO_ALLOWED_HOSTS")
        env("DATABASE_URL")
        env("REDIS_URL")


class TestNoSecurityDefaults:
    """With ``DJANGO_SECRET_KEY``, ``DJANGO_SITE_DOMAIN`` and the
    administrative password unset, the baseline resolves to values nothing
    accepts — no published literal, no ``localhost`` domain, no ``admin``
    password — and settings import still succeeds so development and the
    test suite can run (FR-004, SC-006)."""

    #: The literal secret key FairDM's source used to publish as a default
    #: (research R6) — must never reappear as a resolved value.
    FORMERLY_PUBLISHED_SECRET_KEY = (
        "django-insecure-qQN1YqvsY7dQ1xtdhLavAeXn1mUEAI0Wu8vkDbodEqRKkJbHyMEQS5F"
    )

    def test_secret_key_resolves_to_nothing_published_or_insecure(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

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
        """The absence of every security-critical value does not raise —
        development and the test suite depend on being able to boot without
        them (FR-004, SC-006)."""
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
