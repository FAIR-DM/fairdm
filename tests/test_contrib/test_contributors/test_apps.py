"""Tests for ``fairdm/contrib/contributors/apps.py`` — the app's own
configuration (T001)."""

from django.apps import apps
from django.utils.functional import Promise


class TestContributorsConfig:
    """The contributors app is registered under a stable label with a
    translatable verbose name and an explicit default auto field, like every
    other FairDM-owned app (e.g. ``fairdm.contrib.autocomplete``)."""

    def test_app_config_is_registered_under_the_contributors_label(self):
        config = apps.get_app_config("contributors")

        assert config.name == "fairdm.contrib.contributors"
        assert config.label == "contributors"

    def test_app_config_declares_a_translatable_verbose_name(self):
        """Assert the declared value, not merely that some string is present.

        Django supplies a verbose name derived from the app label when none is
        declared, so a truthiness check passes whether or not the app declares one.
        Comparing against a lazy proxy also proves the value went through the
        translation machinery rather than being hard-coded (Article VIII).
        """
        config = apps.get_app_config("contributors")

        assert isinstance(config.verbose_name, Promise)
        assert str(config.verbose_name) == "Community"

    def test_app_config_declares_a_default_auto_field(self):
        config = apps.get_app_config("contributors")

        assert config.default_auto_field == "django.db.models.BigAutoField"
