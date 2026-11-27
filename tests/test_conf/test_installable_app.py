"""Tests for the portal as an installable app (``MVP_CONFIG["pwa"]`` in ``fairdm/conf/settings/addons.py``)."""

import json

import pytest
from django.contrib.staticfiles import finders
from django.urls import reverse


@pytest.mark.django_db
class TestManifest:
    def test_the_app_is_named_after_the_portal(self, client, settings):
        manifest = json.loads(client.get(reverse("mvp-pwa-manifest")).content)

        assert manifest["name"] == settings.SITE_NAME

    def test_every_image_the_app_names_is_in_the_static_files(self):
        missing = [
            name
            for name in (
                "brand/pwa/icon-192.png",
                "brand/pwa/icon-512.png",
                "brand/pwa/icon-maskable-512.png",
                "brand/pwa/apple-touch-icon.png",
            )
            if finders.find(name) is None
        ]

        assert missing == []
