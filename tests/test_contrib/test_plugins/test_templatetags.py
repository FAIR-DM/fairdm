"""Tests for plugin template tags."""

from unittest.mock import patch

import pytest
from django.template import Context, Template

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("clear_registry")]


class TestPluginUrl:
    def test_plugin_url_with_non_polymorphic_object(self, rf, sample):
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"non_polymorphic_object": sample})

            result = template.render(context)

            mock_reverse.assert_called_once_with(sample, "test-view")
            assert result == "/sample/abc123/test-view/"

    def test_plugin_url_fallback_to_object(self, rf, sample):
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"object": sample})

            result = template.render(context)

            mock_reverse.assert_called_once_with(sample, "test-view")
            assert result == "/sample/abc123/test-view/"

    def test_plugin_url_without_object(self, rf):
        template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
        context = Context({})

        result = template.render(context)

        assert result == ""

    def test_plugin_url_with_kwargs(self, rf, sample):
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template(
                "{% load plugin_tags %}{% plugin_url 'test-view' pk=123 %}"
            )
            context = Context({"object": sample})

            result = template.render(context)

            mock_reverse.assert_called_once_with(sample, "test-view", pk=123)

    def test_plugin_url_prefers_non_polymorphic_object(self, rf, sample, dataset):
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"non_polymorphic_object": sample, "object": dataset})

            result = template.render(context)

            mock_reverse.assert_called_once_with(sample, "test-view")
