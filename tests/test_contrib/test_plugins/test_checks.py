"""A registration that cannot work is refused when it is made."""

import pytest
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.checks import PluginRegistrationError
from fairdm.core.dataset.models import Dataset
from fairdm.core.sample.models import Sample


class TestModelsAreRequired:
    def test_no_model_is_refused(self):
        with pytest.raises(PluginRegistrationError, match="no model was given"):

            @plugins.register()
            class NoModel(Plugin, TemplateView):
                pass

    def test_a_non_model_is_refused(self):
        with pytest.raises(PluginRegistrationError, match="expected a Django model"):

            @plugins.register("Sample")
            class NotAModel(Plugin, TemplateView):
                pass

    def test_the_message_names_what_was_passed(self):
        with pytest.raises(PluginRegistrationError, match="got str"):

            @plugins.register("Sample")
            class AlsoNotAModel(Plugin, TemplateView):
                pass


class TestUniqueness:
    def test_duplicate_name_on_one_record_is_refused(self):
        @plugins.register(Sample)
        class First(Plugin, TemplateView):
            name = "shared-name"

        with pytest.raises(PluginRegistrationError, match="already uses the name"):

            @plugins.register(Sample)
            class Second(Plugin, TemplateView):
                name = "shared-name"

    def test_the_message_names_the_plugin_and_the_record(self):
        @plugins.register(Sample)
        class Alpha(Plugin, TemplateView):
            name = "collide"

        with pytest.raises(
            PluginRegistrationError, match=r"Beta registered against Sample"
        ):

            @plugins.register(Sample)
            class Beta(Plugin, TemplateView):
                name = "collide"

    def test_the_same_name_on_different_records_is_allowed(self):
        @plugins.register(Sample)
        class OnSample(Plugin, TemplateView):
            name = "same-name"

        @plugins.register(Dataset)
        class OnDataset(Plugin, TemplateView):
            name = "same-name"

        assert OnDataset.get_name() == OnSample.get_name()

    def test_duplicate_segment_on_one_record_is_refused(self):
        @plugins.register(Sample)
        class FirstSegment(Plugin, TemplateView):
            url_path = "shared-segment"

        with pytest.raises(PluginRegistrationError, match="already serves the segment"):

            @plugins.register(Sample)
            class SecondSegment(Plugin, TemplateView):
                url_path = "shared-segment"

    def test_a_generated_address_name_cannot_collide(self):
        """Names and segments alone are not enough.

        Plugin ``a`` owning a child ``b`` generates the name ``a-b``, and so does a separate plugin
        named ``a-b``. The paths differ, so no segment check catches it, and Django keeps the last
        registration for reverse without a word.
        """

        class B(Plugin, TemplateView):
            name = "b"
            url_path = "b"

        @plugins.register(Sample)
        class A(Plugin, TemplateView):
            name = "a"
            extra_views = [B]

        with pytest.raises(PluginRegistrationError, match="already generates"):

            @plugins.register(Sample)
            class AB(Plugin, TemplateView):
                name = "a-b"


class TestRoutes:
    def test_an_unusable_segment_is_refused(self):
        with pytest.raises(PluginRegistrationError, match="is not a valid route"):

            @plugins.register(Sample)
            class BadConverter(Plugin, TemplateView):
                url_path = "<nosuchconverter:thing>"

    def test_a_route_converter_is_allowed(self):
        """An additional view needs this to address its own target."""

        class Editor(Plugin, TemplateView):
            url_path = "<int:pk>/edit"

        @plugins.register(Sample)
        class WithConverter(Plugin, TemplateView):
            extra_views = [Editor]

        names = [p.name for p in WithConverter.get_urls(model=Sample)]
        assert names == ["with-converter", "with-converter-editor"]


class TestPredicates:
    def test_a_classmethod_predicate_is_refused(self):
        """Truthy but not callable, so a naive guard would publish the page."""
        with pytest.raises(PluginRegistrationError, match="cannot be called"):

            @plugins.register(Sample)
            class ClassmethodCheck(Plugin, TemplateView):
                @classmethod
                def check(cls, request, obj):
                    return False

    def test_a_staticmethod_predicate_is_accepted(self):
        @plugins.register(Sample)
        class StaticCheck(Plugin, TemplateView):
            check = staticmethod(lambda request, obj: True)

        assert StaticCheck.get_name() == "static-check"


class TestExtraViews:
    def test_a_non_plugin_child_is_refused(self):
        class NotAPlugin:
            pass

        with pytest.raises(PluginRegistrationError, match="not a Plugin subclass"):

            @plugins.register(Sample)
            class BadChild(Plugin, TemplateView):
                extra_views = [NotAPlugin]

    def test_colliding_children_are_refused(self):
        class ChildOne(Plugin, TemplateView):
            url_path = "dup"

        class ChildTwo(Plugin, TemplateView):
            url_path = "dup"

        with pytest.raises(PluginRegistrationError, match="both claim the segment"):

            @plugins.register(Sample)
            class CollidingChildren(Plugin, TemplateView):
                extra_views = [ChildOne, ChildTwo]

    def test_a_child_colliding_with_its_parent_is_refused(self):
        class Rootless(Plugin, TemplateView):
            url_path = None

        with pytest.raises(PluginRegistrationError, match="no url_path"):

            @plugins.register(Sample)
            class ParentCollision(Plugin, TemplateView):
                extra_views = [Rootless]

    def test_nesting_is_refused(self):
        class Grandchild(Plugin, TemplateView):
            url_path = "grandchild"

        class Child(Plugin, TemplateView):
            url_path = "child"
            extra_views = [Grandchild]

        with pytest.raises(PluginRegistrationError, match="nesting is not supported"):

            @plugins.register(Sample)
            class Nested(Plugin, TemplateView):
                extra_views = [Child]


class TestRefusalHappensAtRegistration:
    def test_the_decorator_itself_raises(self):
        """Not at first request, and not from a management command.

        Registration runs at import, so it fails on every start including a production boot. The
        check framework only runs from management commands, which is a weaker guarantee than it
        looks.
        """
        with pytest.raises(PluginRegistrationError):
            plugins.register(Sample)(
                type("Dup", (Plugin, TemplateView), {"name": "at-import"})
            )
            plugins.register(Sample)(
                type("Dup2", (Plugin, TemplateView), {"name": "at-import"})
            )
