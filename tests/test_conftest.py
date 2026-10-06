"""Tests for the fixtures the whole suite shares."""

import pytest
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.project.models import Project
from tests.conftest import PluginSandbox


class SandboxPage(Plugin, TemplateView):
    template_name = "base.html"


class TestPluginSandbox:
    def test_a_declared_plugin_is_served_until_the_sandbox_closes(self):
        sandbox = PluginSandbox()
        with sandbox.declare():
            plugins.register(Project)(SandboxPage)

        served = reverse("project:sandbox-page", kwargs={"uuid": "abc"})
        assert served.endswith("/abc/sandbox-page/")

        sandbox.close()

        assert SandboxPage not in [
            cls for cls, _options in plugins.registry.get_plugins_for_model(Project)
        ]
        with pytest.raises(NoReverseMatch):
            reverse("project:sandbox-page", kwargs={"uuid": "abc"})

    def test_a_plugin_is_in_the_navigation_only_while_the_sandbox_is_open(self):
        sandbox = PluginSandbox()
        with sandbox.declare():
            plugins.register(Project, label="Sandbox Page")(SandboxPage)
        menu = plugins.registry.get_plugin_menu_for_model(Project)
        assert "Sandbox Page" in [i.extra_context["label"] for i in menu.children]

        sandbox.close()

        menu = plugins.registry.get_plugin_menu_for_model(Project)
        assert "Sandbox Page" not in [i.extra_context["label"] for i in menu.children]
