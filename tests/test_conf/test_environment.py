"""Tests for the shared ``django-environ`` ``Env()`` declaration (FR-004, FR-006, research R6)."""

import os

from fairdm.conf.environment import env


class TestEnv:
    def test_security_critical_variables_have_no_working_default(self, isolated_env):
        # Reading an unset variable never refuses a boot. The production-critical checks do that.
        unset = {
            "DJANGO_SECRET_KEY": "",
            "DJANGO_SITE_DOMAIN": "",
            "DJANGO_SUPERUSER_PASSWORD": "",
            "DJANGO_ALLOWED_HOSTS": [],
            "DATABASE_URL": "",
            "REDIS_URL": "",
        }

        read = {name: env(name) for name in unset}

        assert read == unset


class TestNoSecurityDefaults:
    def test_settings_import_succeeds_with_everything_unset_and_publishes_no_default(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        # An empty value, never the insecure key FairDM's source once published or a localhost domain.
        assert module.SECRET_KEY == ""
        assert module.SITE_DOMAIN == ""
