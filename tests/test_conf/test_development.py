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

    def test_development_allowed_hosts_is_localhost(self, isolated_env, settings_module):
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
