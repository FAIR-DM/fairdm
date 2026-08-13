"""
Tests for ``fairdm/conf/settings/api.py`` — the baseline REST API
configuration, including the API-schema finalisation performed entirely
within this module rather than in the entry point (FR-002, FR-003, D10).
"""

import importlib.util
import os
from pathlib import Path


class TestApi:
    def test_entry_point_has_no_post_hoc_spectacular_reconciliation(self):
        """``fairdm.conf.setup`` must not special-case SPECTACULAR_SETTINGS
        after the layers apply — that finalisation belongs entirely to
        settings/api.py, the module that owns REST_FRAMEWORK and
        SPECTACULAR_SETTINGS (D10)."""
        spec = importlib.util.find_spec("fairdm.conf.setup")
        source = Path(spec.origin).read_text()

        assert "SPECTACULAR_SETTINGS" not in source

    def test_spectacular_title_and_description_are_finalised_within_the_module(
        self, isolated_env, settings_module
    ):
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION, FAIRDM_API_TITLE

        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module()

        assert module.SPECTACULAR_SETTINGS["TITLE"] == FAIRDM_API_TITLE
        assert module.SPECTACULAR_SETTINGS["DESCRIPTION"] == FAIRDM_API_DESCRIPTION

    def test_rest_framework_and_cors_are_present(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert "DEFAULT_PERMISSION_CLASSES" in module.REST_FRAMEWORK
        assert module.CORS_ALLOW_ALL_ORIGINS is False

    def test_reading_unconfigured_api_never_raises(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
