"""Access control on the sample record's editing surfaces."""

from datetime import UTC, datetime

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import select_template
from django.test import RequestFactory
from django.test.utils import isolate_apps
from django.urls import reverse
from partial_date import PartialDate
from pytest_django.asserts import assertContains, assertNotContains

from demo.factories import RockSampleFactory, WaterSampleFactory, XRFMeasurementFactory
from demo.models import RockSample
from fairdm.contrib.plugins.access import can_open
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample, SampleDate, SampleDescription
from fairdm.core.sample.plugins import Descriptions, Edit, KeyDates, Keywords, Overview
from fairdm.core.utils import assign_perm
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    PointFactory,
    SampleRelationFactory,
)
from fairdm.registry import registry
from fairdm.registry.config import Citation
from fairdm.utils.choices import Visibility

EDITING_PLUGINS = [Edit, Descriptions, Keywords, KeyDates]


def _request_for(user):
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.fixture
def published_rock_sample(db):
    """A rock sample in a public, published dataset, which anyone may open."""
    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    return RockSampleFactory(dataset=dataset)


@pytest.mark.django_db
class TestSampleWritePluginsAreGated:
    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_anonymous_request_is_refused(self, plugin_class, rock_sample):
        request = _request_for(AnonymousUser())
        assert can_open(plugin_class, request, rock_sample) is False

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_signed_in_user_with_no_rights_is_refused(
        self, plugin_class, rock_sample, user
    ):
        request = _request_for(user)
        assert can_open(plugin_class, request, rock_sample) is False

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_user_holding_dataset_change_rights_is_admitted(
        self, plugin_class, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        request = _request_for(user)
        assert can_open(plugin_class, request, rock_sample) is True

    def test_the_reading_surface_stays_open_for_a_user_with_no_rights(
        self, published_rock_sample, user
    ):
        request = _request_for(user)
        assert can_open(Overview, request, published_rock_sample) is True

    def test_the_reading_surface_stays_open_for_an_anonymous_request(
        self, published_rock_sample
    ):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, published_rock_sample) is True


@pytest.mark.django_db
class TestPermissionStillGatesEvenWithAnAlwaysTruePredicate:
    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    # A truthy-but-not-callable `check` is treated by can_open as no gate at all, so
    # permission alone must still refuse an anonymous request.
    def test_an_always_true_predicate_does_not_reopen_the_surface(
        self, plugin_class, rock_sample
    ):
        always_open = type(
            f"AlwaysOpen{plugin_class.__name__}",
            (plugin_class,),
            {"check": staticmethod(lambda request, obj: True)},
        )
        request = _request_for(AnonymousUser())

        assert can_open(always_open, request, rock_sample) is False


@pytest.mark.django_db
class TestDescriptionsAndKeyDatesRenderTheirOwnForm:
    # Both pages return 200 even when InlineFormSetView silently falls back to the
    # sample's detail template, so status alone never caught it (#280).
    def test_descriptions_page_renders_the_descriptions_form_not_the_detail_page(
        self, client, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        client.force_login(user)

        response = client.get(
            reverse("sample:basic-information", kwargs={"uuid": rock_sample.uuid})
        )

        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/descriptions.html" in template_names
        assert "sample/sample_detail.html" not in template_names
        assert 'id="descriptions-form"' in response.content.decode()

    def test_key_dates_page_renders_the_key_dates_form_not_the_detail_page(
        self, client, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        client.force_login(user)

        response = client.get(
            reverse("sample:key-dates", kwargs={"uuid": rock_sample.uuid})
        )

        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/key-dates.html" in template_names
        assert "sample/sample_detail.html" not in template_names
        content = response.content.decode()
        assert "key-dates-form" in content


# Development data reaches every state; `DatasetFactory()` alone gives a private, unpublished one.
def _dataset(*, public=True, published=True):
    return DatasetFactory(
        visibility=Visibility.PUBLIC if public else Visibility.PRIVATE,
        published=published,
    )


def _page(client, sample):
    """Open the sample's page and return the response with its parsed HTML."""
    response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
    assert response.status_code == 200
    response.page = BeautifulSoup(response.content, "html.parser")
    return response


def _team_member(dataset):
    user = PersonFactory(is_active=True)
    assign_perm("view_dataset", user, dataset)
    return user


@pytest.fixture
def released():
    """A public, published dataset."""
    return _dataset()


@pytest.fixture
def rock(released):
    return RockSampleFactory(dataset=released, name="Zq-4471 rift core")


@pytest.mark.django_db
class TestOverviewTemplateChoice:
    """FR-048 and FR-049, and US-3 scenarios 1 to 3."""

    def test_a_type_with_its_own_template_uses_it_and_keeps_the_shared_page(
        self, client, rock
    ):
        response = _page(client, rock)

        names = [t.name for t in response.templates if t.name]
        assert "demo/rocksample_overview.html" in names
        assert "sample/sample_overview.html" in names
        assert response.page.find(id="citation-text") is not None

    def test_a_type_with_no_template_anywhere_uses_the_shared_page(
        self, client, released
    ):
        water = WaterSampleFactory(dataset=released)

        names = [t.name for t in _page(client, water).templates if t.name]

        assert "sample/sample_overview.html" in names
        assert not any(n.startswith("demo/") and n.endswith("_overview.html") for n in names)

    @isolate_apps("demo")
    def test_a_subtype_with_no_template_of_its_own_uses_its_parents(self):
        class Granite(RockSample):
            class Meta:
                app_label = "demo"

        plugin = Overview()
        plugin.base_object = Granite()

        chosen = select_template(plugin.get_template_names())

        assert plugin.get_template_names()[0] == "demo/granite_overview.html"
        assert chosen.template.name == "demo/rocksample_overview.html"

    def test_the_type_s_own_template_is_tried_before_any_ancestor_s(self):
        plugin = Overview()
        plugin.base_object = RockSample()

        assert plugin.get_template_names() == [
            "demo/rocksample_overview.html",
            "sample/sample_overview.html",
        ]


@pytest.mark.django_db
class TestOverviewFollowsItsDataset:
    """FR-019 and US-3 scenarios 4 and 5."""

    def test_a_visitor_opens_a_sample_in_a_published_dataset(self, client, rock):
        assert client.get(rock.get_absolute_url()).status_code == 200

    @pytest.mark.parametrize(
        ("public", "published"), [(False, False), (False, True), (True, False)]
    )
    def test_a_visitor_gets_not_found_unless_the_dataset_is_public_and_published(
        self, client, public, published
    ):
        sample = RockSampleFactory(dataset=_dataset(public=public, published=published))

        assert client.get(sample.get_absolute_url()).status_code == 404

    def test_a_hidden_sample_and_a_missing_one_raise_the_same_error(self):
        with pytest.raises(Http404) as missing:
            get_object_or_404(Sample, pk=0)
        with pytest.raises(Http404) as hidden:
            Overview().handle_no_permission()

        assert str(hidden.value) == str(missing.value)

    def test_a_signed_in_stranger_gets_not_found(self, client):
        sample = RockSampleFactory(dataset=_dataset(published=False))
        client.force_login(PersonFactory(is_active=True))

        assert client.get(sample.get_absolute_url()).status_code == 404

    def test_the_dataset_team_opens_a_sample_that_is_not_yet_released(self, client):
        dataset = _dataset(public=False, published=False)
        sample = RockSampleFactory(dataset=dataset)
        client.force_login(_team_member(dataset))

        assert client.get(sample.get_absolute_url()).status_code == 200

    def test_a_subtype_with_a_plain_manager_opens_for_the_team_and_not_for_a_visitor(
        self, client, monkeypatch
    ):
        # A portal's sample type may declare a plain manager with no `visible_to`.
        plain = models.QuerySet.as_manager()
        plain.model = RockSample
        dataset = _dataset(public=False, published=False)
        sample = RockSampleFactory(dataset=dataset)
        monkeypatch.setattr(RockSample, "objects", plain)
        assert not hasattr(RockSample.objects, "visible_to")

        assert client.get(sample.get_absolute_url()).status_code == 404
        client.force_login(_team_member(dataset))
        assert client.get(sample.get_absolute_url()).status_code == 200


@pytest.mark.django_db
class TestOverviewMeasurements:
    """FR-023 and US-3 scenarios 6 and 7."""

    def test_measurements_in_another_teams_unpublished_dataset_are_not_listed(
        self, client, rock
    ):
        shown = XRFMeasurementFactory(dataset=rock.dataset, sample=rock)
        hidden = XRFMeasurementFactory(
            dataset=_dataset(published=False), sample=rock
        )

        response = _page(client, rock)

        assert [e["measurement"].pk for e in response.context["measurements"]["items"]] == [shown.pk]
        assert response.context["counts"]["measurements"] == 1
        assertNotContains(response, hidden.get_absolute_url())

    def test_being_on_the_samples_team_opens_nothing_in_the_other_dataset(
        self, client, rock
    ):
        XRFMeasurementFactory(dataset=_dataset(published=False), sample=rock)
        client.force_login(_team_member(rock.dataset))

        assert _page(client, rock).context["measurements"]["total"] == 0

    def test_the_other_datasets_team_sees_its_measurement_marked_as_recorded_elsewhere(
        self, client, rock
    ):
        elsewhere = _dataset(published=False)
        XRFMeasurementFactory(dataset=elsewhere, sample=rock)
        client.force_login(_team_member(elsewhere))

        items = _page(client, rock).context["measurements"]["items"]

        assert [e["elsewhere"] for e in items] == [True]

    def test_the_list_shows_the_ten_most_recent_and_counts_the_rest(self, client, rock):
        measurements = XRFMeasurementFactory.create_batch(
            12, dataset=rock.dataset, sample=rock
        )
        for day, measurement in enumerate(measurements, start=1):
            Measurement.objects.filter(pk=measurement.pk).update(
                added=datetime(2026, 1, day, tzinfo=UTC)
            )

        summary = _page(client, rock).context["measurements"]

        assert summary["total"] == 12
        assert summary["more"] == 2
        assert [e["measurement"].pk for e in summary["items"]] == [
            m.pk for m in reversed(measurements[2:])
        ]


@pytest.mark.django_db
class TestOverviewRelatedSamples:
    """FR-023 and US-3 scenario 8."""

    @pytest.fixture
    def family(self, rock):
        mine = rock.dataset
        parent = RockSampleFactory(dataset=mine, name="Zq-parent-visible")
        child = RockSampleFactory(dataset=_dataset(), name="Zq-child-visible")
        hidden_parent = RockSampleFactory(
            dataset=_dataset(published=False), name="Zq-parent-hidden"
        )
        hidden_child = RockSampleFactory(
            dataset=_dataset(public=False, published=False), name="Zq-child-hidden"
        )
        SampleRelationFactory(source=rock, target=parent, type="child_of")
        SampleRelationFactory(source=rock, target=hidden_parent, type="child_of")
        SampleRelationFactory(source=child, target=rock, type="child_of")
        SampleRelationFactory(source=hidden_child, target=rock, type="child_of")
        return {
            "parent": parent,
            "child": child,
            "hidden": [hidden_parent, hidden_child],
        }

    def test_the_visible_ones_are_listed_each_saying_how_it_relates(
        self, client, rock, family
    ):
        relations = _page(client, rock).context["relations"]

        assert [(e["sample"].pk, str(e["relation"])) for e in relations["items"]] == [
            (family["parent"].pk, "Parent sample"),
            (family["child"].pk, "Subsample"),
        ]
        assert [e["elsewhere"] for e in relations["items"]] == [False, True]

    def test_the_hidden_ones_are_counted_and_never_named_or_linked(
        self, client, rock, family
    ):
        response = _page(client, rock)

        assert response.context["relations"]["hidden"] == 2
        for sample in family["hidden"]:
            assertNotContains(response, sample.name)
            assertNotContains(response, sample.get_absolute_url())
        assertContains(response, family["parent"].get_absolute_url())

    def test_the_figure_counts_only_the_ones_shown(self, client, rock, family):
        assert _page(client, rock).context["counts"]["related"] == 2

    def test_the_summary_says_how_many_parents_and_subsamples_are_shown(
        self, client, rock, family
    ):
        assert _page(client, rock).context["counts"]["related_desc"] == "1 parent · 1 subsample"

    def test_a_sample_with_no_relations_says_none_are_recorded(self, client, rock):
        counts = _page(client, rock).context["counts"]

        assert counts["related"] == 0
        assert counts["related_desc"] == "None recorded"


@pytest.mark.django_db
class TestOverviewHistory:
    """FR-038 and US-3 scenario 9."""

    def test_steps_are_in_date_order_each_dated_as_precisely_as_recorded(
        self, client, rock
    ):
        for kind, value in [
            ("Archival", "2024-03-05"),
            ("Collected", "2023"),
            ("Prepared", "2024-03"),
        ]:
            SampleDate.objects.create(related=rock, type=kind, value=PartialDate(value))

        steps = _page(client, rock).context["lifecycle"]

        assert [s["label"] for s in steps] == ["Collected", "Prepared", "Archived"]
        assert [str(s["date"]) for s in steps] == ["2023", "2024-03", "2024-03-05"]
        assert [s["day"] for s in steps][:2] == [None, None]
        assert steps[2]["day"] is not None

    def test_a_step_with_no_date_follows_the_dated_ones(self, client, rock):
        SampleDescription.objects.create(
            related=rock, type="SamplePreparation", value="Cut and polished."
        )
        SampleDate.objects.create(
            related=rock, type="Collected", value=PartialDate("2024-01-02")
        )

        steps = _page(client, rock).context["lifecycle"]

        assert [s["label"] for s in steps] == ["Collected", "Prepared"]
        assert steps[1]["date"] is None
        assert steps[1]["note"] == "Cut and polished."

    def test_people_credited_for_a_step_join_its_entry(self, client, rock):
        rock.add_contributor(PersonFactory(is_active=True), with_roles=["Collection"])

        steps = _page(client, rock).context["lifecycle"]

        assert [s["label"] for s in steps] == ["Collected"]
        assert len(steps[0]["people"]) == 1


@pytest.mark.django_db
class TestOverviewLocation:
    """US-3 scenario 10."""

    def test_a_sample_with_a_location_shows_a_map_and_lists_the_coordinates(
        self, client, released
    ):
        point = PointFactory(x="12.345678", y="45.678901")
        sample = RockSampleFactory(dataset=released, location=point)

        response = _page(client, sample)

        sample.location.refresh_from_db()
        marker = response.page.select_one(".overview-map")
        assert (marker["data-lon"], marker["data-lat"]) == (
            str(sample.location.x),
            str(sample.location.y),
        )
        assert len(response.page.select("dd.font-mono")) >= 2

    def test_a_sample_without_one_draws_no_map(self, client, rock):
        response = _page(client, rock)

        assert response.context["location"] is None
        assert response.page.select_one(".overview-map") is None


@pytest.mark.django_db
class TestOverviewTypeBadge:
    """FR-036 and US-3 scenario 11."""

    def test_a_type_the_registry_describes_opens_a_dialog(self, client, rock):
        response = _page(client, rock)

        assert response.context["type_info"]["description"]
        assert response.page.find("dialog", id="about-sample-type") is not None

    def test_a_type_the_registry_does_not_describe_opens_nothing(
        self, client, rock, monkeypatch
    ):
        monkeypatch.setattr(registry, "is_registered", lambda model: False)

        response = _page(client, rock)

        assert response.context["type_info"] is None
        assert response.page.find("dialog", id="about-sample-type") is None

    def test_a_registered_type_with_nothing_to_say_is_a_plain_badge(
        self, client, rock, monkeypatch
    ):
        config = registry.get_for_model(RockSample)
        monkeypatch.setattr(config.metadata, "description", "")
        monkeypatch.setattr(config.metadata, "citation", None)
        monkeypatch.setattr(config.metadata, "authority", None)
        monkeypatch.setattr(config.metadata, "keywords", [])
        monkeypatch.setattr(config, "description", "")

        response = _page(client, rock)

        assert response.context["type_info"] is None
        assert response.page.find("dialog", id="about-sample-type") is None
        assert response.page.select("header button[aria-haspopup=dialog]") == []

    @pytest.mark.parametrize(
        ("recorded", "linked"),
        [
            ("10.1000/xyz123", "https://doi.org/10.1000/xyz123"),
            ("https://doi.org/10.1000/xyz123", "https://doi.org/10.1000/xyz123"),
            ("http://example.org/protocol", "http://example.org/protocol"),
        ],
    )
    def test_a_protocol_doi_links_to_an_absolute_address(
        self, client, rock, monkeypatch, recorded, linked
    ):
        config = registry.get_for_model(RockSample)
        monkeypatch.setattr(
            config.metadata, "citation", Citation(text="Protocol text", doi=recorded)
        )

        response = _page(client, rock)

        dialog = response.page.find("dialog", id="about-sample-type")
        assert dialog.find("a", string="Protocol text")["href"] == linked

    def test_the_configuration_description_stands_in_for_an_empty_metadata_one(
        self, client, rock, monkeypatch
    ):
        config = registry.get_for_model(RockSample)
        monkeypatch.setattr(config.metadata, "description", "")
        monkeypatch.setattr(config, "description", "A core of rift rock.")

        response = _page(client, rock)

        assert response.context["type_info"]["description"] == "A core of rift rock."
        assert response.page.find("dialog", id="about-sample-type") is not None


@pytest.mark.django_db
class TestOverviewStatus:
    """FR-039 and US-3 scenario 12."""

    def test_a_destroyed_specimen_is_announced_as_kept_on_record(self, client, released):
        sample = RockSampleFactory(dataset=released, status="destroyed")

        response = _page(client, sample)

        assert response.context["status"]["value"] == "destroyed"
        assert response.page.select_one(".alert-warning") is not None

    def test_a_specimen_that_still_exists_carries_no_such_notice(self, client, released):
        sample = RockSampleFactory(dataset=released, status="stored")

        response = _page(client, sample)

        assert response.context["status"]["variant"] == "neutral"
        assert response.page.select_one(".alert-warning") is None

    def test_a_status_never_recorded_reads_as_unknown(self, client, rock):
        assert _page(client, rock).context["status"]["value"] == "unknown"

    def test_the_details_card_carries_the_status_and_what_it_means(self, client, rock):
        details = _page(client, rock).context["details"]

        status = next(d for d in details if d.get("icon") == "box")
        assert status["note"]


@pytest.mark.django_db
class TestOverviewCardsAlwaysShown:
    """FR-003 and the Edge Cases: a card the page has is shown even with nothing to put in it."""

    def test_a_bare_sample_shows_every_side_card(self, client, rock):
        response = _page(client, rock)

        for card in [
            "details",
            "people",
            "identifiers",
            "citation",
            "location",
            "related",
        ]:
            assert response.page.select_one(f'[data-card="{card}"]') is not None, card


@pytest.mark.django_db
class TestOverviewManageMenu:
    """FR-036: the sample's editing pages are reached from a Manage menu, not from tabs."""

    EDITING_PAGES = ["edit", "basic-information", "keywords", "key-dates"]

    def _addresses(self, sample):
        return [
            reverse(f"sample:{name}", kwargs={"uuid": sample.uuid})
            for name in self.EDITING_PAGES
        ]

    def _editor(self, dataset):
        user = PersonFactory(is_active=True)
        assign_perm("view_dataset", user, dataset)
        assign_perm("change_dataset", user, dataset)
        return user

    def _tab_hrefs(self, response):
        strip = response.page.select_one("ul.menu-horizontal")
        return [a["href"] for a in strip.select("a")]

    def test_the_tab_strip_lists_no_editing_page(self, client, rock, released):
        client.force_login(self._editor(released))

        response = _page(client, rock)

        hrefs = self._tab_hrefs(response)
        assert reverse("sample:overview", kwargs={"uuid": rock.uuid}) in hrefs
        assert not set(hrefs) & set(self._addresses(rock))

    def test_a_user_who_may_change_the_sample_sees_a_manage_menu_with_the_editing_pages(
        self, client, rock, released
    ):
        client.force_login(self._editor(released))

        response = _page(client, rock)

        menu = response.page.select_one('[data-menu="manage"]')
        assert menu is not None
        assert [a["href"] for a in menu.select("a")] == self._addresses(rock)

    def test_a_visitor_sees_no_manage_menu_and_no_editing_link(self, client, rock):
        response = _page(client, rock)

        assert response.page.select_one('[data-menu="manage"]') is None
        page_hrefs = {a.get("href") for a in response.page.select("a")}
        assert not page_hrefs & set(self._addresses(rock))

    def test_a_user_who_may_only_view_the_sample_sees_no_manage_menu(
        self, client, rock, released
    ):
        client.force_login(_team_member(released))

        response = _page(client, rock)

        assert response.page.select_one('[data-menu="manage"]') is None

    def test_the_editing_pages_keep_their_addresses(self, rock):
        assert self._addresses(rock) == [
            f"/samples/{rock.uuid}/{segment}/"
            for segment in ["edit", "basic-information", "keywords", "key-dates"]
        ]
