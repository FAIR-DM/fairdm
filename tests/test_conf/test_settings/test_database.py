"""
Tests for ``fairdm/conf/settings/database.py`` — the baseline database
configuration (FR-002, FR-003).
"""

import os


class TestDatabase:
    """The baseline configures a production-grade database from the
    environment with no environment branching (FR-002, FR-003)."""

    def test_configures_postgres_from_database_url(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands
        os.environ["DATABASE_URL"] = "postgresql://scott:tiger@dbhost:5433/mydatabase"

        module = settings_module()

        assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert module.DATABASES["default"]["NAME"] == "mydatabase"
        assert module.DATABASES["default"]["HOST"] == "dbhost"
        assert module.DATABASES["default"]["PORT"] == 5433

    def test_composes_postgres_from_discrete_vars_when_database_url_unset(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["POSTGRES_DB"] = "mydatabase"
        os.environ["POSTGRES_USER"] = "scott"
        os.environ["POSTGRES_PASSWORD"] = "tiger"
        os.environ["POSTGRES_HOST"] = "dbhost"
        os.environ["POSTGRES_PORT"] = "5433"

        module = settings_module()

        assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert module.DATABASES["default"]["NAME"] == "mydatabase"
        assert module.DATABASES["default"]["HOST"] == "dbhost"
        assert module.DATABASES["default"]["PORT"] == 5433

    def test_never_falls_back_to_sqlite_when_unconfigured(
        self, isolated_env, settings_module
    ):
        """No database configuration at all still resolves to a
        postgres-shaped (if unusable) baseline — never SQLite, which is the
        silent degradation this baseline must not perform (FR-003, D4)."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_reading_unconfigured_database_never_raises(
        self, isolated_env, settings_module
    ):
        """The baseline read is never what refuses a boot — the
        production-critical checks are (research R6's principle, applied to
        every layer-1 module, not only environment.py)."""
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
