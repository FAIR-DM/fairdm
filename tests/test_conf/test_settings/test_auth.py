"""Tests for ``fairdm/conf/settings/auth.py``."""

import os


class TestAuth:
    def test_argon2_is_the_preferred_password_hasher(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert (
            module.PASSWORD_HASHERS[0]
            == "django.contrib.auth.hashers.Argon2PasswordHasher"
        )

    def test_authentication_backends_include_allauth_and_the_shared_object_backend(
        self, isolated_env, settings_module
    ):
        # Raw guardian raises WrongAppError on a polymorphic record's object permissions, so the shared
        # normalising backend replaces it.
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
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.ACCOUNT_EMAIL_VERIFICATION == "mandatory"

    def test_reading_unconfigured_auth_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()

    def test_signup_is_open_by_default(self, isolated_env, settings_module):
        # FAIRDM_INVITATION_ONLY_SIGNUP replaces django-invitations' setting of the same purpose (#266).
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.FAIRDM_INVITATION_ONLY_SIGNUP is False

    def test_django_invitations_settings_are_gone(self, isolated_env, settings_module):
        # django-invitations was removed (#266), so its settings must not survive as dead settings.
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
