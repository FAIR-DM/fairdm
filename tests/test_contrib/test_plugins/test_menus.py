"""Navigation entries: what appears, in what order, and for whom."""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.views.generic import TemplateView

from demo.factories import RockSampleFactory
from demo.models import RockSample
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample
from fairdm.factories import ContributionFactory, DatasetFactory, UserFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility


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
        item = next(
            i for i in menu.children if i.extra_context.get("label") == "Curation"
        )

        request = as_user(plain_user)
        assert item.check(request) is False
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
class TestNavigationRenders:
    def test_every_visible_entry_points_somewhere(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        content = response.content.decode()
        assert f"/samples/{sample.uuid}/" in content


@pytest.mark.django_db
class TestTheCurrentTabIsMarked:
    """The tab strip marks a plugin's tab on every address the plugin mounts."""

    @pytest.fixture
    def dataset(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset)
        return dataset

    def marked(self, response, dataset):
        """Return the addresses of the record's tabs that the strip marks as current.

        The strip is the list that holds the Overview and Contributors tabs.
        """
        page = BeautifulSoup(response.content, "html.parser")
        anchors = {
            dataset.get_absolute_url(),
            self.address("contribution-list", dataset),
        }
        strips = [
            ul
            for ul in page.find_all("ul")
            if anchors <= {a["href"] for a in ul.find_all("a", href=True)}
        ]
        strip = min(strips, key=lambda ul: len(ul.find_all("a")))
        return {
            a["href"]
            for a in strip.find_all("a", href=True)
            if a.get("aria-current") == "page"
        }

    def address(self, name, dataset, **kwargs):
        return reverse(f"dataset:{name}", kwargs={"uuid": dataset.uuid, **kwargs})

    def test_a_tab_is_marked_on_its_own_address(self, client, dataset):
        response = client.get(self.address("samples", dataset))

        assert self.marked(response, dataset) == {self.address("samples", dataset)}

    def test_a_tab_is_marked_on_an_extra_pattern_its_get_urls_mounts(
        self, client, dataset
    ):
        rock = registry.get_for_model(RockSample).get_slug()

        response = client.get(self.address("samples-type", dataset, type=rock))

        assert response.status_code == 200
        assert self.marked(response, dataset) == {self.address("samples", dataset)}

    def test_a_tab_is_not_marked_on_another_plugins_address(self, client, dataset):
        response = client.get(self.address("measurements", dataset))

        assert self.marked(response, dataset) == {self.address("measurements", dataset)}

    def test_a_tab_is_marked_on_each_of_its_extra_views(self, client, dataset):
        from fairdm.contrib.contributors.plugins.shared import ContributionList

        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        extras = ContributionList.get_extra_views()
        assert extras
        checked = 0
        for extra in extras:
            if "<int:pk>" in (extra.get_url_path() or ""):
                continue  # these name one credit and have no page without it
            name = f"contribution-list-{extra.get_name()}"
            response = client.get(self.address(name, dataset))
            assert response.status_code == 200
            assert self.marked(response, dataset) == {
                self.address("contribution-list", dataset)
            }
            checked += 1
        assert checked
