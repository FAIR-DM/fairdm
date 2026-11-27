"""The measurement's overview page: what it opens for, what it draws and what it leaves out."""

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
from django.template.loader import select_template
from django.test import RequestFactory
from django.test.utils import isolate_apps
from django.urls import reverse
from pybtex.database import parse_string
from pytest_django.asserts import assertContains, assertNotContains

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import ICP_MS_Measurement, XRFMeasurement
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementIdentifier,
)
from fairdm.core.measurement.plugins import Overview
from fairdm.core.sample.plugins import Overview as SampleOverview
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    IDENTIFIER_TYPES,
    SAMPLE_STATUS,
)
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
)
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory


# Development data reaches every state; `DatasetFactory()` alone gives a private, unpublished one.
def _dataset(*, public=True, published=True):
    return DatasetFactory(
        visibility=Visibility.PUBLIC if public else Visibility.PRIVATE,
        published=published,
    )


def _page(client, measurement):
    """Open the measurement at its permanent address and return the response with its parsed HTML."""
    response = client.get(f"/measurements/{measurement.uuid}/")
    assert response.status_code == 200
    response.page = BeautifulSoup(response.content, "html.parser")
    return response


def _context(measurement, user=None):
    """Build the overview's context for a viewer without rendering the page.

    The record is read back as the view reads it, and the request carries the site the
    site middleware would set.
    """
    request = RequestFactory().get(measurement.get_absolute_url())
    request.user = user or AnonymousUser()
    request.site = Site.objects.get_current()
    plugin = Overview(registered_model=Measurement)
    plugin.setup(request, uuid=str(measurement.uuid))
    plugin.base_object = Measurement.objects.get(pk=measurement.pk)
    return plugin.get_context_data()


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
def xrf(released):
    sample = RockSampleFactory(dataset=released, name="Zq-4471 rift core")
    return XRFMeasurementFactory(dataset=released, sample=sample, name="Zq-9902 scan")


@pytest.mark.django_db
class TestOverviewAddress:
    """US-4 scenario 1 and FR-040."""

    def test_the_page_opens_at_the_measurements_permanent_address(self, client, xrf):
        assert xrf.get_absolute_url() == f"/measurements/{xrf.uuid}/"
        assert _page(client, xrf).context["record"] == xrf


@pytest.mark.django_db
class TestOverviewTemplateChoice:
    """FR-048 and FR-049, and US-4 scenario 2."""

    def test_a_type_with_its_own_template_uses_it_and_keeps_the_shared_page(
        self, client, xrf
    ):
        names = [t.name for t in _page(client, xrf).templates if t.name]

        assert "demo/xrfmeasurement_overview.html" in names
        assert "measurement/measurement_overview.html" in names

    def test_a_type_with_no_template_anywhere_uses_the_shared_page(self):
        plugin = Overview()
        plugin.base_object = ICP_MS_Measurement()

        chosen = select_template(plugin.get_template_names())

        assert chosen.template.name == "measurement/measurement_overview.html"

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

    def test_a_visitor_gets_not_found_while_its_own_dataset_is_unpublished(
        self, client, released
    ):
        measurement = XRFMeasurementFactory(
            dataset=_dataset(published=False),
            sample=RockSampleFactory(dataset=released),
        )

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
    def hidden_sample(self, released):
        sample = RockSampleFactory(
            dataset=_dataset(published=False),
            name="Hidden-3318 core",
            location=GEOSPoint(12.345678, 45.678901, srid=4326),
        )
        return sample, XRFMeasurementFactory(dataset=released, sample=sample)

    def test_a_sample_in_an_unpublished_dataset_is_neither_named_nor_linked(
        self, client, hidden_sample
    ):
        sample, measurement = hidden_sample

        response = _page(client, measurement)

        assert response.context["sample_visible"] is False
        assertNotContains(response, sample.name)
        assertNotContains(response, sample.get_absolute_url())
        assert response.page.select_one("[data-map]") is None

    def test_the_citation_describes_a_hidden_sample_as_unpublished(self, hidden_sample):
        _, measurement = hidden_sample

        assert "an unpublished sample" in _context(measurement)["citation"]["text"]

    def test_a_hidden_sample_in_another_dataset_is_not_said_to_be_elsewhere(
        self, hidden_sample
    ):
        _, measurement = hidden_sample

        assert _context(measurement)["other_dataset"] is False

    def test_a_sample_the_visitor_may_see_is_visible(self, xrf):
        assert _context(xrf)["sample_visible"] is True

    def test_a_measurement_in_a_different_dataset_from_its_sample_says_so(
        self, released
    ):
        sample = RockSampleFactory(dataset=_dataset())
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        assert _context(measurement)["other_dataset"] is True

    def test_a_measurement_in_its_samples_dataset_does_not(self, xrf):
        assert _context(xrf)["other_dataset"] is False

    def test_the_sample_card_carries_the_samples_status_in_its_page_colour(
        self, released
    ):
        sample = RockSampleFactory(
            dataset=released, status=f"{SAMPLE_STATUS}/destroyed"
        )
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        status = _context(measurement)["sample_status"]

        assert status["label"] == sample.get_status_label()
        assert status["variant"] == SampleOverview.status_variants[sample.status_id]


@pytest.mark.django_db
class TestOverviewHeader:
    """FR-043: the header's key facts name the sample, dataset and identifier."""

    def test_the_sample_the_viewer_may_open_is_linked_from_the_header(
        self, client, xrf
    ):
        facts = _page(client, xrf).page.select_one(".ov-facts")

        assert facts.find("a", href=xrf.sample.get_absolute_url()) is not None
        assert facts.find("a", href=xrf.dataset.get_absolute_url()) is not None

    def test_the_identifier_that_resolves_is_linked_from_the_header(self, client, xrf):
        MeasurementIdentifier.objects.create(
            related=xrf, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.1234/meas.1"
        )

        response = _page(client, xrf)

        link = response.context["primary_identifier"]["link"]
        assert response.page.select_one(".ov-facts").find("a", href=link) is not None

    def test_a_measurement_with_no_identifier_that_resolves_names_none(self, xrf):
        assert _context(xrf)["primary_identifier"] is None


@pytest.mark.django_db
class TestOverviewResult:
    """US-4 scenario 7."""

    def test_a_type_that_declares_a_value_shows_it_with_its_uncertainty(self, released):
        icp = ICP_MS_MeasurementFactory(
            dataset=released,
            sample=RockSampleFactory(dataset=released),
            value="120.5",
            uncertainty="2.5",
        )

        result = _context(icp)["result"]

        assert "120.5" in result["text"]
        assert "±" in result["text"]
        assert "2.5" in result["text"]

    def test_a_negative_uncertainty_still_shows_the_page_with_the_plain_value(
        self, released
    ):
        icp = ICP_MS_MeasurementFactory(
            dataset=released,
            sample=RockSampleFactory(dataset=released),
            value="120.5",
            uncertainty="-2.5",
        )

        result = _context(icp)["result"]

        assert "120.5" in result["text"]
        assert "±" not in result["text"]

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
        self, xrf, monkeypatch
    ):
        monkeypatch.setattr(registry, "is_registered", lambda model: False)

        assert _context(xrf)["type_info"] is None


@pytest.mark.django_db
class TestOverviewSiblings:
    """FR-023 and US-4 scenario 9."""

    def test_only_measurements_in_published_datasets_are_listed_for_a_visitor(
        self, xrf
    ):
        shown = XRFMeasurementFactory(dataset=xrf.dataset, sample=xrf.sample)
        XRFMeasurementFactory(dataset=_dataset(published=False), sample=xrf.sample)

        siblings = _context(xrf)["siblings"]

        assert [r["measurement"].pk for r in siblings["rows"]] == [shown.pk]
        assert siblings["total"] == 1

    def test_being_on_the_measurements_team_opens_nothing_in_the_other_dataset(
        self, xrf
    ):
        XRFMeasurementFactory(dataset=_dataset(published=False), sample=xrf.sample)

        siblings = _context(xrf, _team_member(xrf.dataset))["siblings"]

        assert siblings["total"] == 0

    def test_the_page_does_not_list_itself(self, xrf):
        assert _context(xrf)["siblings"]["total"] == 0

    def test_a_row_says_whether_it_is_of_the_same_type(self, xrf, released):
        XRFMeasurementFactory(dataset=released, sample=xrf.sample)
        ICP_MS_MeasurementFactory(dataset=released, sample=xrf.sample)

        rows = _context(xrf)["siblings"]["rows"]

        assert sorted(r["same_type"] for r in rows) == [False, True]

    def test_the_card_leads_to_the_samples_measurements_tab_where_the_sample_opens(
        self, xrf
    ):
        tab = reverse("sample:measurements", kwargs={"uuid": xrf.sample.uuid})

        assert _context(xrf)["sample_measurements_url"] == tab

    def test_the_card_offers_no_tab_when_the_sample_is_hidden(self, released):
        hidden = RockSampleFactory(dataset=_dataset(published=False))
        xrf = XRFMeasurementFactory(dataset=released, sample=hidden)
        XRFMeasurementFactory(dataset=released, sample=hidden)

        context = _context(xrf)

        assert context["siblings"]["total"] == 1
        assert context["sample_measurements_url"] is None

    def test_the_list_shows_the_most_recent_and_counts_the_rest(self, xrf, monkeypatch):
        monkeypatch.setattr(Overview, "siblings_shown", 2)
        others = XRFMeasurementFactory.create_batch(
            3, dataset=xrf.dataset, sample=xrf.sample
        )
        for day, measurement in enumerate(others, start=1):
            Measurement.objects.filter(pk=measurement.pk).update(
                added=datetime(2026, 1, day, tzinfo=UTC)
            )

        siblings = _context(xrf)["siblings"]

        assert siblings["total"] == 3
        assert siblings["more"] == 1
        assert [r["measurement"].pk for r in siblings["rows"]] == [
            m.pk for m in reversed(others[1:])
        ]

    def test_the_count_of_the_rest_leads_to_the_samples_measurements_tab(
        self, client, xrf, monkeypatch
    ):
        monkeypatch.setattr(Overview, "siblings_shown", 1)
        XRFMeasurementFactory.create_batch(2, dataset=xrf.dataset, sample=xrf.sample)
        tab = reverse("sample:measurements", kwargs={"uuid": xrf.sample.uuid})

        page = _page(client, xrf).page

        assert page.select_one(".ov-rows__more")["href"] == tab


@pytest.mark.django_db
class TestOverviewProcedure:
    """FR-041: how the measurement was made, put back together from dates, roles and descriptions."""

    def test_a_dated_step_appears_in_the_timeline(self, xrf):
        MeasurementDate.objects.create(
            related=xrf, type_id=f"{DATE_TYPES}/setup", value="2024-01-15"
        )

        assert len(_context(xrf)["procedure"]) == 1

    def test_a_measurement_with_nothing_recorded_has_an_empty_timeline(self, xrf):
        assert _context(xrf)["procedure"] == []


@pytest.mark.django_db
class TestOverviewCitation:
    """FR-044: the page suggests citing the dataset where the measurement has no DOI."""

    def test_a_measurement_with_no_doi_points_the_citation_at_its_dataset(self, xrf):
        citation = _context(xrf)["citation"]

        assert citation["note_url"] == xrf.dataset.get_absolute_url() + "#cite"
        assert f"http://testserver/{xrf.uuid}/" in citation["text"]

    def test_a_measurement_with_a_doi_is_cited_by_it_and_carries_no_note(self, xrf):
        MeasurementIdentifier.objects.create(
            related=xrf, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.1234/meas.1"
        )

        citation = _context(xrf)["citation"]

        assert "note" not in citation
        assert "10.1234/meas.1" in citation["text"]
        assert str(xrf.uuid) not in citation["text"]


@pytest.mark.django_db
class TestOverviewBreadcrumbs:
    """FR-047 and US-4 scenario 10."""

    def test_the_trail_leads_from_the_list_of_its_type_to_the_measurement(self, xrf):
        trail = _context(xrf)["breadcrumbs"]

        assert [entry["text"] for entry in trail] == ["XRF Measurements", str(xrf)]
        assert trail[0]["href"] == reverse("xrfmeasurement-list")


@pytest.mark.django_db
class TestOverviewCardsAlwaysShown:
    """FR-003 and the Edge Cases: a card the page has is shown even with nothing to put in it."""

    def test_a_bare_measurement_shows_every_side_card(self, client, xrf):
        response = _page(client, xrf)

        for card in ["details", "people", "identifiers", "citation", "location"]:
            assert response.page.select_one(f'[data-card="{card}"]') is not None, card

    def test_the_sample_location_card_shows_when_the_sample_is_hidden_and_draws_no_map(
        self, client, released
    ):
        hidden = _dataset(published=False)
        sample = RockSampleFactory(
            dataset=hidden, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        response = _page(client, measurement)

        assert response.page.select_one('[data-card="location"]') is not None
        assert response.page.select_one("[data-map]") is None
        assertNotContains(response, "12.5")


@pytest.mark.django_db
class TestOverviewUnnamedMeasurement:
    """FR-047: a measurement with no name is called by its portal ID."""

    @pytest.fixture
    def unnamed(self, released):
        # The column is not nullable, so "no name" is the empty string.
        sample = RockSampleFactory(dataset=released)
        return XRFMeasurementFactory(dataset=released, sample=sample, name="")

    def test_the_heading_and_the_browser_title_are_the_portal_id(self, client, unnamed):
        response = _page(client, unnamed)

        assert response.page.h1.get_text(strip=True) == str(unnamed.uuid)
        assert str(unnamed.uuid) in response.page.title.get_text()
        assert "None" not in response.page.title.get_text()

    def test_the_breadcrumbs_end_in_the_portal_id(self, unnamed):
        trail = _context(unnamed)["breadcrumbs"]

        assert trail[-1]["text"] == str(unnamed.uuid)


@pytest.mark.django_db
class TestOverviewLocation:
    """US-3 scenarios 2 to 4, FR-013, FR-014 and FR-025."""

    def _measurement(self, released, *, own=None, sample_location=None, hidden=False):
        sample = RockSampleFactory(
            dataset=_dataset(published=False) if hidden else released,
            location=sample_location,
            location_elevation=40.0 if sample_location else None,
        )
        return XRFMeasurementFactory(
            dataset=released,
            sample=sample,
            location=own,
            location_elevation=112.0 if own else None,
            location_uncertainty=25.0 if own else None,
        )

    def test_a_measurement_with_a_location_of_its_own_shows_it_as_its_own(
        self, client, released
    ):
        measurement = self._measurement(
            released,
            own=GEOSPoint(8.43180, 49.09495, srid=4326),
            sample_location=GEOSPoint(12.5, 41.5, srid=4326),
        )

        response = _page(client, measurement)

        marker = response.page.select_one("[data-map]")
        assert (marker["data-lon"], marker["data-lat"]) == ("8.4318", "49.09495")
        shown = response.context["effective_location"]
        assert shown.source == "own"
        assert (shown.elevation, shown.uncertainty) == (112.0, 25.0)

    def test_a_measurement_with_none_of_its_own_shows_the_sample_as_the_samples(
        self, released
    ):
        measurement = self._measurement(
            released, sample_location=GEOSPoint(12.5, 41.5, srid=4326)
        )

        shown = _context(measurement)["effective_location"]

        assert shown.source == "sample"
        assert (shown.point.x, shown.point.y) == (12.5, 41.5)
        assert shown.elevation == 40.0

    def test_a_sample_the_viewer_may_not_open_gives_no_location(self, released):
        measurement = self._measurement(
            released, sample_location=GEOSPoint(12.5, 41.5, srid=4326), hidden=True
        )

        assert _context(measurement)["effective_location"] is None

    def test_the_own_location_is_shown_even_when_the_sample_is_hidden(self, released):
        measurement = self._measurement(
            released,
            own=GEOSPoint(8.43180, 49.09495, srid=4326),
            sample_location=GEOSPoint(12.5, 41.5, srid=4326),
            hidden=True,
        )

        shown = _context(measurement)["effective_location"]

        assert shown.source == "own"
        assert (shown.point.x, shown.point.y) == (8.4318, 49.09495)

    def test_a_person_who_may_open_the_hidden_sample_sees_its_location(self, released):
        measurement = self._measurement(
            released, sample_location=GEOSPoint(12.5, 41.5, srid=4326), hidden=True
        )

        shown = _context(measurement, _team_member(measurement.sample.dataset))[
            "effective_location"
        ]

        assert shown.source == "sample"
        assert (shown.point.x, shown.point.y) == (12.5, 41.5)


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
    """The measurement's citation as BibTeX and RIS, as the Cite panel offers it."""

    def credit(self, measurement):
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            measurement.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/measurement-collection"],
            )
        MeasurementDate.objects.create(
            related=measurement,
            type_id=f"{DATE_TYPES}/setup",
            value="2024-01-15",
        )
        return measurement

    def formats_of(self, context):
        return {
            entry["key"]: entry["value"] for entry in context["citation"]["formats"]
        }

    def entry_of(self, formats):
        data = parse_string(formats["bibtex"], "bibtex")
        assert len(data.entries) == 1
        key, entry = next(iter(data.entries.items()))
        return key, entry, rispy.loads(formats["ris"])[0]

    def test_the_text_and_both_files_give_the_same_people_year_title_and_publisher(
        self, client, xrf, portal_name
    ):
        self.credit(xrf)

        formats = self.formats_of(_context(xrf))
        key, entry, ris = self.entry_of(formats)

        title = "Zq-9902 scan [XRF Measurement] of Zq-4471 rift core"
        assert formats["text"].startswith("Keller, A. & Oliveira, T. (2024). ")
        assert f"{title}. Acme Data Portal." in formats["text"]
        assert [(p.last_names, p.first_names) for p in entry.persons["author"]] == [
            (["Keller"], ["Anna"]),
            (["Oliveira"], ["Tomas"]),
        ]
        assert entry.fields["year"] == "2024"
        assert codecs.decode(entry.fields["title"], "ulatex") == title
        assert codecs.decode(entry.fields["publisher"], "ulatex") == portal_name
        assert key == str(xrf.uuid)
        assert ris["authors"] == ["Keller, Anna", "Oliveira, Tomas"]
        assert (ris["year"], ris["title"], ris["publisher"]) == (
            "2024",
            title,
            portal_name,
        )

    def test_without_a_doi_the_files_give_the_permalink_and_no_doi(self, xrf):
        permalink = f"http://testserver/{xrf.uuid}/"

        formats = self.formats_of(_context(xrf))
        entry, ris = self.entry_of(formats)[1:]

        assert formats["text"].endswith(permalink)
        assert entry.fields["url"] == permalink
        assert "doi" not in entry.fields
        assert ris["urls"] == [permalink]
        assert "doi" not in ris

    def test_with_a_doi_the_files_give_the_doi_and_its_link(self, xrf):
        MeasurementIdentifier.objects.create(
            related=xrf, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.1234/meas_1"
        )

        formats = self.formats_of(_context(xrf))
        entry, ris = self.entry_of(formats)[1:]

        assert formats["text"].endswith("https://doi.org/10.1234/meas_1")
        assert entry.fields["doi"] == "10.1234/meas_1"
        assert entry.fields["url"] == "https://doi.org/10.1234/meas_1"
        assert ris["doi"] == "10.1234/meas_1"
        assert ris["urls"] == ["https://doi.org/10.1234/meas_1"]

    def test_a_measurement_is_a_dataset_entry_and_a_data_reference(self, xrf):
        formats = self.formats_of(_context(xrf))
        entry, ris = self.entry_of(formats)[1:]

        assert entry.type == "dataset"
        assert ris["type_of_reference"] == "DATA"

    def test_with_nobody_credited_no_author_is_given(self, xrf):
        formats = self.formats_of(_context(xrf))
        entry, ris = self.entry_of(formats)[1:]

        assert "author" not in entry.persons
        assert "authors" not in ris
        assert formats["text"].startswith("(")

    def test_a_sample_the_viewer_may_not_see_is_an_unpublished_sample_in_every_format(
        self, released
    ):
        sample = RockSampleFactory(
            dataset=_dataset(published=False), name="Hidden-3318 core"
        )
        measurement = XRFMeasurementFactory(dataset=released, sample=sample)

        formats = self.formats_of(_context(measurement))
        entry, ris = self.entry_of(formats)[1:]

        assert "of an unpublished sample" in formats["text"]
        assert codecs.decode(entry.fields["title"], "ulatex").endswith(
            "of an unpublished sample"
        )
        assert ris["title"].endswith("of an unpublished sample")
        assert "Hidden-3318" not in "".join(formats.values())

    def test_a_portal_measurement_type_gets_all_three_formats(self, released):
        sample = ConcreteSampleFactory(dataset=released, name="Portal core")
        measurement = ConcreteMeasurementFactory(
            dataset=released, sample=sample, name="Portal reading"
        )

        context = _context(measurement)
        formats = self.formats_of(context)
        entry, ris = self.entry_of(formats)[1:]

        title = "Portal reading [concrete measurement] of Portal core"
        assert list(formats) == ["text", "bibtex", "ris"]
        assert title in formats["text"]
        assert codecs.decode(entry.fields["title"], "ulatex") == title
        assert ris["title"] == title
        assert [e["url"] for e in context["citation"]["formats"]] == [
            reverse(
                "measurement:overview-citation",
                kwargs={"uuid": measurement.uuid, "format": key},
            )
            for key in ("text", "bibtex", "ris")
        ]
