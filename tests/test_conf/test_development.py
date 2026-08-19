"""
Tests for ``fairdm/conf/development.py`` — FairDM's shipped override module
for ``DJANGO_ENV=development`` (FR-004, FR-009).
"""

import os


class TestDevelopmentDefaults:
    """``development.py`` supplies a clearly-marked development-only secret
    key and a ``localhost`` allowed-hosts list, and neither value exists in
    the production baseline (FR-004, FR-009)."""

    def test_development_secret_key_is_clearly_marked_and_not_empty(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        assert module.SECRET_KEY != ""
        assert "insecure" in module.SECRET_KEY.lower()
        assert "dev" in module.SECRET_KEY.lower()

    def test_development_secret_key_not_in_production_baseline(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module()

        assert module.SECRET_KEY == ""

    def test_development_allowed_hosts_is_localhost(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        assert "localhost" in module.ALLOWED_HOSTS
        assert "*" not in module.ALLOWED_HOSTS

    def test_development_allowed_hosts_not_in_production_baseline(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert "localhost" not in module.ALLOWED_HOSTS
        assert module.ALLOWED_HOSTS == []

    def test_thumbnail_debug_is_a_development_override_not_a_baseline_default(
        self, isolated_env, settings_module
    ):
        """
        easy-thumbnails re-raises rather than degrading when this is on, so it
        belongs to development and not to the baseline every deployment gets
        (FR-003, D21).
        """
        os.environ["DJANGO_ENV"] = "qa"
        assert settings_module().THUMBNAIL_DEBUG is False

        os.environ["DJANGO_ENV"] = "development"
        assert settings_module().THUMBNAIL_DEBUG is True


class TestDevelopmentCookieNames:
    """A cookie named with the ``__Secure-`` prefix is rejected by the browser
    unless it is actually sent with the ``Secure`` attribute, so development —
    which serves plain HTTP and therefore turns that attribute off — has to
    take the prefix off the names too, or no cookie is ever stored."""

    def test_development_cookie_names_carry_no_browser_enforced_prefix(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        assert not module.CSRF_COOKIE_NAME.startswith(("__Secure-", "__Host-"))
        assert not module.SESSION_COOKIE_NAME.startswith(("__Secure-", "__Host-"))

    def test_development_pairs_no_prefixed_name_with_an_insecure_cookie(
        self, isolated_env, settings_module
    ):
        """The pairing is the defect, not either half of it: a prefixed name
        is correct when the cookie is secure, and an unprefixed name is
        correct when it is not."""
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        for name_setting, secure_setting in (
            ("CSRF_COOKIE_NAME", "CSRF_COOKIE_SECURE"),
            ("SESSION_COOKIE_NAME", "SESSION_COOKIE_SECURE"),
        ):
            name = getattr(module, name_setting)
            secure = getattr(module, secure_setting)
            assert secure or not name.startswith(("__Secure-", "__Host-")), (
                f"{name_setting}={name!r} is rejected by browsers "
                f"while {secure_setting} is False"
            )

    def test_development_csrf_cookie_is_one_a_browser_will_store(
        self, isolated_env, settings_module
    ):
        """End of the chain the report describes: the login page renders its
        hidden token either way, so the failure only shows up in the header
        that carries the matching cookie."""
        from django.http import HttpResponse
        from django.middleware.csrf import CsrfViewMiddleware, get_token
        from django.test import RequestFactory, override_settings

        os.environ["DJANGO_ENV"] = "development"
        module = settings_module()

        def view(request):
            get_token(request)  # what {% csrf_token %} does in the template
            return HttpResponse()

        with override_settings(
            CSRF_COOKIE_NAME=module.CSRF_COOKIE_NAME,
            CSRF_COOKIE_SECURE=module.CSRF_COOKIE_SECURE,
            CSRF_USE_SESSIONS=False,
        ):
            request = RequestFactory().get("/account-center/login/", secure=False)
            response = CsrfViewMiddleware(view)(request)

        cookie = response.cookies[module.CSRF_COOKIE_NAME]

        assert not (
            cookie.key.startswith(("__Secure-", "__Host-")) and not cookie["secure"]
        ), f"browsers discard this header: {cookie.OutputString()}"


class TestSetupToolsCommands:
    """``DJANGO_SETUP_TOOLS`` ships only commands FairDM actually provides —
    the template scaffold it was copied from named an app and a function that
    do not exist, which fail the boot sequence of any portal that runs them
    (FR-003, D21)."""

    def test_no_environment_declares_a_scaffold_placeholder(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        commands = settings_module().DJANGO_SETUP_TOOLS

        declared = [
            step
            for profile in commands.values()
            for key in ("on_initial", "always_run")
            for step in profile.get(key, [])
        ]
        flattened = " ".join(
            step if isinstance(step, str) else " ".join(step) for step in declared
        )

        assert "myapp" not in flattened
        assert "some_extra_func" not in flattened
