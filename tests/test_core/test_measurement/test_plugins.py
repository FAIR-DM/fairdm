"""The measurement's overview page: what it opens for, what it draws and what it leaves out."""

from datetime import UTC, datetime

import pytest
from bs4 import BeautifulSoup
from django.db import models
from django.template.loader import select_template
from django.test.utils import isolate_apps
from pytest_django.asserts import assertContains, assertNotContains

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import XRFMeasurement
from fairdm import plugins
from fairdm.core.measurement.models import Measurement, MeasurementDate
from fairdm.core.measurement.plugins import Overview
from fairdm.core.utils import assign_perm
from fairdm.factories import DatasetFactory, PersonFactory, PointFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility


# Development data reaches every state; `DatasetFactory()` alone gives a private, unpublished one.
def _dataset(*, public=True, published=True):
    return DatasetFactory(
        visibility=Visibility.PUBLIC if public else Visibility.PRIVATE,
        published=published,
    )


def _page(client, measurement):
    """Open the measurement at its permanent address and return the response with its parsed HTML."""
    response = client.get(f"/measurement/{measurement.uuid}/")
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
def xrf(released):
    sample = RockSampleFactory(dataset=released, name="Zq-4471 rift core")
    return XRFMeasurementFactory(dataset=released, sample=sample, name="Zq-9902 scan")


@pytest.mark.django_db
class TestOverviewAddress:
    """US-4 scenario 1 and FR-040."""

    def test_the_page_opens_at_the_measurements_permanent_address(self, client, xrf):
        assert xrf.get_absolute_url() == f"/measurement/{xrf.uuid}/"
        assert client.get(f"/measurement/{xrf.uuid}/").status_code == 200

    def test_the_overview_is_the_first_tab_of_the_tabbed_detail_view(self, client, xrf):
        assert _page(client, xrf).context["record"] == xrf
        plugins.registry.get_urls_for_model(Measurement)
        menu = plugins.registry.get_plugin_menu_for_model(Measurement)
        assert menu.children[0].view_name == "measurement:overview"


@pytest.mark.django_db
class TestOverviewTemplateChoice:
    """FR-048 and FR-049, and US-4 scenario 2."""

    def test_a_type_with_its_own_template_uses_it_and_keeps_the_shared_page(
        self, client, xrf
    ):
        names = [t.name for t in _page(client, xrf).templates if t.name]

        assert "demo/xrfmeasurement_overview.html" in names
        assert "measurement/measurement_overview.html" in names

    def test_a_type_with_no_template_anywhere_uses_the_shared_page(
        self, client, released
    ):
        icp = ICP_MS_MeasurementFactory(
            dataset=released, sample=RockSampleFactory(dataset=released)
        )

        names = [t.name for t in _page(client, icp).templates if t.name]

        assert "measurement/measurement_overview.html" in names
        assert not any(
            n.startswith("demo/") and n.endswith("_overview.html") for n in names
        )

    @isolate_apps("demo")
    def test_a_subtype_with_no_template_of_its_own_uses_its_parents(self):
        class DeepXRF(XRFMeasurement):
            class Meta:
                app_label = "demo"

        plugin = Overview()
        plugin.base_object = DeepXRF()

        chosen = select_template(plugin.get_template_names())

        assert plugin.get_template_names()[0] == "demo/deepxrf_overview.html"
        assert chosen.template.name == "demo/xrfmeasurement_overview.html"

    def test_the_type_s_own_template_is_tried_before_any_ancestor_s(self):
        plugin = Overview()
        plugin.base_object = XRFMeasurement()

        assert plugin.get_template_names() == [
            "demo/xrfmeasurement_overview.html",
            "measurement/measurement_overview.html",
        ]


@pytest.mark.django_db
class TestOverviewFollowsItsOwnDataset:
    """FR-020 and US-4 scenarios 3 and 4."""

    def test_a_visitor_opens_a_measurement_whatever_the_state_of_its_samples_dataset(
        self, client, released
    ):
        sample = RockSampleFactory(dataset=_dataset(public=False, published=False))
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        assert client.get(measurement.get_absolute_url()).status_code == 200

    @pytest.mark.parametrize(
        ("public", "published"), [(False, False), (False, True), (True, False)]
    )
    def test_a_visitor_gets_not_found_unless_its_own_dataset_is_public_and_published(
        self, client, released, public, published
    ):
        sample = RockSampleFactory(dataset=released)
        measurement = XRFMeasurementFactory(
            dataset=_dataset(public=public, published=published), sample=sample
        )

        assert client.get(measurement.get_absolute_url()).status_code == 404

    def test_a_signed_in_stranger_gets_not_found(self, client, released):
        measurement = XRFMeasurementFactory(
            dataset=_dataset(published=False),
            sample=RockSampleFactory(dataset=released),
        )
        client.force_login(PersonFactory(is_active=True))

        assert client.get(measurement.get_absolute_url()).status_code == 404

    def test_the_dataset_team_opens_a_measurement_that_is_not_yet_released(
        self, client, released
    ):
        dataset = _dataset(public=False, published=False)
        measurement = XRFMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=released)
        )
        client.force_login(_team_member(dataset))

        assert client.get(measurement.get_absolute_url()).status_code == 200

    def test_a_subtype_with_a_plain_manager_opens_for_the_team_and_not_for_a_visitor(
        self, client, released, monkeypatch
    ):
        # A portal's measurement type may declare a plain manager with no `visible_to`.
        plain = models.QuerySet.as_manager()
        plain.model = XRFMeasurement
        dataset = _dataset(public=False, published=False)
        measurement = XRFMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=released)
        )
        monkeypatch.setattr(XRFMeasurement, "objects", plain)
        assert not hasattr(XRFMeasurement.objects, "visible_to")

        assert client.get(measurement.get_absolute_url()).status_code == 404
        client.force_login(_team_member(dataset))
        assert client.get(measurement.get_absolute_url()).status_code == 200


@pytest.mark.django_db
class TestOverviewSample:
    """FR-020 and US-4 scenarios 5 and 6."""

    @pytest.fixture
    def hidden_sample_page(self, client, released):
        sample = RockSampleFactory(
            dataset=_dataset(published=False),
            name="Hidden-3318 core",
            location=PointFactory(x="12.345678", y="45.678901"),
        )
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)
        return sample, _page(client, measurement)

    def test_a_sample_in_an_unpublished_dataset_is_neither_named_nor_linked(
        self, hidden_sample_page
    ):
        sample, response = hidden_sample_page

        assert response.context["sample_visible"] is False
        assertNotContains(response, sample.name)
        assertNotContains(response, sample.get_absolute_url())

    def test_the_page_describes_the_sample_as_unpublished(self, hidden_sample_page):
        _, response = hidden_sample_page

        assert "an unpublished sample" in response.context["citation"]["text"]

    def test_no_map_is_drawn_for_a_sample_the_visitor_may_not_see(
        self, hidden_sample_page
    ):
        _, response = hidden_sample_page

        assert response.page.select_one(".overview-map") is None

    def test_a_sample_the_visitor_may_see_is_named_and_linked(self, client, xrf):
        response = _page(client, xrf)

        assert response.context["sample_visible"] is True
        assertContains(response, xrf.sample.get_absolute_url())

    def test_the_sample_card_carries_the_samples_status(self, client, released):
        sample = RockSampleFactory(dataset=released, status="stored")
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        status = _page(client, measurement).context["sample_status"]

        assert status == {"label": "Stored", "variant": "neutral"}

    def test_a_measurement_in_a_different_dataset_from_its_sample_says_so(
        self, client, released
    ):
        sample = RockSampleFactory(dataset=_dataset())
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        assert _page(client, measurement).context["other_dataset"] is True

    def test_a_measurement_in_its_samples_dataset_does_not(self, client, xrf):
        assert _page(client, xrf).context["other_dataset"] is False

    def test_a_sample_with_a_location_shows_a_map(self, client, released):
        sample = RockSampleFactory(
            dataset=released, location=PointFactory(x="12.345678", y="45.678901")
        )
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        response = _page(client, measurement)

        sample.location.refresh_from_db()
        marker = response.page.select_one(".overview-map")
        assert (marker["data-lon"], marker["data-lat"]) == (
            str(sample.location.x),
            str(sample.location.y),
        )

    def test_a_sample_with_no_location_draws_no_map(self, client, xrf):
        assert _page(client, xrf).page.select_one(".overview-map") is None


@pytest.mark.django_db
class TestOverviewResult:
    """US-4 scenario 7."""

    def test_a_type_that_declares_a_value_shows_it_with_its_uncertainty(
        self, client, released
    ):
        icp = ICP_MS_MeasurementFactory(
            dataset=released,
            sample=RockSampleFactory(dataset=released),
            value="120.5",
            uncertainty="2.5",
        )

        result = _page(client, icp).context["result"]

        assert "120.5" in result["text"]
        assert "±" in result["text"]
        assert "2.5" in result["text"]

    def test_a_type_that_declares_no_value_leaves_the_result_to_its_own_template(
        self, client, released
    ):
        xrf = XRFMeasurementFactory(
            dataset=released,
            sample=RockSampleFactory(dataset=released),
            concentration_ppm=250000,
        )

        response = _page(client, xrf)

        assert response.context["result"] is None
        assertContains(response, "250,000")


@pytest.mark.django_db
class TestOverviewTypeBadge:
    """FR-036 and US-4 scenario 8."""

    def test_a_type_the_registry_describes_opens_a_dialog(self, client, xrf):
        response = _page(client, xrf)

        assert response.context["type_info"]["description"]
        assert response.page.find("dialog", id="about-measurement-type") is not None

    def test_a_type_the_registry_does_not_describe_opens_nothing(
        self, client, xrf, monkeypatch
    ):
        monkeypatch.setattr(registry, "is_registered", lambda model: False)

        response = _page(client, xrf)

        assert response.context["type_info"] is None
        assert response.page.find("dialog", id="about-measurement-type") is None


@pytest.mark.django_db
class TestOverviewSiblings:
    """FR-023 and US-4 scenario 9."""

    def test_only_measurements_in_published_datasets_are_listed_for_a_visitor(
        self, client, xrf
    ):
        shown = XRFMeasurementFactory(dataset=xrf.dataset, sample=xrf.sample)
        hidden = XRFMeasurementFactory(
            dataset=_dataset(published=False), sample=xrf.sample
        )

        response = _page(client, xrf)

        assert [r["measurement"].pk for r in response.context["siblings"]["rows"]] == [
            shown.pk
        ]
        assert response.context["siblings"]["total"] == 1
        assertNotContains(response, hidden.get_absolute_url())

    def test_being_on_the_measurements_team_opens_nothing_in_the_other_dataset(
        self, client, xrf
    ):
        XRFMeasurementFactory(dataset=_dataset(published=False), sample=xrf.sample)
        client.force_login(_team_member(xrf.dataset))

        assert _page(client, xrf).context["siblings"]["total"] == 0

    def test_the_page_does_not_list_itself(self, client, xrf):
        assert _page(client, xrf).context["siblings"]["total"] == 0

    def test_a_row_says_whether_it_is_of_the_same_type(self, client, xrf, released):
        XRFMeasurementFactory(dataset=released, sample=xrf.sample)
        ICP_MS_MeasurementFactory(dataset=released, sample=xrf.sample)

        rows = _page(client, xrf).context["siblings"]["rows"]

        assert sorted(r["same_type"] for r in rows) == [False, True]

    def test_the_list_shows_the_eight_most_recent_and_counts_the_rest(
        self, client, xrf
    ):
        others = XRFMeasurementFactory.create_batch(
            10, dataset=xrf.dataset, sample=xrf.sample
        )
        for day, measurement in enumerate(others, start=1):
            Measurement.objects.filter(pk=measurement.pk).update(
                added=datetime(2026, 1, day, tzinfo=UTC)
            )

        siblings = _page(client, xrf).context["siblings"]

        assert siblings["total"] == 10
        assert siblings["more"] == 2
        assert [r["measurement"].pk for r in siblings["rows"]] == [
            m.pk for m in reversed(others[2:])
        ]


@pytest.mark.django_db
class TestOverviewProcedure:
    """FR-041: how the measurement was made, put back together from dates, roles and descriptions."""

    def test_a_dated_step_appears_in_the_timeline(self, client, xrf):
        MeasurementDate.objects.create(related=xrf, type="Setup", value="2024-01-15")

        steps = _page(client, xrf).context["procedure"]

        assert len(steps) == 1

    def test_a_measurement_with_nothing_recorded_has_an_empty_timeline(
        self, client, xrf
    ):
        assert _page(client, xrf).context["procedure"] == []


@pytest.mark.django_db
class TestOverviewCitation:
    """FR-044: the page suggests citing the dataset where the measurement has no DOI."""

    def test_a_measurement_with_no_doi_points_the_citation_at_its_dataset(
        self, client, xrf
    ):
        citation = _page(client, xrf).context["citation"]

        assert citation["note_url"] == xrf.dataset.get_absolute_url() + "#cite"
        assert xrf.get_absolute_url() in citation["text"]

    def test_a_measurement_with_a_doi_is_cited_by_it_and_carries_no_note(
        self, client, xrf
    ):
        from fairdm.core.measurement.models import MeasurementIdentifier

        MeasurementIdentifier.objects.create(
            related=xrf, type="DOI", value="10.1234/meas.1"
        )

        citation = _page(client, xrf).context["citation"]

        assert "note" not in citation
        assert "10.1234/meas.1" in citation["text"]


@pytest.mark.django_db
class TestOverviewBreadcrumbs:
    """FR-047 and US-4 scenario 10."""

    def test_the_trail_leads_from_the_list_of_measurements_to_the_measurement(
        self, client, xrf
    ):
        trail = _page(client, xrf).context["breadcrumbs"]

        assert [entry["text"] for entry in trail] == ["Measurements", str(xrf)]
