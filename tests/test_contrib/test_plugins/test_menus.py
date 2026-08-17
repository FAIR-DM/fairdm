"""Navigation entries: what appears, in what order, and for whom."""

import pytest
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample


def entry_labels(model):
    menu = plugins.registry.get_plugin_menu_for_model(model)
    return [item.extra_context.get("label") for item in menu.children]


@pytest.mark.django_db
class TestEntriesAppear:
    def test_a_registration_gets_an_entry_by_default(self):
        @plugins.register(Sample, label="Listed")
        class Listed(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)
        assert "Listed" in entry_labels(Sample)

    def test_a_registration_can_decline_its_entry(self):
        @plugins.register(Sample, label="Hidden", menu=False)
        class Hidden(Plugin, TemplateView):
            template_name = "base.html"

        patterns = plugins.registry.get_urls_for_model(Sample)
        assert "Hidden" not in entry_labels(Sample)
        # ...and it is still served.
        assert "hidden" in [p.name for p in patterns]

    def test_the_declared_label_and_icon_are_used(self):
        @plugins.register(Sample, label="Chosen Label", icon="chosen-icon")
        class Chosen(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)
        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        item = next(
            i for i in menu.children if i.extra_context.get("label") == "Chosen Label"
        )
        assert item.extra_context["icon"] == "chosen-icon"

    def test_defaults_come_from_the_class_and_the_framework(self):
        @plugins.register(Sample)
        class QuietPlugin(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)
        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        item = next(
            i for i in menu.children if i.extra_context.get("label") == "Quiet Plugin"
        )
        assert item.extra_context["icon"] == "circle"

    def test_a_class_attribute_cannot_configure_the_entry(self):
        """The `menu` dict belonged to a navigation system that no longer exists."""

        @plugins.register(Sample, label="From Decorator")
        class Contested(Plugin, TemplateView):
            template_name = "base.html"
            menu = {"label": "From Attribute", "icon": "ignored", "order": -999}

        plugins.registry.get_urls_for_model(Sample)
        labels = entry_labels(Sample)
        assert "From Decorator" in labels
        assert "From Attribute" not in labels


@pytest.mark.django_db
class TestOrdering:
    def test_entries_follow_declared_position_not_registration_order(self):
        @plugins.register(Sample, label="Third", order=300)
        class Third(Plugin, TemplateView):
            template_name = "base.html"

        @plugins.register(Sample, label="First", order=100)
        class First(Plugin, TemplateView):
            template_name = "base.html"

        @plugins.register(Sample, label="Second", order=200)
        class Second(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)
        labels = [
            label
            for label in entry_labels(Sample)
            if label in {"First", "Second", "Third"}
        ]
        assert labels == ["First", "Second", "Third"]


@pytest.mark.django_db
class TestVisibilityMatchesReachability:
    """The guarantee, end to end rather than at the unit."""

    def test_a_refused_plugin_is_neither_listed_nor_reachable(
        self, client, as_user, plain_user
    ):
        from fairdm.contrib.plugins.access import can_open

        @plugins.register(Sample, label="Curation")
        class Curation(Plugin, TemplateView):
            template_name = "base.html"
            check = staticmethod(lambda request, obj: False)

        plugins.registry.get_urls_for_model(Sample)
        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        item = next(i for i in menu.children if i.extra_context.get("label") == "Curation")

        request = as_user(plain_user)
        # Not shown...
        assert item.check(request) is False
        # ...and not reachable.
        assert can_open(Curation, request, None) is False

    def test_a_permitted_plugin_is_both(self, as_user, plain_user):
        from fairdm.contrib.plugins.access import can_open

        @plugins.register(Sample, label="Open")
        class Open(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)
        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        item = next(i for i in menu.children if i.extra_context.get("label") == "Open")

        request = as_user(plain_user)
        assert item.check(request) is True
        assert can_open(Open, request, None) is True

    def test_a_plugin_whose_permission_is_missing_is_not_listed(
        self, as_user, plain_user, sample
    ):
        @plugins.register(Sample, label="Restricted")
        class Restricted(Plugin, TemplateView):
            template_name = "base.html"
            permission = "sample.delete_sample"

        plugins.registry.get_urls_for_model(Sample)
        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        item = next(
            i for i in menu.children if i.extra_context.get("label") == "Restricted"
        )
        assert item.check(as_user(plain_user), object=sample) is False


@pytest.mark.django_db
class TestMenusExistForAnyRecord:
    def test_a_record_with_no_hand_written_menu_still_gets_one(self):
        """Location had none, and the registry appended to None."""
        from fairdm.contrib.location.models import Point

        menu = plugins.registry.get_plugin_menu_for_model(Point)
        assert menu is not None
        assert plugins.registry.get_urls_for_model(Point)
