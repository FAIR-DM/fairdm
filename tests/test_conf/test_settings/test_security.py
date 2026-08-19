"""
Tests for ``fairdm/conf/settings/security.py`` — the baseline security
headers configuration (FR-002, FR-003).
"""

import os


class TestSecurity:
    """The baseline sets production-grade security headers unconditionally —
    no branching on environment-derived state such as ``DJANGO_SECURE``
    (FR-002, FR-003)."""

    def test_ssl_and_cookie_security_apply_unconditionally(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module()

        assert module.SECURE_SSL_REDIRECT is True
        assert module.SESSION_COOKIE_SECURE is True
        assert module.CSRF_COOKIE_SECURE is True
        assert module.SECURE_CONTENT_TYPE_NOSNIFF is True
        assert module.SECURE_HSTS_INCLUDE_SUBDOMAINS is True

    def test_security_headers_are_not_gated_by_django_secure(
        self, isolated_env, settings_module
    ):
        """Setting DJANGO_SECURE=False no longer disables production
        security headers in the baseline — that variable is vestigial once
        the baseline stops branching on it (FR-003)."""
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DJANGO_SECURE"] = "False"

        module = settings_module()

        assert module.SECURE_SSL_REDIRECT is True
        assert module.SESSION_COOKIE_SECURE is True

    def test_baseline_keeps_the_browser_enforced_cookie_name_prefixes(
        self, isolated_env, settings_module
    ):
        """The prefix is what stops a network attacker overwriting these
        cookies from a plain-HTTP subdomain, so relaxing it for local
        development must not reach the baseline every deployment gets."""
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module()

        assert module.CSRF_COOKIE_NAME.startswith("__Secure-")
        assert module.SESSION_COOKIE_NAME.startswith("__Secure-")

    def test_reading_unconfigured_security_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise


class TestAllowedHostsComposition:
    """``ALLOWED_HOSTS`` composes from truthy entries only, so an unset
    domain yields ``[]`` rather than ``[""]`` — otherwise
    ``check_allowed_hosts_configured``'s emptiness test can never fire
    (FR-004, SC-006, research R6, T055)."""

    def test_unset_site_domain_and_allowed_hosts_yields_empty_list(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.ALLOWED_HOSTS == []

    def test_check_allowed_hosts_configured_fires_when_everything_unset(
        self, isolated_env, settings_module
    ):
        """The emptiness check FR-004/SC-006 depends on is reachable now
        that an unset domain does not smuggle in a truthy empty string."""
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
