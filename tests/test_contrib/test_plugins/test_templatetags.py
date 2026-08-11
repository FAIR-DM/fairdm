"""Tests for plugin template tags."""

from unittest.mock import patch

import pytest
from django.template import Context, Template

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("clear_registry")]


class TestPluginUrl:
    """Tests for plugin_url template tag."""

    def test_plugin_url_with_non_polymorphic_object(self, rf, sample):
        """plugin_url should use non_polymorphic_object from context."""
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"non_polymorphic_object": sample})

            result = template.render(context)

            # Should call reverse with the sample object
            mock_reverse.assert_called_once_with(sample, "test-view")
            assert result == "/sample/abc123/test-view/"

    def test_plugin_url_fallback_to_object(self, rf, sample):
        """plugin_url should fall back to 'object' if non_polymorphic_object not present."""
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"object": sample})

            result = template.render(context)

            # Should call reverse with the sample object
            mock_reverse.assert_called_once_with(sample, "test-view")
            assert result == "/sample/abc123/test-view/"

    def test_plugin_url_without_object(self, rf):
        """plugin_url should return empty string when no object in context."""
        template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
        context = Context({})

        result = template.render(context)

        assert result == ""

    def test_plugin_url_with_kwargs(self, rf, sample):
        """plugin_url should pass kwargs to reverse function."""
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template(
                "{% load plugin_tags %}{% plugin_url 'test-view' pk=123 %}"
            )
            context = Context({"object": sample})

            result = template.render(context)

            # Should call reverse with kwargs
            mock_reverse.assert_called_once_with(sample, "test-view", pk=123)

    def test_plugin_url_prefers_non_polymorphic_object(self, rf, sample, dataset):
        """plugin_url should prefer non_polymorphic_object over object."""
        with patch(
            "fairdm.contrib.plugins.templatetags.plugin_tags.reverse"
        ) as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"

            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"non_polymorphic_object": sample, "object": dataset})

            result = template.render(context)

            # Should use sample (non_polymorphic_object), not dataset
            mock_reverse.assert_called_once_with(sample, "test-view")
