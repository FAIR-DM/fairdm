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


class TestHoldsLevel:
    TEMPLATE = (
        "{% load plugin_tags %}"
        "{% holds_level 'edit' record as can_edit %}"
        "{% if can_edit %}shown{% endif %}"
    )

    def test_what_the_tag_guards_is_rendered_for_a_viewer_who_holds_the_level(
        self, as_user, object_perm_user, sample
    ):
        context = Context({"request": as_user(object_perm_user), "record": sample})

        assert Template(self.TEMPLATE).render(context) == "shown"

    def test_what_the_tag_guards_is_left_out_for_a_viewer_who_does_not(
        self, as_user, plain_user, sample
    ):
        context = Context({"request": as_user(plain_user), "record": sample})

        assert Template(self.TEMPLATE).render(context) == ""

    def test_what_the_tag_guards_is_left_out_for_a_visitor(
        self, as_user, anonymous_user, sample
    ):
        context = Context({"request": as_user(anonymous_user), "record": sample})

        assert Template(self.TEMPLATE).render(context) == ""

    def test_what_the_tag_guards_is_left_out_where_there_is_no_request(self, sample):
        context = Context({"record": sample})

        assert Template(self.TEMPLATE).render(context) == ""
