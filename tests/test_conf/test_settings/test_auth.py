"""
Tests for ``fairdm/conf/settings/auth.py`` — the baseline authentication and
authorization configuration (FR-002, FR-003).
"""

import os


class TestAuth:
    """The baseline configures authentication with no environment branching
    (FR-002, FR-003)."""

    def test_argon2_is_the_preferred_password_hasher(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module()

        assert (
            module.PASSWORD_HASHERS[0]
            == "django.contrib.auth.hashers.Argon2PasswordHasher"
        )

    def test_authentication_backends_include_allauth_and_the_shared_object_backend(
        self, isolated_env, settings_module
    ):
        """005-core-samples T101/D-018: the shared, normalising backend is registered in
        place of raw guardian, so that a polymorphic record's object-level permissions
        resolve instead of raising ``WrongAppError``. Registered directly rather than
        reached only by delegation through one of the record-specific backends below it."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert "allauth.account.auth_backends.AuthenticationBackend" in (
            module.AUTHENTICATION_BACKENDS
        )
        assert "fairdm.core.permissions.PolymorphicObjectPermissionBackend" in (
            module.AUTHENTICATION_BACKENDS
        )
        assert "guardian.backends.ObjectPermissionBackend" not in (
            module.AUTHENTICATION_BACKENDS
        )

    def test_email_verification_is_mandatory_in_the_baseline(
        self, isolated_env, settings_module
    ):
        """Mandatory verification is the production-grade default; only
        development.py relaxes it (FR-003)."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.ACCOUNT_EMAIL_VERIFICATION == "mandatory"

    def test_reading_unconfigured_auth_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
