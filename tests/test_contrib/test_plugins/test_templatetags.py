"""Tests for plugin template tags."""

import pytest
from django.template import Context, Template
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestPluginUrl:
    TEMPLATE = "{% load plugin_tags %}{% plugin_url 'overview' %}"

    def test_the_url_is_the_record_s_own_plugin_page(self, sample):
        context = Context({"non_polymorphic_object": sample})

        assert Template(self.TEMPLATE).render(context) == reverse(
            "sample:overview", kwargs={"uuid": sample.uuid}
        )

    def test_the_object_is_used_when_there_is_no_non_polymorphic_one(self, sample):
        context = Context({"object": sample})

        assert Template(self.TEMPLATE).render(context) == reverse(
            "sample:overview", kwargs={"uuid": sample.uuid}
        )

    def test_the_non_polymorphic_object_wins_over_the_object(self, sample, dataset):
        context = Context({"non_polymorphic_object": sample, "object": dataset})

        assert Template(self.TEMPLATE).render(context) == reverse(
            "sample:overview", kwargs={"uuid": sample.uuid}
        )

    def test_without_an_object_the_url_is_empty(self):
        assert Template(self.TEMPLATE).render(Context({})) == ""


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
