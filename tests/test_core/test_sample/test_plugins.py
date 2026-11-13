"""Access control on the sample record's editing surfaces."""

import codecs
from datetime import UTC, datetime

import latexcodec  # noqa: F401  (registers the "ulatex" codec)
import pytest
import rispy
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.sites.models import Site
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import select_template
from django.test import RequestFactory
from django.test.utils import isolate_apps
from django.urls import reverse
from partial_dates import PartialDate
from pybtex.database import parse_string
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    WaterSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import RockSample
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.plugins.access import can_open
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import (
    Sample,
    SampleDate,
    SampleDescription,
)
from fairdm.core.sample.plugins import Overview
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IGSN,
    SAMPLE_STATUS,
)
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    SampleIdentifierFactory,
    SampleRelationFactory,
)
from fairdm.registry import registry
from fairdm.registry.config import Citation
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteSampleFactory


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
class TestSampleReadingSurfaceIsOpen:
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
    ContributionFactory(
        content_object=dataset, contributor=user, level=ContributionLevel.VIEW
    )
    return user


@pytest.fixture
def released():
    """A public, published dataset."""
    return _dataset()


@pytest.fixture
def rock(released):
    return RockSampleFactory(dataset=released, name="Zq-4471 rift core")


@pytest.mark.django_db
class TestOverviewAddress:
    def test_the_page_opens_at_the_samples_own_address(self, client, rock):
        assert rock.get_absolute_url() == f"/samples/{rock.uuid}/"
        assert client.get(f"/samples/{rock.uuid}/").status_code == 200

    def test_the_former_address_redirects_to_the_samples_own_address(
        self, client, rock
    ):
        response = client.get(f"/samples/{rock.uuid}/overview/?from=citation")

        assertRedirects(
            response, f"/samples/{rock.uuid}/?from=citation", status_code=301
        )

    def test_the_former_address_says_no_more_than_the_page_about_a_private_sample(
        self, client
    ):
        private = RockSampleFactory(dataset=_dataset(public=False, published=False))

        response = client.get(f"/samples/{private.uuid}/overview/", follow=True)

        assert response.status_code == 404


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
        assert not any(
            n.startswith("demo/") and n.endswith("_overview.html") for n in names
        )

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
        hidden = XRFMeasurementFactory(dataset=_dataset(published=False), sample=rock)

        response = _page(client, rock)

        assert [
            e["measurement"].pk for e in response.context["measurements"]["items"]
        ] == [shown.pk]
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

    def test_the_list_shows_the_thirty_most_recent_and_counts_the_rest(
        self, client, rock
    ):
        measurements = XRFMeasurementFactory.create_batch(
            32, dataset=rock.dataset, sample=rock
        )
        for minute, measurement in enumerate(measurements):
            Measurement.objects.filter(pk=measurement.pk).update(
                added=datetime(2026, 1, 1, 0, minute, tzinfo=UTC)
            )

        summary = _page(client, rock).context["measurements"]

        assert summary["total"] == 32
        assert summary["more"] == 2
        assert [e["measurement"].pk for e in summary["items"]] == [
            m.pk for m in reversed(measurements[2:])
        ]

    def test_the_figure_leads_to_the_panel_and_the_panel_to_the_measurements_tab(
        self, client, rock
    ):
        XRFMeasurementFactory(dataset=rock.dataset, sample=rock)
        tab = reverse("sample:measurements", kwargs={"uuid": rock.uuid})

        page = _page(client, rock).page

        panel = page.find(id="measurements")
        assert panel.find("a", href=tab) is not None
        assert page.select_one(".ov-figures").find("a", href="#measurements")


@pytest.mark.django_db
class TestOverviewMeasurementTypes:
    """FR-037 and US-3 scenario 13."""

    def test_each_type_is_counted_among_the_visible_measurements_most_first(
        self, client, rock
    ):
        XRFMeasurementFactory.create_batch(2, dataset=rock.dataset, sample=rock)
        ICP_MS_MeasurementFactory(dataset=rock.dataset, sample=rock)
        ICP_MS_MeasurementFactory(dataset=_dataset(published=False), sample=rock)

        types = _page(client, rock).context["measurement_types"]

        assert [(t["key"], t["n"]) for t in types] == [
            ("demo.xrfmeasurement", 2),
            ("demo.icp_ms_measurement", 1),
        ]

    def test_each_listed_measurement_carries_the_key_of_its_type(self, client, rock):
        ICP_MS_MeasurementFactory(dataset=rock.dataset, sample=rock)

        items = _page(client, rock).context["measurements"]["items"]

        assert [e["type_key"] for e in items] == ["demo.icp_ms_measurement"]

    def test_with_two_types_the_list_can_be_narrowed_to_either(self, client, rock):
        XRFMeasurementFactory(dataset=rock.dataset, sample=rock)
        ICP_MS_MeasurementFactory(dataset=rock.dataset, sample=rock)

        page = _page(client, rock).page

        group = page.select_one("[data-filter-chips]")
        rows = page.find(id=group["data-filter-chips"]).select("li[data-type]")
        values = [b["data-value"] for b in group.select("button")]
        assert values[0] == ""
        assert sorted(values[1:]) == sorted(r["data-type"] for r in rows)

    def test_with_one_type_there_is_nothing_to_filter(self, client, rock):
        XRFMeasurementFactory.create_batch(2, dataset=rock.dataset, sample=rock)

        assert _page(client, rock).page.select_one("[data-filter-chips]") is None


@pytest.mark.django_db
class TestOverviewHeaderFacts:
    """FR-036 and US-3 scenario 14."""

    def test_the_header_links_to_the_dataset(self, client, rock):
        page = _page(client, rock).page

        facts = page.select_one(".ov-facts")
        assert facts.find("a", href=rock.dataset.get_absolute_url()) is not None

    def test_the_igsn_is_the_identifier_the_header_gives(self, client, rock):
        SampleIdentifierFactory(related=rock, type=IGSN, value="10.58052/IGSN0001")

        response = _page(client, rock)

        assert response.context["primary_identifier"]["value"] == "10.58052/IGSN0001"
        assert response.page.select_one(".ov-facts").find(
            "a", href="https://doi.org/10.58052/IGSN0001"
        )

    def test_where_it_was_taken_leads_to_the_location_panel(self, client, released):
        sample = RockSampleFactory(
            dataset=released, location=GEOSPoint(12.3, 45.6, srid=4326)
        )

        page = _page(client, sample).page

        assert page.select_one(".ov-facts").find("a", href="#location")
        assert page.find(id="location") is not None


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
        assert (
            _page(client, rock).context["counts"]["related_desc"]
            == "1 parent · 1 subsample"
        )

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
            (f"{DATE_TYPES}/archival", "2024-03-05"),
            (f"{DATE_TYPES}/collected", "2023"),
            (f"{DATE_TYPES}/prepared", "2024-03"),
        ]:
            SampleDate.objects.create(
                related=rock, type_id=kind, value=PartialDate.fromisoformat(value)
            )

        steps = _page(client, rock).context["lifecycle"]

        assert [s["label"] for s in steps] == ["Collected", "Prepared", "Archived"]
        assert [str(s["date"]) for s in steps] == ["2023", "2024-03", "2024-03-05"]
        assert [s["day"] for s in steps][:2] == [None, None]
        assert steps[2]["day"] is not None

    def test_a_step_with_no_date_follows_the_dated_ones(self, client, rock):
        SampleDescription.objects.create(
            related=rock,
            type_id=f"{DESCRIPTION_TYPES}/sample-preparation",
            value="Cut and polished.",
        )
        SampleDate.objects.create(
            related=rock,
            type_id=f"{DATE_TYPES}/collected",
            value=PartialDate.fromisoformat("2024-01-02"),
        )

        steps = _page(client, rock).context["lifecycle"]

        assert [s["label"] for s in steps] == ["Collected", "Prepared"]
        assert steps[1]["date"] is None
        assert steps[1]["note"] == "Cut and polished."

    def test_people_credited_for_a_step_join_its_entry(self, client, rock):
        rock.add_contributor(
            PersonFactory(is_active=True),
            with_roles=[f"{CONTRIBUTOR_ROLES}/collection"],
        )

        steps = _page(client, rock).context["lifecycle"]

        assert [s["label"] for s in steps] == ["Collected"]
        assert len(steps[0]["people"]) == 1


@pytest.mark.django_db
class TestOverviewLocation:
    """US-3 scenario 10."""

    def test_a_sample_with_a_location_shows_a_map_and_lists_the_coordinates(
        self, client, released
    ):
        point = GEOSPoint(12.345678, 45.678901, srid=4326)
        sample = RockSampleFactory(dataset=released, location=point)

        response = _page(client, sample)

        sample.refresh_from_db()
        marker = response.page.select_one("[data-map]")
        assert (marker["data-lon"], marker["data-lat"]) == (
            str(sample.location.x),
            str(sample.location.y),
        )
        assert response.context["has_map"] is True

    def test_latitude_and_longitude_are_given_to_five_places_with_elevation_and_uncertainty(
        self, client, released
    ):
        sample = RockSampleFactory(
            dataset=released,
            location=GEOSPoint(12.345678, 45.678901, srid=4326),
            location_elevation=112.0,
            location_uncertainty=5.0,
        )

        response = _page(client, sample)

        shown = [
            dd.get_text(strip=True)
            for dd in response.page.select('[data-card="location"] dd')
        ]
        assert shown[:2] == ["45.67890", "12.34568"]
        assert len(shown) == 4
        assert "112" in shown[2]
        assert "5" in shown[3]

    def test_elevation_and_uncertainty_are_left_out_where_they_are_not_recorded(
        self, client, released
    ):
        sample = RockSampleFactory(
            dataset=released, location=GEOSPoint(12.345678, 45.678901, srid=4326)
        )

        response = _page(client, sample)

        assert len(response.page.select('[data-card="location"] dd')) == 2

    def test_a_sample_without_one_draws_no_map(self, client, rock):
        response = _page(client, rock)

        assert response.context["location"] is None
        assert response.context["has_map"] is False
        assert response.page.select_one("[data-map]") is None


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

    def test_a_destroyed_specimen_is_announced_as_kept_on_record(
        self, client, released
    ):
        sample = RockSampleFactory(
            dataset=released, status=f"{SAMPLE_STATUS}/destroyed"
        )

        response = _page(client, sample)

        assert response.context["status"]["value"] == f"{SAMPLE_STATUS}/destroyed"
        assert response.page.select_one(".alert-warning") is not None

    def test_a_specimen_that_still_exists_carries_no_such_notice(
        self, client, released
    ):
        sample = RockSampleFactory(dataset=released, status=f"{SAMPLE_STATUS}/stored")

        response = _page(client, sample)

        assert response.context["status"]["variant"] == "neutral"
        assert response.page.select_one(".alert-warning") is None

    def test_a_status_never_recorded_reads_as_unknown(self, client, rock):
        assert (
            _page(client, rock).context["status"]["value"] == f"{SAMPLE_STATUS}/unknown"
        )

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
class TestOverviewEditingLinks:
    """FR-036: the sample's editing pages are reached from the page, not from tabs."""

    EDITING_PAGES = ["edit", "descriptions", "keywords", "key-dates", "identifiers"]

    def _addresses(self, sample):
        return [
            reverse(f"sample:{name}", kwargs={"uuid": sample.uuid})
            for name in self.EDITING_PAGES
        ]

    def _editor(self, dataset):
        user = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
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

    def test_a_user_who_may_change_the_sample_reaches_the_editing_pages_from_its_panels(
        self, client, rock, released
    ):
        client.force_login(self._editor(released))

        response = _page(client, rock)

        page_hrefs = {a.get("href") for a in response.page.select("a")}
        shown = {
            reverse(f"sample:{name}", kwargs={"uuid": rock.uuid})
            for name in ("edit", "keywords", "key-dates", "identifiers")
        }
        assert shown <= page_hrefs

    def test_a_visitor_sees_no_editing_link(self, client, rock):
        response = _page(client, rock)

        page_hrefs = {a.get("href") for a in response.page.select("a")}
        assert not page_hrefs & set(self._addresses(rock))

    def test_a_user_who_may_only_view_the_sample_sees_no_editing_link(
        self, client, rock, released
    ):
        client.force_login(_team_member(released))

        response = _page(client, rock)

        page_hrefs = {a.get("href") for a in response.page.select("a")}
        assert not page_hrefs & set(self._addresses(rock))

    def test_the_editing_pages_keep_their_addresses(self, rock):
        assert self._addresses(rock) == [
            f"/samples/{rock.uuid}/{segment}/" for segment in self.EDITING_PAGES
        ]


@pytest.mark.django_db
class TestOverviewCitationAddress:
    def _citation(self, client, sample):
        return _page(client, sample).page.find(id="citation-text").get_text(strip=True)

    def test_without_an_igsn_the_citation_ends_with_the_samples_permalink(
        self, client, rock
    ):
        assert self._citation(client, rock).endswith(f"http://testserver/{rock.uuid}/")

    def test_with_an_igsn_the_citation_names_no_permalink(self, client, rock):
        SampleIdentifierFactory(related=rock, type=IGSN, value="10.58052/IGSN0001")

        citation = self._citation(client, rock)

        assert citation.endswith("https://doi.org/10.58052/IGSN0001")
        assert str(rock.uuid) not in citation


@pytest.fixture
def portal_name(db):
    """Name the site, which a citation gives as its publisher."""
    Site.objects.filter(pk=Site.objects.get_current().pk).update(
        name="Acme Data Portal"
    )
    Site.objects.clear_cache()
    yield "Acme Data Portal"
    Site.objects.clear_cache()


@pytest.mark.django_db
class TestOverviewCitationFormats:
    """The sample's citation as BibTeX and RIS, as the Cite panel offers it."""

    def _collected(self, sample):
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            sample.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/collection"],
            )
        SampleDate.objects.create(
            related=sample,
            type_id=f"{DATE_TYPES}/collected",
            value=PartialDate.fromisoformat("2023-04-05"),
        )
        return sample

    def _formats(self, client, sample):
        citation = _page(client, sample).context["citation"]
        return {entry["key"]: entry["value"] for entry in citation["formats"]}

    def _entry(self, formats):
        data = parse_string(formats["bibtex"], "bibtex")
        assert len(data.entries) == 1
        key, entry = next(iter(data.entries.items()))
        return key, entry, rispy.loads(formats["ris"])[0]

    def test_the_text_and_both_files_give_the_same_people_year_title_and_publisher(
        self, client, rock, portal_name
    ):
        self._collected(rock)

        formats = self._formats(client, rock)
        key, entry, ris = self._entry(formats)

        title = "Zq-4471 rift core [Rock Sample]"
        assert formats["text"].startswith("Keller, A. & Oliveira, T. (2023). ")
        assert f"{title}. Acme Data Portal." in formats["text"]
        assert [(p.last_names, p.first_names) for p in entry.persons["author"]] == [
            (["Keller"], ["Anna"]),
            (["Oliveira"], ["Tomas"]),
        ]
        assert entry.fields["year"] == "2023"
        assert codecs.decode(entry.fields["title"], "ulatex") == title
        assert codecs.decode(entry.fields["publisher"], "ulatex") == portal_name
        assert key == str(rock.uuid)
        assert ris["authors"] == ["Keller, Anna", "Oliveira, Tomas"]
        assert (ris["year"], ris["title"], ris["publisher"]) == (
            "2023",
            title,
            portal_name,
        )

    def test_without_an_igsn_the_files_give_the_permalink_and_no_doi(
        self, client, rock
    ):
        permalink = f"http://testserver/{rock.uuid}/"

        formats = self._formats(client, rock)
        _key, entry, ris = self._entry(formats)

        assert formats["text"].endswith(permalink)
        assert entry.fields["url"] == permalink
        assert "doi" not in entry.fields
        assert ris["urls"] == [permalink]
        assert "doi" not in ris

    def test_with_an_igsn_the_files_give_it_as_the_doi_and_its_link(self, client, rock):
        SampleIdentifierFactory(related=rock, type=IGSN, value="10.58052/IGSN_1")

        formats = self._formats(client, rock)
        _key, entry, ris = self._entry(formats)

        assert formats["text"].endswith("https://doi.org/10.58052/IGSN_1")
        assert entry.fields["doi"] == "10.58052/IGSN_1"
        assert entry.fields["url"] == "https://doi.org/10.58052/IGSN_1"
        assert ris["doi"] == "10.58052/IGSN_1"
        assert ris["urls"] == ["https://doi.org/10.58052/IGSN_1"]

    def test_a_legacy_igsn_that_does_not_resolve_gives_no_link_and_no_doi(
        self, client, rock
    ):
        SampleIdentifierFactory(related=rock, type=IGSN, value="AU1101")

        formats = self._formats(client, rock)
        _key, entry, ris = self._entry(formats)

        assert "http" not in formats["text"]
        assert "doi" not in entry.fields
        assert "url" not in entry.fields
        assert "doi" not in ris
        assert "urls" not in ris

    def test_a_sample_is_a_misc_entry_and_a_general_reference(self, client, rock):
        formats = self._formats(client, rock)
        _key, entry, ris = self._entry(formats)

        assert entry.type == "misc"
        assert ris["type_of_reference"] == "GEN"

    def test_with_nobody_credited_no_author_is_given(self, client, rock):
        formats = self._formats(client, rock)
        _key, entry, ris = self._entry(formats)

        assert "author" not in entry.persons
        assert "authors" not in ris
        assert formats["text"].startswith("(")

    def test_a_portal_sample_type_gets_all_three_formats(self, client, released):
        sample = ConcreteSampleFactory(dataset=released, name="Portal core")

        citation = _page(client, sample).context["citation"]
        formats = {entry["key"]: entry["value"] for entry in citation["formats"]}
        _key, entry, ris = self._entry(formats)

        assert list(formats) == ["text", "bibtex", "ris"]
        assert "Portal core [concrete sample]" in formats["text"]
        assert codecs.decode(entry.fields["title"], "ulatex") == (
            "Portal core [concrete sample]"
        )
        assert ris["title"] == "Portal core [concrete sample]"
        assert [e["url"] for e in citation["formats"]] == [
            reverse(
                "sample:overview-citation",
                kwargs={"uuid": sample.uuid, "format": key},
            )
            for key in ("text", "bibtex", "ris")
        ]
