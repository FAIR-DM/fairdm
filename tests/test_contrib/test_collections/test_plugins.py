"""The Samples and Measurements tabs of a dataset."""

import django_tables2 as tables
import pytest
from bs4 import BeautifulSoup
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import RockSample, SoilSample, XRFMeasurement
from fairdm.contrib.collections.plugins import Measurements
from fairdm.contrib.collections.tables import SampleTable
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, DatasetFactory, UserFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db


def address(dataset, kind, type_model=None):
    """Return the address of a dataset's tab, or of one type beneath it."""
    kwargs = {"uuid": dataset.uuid}
    if type_model is None:
        return reverse(f"dataset:{kind}", kwargs=kwargs)
    slug = registry.get_for_model(type_model).get_slug()
    return reverse(f"dataset:{kind}-type", kwargs={**kwargs, "type": slug})


def listed(response):
    """Return the records one page of the response's table lists."""
    return [row.record for row in response.context["table"].page.object_list]


def tab_links(response, dataset):
    """Return the addresses of the two tabs that the response's tab strip offers.

    The strip is the list that holds the dataset's Overview and Contributors tabs, which every
    viewer of a public dataset is offered.
    """
    page = BeautifulSoup(response.content, "html.parser")
    anchors = {dataset.get_absolute_url(), address(dataset, "contribution-list")}
    strips = [
        [a["href"] for a in ul.find_all("a", href=True)] for ul in page.find_all("ul")
    ]
    strip = min((hrefs for hrefs in strips if anchors <= set(hrefs)), key=len)
    wanted = {address(dataset, "samples"), address(dataset, "measurements")}
    return wanted & set(strip)


def team_member(dataset, level=ContributionLevel.VIEW):
    """Return a user listed on the dataset at the given level."""
    user = UserFactory()
    ContributionFactory(content_object=dataset, contributor=user, level=level)
    return user


@pytest.fixture
def dataset():
    """A published dataset with three rocks and two soils, three XRF and two ICP-MS runs."""
    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    rocks = RockSampleFactory.create_batch(3, dataset=dataset)
    SoilSampleFactory.create_batch(2, dataset=dataset)
    XRFMeasurementFactory.create_batch(3, dataset=dataset, sample=rocks[0])
    ICP_MS_MeasurementFactory.create_batch(2, dataset=dataset, sample=rocks[1])
    dataset.rocks = rocks
    return dataset


class TestDatasetRecords:
    def test_each_tab_lists_the_most_numerous_type_of_only_this_dataset(
        self, client, dataset
    ):
        other = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        foreign = RockSampleFactory.create_batch(5, dataset=other)
        XRFMeasurementFactory.create_batch(5, dataset=other, sample=foreign[0])

        samples = client.get(address(dataset, "samples"))
        measurements = client.get(address(dataset, "measurements"))

        assert samples.status_code == measurements.status_code == 200
        assert {r.pk for r in listed(samples)} == {r.pk for r in dataset.rocks}
        assert {type(r) for r in listed(measurements)} == {XRFMeasurement}
        assert len(listed(measurements)) == 3

    def test_exactly_the_types_the_dataset_holds_are_offered_with_their_counts(
        self, client, dataset
    ):
        samples = client.get(address(dataset, "samples"))
        measurements = client.get(address(dataset, "measurements"))

        assert [e["count"] for e in samples.context["type_entries"]] == [3, 2]
        assert [e["count"] for e in measurements.context["type_entries"]] == [3, 2]
        assert [e["url"] for e in samples.context["type_entries"]] == [
            address(dataset, "samples", RockSample),
            address(dataset, "samples", SoilSample),
        ]

    def test_a_tie_in_counts_is_ordered_by_name(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        SoilSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)

        response = client.get(address(dataset, "samples"))

        names = [e["name"] for e in response.context["type_entries"]]
        assert len(names) == 2
        assert names == sorted(names)

    def test_a_types_own_address_shows_that_type(self, client, dataset):
        response = client.get(address(dataset, "samples", SoilSample))

        assert response.status_code == 200
        assert {type(r) for r in listed(response)} == {SoilSample}
        assert len(listed(response)) == 2
        current = [e for e in response.context["type_entries"] if e["is_current"]]
        assert [e["count"] for e in current] == [2]

    def test_a_type_the_dataset_holds_none_of_is_not_found(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset)

        response = client.get(address(dataset, "samples", SoilSample))

        assert response.status_code == 404

    def test_an_unregistered_slug_is_not_found(self, client, dataset):
        url = reverse(
            "dataset:samples-type", kwargs={"uuid": dataset.uuid, "type": "no-such"}
        )

        assert client.get(url).status_code == 404

    def test_a_type_address_on_an_empty_tab_is_not_found(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        assert client.get(address(dataset, "samples", RockSample)).status_code == 404

    def test_a_measurement_on_another_datasets_sample_is_listed_with_its_own_dataset(
        self, client, dataset
    ):
        other = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        borrowed = RockSampleFactory(dataset=other)
        measurement = XRFMeasurementFactory(dataset=dataset, sample=borrowed)

        measurements = client.get(address(dataset, "measurements"))
        samples = client.get(address(other, "samples"))
        elsewhere = client.get(address(dataset, "samples"))

        assert measurement.pk in {r.pk for r in listed(measurements)}
        assert borrowed.pk in {r.pk for r in listed(samples)}
        assert borrowed.pk not in {r.pk for r in listed(elsewhere)}

    def test_a_private_dataset_is_not_found_to_a_visitor_and_open_to_its_team(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE, published=True)
        rock = RockSampleFactory(dataset=dataset)
        XRFMeasurementFactory(dataset=dataset, sample=rock)

        assert client.get(address(dataset, "samples")).status_code == 404
        assert client.get(address(dataset, "measurements")).status_code == 404

        client.force_login(team_member(dataset))
        assert client.get(address(dataset, "samples")).status_code == 200
        assert client.get(address(dataset, "measurements")).status_code == 200

    def test_each_rows_name_links_to_the_record(self, client, dataset):
        response = client.get(address(dataset, "samples"))

        for record in dataset.rocks:
            assert f'href="{record.get_absolute_url()}"' in response.content.decode()

    def test_a_sample_page_has_neither_tab(self, client, dataset):
        sample = dataset.rocks[0]

        response = client.get(sample.get_absolute_url())

        page = BeautifulSoup(response.content, "html.parser")
        tabs = [
            a["href"]
            for a in page.find_all("a", href=True)
            if a["href"].startswith(sample.get_absolute_url())
        ]
        assert tabs  # the sample's own tab strip is there
        assert not [
            h for h in tabs if h.rstrip("/").endswith(("samples", "measurements"))
        ]


class TestRecordState:
    @pytest.fixture
    def waiting(self):
        """A public dataset not yet published, holding a rock and its measurement."""
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        rock = RockSampleFactory(dataset=dataset)
        XRFMeasurementFactory(dataset=dataset, sample=rock)
        return dataset

    def test_a_visitor_is_offered_neither_tab_and_both_addresses_are_not_found(
        self, client, waiting
    ):
        overview = client.get(waiting.get_absolute_url())

        assert overview.status_code == 200
        assert tab_links(overview, waiting) == set()
        assert client.get(address(waiting, "samples")).status_code == 404
        assert client.get(address(waiting, "measurements")).status_code == 404
        assert client.get(address(waiting, "samples", RockSample)).status_code == 404

    def test_the_team_gets_both_tabs_and_the_rows(self, client, waiting):
        client.force_login(team_member(waiting))

        overview = client.get(waiting.get_absolute_url())
        samples = client.get(address(waiting, "samples"))
        measurements = client.get(address(waiting, "measurements"))

        assert tab_links(overview, waiting) == {
            address(waiting, "samples"),
            address(waiting, "measurements"),
        }
        assert samples.context["record_state"] == "listed"
        assert len(listed(samples)) == 1
        assert len(listed(measurements)) == 1

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_a_dataset_holding_nothing_is_empty_for_everyone(self, client, kind):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        overview = client.get(dataset.get_absolute_url())
        response = client.get(address(dataset, kind))

        assert len(tab_links(overview, dataset)) == 2
        assert response.status_code == 200
        assert response.context["record_state"] == "empty"
        assert response.context["type_entries"] == []

    def test_an_unpublished_dataset_holding_nothing_is_empty_for_its_team(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        client.force_login(team_member(dataset))

        response = client.get(address(dataset, "samples"))

        assert response.status_code == 200
        assert response.context["record_state"] == "empty"
        assert len(tab_links(client.get(dataset.get_absolute_url()), dataset)) == 2

    def test_with_no_measurement_type_registered_the_tab_is_empty(
        self, client, monkeypatch
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        monkeypatch.setattr(type(registry), "measurements", property(lambda self: []))

        response = client.get(address(dataset, "measurements"))

        assert response.status_code == 200
        assert response.context["record_state"] == "empty"


def table_of(response):
    """Return the table the response drew."""
    return response.context["table"]


def cell(response, record, column):
    """Return what the table drew in a record's cell of a column."""
    row = next(
        r for r in table_of(response).page.object_list if r.record.pk == record.pk
    )
    return str(row.get_cell(column))


@pytest.fixture
def sample_dataset():
    """A published dataset and a hidden-sample measurement, an openable one and a foreign one.

    The hidden sample belongs to a dataset that is not published, so a visitor may not
    open it. The foreign measurement belongs to another dataset and shares a name with an
    own one.
    """
    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    other = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
    shown = RockSampleFactory(dataset=dataset, name="Granite-shown")
    hidden = RockSampleFactory(dataset=other, name="Zq-hidden-sample")
    also_hidden = RockSampleFactory(dataset=other, name="Zq-also-hidden")
    own = XRFMeasurementFactory(dataset=dataset, sample=shown, name="needle own")
    behind = XRFMeasurementFactory(dataset=dataset, sample=hidden, name="needle behind")
    behind_too = XRFMeasurementFactory(dataset=dataset, sample=also_hidden)
    foreign_dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    foreign = XRFMeasurementFactory(
        dataset=foreign_dataset,
        sample=RockSampleFactory(dataset=foreign_dataset),
        name="needle foreign",
    )
    dataset.other = other
    dataset.records = {
        "shown": shown,
        "hidden": hidden,
        "also_hidden": also_hidden,
        "own": own,
        "behind": behind,
        "behind_too": behind_too,
        "foreign": foreign,
    }
    return dataset


class TestRecordTable:
    def test_measurements_lead_with_name_then_sample_and_have_no_dataset(
        self, client, sample_dataset
    ):
        response = client.get(address(sample_dataset, "measurements"))

        names = [column.name for column in table_of(response).columns]
        assert names[:2] == ["name", "sample_name"]
        assert "dataset" not in names
        assert "sample" not in names

    def test_samples_lead_with_name_and_have_no_dataset(self, client, dataset):
        response = client.get(address(dataset, "samples"))

        names = [column.name for column in table_of(response).columns]
        assert names[0] == "name"
        assert "dataset" not in names

    def test_a_sample_the_viewer_may_open_is_linked(self, client, sample_dataset):
        shown = sample_dataset.records["shown"]
        response = client.get(address(sample_dataset, "measurements"))

        drawn = cell(response, sample_dataset.records["own"], "sample_name")

        assert f'href="{shown.get_absolute_url()}"' in drawn

    def test_a_sample_the_viewer_may_not_see_is_a_dash_and_never_named(
        self, client, sample_dataset
    ):
        response = client.get(address(sample_dataset, "measurements"))

        assert cell(response, sample_dataset.records["behind"], "sample_name") == "—"
        assert "Zq-hidden-sample" not in response.content.decode()
        assert "Zq-also-hidden" not in response.content.decode()

    def test_the_sample_is_opened_by_the_viewers_own_credit_on_that_sample_alone(
        self, client, sample_dataset
    ):
        hidden = sample_dataset.records["hidden"]
        user = UserFactory()
        ContributionFactory(
            content_object=hidden, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        response = client.get(address(sample_dataset, "measurements"))

        opened = cell(response, sample_dataset.records["behind"], "sample_name")
        assert f'href="{hidden.get_absolute_url()}"' in opened
        assert (
            cell(response, sample_dataset.records["behind_too"], "sample_name") == "—"
        )

    def test_the_team_of_the_samples_dataset_may_open_the_sample(
        self, client, sample_dataset
    ):
        client.force_login(team_member(sample_dataset.other))

        response = client.get(address(sample_dataset, "measurements"))

        opened = cell(response, sample_dataset.records["behind"], "sample_name")
        assert "href=" in opened

    def test_search_filter_and_sort_stay_within_the_dataset(
        self, client, sample_dataset
    ):
        url = address(sample_dataset, "measurements")
        own = {r.pk for r in XRFMeasurement.objects.filter(dataset=sample_dataset)}

        searched = listed(client.get(url, {"q": "needle"}))
        sorted_up = listed(client.get(url, {"sort": "name"}))
        sorted_down = listed(client.get(url, {"sort": "-name"}))

        assert {r.name for r in searched} == {"needle own", "needle behind"}
        assert {r.pk for r in sorted_up} == {r.pk for r in sorted_down} == own
        assert [r.name for r in sorted_up] == sorted(r.name for r in sorted_up)
        assert [r.name for r in sorted_down] == [r.name for r in sorted_up][::-1]

    def test_a_filter_narrows_within_the_dataset(self, client, sample_dataset):
        url = address(sample_dataset, "measurements")
        sample_dataset.records["foreign"].__class__.objects.filter(
            pk=sample_dataset.records["foreign"].pk
        ).update(element="Fe")
        XRFMeasurement.objects.filter(dataset=sample_dataset).update(element="Si")
        XRFMeasurement.objects.filter(pk=sample_dataset.records["own"].pk).update(
            element="Fe"
        )

        rows = listed(client.get(url, {"element": "Fe"}))

        assert [r.pk for r in rows] == [sample_dataset.records["own"].pk]

    @pytest.mark.parametrize("sort", ["sample_name", "-sample_name"])
    def test_sorting_by_sample_puts_the_hidden_samples_in_one_block_after_the_named(
        self, client, sample_dataset, sort
    ):
        response = client.get(address(sample_dataset, "measurements"), {"sort": sort})

        rows = listed(response)
        hidden_flags = [bool(r.sample_open) for r in rows]
        assert hidden_flags == sorted(hidden_flags, reverse=True)
        assert hidden_flags.count(False) == 2
        named = [r.sample.name for r in rows if r.sample_open]
        assert named == sorted(named, reverse=sort.startswith("-"))

    def test_the_order_of_a_generated_table_ends_in_a_unique_key(
        self, client, sample_dataset
    ):
        url = address(sample_dataset, "measurements")

        for params in ({}, {"sort": "name"}, {"sort": "-sample_name"}):
            ordering = table_of(client.get(url, params)).data.data.query.order_by
            assert str(ordering[-1]).lstrip("-") in ("pk", "id")

    def test_the_order_of_a_declared_table_with_no_order_by_ends_in_a_unique_key(
        self, client, sample_dataset, monkeypatch
    ):
        class Plain(tables.Table):
            name = tables.Column()

            class Meta:
                model = XRFMeasurement
                fields = ("name",)

        monkeypatch.setattr(Measurements, "get_table_class", lambda self: Plain)

        response = client.get(address(sample_dataset, "measurements"))

        ordering = table_of(response).data.data.query.order_by
        assert str(ordering[-1]).lstrip("-") in ("pk", "id")

    def test_a_page_holds_fifty_rows(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory.create_batch(51, dataset=dataset)
        url = address(dataset, "samples")

        first = client.get(url)
        second = client.get(url, {"page": 2})

        assert len(listed(first)) == 50
        assert len(listed(second)) == 1


class TestRecordColumns:
    def test_a_dataset_the_viewer_may_open_is_linked_and_otherwise_only_named(
        self, dataset
    ):
        from types import SimpleNamespace

        from fairdm.contrib.collections.plugins import DatasetColumn

        column = DatasetColumn()

        opened = column.render(SimpleNamespace(dataset_open=True), dataset)
        closed = column.render(SimpleNamespace(dataset_open=False), dataset)

        assert f'href="{dataset.get_absolute_url()}"' in opened
        assert "href" not in closed
        assert dataset.name in closed

    def test_the_tab_marks_each_row_with_whether_its_dataset_and_sample_open(
        self, client, sample_dataset
    ):
        rows = listed(client.get(address(sample_dataset, "measurements")))

        assert {r.dataset_open for r in rows} == {True}
        by_pk = {r.pk: r.sample_open for r in rows}
        assert by_pk[sample_dataset.records["own"].pk] is True
        assert by_pk[sample_dataset.records["behind"].pk] is False


class TestRecordChoices:
    @staticmethod
    def offered_samples(response, user):
        """Return the samples the page's sample filter offers the request's user."""
        field = response.context["filter"].filters["sample"].field
        view = field.view_class.for_scope(field.scope)()
        return set(view.offered(user))

    def test_a_team_members_sample_filter_offers_their_unpublished_samples(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        sample = RockSampleFactory(dataset=dataset)
        XRFMeasurementFactory(dataset=dataset, sample=sample)
        member = team_member(dataset)
        client.force_login(member)

        response = client.get(address(dataset, "measurements"))

        field = response.context["filter"].filters["sample"].field
        assert field.scope == "view"
        assert sample in self.offered_samples(response, member)

    def test_a_visitors_sample_filter_offers_no_unpublished_sample(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        shown = RockSampleFactory(dataset=dataset)
        XRFMeasurementFactory(dataset=dataset, sample=shown)
        waiting_dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        waiting = RockSampleFactory(dataset=waiting_dataset)

        response = client.get(address(dataset, "measurements"))

        offered = self.offered_samples(response, response.wsgi_request.user)
        assert waiting not in offered
        assert shown in offered

    def test_a_datasets_own_tab_has_no_dataset_filter(self, client, dataset):
        for kind in ("samples", "measurements"):
            response = client.get(address(dataset, kind))

            assert "dataset" not in response.context["filter"].filters

    def test_the_type_filter_offers_only_the_types_of_the_listed_rows(
        self, client, dataset
    ):
        response = client.get(address(dataset, "measurements"))

        offered = response.context["filter"].filters["polymorphic_ctype"].queryset
        listed_types = {type(r) for r in listed(response)}
        assert {ct.model_class() for ct in offered} == listed_types


class TestRecordPage:
    @staticmethod
    def page(response):
        return BeautifulSoup(response.content, "html.parser")

    def test_the_trail_ends_in_the_dataset_and_the_kind(self, client, dataset):
        for kind, label in (("samples", "Samples"), ("measurements", "Measurements")):
            response = client.get(address(dataset, kind))

            trail = response.context["page"]["breadcrumbs"]
            assert [crumb["text"] for crumb in trail[-2:]] == [str(dataset), label]
            assert trail[-2]["href"] == dataset.get_absolute_url()

    def test_the_switcher_links_each_listed_type_to_its_address(self, client, dataset):
        response = client.get(address(dataset, "samples"))

        switcher = self.page(response).find(id="type-switcher")
        links = {a["href"] for a in switcher.find_all("a", href=True)}
        assert links == {
            address(dataset, "samples", RockSample),
            address(dataset, "samples", SoilSample),
        }

    def test_one_listed_type_has_no_switcher(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset)

        response = client.get(address(dataset, "samples"))

        assert response.status_code == 200
        assert self.page(response).find(id="type-switcher") is None

    def test_the_filter_panel_is_drawn_where_records_are_listed(self, client, dataset):
        response = client.get(address(dataset, "samples"))

        assert self.page(response).find(id="filterForm") is not None

    def test_an_empty_tab_has_no_filter_panel(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        response = client.get(address(dataset, "samples"))

        assert response.status_code == 200
        assert self.page(response).find(id="filterForm") is None


class TestUnregisteredType:
    @pytest.fixture
    def soils_unregistered(self, monkeypatch):
        """Take the soil sample type out of the registry, as a portal that dropped it would."""
        held = {
            model: config
            for model, config in registry._registry.items()
            if model is not SoilSample
        }
        monkeypatch.setattr(registry, "_registry", held)

    def test_records_of_an_unregistered_type_are_listed_under_the_fallback_entry(
        self, client, dataset, soils_unregistered
    ):
        response = client.get(address(dataset, "samples"))

        assert response.status_code == 200
        fallback = reverse(
            "dataset:samples-type", kwargs={"uuid": dataset.uuid, "type": "other"}
        )
        counts = {e["url"]: e["count"] for e in response.context["type_entries"]}
        assert counts[fallback] == 2

    def test_the_fallback_entry_lists_only_the_unregistered_records_in_the_base_table(
        self, client, dataset, soils_unregistered
    ):
        url = reverse(
            "dataset:samples-type", kwargs={"uuid": dataset.uuid, "type": "other"}
        )

        response = client.get(url)

        assert response.status_code == 200
        assert {type(r) for r in listed(response)} == {SoilSample}
        assert len(listed(response)) == 2
        assert type(response.context["table"]) is SampleTable

    def test_a_dataset_holding_only_unregistered_records_answers_200_and_lists_them(
        self, client, soils_unregistered
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        SoilSampleFactory.create_batch(3, dataset=dataset)

        response = client.get(address(dataset, "samples"))

        assert response.status_code == 200
        assert len(listed(response)) == 3
        assert response.context["record_state"] == "listed"

    def test_no_fallback_entry_is_offered_while_every_type_is_registered(
        self, client, dataset
    ):
        response = client.get(address(dataset, "samples"))

        assert all("/other/" not in e["url"] for e in response.context["type_entries"])


class TestRecordQueries:
    @staticmethod
    def count(client, url):
        client.get(url)  # warm the per-process caches
        with CaptureQueriesContext(connection) as queries:
            assert client.get(url).status_code == 200
        return len(queries)

    def test_samples_cost_the_same_queries_at_ten_rows_and_at_sixty(self, client):
        small = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        large = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory.create_batch(10, dataset=small)
        RockSampleFactory.create_batch(60, dataset=large)

        assert self.count(client, address(small, "samples")) == self.count(
            client, address(large, "samples")
        )

    def test_measurements_cost_the_same_queries_at_ten_rows_and_at_sixty(self, client):
        small = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        large = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        for dataset, rows in ((small, 10), (large, 60)):
            for _ in range(rows):
                sample = RockSampleFactory(dataset=dataset)
                XRFMeasurementFactory(dataset=dataset, sample=sample)

        assert self.count(client, address(small, "measurements")) == self.count(
            client, address(large, "measurements")
        )
