"""Tests for the contributors app configuration."""

from django.apps import apps
from django.utils.functional import Promise


class TestContributorsConfig:
    def test_app_config_is_registered_under_the_contributors_label(self):
        config = apps.get_app_config("contributors")

        assert config.name == "fairdm.contrib.contributors"
        assert config.label == "contributors"

    def test_app_config_declares_a_translatable_verbose_name(self):
        config = apps.get_app_config("contributors")

        assert isinstance(config.verbose_name, Promise)

    def test_app_config_declares_a_default_auto_field(self):
        config = apps.get_app_config("contributors")

        assert config.default_auto_field == "django.db.models.BigAutoField"
