"""Tests for plugin template tags."""

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from unittest.mock import patch

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.dataset.models import Dataset
from fairdm.core.sample.models import Sample
from fairdm.factories.contributors import UserFactory

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("clear_registry")]


class TestGetPluginTabs:
    """Tests for get_plugin_tabs template tag."""

    def test_get_plugin_tabs_with_model_and_object(self, rf: RequestFactory, sample):
        """get_plugin_tabs should return tabs for a model+object."""

        @plugins.register(Sample)
        class TestPlugin(Plugin):
            name = "test"
            menu = {"label": "Test", "order": 0}
            template_name = "test.html"

        request = rf.get("/")
        request.user = UserFactory()

        template = Template(
            "{% load plugin_tags %}{% get_plugin_tabs model=model obj=obj as tabs %}{{ tabs|length }}"
        )
        context = Context({"request": request, "model": Sample, "obj": sample})
        result = template.render(context)

        # Should return at least the test plugin
        assert int(result) > 0

    def test_get_plugin_tabs_with_model_only(self, rf: RequestFactory):
        """get_plugin_tabs should work with just a model (no object)."""

        @plugins.register(Sample)
        class TestPlugin(Plugin):
            name = "test"
            menu = {"label": "Test", "order": 0}
            template_name = "test.html"

        request = rf.get("/")
        request.user = UserFactory()

        template = Template(
            "{% load plugin_tags %}{% get_plugin_tabs model=model as tabs %}{{ tabs|length }}"
        )
        context = Context({"request": request, "model": Sample})
        result = template.render(context)

        assert result == "1"

    def test_get_plugin_tabs_infers_model_from_object(self, rf: RequestFactory, sample):
        """get_plugin_tabs should infer model from obj if model not provided."""

        @plugins.register(Sample)
        class TestPlugin(Plugin):
            name = "test"
            menu = {"label": "Test", "order": 0}
            template_name = "test.html"
        request = rf.get("/")
        request.user = UserFactory()

        template = Template(
            "{% load plugin_tags %}{% get_plugin_tabs obj=obj as tabs %}{{ tabs|length }}"
        )
        context = Context({"request": request, "obj": sample})
        result = template.render(context)

        assert int(result) > 0

    def test_get_plugin_tabs_without_request(self):
        """get_plugin_tabs should return empty list without request."""
        template = Template(
            "{% load plugin_tags %}{% get_plugin_tabs model=model as tabs %}{{ tabs|length }}"
        )
        context = Context({"model": Sample})  # No request
        result = template.render(context)

        assert result.strip() == "0"

    def test_get_plugin_tabs_without_model_or_object(self, rf: RequestFactory):
        """get_plugin_tabs should return empty list without model or obj."""
        request = rf.get("/")
        request.user = UserFactory()

        template = Template("{% load plugin_tags %}{% get_plugin_tabs as tabs %}{{ tabs|length }}")
        context = Context({"request": request})
        result = template.render(context)

        assert result.strip() == "0"

    def test_get_plugin_tabs_respects_order(self, rf: RequestFactory):
        """get_plugin_tabs should return tabs sorted by order."""

        @plugins.register(Sample)
        class Plugin1(Plugin):
            name = "plugin1"
            menu = {"label": "ZZZ", "order": 10}
            template_name = "test.html"

        @plugins.register(Sample)
        class Plugin2(Plugin):
            name = "plugin2"
            menu = {"label": "AAA", "order": 1}
            template_name = "test.html"

        @plugins.register(Sample)
        class Plugin3(Plugin):
            name = "plugin3"
            menu = {"label": "MMM", "order": 5}
            template_name = "test.html"

        request = rf.get("/")
        request.user = UserFactory()

        template = Template(
            "{% load plugin_tags %}{% get_plugin_tabs model=model as tabs %}"
            "{% for tab in tabs %}{{ tab.order }},{% endfor %}"
        )
        context = Context({"request": request, "model": Sample})
        result = template.render(context)

        # Order should be ascending (1, 5, 10, ...)
        orders = [int(x) for x in result.strip().rstrip(",").split(",") if x]
        assert orders == sorted(orders)


class TestPluginUrl:
    """Tests for plugin_url template tag."""

    def test_plugin_url_with_non_polymorphic_object(self, rf, sample):
        """plugin_url should use non_polymorphic_object from context."""
        with patch("fairdm.contrib.plugins.templatetags.plugin_tags.reverse") as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"
            
            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"non_polymorphic_object": sample})
            
            result = template.render(context)
            
            # Should call reverse with the sample object
            mock_reverse.assert_called_once_with(sample, 'test-view')
            assert result == "/sample/abc123/test-view/"

    def test_plugin_url_fallback_to_object(self, rf, sample):
        """plugin_url should fall back to 'object' if non_polymorphic_object not present."""
        with patch("fairdm.contrib.plugins.templatetags.plugin_tags.reverse") as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"
            
            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"object": sample})
            
            result = template.render(context)
            
            # Should call reverse with the sample object
            mock_reverse.assert_called_once_with(sample, 'test-view')
            assert result == "/sample/abc123/test-view/"

    def test_plugin_url_without_object(self, rf):
        """plugin_url should return empty string when no object in context."""
        template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
        context = Context({})
        
        result = template.render(context)
        
        assert result == ""

    def test_plugin_url_with_kwargs(self, rf, sample):
        """plugin_url should pass kwargs to reverse function."""
        with patch("fairdm.contrib.plugins.templatetags.plugin_tags.reverse") as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"
            
            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' pk=123 %}")
            context = Context({"object": sample})
            
            result = template.render(context)
            
            # Should call reverse with kwargs
            mock_reverse.assert_called_once_with(sample, 'test-view', pk=123)

    def test_plugin_url_prefers_non_polymorphic_object(self, rf, sample, dataset):
        """plugin_url should prefer non_polymorphic_object over object."""
        with patch("fairdm.contrib.plugins.templatetags.plugin_tags.reverse") as mock_reverse:
            mock_reverse.return_value = "/sample/abc123/test-view/"
            
            template = Template("{% load plugin_tags %}{% plugin_url 'test-view' %}")
            context = Context({"non_polymorphic_object": sample, "object": dataset})
            
            result = template.render(context)
            
            # Should use sample (non_polymorphic_object), not dataset
            mock_reverse.assert_called_once_with(sample, 'test-view')
