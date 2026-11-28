"""Tests for ``fairdm/conf/settings/auth.py``."""

import os


class TestAuth:
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


class TestAccountModel:
    def test_auth_user_model_resolves_to_the_real_person_class(self, db):
        from django.apps import apps
        from django.conf import settings

        from fairdm.contrib.contributors.models import Person

        assert apps.get_model(settings.AUTH_USER_MODEL) is Person
