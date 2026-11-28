"""Tests for ``fairdm/conf/settings/email.py``."""

import os


class TestEmail:
    def test_email_host_and_backend_come_from_the_environment(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["EMAIL_HOST"] = "smtp.example.com"
        os.environ["EMAIL_HOST_USER"] = "portal@example.com"
        os.environ["EMAIL_HOST_PASSWORD"] = "s3cret"

        module = settings_module()

        assert module.EMAIL_HOST == "smtp.example.com"
        assert module.EMAIL_HOST_USER == "portal@example.com"
        assert module.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"

    def test_both_addresses_use_the_default_site_name_when_it_is_unset(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DJANGO_SITE_DOMAIN"] = "example.com"

        module = settings_module()

        assert f"{module.SITE_NAME} <noreply@example.com>" == module.DEFAULT_FROM_EMAIL
        assert f"{module.SITE_NAME} Server <server@example.com>" == module.SERVER_EMAIL
