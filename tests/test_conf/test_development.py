"""Tests for ``fairdm/conf/development.py``."""

import os


class TestDevelopmentDefaults:
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
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.SECRET_KEY == ""

    def test_development_allows_any_host(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module()

        assert module.ALLOWED_HOSTS == ["*"]

    def test_development_allowed_hosts_not_in_production_baseline(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.ALLOWED_HOSTS == []

    def test_thumbnail_debug_is_a_development_override_not_a_baseline_default(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        assert settings_module().THUMBNAIL_DEBUG is False

        os.environ["DJANGO_ENV"] = "development"
        assert settings_module().THUMBNAIL_DEBUG is True


class TestDevelopmentCookieNames:
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


LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
REDIS = "django_redis.cache.RedisCache"


class TestDevelopmentWithoutRedis:
    def test_every_cache_alias_is_in_memory_when_redis_url_is_unset(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        baseline_aliases = set(settings_module().CACHES)

        os.environ["DJANGO_ENV"] = "development"
        caches = settings_module().CACHES

        assert set(caches) == baseline_aliases
        assert {config["BACKEND"] for config in caches.values()} == {LOCMEM}

    def test_in_memory_aliases_do_not_share_a_store(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        caches = settings_module().CACHES

        locations = [config["LOCATION"] for config in caches.values()]
        assert len(set(locations)) == len(locations)

    def test_an_empty_redis_url_counts_as_unset(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "development"
        os.environ["REDIS_URL"] = ""

        module = settings_module()

        assert module.CACHES["default"]["BACKEND"] == LOCMEM
        assert module.CELERY_TASK_ALWAYS_EAGER is True

    def test_first_sign_in_attempt_is_not_rate_limited(
        self, isolated_env, settings_module
    ):
        from allauth.core import ratelimit
        from django.test import RequestFactory, override_settings

        os.environ["DJANGO_ENV"] = "development"
        module = settings_module()
        request = RequestFactory().post("/account-center/login/")

        with override_settings(CACHES=module.CACHES):
            assert ratelimit.consume(request, action="login", key="someone@example.com")

    def test_tasks_run_in_process_when_redis_url_is_unset(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        assert settings_module().CELERY_TASK_ALWAYS_EAGER is True

    def test_a_configured_redis_url_is_used_as_given(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        os.environ["REDIS_URL"] = "redis://cachehost:6380/2"

        module = settings_module()

        assert {config["BACKEND"] for config in module.CACHES.values()} == {REDIS}
        assert module.CACHES["default"]["LOCATION"] == "redis://cachehost:6380/2"
        assert module.CELERY_BROKER_URL == "redis://cachehost:6380/2"
        assert module.CELERY_TASK_ALWAYS_EAGER is False


class TestSetupToolsCommands:
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
