"""
Tests for ``fairdm/conf/settings/email.py`` — the baseline email
configuration (FR-002, FR-003).
"""

import os


class TestEmail:
    """The baseline configures email from the environment, with no
    environment branching (FR-002, FR-003)."""

    def test_email_host_and_backend_come_from_the_environment(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands
        os.environ["EMAIL_HOST"] = "smtp.example.com"
        os.environ["EMAIL_HOST_USER"] = "portal@example.com"
        os.environ["EMAIL_HOST_PASSWORD"] = "s3cret"  # noqa: S105 — test fixture value

        module = settings_module()

        assert module.EMAIL_HOST == "smtp.example.com"
        assert module.EMAIL_HOST_USER == "portal@example.com"
        assert module.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"

    def test_default_from_email_derives_from_site_domain(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DJANGO_SITE_DOMAIN"] = "example.com"
        os.environ["DJANGO_SITE_NAME"] = "Example Portal"

        module = settings_module()

        assert module.DEFAULT_FROM_EMAIL == "Example Portal <noreply@example.com>"

    def test_reading_unconfigured_email_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
