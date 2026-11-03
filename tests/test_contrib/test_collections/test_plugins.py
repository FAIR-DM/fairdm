"""The Samples and Measurements tabs of a dataset, a project and a contributor."""

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
    WaterSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import (
    ICP_MS_Measurement,
    RockSample,
    SoilSample,
    XRFMeasurement,
)
from fairdm.contrib.collections.plugins import Measurements
from fairdm.contrib.collections.tables import SampleTable
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
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

    def test_the_hidden_samples_keep_one_order_whichever_way_the_sort_runs(
        self, client, sample_dataset
    ):
        url = address(sample_dataset, "measurements")

        def hidden_block(sort):
            rows = listed(client.get(url, {"sort": sort}))
            return [r.pk for r in rows if not r.sample_open]

        ascending = hidden_block("sample_name")
        assert len(ascending) == 2
        assert hidden_block("-sample_name") == ascending

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


def project_address(project, kind, type_model=None):
    """Return the address of a project's tab, or of one type beneath it."""
    kwargs = {"uuid": project.uuid}
    if type_model is None:
        return reverse(f"project:{kind}", kwargs=kwargs)
    slug = registry.get_for_model(type_model).get_slug()
    return reverse(f"project:{kind}-type", kwargs={**kwargs, "type": slug})


def project_member(project, level=ContributionLevel.VIEW):
    """Return a user listed on the project at the given level."""
    user = UserFactory()
    ContributionFactory(content_object=project, contributor=user, level=level)
    return user


def tab_total(client, project, kind):
    """Return how many records a project's tab lists, added up across its types."""
    response = client.get(project_address(project, kind))
    return sum(entry["count"] for entry in response.context["type_entries"])


@pytest.fixture
def project():
    """A public project with a published, an unpublished and a private dataset.

    The published dataset holds two rocks and, as measurements, two XRF runs on the first rock
    and one on a rock of another project's dataset. The unpublished dataset holds two waters
    and the private one three soils and an ICP-MS run on the first soil.
    """
    project = ProjectFactory(visibility=Visibility.PUBLIC)
    published = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=True
    )
    unpublished = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=False
    )
    private = DatasetFactory(
        project=project, visibility=Visibility.PRIVATE, published=False
    )
    rocks = RockSampleFactory.create_batch(2, dataset=published)
    XRFMeasurementFactory.create_batch(2, dataset=published, sample=rocks[0])
    elsewhere = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    foreign_rock = RockSampleFactory(dataset=elsewhere)
    borrowing = XRFMeasurementFactory(dataset=published, sample=foreign_rock)
    WaterSampleFactory.create_batch(2, dataset=unpublished)
    soils = SoilSampleFactory.create_batch(3, dataset=private)
    ICP_MS_MeasurementFactory(dataset=private, sample=soils[0])
    project.published, project.unpublished, project.private = (
        published,
        unpublished,
        private,
    )
    project.rocks, project.foreign_rock, project.borrowing = (
        rocks,
        foreign_rock,
        borrowing,
    )
    return project


class TestProjectRecords:
    def test_a_visitor_is_listed_the_published_datasets_records_and_nothing_else(
        self, client, project
    ):
        samples = client.get(project_address(project, "samples"))
        measurements = client.get(project_address(project, "measurements"))

        assert samples.status_code == measurements.status_code == 200
        assert {r.pk for r in listed(samples)} == {r.pk for r in project.rocks}
        assert [e["count"] for e in samples.context["type_entries"]] == [2]
        assert [e["count"] for e in measurements.context["type_entries"]] == [3]
        everything = samples.content.decode() + measurements.content.decode()
        assert project.private.name not in everything
        assert project.unpublished.name not in everything

    def test_a_member_of_the_private_dataset_is_listed_its_records_too(
        self, client, project
    ):
        client.force_login(team_member(project.private))

        samples = client.get(project_address(project, "samples"))
        measurements = client.get(project_address(project, "measurements"))

        assert [e["count"] for e in samples.context["type_entries"]] == [3, 2]
        assert [e["count"] for e in measurements.context["type_entries"]] == [3, 1]
        assert {type(r) for r in listed(samples)} == {SoilSample}
        assert project.unpublished.name not in samples.content.decode()

    def test_the_projects_team_is_listed_every_record(self, client, project):
        client.force_login(project_member(project, ContributionLevel.EDIT))

        assert tab_total(client, project, "samples") == 7
        assert tab_total(client, project, "measurements") == 4

    def test_each_row_names_its_dataset_after_its_own_name_and_links_it_where_it_opens(
        self, client, project
    ):
        client.force_login(team_member(project.private))

        samples = client.get(project_address(project, "samples", SoilSample))
        rocks = client.get(project_address(project, "samples", RockSample))

        names = [column.name for column in table_of(samples).columns]
        assert names[:2] == ["name", "dataset_name"]
        assert "dataset" not in names
        soil = listed(samples)[0]
        assert f'href="{project.private.get_absolute_url()}"' in cell(
            samples, soil, "dataset_name"
        )
        rock = listed(rocks)[0]
        assert f'href="{project.published.get_absolute_url()}"' in cell(
            rocks, rock, "dataset_name"
        )

    def test_a_measurement_on_another_projects_sample_is_listed_and_the_sample_is_not(
        self, client, project
    ):
        measurements = client.get(project_address(project, "measurements"))
        samples = client.get(project_address(project, "samples"))

        assert project.borrowing.pk in {r.pk for r in listed(measurements)}
        assert project.foreign_rock.pk not in {r.pk for r in listed(samples)}

    def test_a_type_only_a_private_dataset_holds_is_not_found_to_a_visitor(
        self, client, project
    ):
        assert (
            client.get(project_address(project, "samples", SoilSample)).status_code
            == 404
        )
        assert (
            client.get(
                project_address(project, "measurements", ICP_MS_Measurement)
            ).status_code
            == 404
        )

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_no_visible_record_is_the_same_empty_as_no_record_at_all(
        self, client, kind
    ):
        none = ProjectFactory(visibility=Visibility.PUBLIC)
        waiting = ProjectFactory(visibility=Visibility.PUBLIC)
        waiting_dataset = DatasetFactory(
            project=waiting, visibility=Visibility.PUBLIC, published=False
        )
        hidden = ProjectFactory(visibility=Visibility.PUBLIC)
        hidden_dataset = DatasetFactory(
            project=hidden, visibility=Visibility.PRIVATE, published=True
        )
        for dataset in (waiting_dataset, hidden_dataset):
            sample = RockSampleFactory(dataset=dataset)
            XRFMeasurementFactory(dataset=dataset, sample=sample)

        answers = []
        for each in (none, waiting, hidden):
            response = client.get(project_address(each, kind))
            answers.append(
                (
                    response.status_code,
                    response.context["record_state"],
                    response.context["type_entries"],
                    len(listed(response)),
                )
            )

        assert answers == [(200, "empty", [], 0)] * 3

    def test_a_private_project_is_not_found_to_a_visitor_and_open_to_its_team(
        self, client
    ):
        private = ProjectFactory(visibility=Visibility.PRIVATE)
        dataset = DatasetFactory(
            project=private, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=dataset)

        assert client.get(project_address(private, "samples")).status_code == 404
        assert client.get(project_address(private, "measurements")).status_code == 404

        client.force_login(project_member(private))
        assert client.get(project_address(private, "samples")).status_code == 200
        assert client.get(project_address(private, "measurements")).status_code == 200

    def test_the_tabs_are_offered_on_the_projects_page(self, client, project):
        response = client.get(project.get_absolute_url())

        links = {
            a["href"]
            for a in BeautifulSoup(response.content, "html.parser").find_all(
                "a", href=True
            )
        }
        assert project_address(project, "samples") in links
        assert project_address(project, "measurements") in links

    def test_the_trail_ends_in_the_project_and_the_kind(self, client, project):
        response = client.get(project_address(project, "samples"))

        trail = response.context["page"]["breadcrumbs"]
        assert trail[-2]["href"] == project.get_absolute_url()
        assert response.context["holder"] == "project"


class TestProjectRecordChoices:
    @staticmethod
    def offered_datasets(response, user):
        """Return the datasets the page's dataset filter offers the request's user."""
        field = response.context["filter"].filters["dataset"].field
        view = field.view_class.for_scope(field.scope)()
        return set(view.offered(user))

    def test_the_dataset_filter_stays_and_offers_the_viewer_what_they_may_see(
        self, client, project
    ):
        response = client.get(project_address(project, "measurements"))

        field = response.context["filter"].filters["dataset"].field
        assert field.scope == "view"
        offered = self.offered_datasets(response, response.wsgi_request.user)
        assert project.published in offered
        assert project.private not in offered

    def test_a_member_of_the_private_dataset_is_offered_it(self, client, project):
        member = team_member(project.private)
        client.force_login(member)

        response = client.get(project_address(project, "measurements"))

        assert project.private in self.offered_datasets(response, member)

    def test_the_sample_filter_offers_no_sample_the_viewer_may_not_see(
        self, client, project
    ):
        response = client.get(project_address(project, "measurements"))

        field = response.context["filter"].filters["sample"].field
        view = field.view_class.for_scope(field.scope)()
        offered = set(view.offered(response.wsgi_request.user))
        assert set(project.rocks) <= offered
        assert not offered & set(Sample.objects.filter(dataset=project.private))


def project_figures(page, project):
    """Return the Samples and Measurements figures as ``{tab: value}``, found by their link."""
    figures = {}
    for kind in ("samples", "measurements"):
        link = page.select_one(
            f'.stat-title a[href="{project_address(project, kind)}"]'
        )
        if link is not None:
            figure = link.find_parent(class_="stat")
            figures[kind] = figure.select_one(".stat-value").get_text(strip=True)
    return figures


class TestProjectOverviewFigures:
    @staticmethod
    def figures(client, project):
        response = client.get(project.get_absolute_url())
        return project_figures(BeautifulSoup(response.content, "html.parser"), project)

    def test_the_figures_link_to_the_tabs_and_equal_their_totals_for_every_viewer(
        self, client, project
    ):
        viewers = {
            "visitor": (None, {"samples": "2", "measurements": "3"}),
            "private member": (
                team_member(project.private),
                {"samples": "5", "measurements": "4"},
            ),
            "team": (
                project_member(project, ContributionLevel.EDIT),
                {"samples": "7", "measurements": "4"},
            ),
        }
        for viewer, expected in viewers.values():
            client.logout()
            if viewer is not None:
                client.force_login(viewer)

            figures = self.figures(client, project)

            assert figures == {
                "samples": str(tab_total(client, project, "samples")),
                "measurements": str(tab_total(client, project, "measurements")),
            }
            assert figures == expected

    def test_a_private_datasets_member_gets_the_same_figure_and_total_in_a_public_project(
        self, client, project
    ):
        client.force_login(team_member(project.private))

        figures = self.figures(client, project)

        assert figures["samples"] == str(tab_total(client, project, "samples")) == "5"

    def test_the_datasets_figure_counts_the_datasets_the_viewer_may_see(
        self, client, project
    ):
        response = client.get(project.get_absolute_url())

        assert response.context["counts"]["datasets"] == 2
        client.force_login(team_member(project.private))
        response = client.get(project.get_absolute_url())
        assert response.context["counts"]["datasets"] == 3


class TestProjectRecordQueries:
    @staticmethod
    def count(client, url):
        client.get(url)  # warm the per-process caches
        with CaptureQueriesContext(connection) as queries:
            assert client.get(url).status_code == 200
        return len(queries)

    @staticmethod
    def project_of(rows):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        for _ in range(rows):
            sample = RockSampleFactory(dataset=dataset)
            XRFMeasurementFactory(dataset=dataset, sample=sample)
        return project

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_a_tab_costs_the_same_queries_at_ten_rows_and_at_sixty(self, client, kind):
        small, large = self.project_of(10), self.project_of(60)

        assert self.count(client, project_address(small, kind)) == self.count(
            client, project_address(large, kind)
        )

    def test_the_overview_costs_the_same_queries_at_ten_rows_and_at_sixty(self, client):
        small, large = self.project_of(10), self.project_of(60)

        assert self.count(client, small.get_absolute_url()) == self.count(
            client, large.get_absolute_url()
        )


def contributor_address(contributor, kind, type_model=None):
    """Return the address of a contributor's tab, or of one type beneath it."""
    kwargs = {"uuid": contributor.uuid}
    if type_model is None:
        return reverse(f"contributor:{kind}", kwargs=kwargs)
    slug = registry.get_for_model(type_model).get_slug()
    return reverse(f"contributor:{kind}-type", kwargs={**kwargs, "type": slug})


def credit(contributor, record):
    """Credit a contributor on a record, a person at the view level as the Contributors tab does."""
    level = None if isinstance(contributor, Organization) else ContributionLevel.VIEW
    ContributionFactory(content_object=record, contributor=contributor, level=level)


def released_dataset(project=None):
    """Return a published public dataset, in the project when one is given."""
    return DatasetFactory(project=project, visibility=Visibility.PUBLIC, published=True)


@pytest.fixture
def credited():
    """A person credited on a project, on a dataset in another project and on one sample.

    The project holds a released dataset of two rocks and an XRF run on the first, and an
    unpublished dataset of one rock. The other project holds the credited dataset of three
    rocks and a sibling of two. A third dataset holds the credited sample, its sibling and an
    XRF run on the credited sample made by someone else. The credited dataset also holds an
    XRF run on a rock of a private dataset. One rock of the first project is credited directly
    too.
    """
    person = PersonFactory()
    project = ProjectFactory(visibility=Visibility.PUBLIC)
    first = released_dataset(project)
    unpublished = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=False
    )
    first_rocks = RockSampleFactory.create_batch(2, dataset=first)
    first_run = XRFMeasurementFactory(dataset=first, sample=first_rocks[0])
    RockSampleFactory(dataset=unpublished)
    credit(person, project)
    credit(person, first_rocks[0])

    other = ProjectFactory(visibility=Visibility.PUBLIC)
    own = released_dataset(other)
    sibling = released_dataset(other)
    own_rocks = RockSampleFactory.create_batch(3, dataset=own)
    sibling_rocks = RockSampleFactory.create_batch(2, dataset=sibling)
    credit(person, own)
    private = DatasetFactory(visibility=Visibility.PRIVATE, published=True)
    behind = RockSampleFactory(dataset=private)
    behind_run = XRFMeasurementFactory(dataset=own, sample=behind)

    holder = released_dataset()
    picked, left = RockSampleFactory.create_batch(2, dataset=holder)
    credit(person, picked)
    others_run = XRFMeasurementFactory(dataset=holder, sample=picked)
    person.samples_listed = [*first_rocks, *own_rocks, picked]
    person.samples_unlisted = [*sibling_rocks, left]
    person.runs_listed = [first_run, behind_run]
    person.runs_unlisted = [others_run]
    person.held = {"first": first, "own": own}
    return person


class TestContributorRecords:
    def test_a_person_lists_the_records_credited_directly_or_beneath_a_credit_once_each(
        self, client, credited
    ):
        response = client.get(contributor_address(credited, "samples"))

        assert response.status_code == 200
        pks = [r.pk for r in listed(response)]
        assert sorted(pks) == sorted(r.pk for r in credited.samples_listed)
        assert not set(pks) & {r.pk for r in credited.samples_unlisted}

    def test_credit_on_a_sample_brings_in_no_one_elses_measurements_of_it(
        self, client, credited
    ):
        response = client.get(contributor_address(credited, "measurements"))

        pks = {r.pk for r in listed(response)}
        assert pks == {r.pk for r in credited.runs_listed}
        assert not pks & {r.pk for r in credited.runs_unlisted}

    def test_a_measurement_released_with_an_unreleased_sample_is_listed_with_a_dash(
        self, client, credited
    ):
        response = client.get(contributor_address(credited, "measurements"))

        run = credited.runs_listed[1]
        assert run.pk in {r.pk for r in listed(response)}
        assert cell(response, run, "sample_name") == "—"

    def test_each_rows_dataset_is_linked_where_it_opens(self, client, credited):
        response = client.get(contributor_address(credited, "samples"))

        row = next(
            r for r in listed(response) if r.dataset_id == credited.held["own"].pk
        )
        assert f'href="{credited.held["own"].get_absolute_url()}"' in cell(
            response, row, "dataset_name"
        )

    def test_an_organization_lists_the_records_of_a_project_it_owns_and_not_its_members(
        self, client
    ):
        organization = OrganizationFactory()
        owned = ProjectFactory(visibility=Visibility.PUBLIC, owner=organization)
        inside = released_dataset(owned)
        mine = RockSampleFactory.create_batch(2, dataset=inside)
        member = PersonFactory()
        AffiliationFactory(person=member, organization=organization)
        elsewhere = released_dataset()
        RockSampleFactory.create_batch(2, dataset=elsewhere)
        credit(member, elsewhere)

        response = client.get(contributor_address(organization, "samples"))

        assert response.status_code == 200
        assert {r.pk for r in listed(response)} == {r.pk for r in mine}


class TestContributorViewer:
    @pytest.fixture
    def hidden(self):
        """A person credited on a private, an unpublished public and a private-project dataset."""
        person = PersonFactory()
        private = DatasetFactory(visibility=Visibility.PRIVATE, published=True)
        unpublished = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        walled = DatasetFactory(
            project=ProjectFactory(visibility=Visibility.PRIVATE),
            visibility=Visibility.PUBLIC,
            published=True,
        )
        person.hidden = {}
        for name, dataset in (
            ("private", private),
            ("unpublished", unpublished),
            ("walled", walled),
        ):
            credit(person, dataset)
            sample = RockSampleFactory(dataset=dataset)
            XRFMeasurementFactory(dataset=dataset, sample=sample)
            person.hidden[name] = dataset
        return person

    @staticmethod
    def offered_datasets(response, user):
        """Return the datasets the page's dataset filter offers the request's user."""
        field = response.context["filter"].filters["dataset"].field
        view = field.view_class.for_scope(field.scope)()
        return set(view.offered(user, owner=field.owner_pk))

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_anyone_else_sees_none_of_them_in_rows_totals_types_or_choices(
        self, client, hidden, kind
    ):
        client.force_login(team_member(hidden.hidden["private"]))

        response = client.get(contributor_address(hidden, kind))

        assert response.context["record_state"] == "empty"
        assert listed(response) == []
        assert response.context["type_entries"] == []
        page = response.content.decode()
        assert not any(d.name in page for d in hidden.hidden.values())

    def test_the_filter_choices_of_someone_elses_page_hold_none_of_them(
        self, client, hidden
    ):
        released = released_dataset()
        XRFMeasurementFactory(
            dataset=released, sample=RockSampleFactory(dataset=released)
        )
        credit(hidden, released)

        response = client.get(contributor_address(hidden, "measurements"))

        filters = response.context["filter"].filters
        assert filters["dataset"].field.scope == "public"
        assert filters["dataset"].field.owner_pk is None
        user = response.wsgi_request.user
        datasets = self.offered_datasets(response, user)
        assert released in datasets
        assert not datasets & {hidden.hidden["private"], hidden.hidden["walled"]}
        field = filters["sample"].field
        samples = set(field.view_class.for_scope(field.scope)().offered(user))
        assert not samples & set(
            Sample.objects.filter(dataset__in=hidden.hidden.values())
        )

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_the_person_sees_them_and_their_choices_include_them(
        self, client, hidden, kind
    ):
        client.force_login(hidden)

        response = client.get(contributor_address(hidden, kind))

        assert response.context["record_state"] == "listed"
        assert {r.dataset_id for r in listed(response)} == {
            d.pk for d in hidden.hidden.values()
        }
        assert sum(e["count"] for e in response.context["type_entries"]) == 3

    def test_the_persons_own_filters_offer_their_records(self, client, hidden):
        client.force_login(hidden)

        response = client.get(contributor_address(hidden, "measurements"))

        field = response.context["filter"].filters["dataset"].field
        assert field.owner_pk == hidden.pk
        assert set(hidden.hidden.values()) <= self.offered_datasets(response, hidden)

    def test_an_organization_shows_none_of_them_even_to_a_member_of_the_dataset(
        self, client
    ):
        organization = OrganizationFactory()
        private = DatasetFactory(visibility=Visibility.PRIVATE, published=True)
        RockSampleFactory(dataset=private)
        credit(organization, private)
        client.force_login(team_member(private, ContributionLevel.MANAGE))

        response = client.get(contributor_address(organization, "samples"))

        assert response.status_code == 200
        assert response.context["record_state"] == "empty"
        assert listed(response) == []

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_a_contributor_with_nothing_the_viewer_may_see_is_empty(self, client, kind):
        person = PersonFactory()

        response = client.get(contributor_address(person, kind))

        assert (
            response.status_code,
            response.context["record_state"],
            response.context["type_entries"],
        ) == (200, "empty", [])


class TestContributorRecordQueries:
    @staticmethod
    def count(client, url):
        client.get(url)  # warm the per-process caches
        with CaptureQueriesContext(connection) as queries:
            assert client.get(url).status_code == 200
        return len(queries)

    @staticmethod
    def person_of(rows):
        person = PersonFactory()
        dataset = released_dataset()
        credit(person, dataset)
        for _ in range(rows):
            sample = RockSampleFactory(dataset=dataset)
            XRFMeasurementFactory(dataset=dataset, sample=sample)
        return person

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_a_tab_costs_the_same_queries_at_ten_rows_and_at_sixty(self, client, kind):
        small, large = self.person_of(10), self.person_of(60)

        assert self.count(client, contributor_address(small, kind)) == self.count(
            client, contributor_address(large, kind)
        )
