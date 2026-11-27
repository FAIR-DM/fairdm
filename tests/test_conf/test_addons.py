"""Tests for FairDM addon integration system."""

import importlib
import os
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import clear_url_caches, resolve

from fairdm.conf.addons import discover_addon_urls


@pytest.fixture
def addon_env():
    original_env = os.environ.copy()

    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    os.environ.update(
        {
            "DJANGO_ENV": "development",
            "DJANGO_SECRET_KEY": "test_secret_key_1234567890",
            "DJANGO_SITE_DOMAIN": "localhost:8000",
            "DJANGO_SITE_NAME": "Test Portal",
        }
    )

    yield

    os.environ.clear()
    os.environ.update(original_env)


class TestAddonDiscovery:
    def test_addon_with_setup_module_is_loaded(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.dummy_addon'])",
            directory=tmp_path,
        )

        assert module.DUMMY_ADDON_INSTALLED is True
        assert module.DUMMY_ADDON_VERSION == "1.0.0"
        # The addon's settings are added to the composed ones, not substituted for them.
        assert "tests.test_conf.dummy_addon" in module.INSTALLED_APPS
        assert "django.contrib.auth" in module.INSTALLED_APPS
        assert "dummy_addon" in module.LOGGING["loggers"]

    def test_addon_without_setup_module_logs_warning(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.addons.logger.warning") as mock_warning:
            module = settings_module(
                setup_call="fairdm.setup(addons=['tests.test_conf.no_setup_addon'])",
                directory=tmp_path,
            )

        assert module.DJANGO_ENV == "development"

        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "does not define '__fdm_setup_module__'" in warned_text
        assert "no_setup_addon" in warned_text

    def test_addon_with_invalid_module_fails_gracefully_in_development(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.checks.logger.warning") as mock_warning:
            module = settings_module(
                setup_call="fairdm.setup(addons=['tests.test_conf.unloadable_addon'])",
                directory=tmp_path,
            )

        assert module.DJANGO_ENV == "development"

        assert mock_warning.called
        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "unloadable_addon" in warned_text

        from fairdm.conf import record

        addons_layer = next(
            layer for layer in record.layers() if layer.name == "addons"
        )
        assert addons_layer.found is False
        assert addons_layer.settings == ()

    def test_addon_url_discovery(self, addon_env, tmp_path):
        from fairdm.conf.addons import addon_urls, discover_addon_urls

        addon_urls.clear()

        urls = discover_addon_urls(["tests.test_conf.dummy_addon"])

        assert "tests.test_conf.dummy_addon.urls" in urls


class TestAddonUrlMounting:
    @pytest.fixture
    def root_urls(self):
        from fairdm.conf import urls

        yield urls

        discover_addon_urls([])
        importlib.reload(urls)
        clear_url_caches()

    def test_an_address_the_addon_defines_resolves(
        self, production_env, settings_module, root_urls
    ):
        os.environ["DJANGO_ENV"] = "development"

        settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.routed_addon'])"
        )
        importlib.reload(root_urls)
        clear_url_caches()

        match = resolve("/routed-addon/", urlconf=root_urls)

        assert match.url_name == "routed-addon-page"

    def test_an_addon_address_shaped_like_a_portal_id_wins_over_the_permalink(
        self, production_env, settings_module, root_urls
    ):
        os.environ["DJANGO_ENV"] = "development"

        settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.routed_addon'])"
        )
        importlib.reload(root_urls)
        clear_url_caches()

        match = resolve("/p" + "2" * 22 + "/", urlconf=root_urls)

        assert match.url_name == "routed-addon-portal-id-page"


class TestAddonPosition:
    def test_addon_setting_beats_fairdm_environment_override(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.conflicting_addon'])",
            directory=tmp_path,
        )

        # fairdm/conf/development.py (layer 2) sets DEBUG = True; the addon
        # (layer 3) applies after it and must win.
        assert module.DEBUG == "addon-value"

    def test_portal_environment_override_beats_addon_setting(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text("DEBUG = 'portal-value'\n")

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.conflicting_addon'])",
            directory=tmp_path,
        )

        # The portal's own override (layer 4) applies after the addon
        # (layer 3) and must win.
        assert module.DEBUG == "portal-value"


class TestEnvironmentsThatStopOnABrokenAddon:
    @pytest.mark.parametrize("environment", ["production", "prod", "staging", ""])
    @pytest.mark.parametrize(
        "addon",
        ["tests.test_conf.broken_execution_addon", "tests.test_conf.unloadable_addon"],
    )
    def test_every_environment_built_on_the_baseline_refuses_to_start(
        self, production_env, settings_module, environment, addon
    ):
        os.environ["DJANGO_ENV"] = environment

        with pytest.raises(ImproperlyConfigured, match=addon):
            settings_module(setup_call=f"fairdm.setup(addons=['{addon}'])")


class TestAddonPartialFailure:

    def test_partial_write_does_not_reach_settings_in_development(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.setup.logger.warning") as mock_warning:
            module = settings_module(
                setup_call=(
                    "fairdm.setup(addons=['tests.test_conf.broken_execution_addon'])"
                ),
                directory=tmp_path,
            )

        # The portal started, and the addon's partial write never reached
        # the composed scope — assert the scope, not just the exception.
        assert not hasattr(module, "BROKEN_EXECUTION_ADDON_PARTIAL")

        assert mock_warning.called
        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "broken_execution_addon" in warned_text

        from fairdm.conf import record

        addons_layer = next(
            layer for layer in record.layers() if layer.name == "addons"
        )
        assert addons_layer.found is False
        assert "BROKEN_EXECUTION_ADDON_PARTIAL" not in addons_layer.settings


class TestAddonScopeIsolation:
    def test_portal_non_setting_objects_keep_their_identity(
        self, production_env, tmp_path, settings_module
    ):
        # setup() runs each addon against a copy of the scope and merges it back, which must not rebind
        # names Django never reads, such as a list or dict a portal shares with another module.
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(
            setup_call=(
                "shared = {'a': 1}\n"
                "alias = shared\n"
                "fairdm.setup(addons=['tests.test_conf.conflicting_addon'])"
            ),
            after="SHARED_IDENTITY_KEPT = shared is alias",
            directory=tmp_path,
        )

        assert module.SHARED_IDENTITY_KEPT is True
        # The addon still applied — the isolation is scoped, not disabled.
        assert module.DEBUG == "addon-value"

    def test_in_place_mutation_by_a_failing_addon_is_discarded(
        self, production_env, tmp_path, settings_module
    ):
        # The scratch scope must copy the container, not just the binding: a shallow copy shares the list
        # that `INSTALLED_APPS += [...]` mutates.
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.setup.logger.warning"):
            module = settings_module(
                setup_call=(
                    "fairdm.setup(addons=['tests.test_conf.mutating_broken_addon'])"
                ),
                directory=tmp_path,
            )

        assert "tests.test_conf.mutating_broken_addon" not in module.INSTALLED_APPS
