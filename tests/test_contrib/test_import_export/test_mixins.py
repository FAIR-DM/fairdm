"""Tests for the export a records table answers with."""

import datetime
import re
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.utils.text import slugify

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from demo.models import RockSample, XRFMeasurement
from fairdm.contrib.collections.plugins import Samples
from fairdm.contrib.import_export.exports import EXPORT_FORMATS
from fairdm.factories import DatasetFactory, UserFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db


class TestExportRequest:
    """What a request carrying ``export`` is answered with."""

    def test_a_datasets_tab_exports_the_datasets_rows_only(
        self, client, tab_url, csv_rows, open_dataset, named_rocks
    ):
        RockSampleFactory(name="Elsewhere", dataset=DatasetFactory(published=True))

        response = client.get(
            tab_url(open_dataset, "samples", RockSample), {"export": "csv"}
        )

        assert response.status_code == 200
        assert response["Content-Disposition"].startswith("attachment")
        assert sorted(row["name"] for row in csv_rows(response)) == sorted(
            rock.name for rock in named_rocks
        )

    @pytest.mark.parametrize("key", ["xls", ""])
    def test_a_key_that_is_no_format_answers_404_and_sends_no_file(
        self, client, tab_url, open_dataset, named_rocks, key
    ):
        response = client.get(
            tab_url(open_dataset, "samples", RockSample), {"export": key}
        )

        assert response.status_code == 404
        assert "Content-Disposition" not in response

    def test_a_tab_with_no_types_answers_404_and_sends_no_file(
        self, client, tab_url, open_dataset
    ):
        response = client.get(tab_url(open_dataset, "samples"), {"export": "csv"})

        assert response.status_code == 404
        assert "Content-Disposition" not in response

    def test_a_listing_with_no_definition_for_its_type_answers_404(
        self, client, listing_url, monkeypatch
    ):
        monkeypatch.setattr(
            "fairdm.contrib.import_export.mixins.get_definition", lambda name: None
        )

        response = client.get(listing_url(RockSample), {"export": "csv"})

        assert response.status_code == 404

    def test_a_search_exports_the_matching_rows_from_every_page(
        self, client, tab_url, csv_rows, open_dataset, named_rocks, monkeypatch
    ):
        monkeypatch.setattr(Samples, "paginate_by", 2)

        response = client.get(
            tab_url(open_dataset, "samples", RockSample),
            {"q": "granite", "export": "csv"},
        )

        assert sorted(row["name"] for row in csv_rows(response)) == [
            "Granite A",
            "Granite B",
            "Granite C",
        ]

    def test_scope_all_exports_every_row_whatever_the_search(
        self, client, tab_url, csv_rows, open_dataset, named_rocks, monkeypatch
    ):
        monkeypatch.setattr(Samples, "paginate_by", 2)

        response = client.get(
            tab_url(open_dataset, "samples", RockSample),
            {"q": "granite", "export": "csv", "scope": "all"},
        )

        assert len(csv_rows(response)) == len(named_rocks)

    def test_the_page_in_the_address_does_not_change_the_file(
        self, client, tab_url, open_dataset, named_rocks, monkeypatch
    ):
        monkeypatch.setattr(Samples, "paginate_by", 2)
        url = tab_url(open_dataset, "samples", RockSample)

        first = client.get(url, {"export": "csv"})
        later = client.get(url, {"export": "csv", "page": "2"})

        assert later.content == first.content

    def test_a_request_without_export_renders_the_page(
        self, client, tab_url, open_dataset, named_rocks
    ):
        response = client.get(tab_url(open_dataset, "samples", RockSample))

        assert response.status_code == 200
        assert "Content-Disposition" not in response


class TestExportVisibility:
    """Nobody downloads what the table would not show them."""

    @pytest.mark.parametrize(("scope", "signed_in"), [("", False), ("all", True)])
    def test_a_portal_wide_export_holds_no_private_rocks(
        self,
        client,
        listing_url,
        csv_rows,
        named_rocks,
        private_rocks,
        scope,
        signed_in,
    ):
        if signed_in:
            client.force_login(UserFactory())

        response = client.get(
            listing_url(RockSample), {"export": "csv", "scope": scope}
        )

        names = {row["name"] for row in csv_rows(response)}
        assert names == {rock.name for rock in named_rocks}

    def test_a_measurement_whose_sample_the_viewer_may_not_open_is_still_listed(
        self, client, listing_url, csv_rows, open_dataset, private_rocks
    ):
        hidden = private_rocks[0]
        visible_sample = RockSampleFactory(dataset=open_dataset)
        XRFMeasurementFactory(dataset=open_dataset, sample=hidden)
        XRFMeasurementFactory(dataset=open_dataset, sample=visible_sample)

        response = client.get(listing_url(XRFMeasurement), {"export": "csv"})

        rows = csv_rows(response)
        assert len(rows) == 2
        by_sample_name = {row["sample_name"] for row in rows}
        assert hidden.name not in by_sample_name
        assert visible_sample.name in by_sample_name
        hidden_row = next(row for row in rows if row["sample_name"] == "")
        assert hidden_row["sample"] == ""


class TestExportStability:
    """The same rows come out in the same order."""

    def test_the_tables_sort_does_not_change_the_file(
        self, client, listing_url, named_rocks
    ):
        url = listing_url(RockSample)

        plain = client.get(url, {"export": "csv"})
        sorted_ = client.get(url, {"export": "csv", "sort": "-name"})

        assert sorted_.content == plain.content


class TestExportMenuContext:
    """What the page hands the menu."""

    def test_a_tab_with_no_records_has_no_menu(self, client, tab_url, open_dataset):
        response = client.get(tab_url(open_dataset, "samples"))

        assert response.context["export_menu"] is None

    def test_a_search_with_no_match_has_no_menu(
        self, client, tab_url, open_dataset, named_rocks
    ):
        response = client.get(
            tab_url(open_dataset, "samples", RockSample), {"q": "zzzzzz"}
        )

        assert response.context["export_menu"] is None

    def test_a_table_nobody_asked_to_narrow_is_not_filtered_and_names_its_type(
        self, client, tab_url, open_dataset, named_rocks
    ):
        response = client.get(tab_url(open_dataset, "samples", RockSample))

        menu = response.context["export_menu"]
        assert menu["filtered"] is False
        assert menu["shown"] == response.context["result_count"] == len(named_rocks)
        config = registry.get_for_model(RockSample)
        assert menu["type_name"] == config.get_verbose_name_plural()

    def test_a_search_makes_the_menu_filtered_and_counts_the_rows_it_shows(
        self, client, tab_url, open_dataset, named_rocks
    ):
        response = client.get(
            tab_url(open_dataset, "samples", RockSample), {"q": "granite"}
        )

        menu = response.context["export_menu"]
        assert menu["filtered"] is True
        assert menu["shown"] == response.context["result_count"] == 3

    def test_the_urls_keep_the_search_and_drop_the_page(
        self, client, tab_url, open_dataset, named_rocks, monkeypatch
    ):
        monkeypatch.setattr(Samples, "paginate_by", 2)

        response = client.get(
            tab_url(open_dataset, "samples", RockSample),
            {"q": "granite", "page": "2", "sort": "name"},
        )

        for export_format, entry in zip(
            EXPORT_FORMATS, response.context["export_menu"]["formats"], strict=True
        ):
            shown = parse_qs(urlsplit(entry["shown_url"]).query)
            assert shown == {
                "q": ["granite"],
                "sort": ["name"],
                "export": [export_format.key],
            }
            assert parse_qs(urlsplit(entry["all_url"]).query) == {
                "export": [export_format.key],
                "scope": ["all"],
            }


class TestFileName:
    """What a download is called."""

    @pytest.fixture
    def today(self, monkeypatch):
        """Hold the date still."""
        day = datetime.date(2026, 3, 4)
        monkeypatch.setattr(timezone, "localdate", lambda: day)
        return day

    def name_of(self, response):
        """Read the file name out of the response."""
        header = unquote(response["Content-Disposition"])
        return re.search(r"filename\*?=(?:utf-8'')?\"?([^\";]+)", header).group(1)

    def test_a_datasets_file_names_the_dataset_the_type_and_the_day(
        self, client, tab_url, today, named_rocks
    ):
        dataset = named_rocks[0].dataset
        response = client.get(
            tab_url(dataset, "samples", RockSample), {"export": "csv"}
        )

        plural = registry.get_for_model(RockSample).get_verbose_name_plural()
        expected = slugify(f"{dataset.name} {plural} {today.isoformat()}")
        assert self.name_of(response) == f"{expected}.csv"

    def test_a_portal_wide_file_names_the_type_and_the_day(
        self, client, listing_url, today, named_rocks
    ):
        response = client.get(listing_url(RockSample), {"export": "tsv"})

        plural = registry.get_for_model(RockSample).get_verbose_name_plural()
        assert self.name_of(response) == (
            f"{slugify(f'{plural} {today.isoformat()}')}.tsv"
        )

    def test_a_name_in_another_script_stays_in_that_script(
        self, client, tab_url, today
    ):
        dataset = DatasetFactory(
            name="Горные породы", visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=dataset)

        response = client.get(
            tab_url(dataset, "samples", RockSample), {"export": "csv"}
        )

        assert self.name_of(response).startswith("горные-породы-")


class TestExportQueries:
    """A row costs no query of its own."""

    @pytest.mark.parametrize("model", [RockSample, XRFMeasurement])
    def test_more_rows_cost_what_fewer_do(
        self, client, tab_url, open_dataset, model, django_assert_max_num_queries
    ):
        sample = RockSampleFactory(dataset=open_dataset)

        def add(count):
            """Add records of the type to the dataset."""
            if model is RockSample:
                RockSampleFactory.create_batch(count, dataset=open_dataset)
            else:
                XRFMeasurementFactory.create_batch(
                    count, dataset=open_dataset, sample=sample
                )

        kind = "samples" if model is RockSample else "measurements"
        url = tab_url(open_dataset, kind, model)
        add(1)
        client.get(url, {"export": "csv"})
        with CaptureQueriesContext(connection) as few:
            client.get(url, {"export": "csv"})

        add(2)

        with django_assert_max_num_queries(len(few.captured_queries)):
            response = client.get(url, {"export": "csv"})
        assert response.status_code == 200
