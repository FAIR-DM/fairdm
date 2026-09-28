"""Tests for ``fairdm/conf/settings/security.py``."""

import os


class TestSecurity:
    def test_ssl_and_cookie_security_apply_unconditionally(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.SECURE_SSL_REDIRECT is True
        assert module.SESSION_COOKIE_SECURE is True
        assert module.CSRF_COOKIE_SECURE is True
        assert module.SECURE_CONTENT_TYPE_NOSNIFF is True
        assert module.SECURE_HSTS_INCLUDE_SUBDOMAINS is True

    def test_security_headers_are_not_gated_by_django_secure(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DJANGO_SECURE"] = "False"

        module = settings_module()

        assert module.SECURE_SSL_REDIRECT is True
        assert module.SESSION_COOKIE_SECURE is True

    def test_baseline_keeps_the_browser_enforced_cookie_name_prefixes(
        self, isolated_env, settings_module
    ):
        # The prefix stops a network attacker overwriting these cookies from a plain-HTTP subdomain.
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.CSRF_COOKIE_NAME.startswith("__Secure-")
        assert module.SESSION_COOKIE_NAME.startswith("__Secure-")

    def test_reading_unconfigured_security_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()


class TestAllowedHostsComposition:
    # Only truthy entries compose, so an unset domain gives [] rather than [""]. Otherwise the
    # emptiness check could never fire.
    def test_unset_site_domain_and_allowed_hosts_yields_empty_list(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.ALLOWED_HOSTS == []

    def test_check_allowed_hosts_configured_fires_when_everything_unset(
        self, isolated_env, settings_module
    ):
        from django.test import override_settings

        from fairdm.conf.checks import check_allowed_hosts_configured

        os.environ["DJANGO_ENV"] = "qa"
        module = settings_module()

        with override_settings(ALLOWED_HOSTS=module.ALLOWED_HOSTS):
            errors = check_allowed_hosts_configured(app_configs=None)

        assert len(errors) == 1
        assert errors[0].id == "fairdm.E003"

    def test_configured_domain_and_extra_hosts_both_included(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DJANGO_SITE_DOMAIN"] = "example.com"
        os.environ["DJANGO_ALLOWED_HOSTS"] = "www.example.com,api.example.com"

        module = settings_module()

        assert module.ALLOWED_HOSTS == [
            "example.com",
            "www.example.com",
            "api.example.com",
        ]
