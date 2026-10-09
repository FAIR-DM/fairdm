"""Tests for ``fairdm/conf/settings/api.py``."""

import importlib.util
import os
from pathlib import Path


class TestApi:
    def test_entry_point_has_no_post_hoc_spectacular_reconciliation(self):
        spec = importlib.util.find_spec("fairdm.conf.setup")
        source = Path(spec.origin).read_text()

        assert "SPECTACULAR_SETTINGS" not in source

    def test_spectacular_title_and_description_are_finalised_within_the_module(
        self, isolated_env, settings_module
    ):
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION, FAIRDM_API_TITLE

        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.SPECTACULAR_SETTINGS["TITLE"] == FAIRDM_API_TITLE
        assert module.SPECTACULAR_SETTINGS["DESCRIPTION"] == FAIRDM_API_DESCRIPTION

    def test_rest_framework_and_cors_are_present(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert "DEFAULT_PERMISSION_CLASSES" in module.REST_FRAMEWORK
        assert module.CORS_ALLOW_ALL_ORIGINS is True

    def test_reading_unconfigured_api_never_raises(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()
