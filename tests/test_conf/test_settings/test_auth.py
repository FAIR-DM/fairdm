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

    def test_signup_is_open_by_default(self, isolated_env, settings_module):
        """FAIRDM_INVITATION_ONLY_SIGNUP replaces django-invitations' setting
        of the same purpose (issue #266): self-service signup stays open
        unless a portal closes it."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.FAIRDM_INVITATION_ONLY_SIGNUP is False

    def test_django_invitations_settings_are_gone(self, isolated_env, settings_module):
        """django-invitations is removed (issue #266, GPL-3.0 incompatible with
        the MIT license). Its settings, and the django-organizations backends
        that were never an installed dependency, must not survive as dead
        settings."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        for name in (
            "INVITATIONS_INVITATION_ONLY",
            "INVITATIONS_ADAPTER",
            "INVITATION_BACKEND",
            "REGISTRATION_BACKEND",
        ):
            assert not hasattr(module, name), f"{name} should have been removed"


class TestAccountModel:
    """T003: the person record is the account, and no second account model
    exists (FR-008). Asserted by name against the setting itself, not by
    calling ``get_user_model()`` and trusting whatever it happens to
    return."""

    def test_auth_user_model_names_the_person_record(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.AUTH_USER_MODEL == "contributors.Person"

    def test_auth_user_model_resolves_to_the_real_person_class(self, db):
        from django.apps import apps
        from django.conf import settings

        from fairdm.contrib.contributors.models import Person

        assert apps.get_model(settings.AUTH_USER_MODEL) is Person
