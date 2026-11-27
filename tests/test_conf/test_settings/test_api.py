"""Tests for ``fairdm/conf/settings/api.py``."""

import os


class TestApi:

    def test_spectacular_title_and_description_are_finalised_within_the_module(
        self, isolated_env, settings_module
    ):
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION, FAIRDM_API_TITLE

        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.SPECTACULAR_SETTINGS["TITLE"] == FAIRDM_API_TITLE
        assert module.SPECTACULAR_SETTINGS["DESCRIPTION"] == FAIRDM_API_DESCRIPTION


