"""Views tests for fairdm.contrib.collections.views.DataTableView (US2)."""

import ast
import datetime
import importlib
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains

import fairdm.contrib.collections as collections_pkg
from fairdm.contrib.collections.views import DataTableView
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm_demo.factories import (
    CustomSampleFactory,
    ExampleMeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
    WaterSampleFactory,
)
from fairdm_demo.models import (
    CustomSample,
    ExampleMeasurement,
    RockSample,
    SoilSample,
    WaterSample,
)


@pytest.mark.django_db
class TestPublicationFiltering:
    """FR-011, SC-002, SC-010: a listing shows only published records, identically for
    every viewer - the four FR-011 names explicitly, and the staff client is the one
    most likely to be widened by accident."""

    @pytest.fixture(autouse=True)
    def _records(self, published_sample, unpublished_sample):
        self.published_sample = published_sample
        self.unpublished_sample = unpublished_sample

    def _get(self, client):
        slug = registry.get_for_model(RockSample).get_slug()
        return client.get(reverse(f"{slug}-list"))

    def test_signed_out_visitor_sees_only_the_published_record(self, client):
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries

    def test_the_records_owner_sees_only_the_published_record(
        self, client, dataset_owner
    ):
        client.force_login(dataset_owner)
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries

    def test_a_contributor_sees_only_the_published_record(
        self, client, dataset_contributor
    ):
        client.force_login(dataset_contributor)
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries

    def test_portal_staff_sees_only_the_published_record(self, client, staff_user):
        client.force_login(staff_user)
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries


@pytest.mark.django_db
class TestColumnsPerType:
    """FR-014, SC-003: a listing's columns come from its type's own registration, so
    two types with different declarations produce different columns."""

    def test_two_types_with_different_field_declarations_produce_different_columns(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        SoilSampleFactory(dataset=published_dataset)

        rock_slug = registry.get_for_model(RockSample).get_slug()
        soil_slug = registry.get_for_model(SoilSample).get_slug()

        rock_response = client.get(reverse(f"{rock_slug}-list"))
        soil_response = client.get(reverse(f"{soil_slug}-list"))

        rock_columns = {c.name for c in rock_response.context["table"].columns}
        soil_columns = {c.name for c in soil_response.context["table"].columns}

        assert "rock_type" in rock_columns
        assert "rock_type" not in soil_columns
        assert "soil_type" in soil_columns
        assert "soil_type" not in rock_columns


@pytest.mark.django_db
class TestDefaultColumns:
    """FR-015: a type registered with no field declarations still produces a working
    listing from the framework's own defaults, rather than failing."""

    def test_a_type_with_no_field_declarations_renders_with_framework_defaults(
        self, client, published_dataset
    ):
        CustomSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(CustomSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert response.status_code == 200
        assert list(response.context["table"].columns)


@pytest.mark.django_db
class TestPaging:
    """FR-017: a listing pages its results, and every page is reachable."""

    def test_a_listing_takes_its_page_size_from_the_base_table_view(
        self, client, published_dataset
    ):
        """T086: the listing declares no page size of its own, so the base
        class's 100 is what reaches it. A base class with no default at all
        would leave it unpaginated."""
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert "paginate_by" not in DataTableView.__dict__
        assert response.context["table"].paginator.per_page == 100

    def test_a_second_page_returns_the_next_slice_and_carries_paging_controls(
        self, client, published_dataset
    ):
        # Enough rows to spill onto a second page at whatever page size the view
        # is configured for, rather than a literal that silently stops producing
        # one when that size changes (T086 raised it from 20 to 100).
        samples = RockSampleFactory.create_batch(
            DataTableView.paginate_by + 5, dataset=published_dataset
        )
        # `Sample`'s default ordering is `added` (auto_now_add), and a tight creation
        # loop can leave several rows with the same timestamp - a stable default order
        # with a tie-break is T041's deliverable (US-3, D5), not this story's. Space
        # the timestamps out here so paging is deterministic without it.
        base = timezone.now()
        for offset, sample in enumerate(samples):
            Sample.objects.filter(pk=sample.pk).update(
                added=base + datetime.timedelta(seconds=offset)
            )
        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        first_page = client.get(url)
        second_page = client.get(url, {"page": 2})

        assert first_page.status_code == 200
        assert second_page.status_code == 200
        assert first_page.context["page_obj"].number == 1
        assert second_page.context["page_obj"].number == 2

        # `context["object_list"]` is the view's own, unpaginated queryset - the table
        # is the only paginator here (`MVPTableViewMixin.paginate_queryset`) - so the
        # slice actually shown on each page is read from the table instead.
        first_ids = {
            row.record.pk for row in first_page.context["table"].paginated_rows
        }
        second_ids = {
            row.record.pk for row in second_page.context["table"].paginated_rows
        }
        assert first_ids.isdisjoint(second_ids)


@pytest.mark.django_db
class TestEmptyState:
    """FR-018: a listing with no published records to show says so - in this
    feature's own words, not the application shell's authoring copy."""

    def test_a_type_with_no_published_records_shows_this_features_own_empty_state(
        self, client
    ):
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        content = response.content.decode()
        assert "Click the button below to get started" not in content
        empty_state = response.context["empty_state"]
        assert empty_state["heading"]
        assert empty_state["message"]
        assert str(empty_state["heading"]) in content
        assert str(empty_state["message"]) in content


@pytest.mark.django_db
class TestRowLinksToRecord:
    """FR-019, Acceptance Scenario 9: selecting a row opens that record's own page -
    for a measurement listing as well as a sample listing."""

    def test_a_sample_listing_row_links_to_the_samples_own_page(
        self, client, published_sample
    ):
        slug = registry.get_for_model(RockSample).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        assertContains(response, published_sample.get_absolute_url())

    def test_a_measurement_listing_row_links_to_the_measurements_own_page(
        self, client, published_dataset
    ):
        sample = RockSampleFactory(dataset=published_dataset)
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=published_dataset
        )
        slug = registry.get_for_model(ExampleMeasurement).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        assertContains(response, measurement.get_absolute_url())


@pytest.mark.django_db
class TestQueryCount:
    """FR-020, SC-006: the number of database queries a listing page issues does not
    grow with the number of rows it shows - for the measurement listing as well as the
    sample listing.

    Two pieces of measurement hygiene make this readable at the page level, and both
    are load-bearing.

    `orbit` is disabled for the duration. It records requests and signals by writing
    rows of its own, and it reaches signals by monkey-patching `Signal.send` globally
    and `repr()`ing every kwarg - which, under Django's `instrumented_test_render`,
    reprs the render context and re-evaluates whatever queryset it still carries.
    Either way its writes land in the same count as the page's own.
    `orbit.conf.get_config()` reads `settings.ORBIT` at call time, so turning it off
    here removes the noise at source rather than filtering it afterwards.

    The page is also fetched once before either measurement. The first request in a
    test process does one-time work the second never repeats - the site cache, the
    identity records, their savepoints - which shows up as the first count being the
    larger one however flat the feature is.
    """

    @pytest.fixture(autouse=True)
    def without_orbit(self, settings):
        settings.ORBIT = {"ENABLED": False}

    def _page_query_count(self, client, url):
        client.get(url)  # warm up one-time per-process setup
        with CaptureQueriesContext(connection) as ctx:
            response = client.get(url)
        assert response.status_code == 200
        return len(ctx.captured_queries)

    def test_sample_listing_query_count_is_flat(self, client, published_dataset):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        one_row_count = self._page_query_count(client, url)

        RockSampleFactory.create_batch(19, dataset=published_dataset)  # a full page

        full_page_count = self._page_query_count(client, url)

        assert full_page_count == one_row_count

    def test_measurement_listing_query_count_is_flat(self, client, published_dataset):
        sample = RockSampleFactory(dataset=published_dataset)
        ExampleMeasurementFactory(sample=sample, dataset=published_dataset)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()
        url = reverse(f"{slug}-list")

        one_row_count = self._page_query_count(client, url)

        other_samples = RockSampleFactory.create_batch(19, dataset=published_dataset)
        for other_sample in other_samples:
            ExampleMeasurementFactory(sample=other_sample, dataset=published_dataset)

        full_page_count = self._page_query_count(client, url)

        assert full_page_count == one_row_count


@pytest.mark.django_db
class TestSearch:
    """FR-024, FR-025, FR-031, SC-004: `?q=` searches the fields a type
    declares, or `name` by default when it declares none - and never widens
    what publication already excluded."""

    def _search(self, client, slug, term):
        return client.get(reverse(f"{slug}-list"), {"q": term})

    def test_with_no_search_fields_declared_a_word_from_the_name_matches(
        self, client, published_dataset
    ):
        target = WaterSampleFactory(name="Riverbank Alpha", dataset=published_dataset)
        WaterSampleFactory(name="Coastal Beta", dataset=published_dataset)

        slug = registry.get_for_model(WaterSample).get_slug()
        response = self._search(client, slug, "Alpha")

        assert list(response.context["object_list"]) == [target]

    def test_a_word_held_only_by_a_declared_search_field_matches(
        self, client, published_dataset
    ):
        target = RockSampleFactory(
            rock_type="Basalt", mineral_content="Quartz", dataset=published_dataset
        )
        RockSampleFactory(
            rock_type="Granite", mineral_content="Feldspar", dataset=published_dataset
        )

        slug = registry.get_for_model(RockSample).get_slug()
        response = self._search(client, slug, "Basalt")

        assert list(response.context["object_list"]) == [target]

    def test_a_word_held_only_by_an_undeclared_field_does_not_match(
        self, client, published_dataset
    ):
        RockSampleFactory(
            rock_type="Basalt", mineral_content="Quartz", dataset=published_dataset
        )

        slug = registry.get_for_model(RockSample).get_slug()
        response = self._search(client, slug, "Quartz")

        assert list(response.context["object_list"]) == []

    def test_a_search_matching_nothing_renders_the_empty_state(
        self, client, published_sample
    ):
        slug = registry.get_for_model(RockSample).get_slug()
        response = self._search(client, slug, "NoSuchWordAnywhereInThisSuite")

        content = response.content.decode()
        empty_state = response.context["empty_state"]
        assert str(empty_state["heading"]) in content
        assert str(empty_state["message"]) in content

    def test_a_search_matching_an_unpublished_records_field_returns_nothing(
        self, client, unpublished_dataset
    ):
        RockSampleFactory(rock_type="Obsidian", dataset=unpublished_dataset)

        slug = registry.get_for_model(RockSample).get_slug()
        response = self._search(client, slug, "Obsidian")

        assert list(response.context["object_list"]) == []


@pytest.mark.django_db
class TestFilters:
    """FR-029, Acceptance Scenario 6: every filter the registry generates for
    a type narrows the listing to matching records and raises nothing."""

    def test_a_char_filter_narrows_to_matching_records(self, client, published_dataset):
        target = SoilSampleFactory(soil_type="Clay", dataset=published_dataset)
        SoilSampleFactory(soil_type="Sand", dataset=published_dataset)

        slug = registry.get_for_model(SoilSample).get_slug()
        response = client.get(reverse(f"{slug}-list"), {"soil_type": "Clay"})

        assert response.status_code == 200
        assert list(response.context["object_list"]) == [target]

    def test_a_range_filter_on_a_decimal_field_narrows_to_matching_records(
        self, client, published_dataset
    ):
        target = SoilSampleFactory(ph_level="6.50", dataset=published_dataset)
        SoilSampleFactory(ph_level="8.00", dataset=published_dataset)

        slug = registry.get_for_model(SoilSample).get_slug()
        response = client.get(
            reverse(f"{slug}-list"),
            {"ph_level_min": "6.00", "ph_level_max": "7.00"},
        )

        assert response.status_code == 200
        assert list(response.context["object_list"]) == [target]

    def test_a_range_filter_on_an_integer_field_narrows_to_matching_records(
        self, client, published_dataset
    ):
        target = SoilSampleFactory(depth_cm=10, dataset=published_dataset)
        SoilSampleFactory(depth_cm=100, dataset=published_dataset)

        slug = registry.get_for_model(SoilSample).get_slug()
        response = client.get(
            reverse(f"{slug}-list"), {"depth_cm_min": "0", "depth_cm_max": "20"}
        )

        assert response.status_code == 200
        assert list(response.context["object_list"]) == [target]


@pytest.mark.django_db
class TestFilterChoicesOnTheRenderedPage:
    """T078, FR-030, SC-002: no filter on a listing offers the name of a record
    whose own dataset is unpublished, to any viewer.

    Measured on the page's own filter set rather than on the generated class,
    because the two are not the same object and the difference is where the leak
    lived. `SampleFilterMixin.__init__` and `MeasurementFilterMixin.__init__`
    assign their hand-declared `dataset` and `sample` choice lists at
    instantiation, after any class-level scoping, from managers that apply no
    publication test. A test that reads `base_filters` off the class never runs
    that code and passes either way.
    """

    def _page_filters(self, client, model):
        slug = registry.get_for_model(model).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        assert response.status_code == 200
        return response.context["filter"].filters

    def test_a_measurement_listings_sample_filter_offers_no_unpublished_sample(
        self, client, published_dataset, unpublished_dataset
    ):
        offered = RockSampleFactory(dataset=published_dataset)
        withheld = RockSampleFactory(dataset=unpublished_dataset)
        ExampleMeasurementFactory(sample=offered, dataset=published_dataset)

        choices = self._page_filters(client, ExampleMeasurement)["sample"].queryset

        assert offered in choices
        assert withheld not in choices

    def test_a_measurement_listings_dataset_filter_offers_no_unpublished_dataset(
        self, client, published_dataset, unpublished_dataset
    ):
        sample = RockSampleFactory(dataset=published_dataset)
        ExampleMeasurementFactory(sample=sample, dataset=published_dataset)

        choices = self._page_filters(client, ExampleMeasurement)["dataset"].queryset

        assert published_dataset in choices
        assert unpublished_dataset not in choices

    def test_a_sample_listings_dataset_filter_offers_no_unpublished_dataset(
        self, client, published_dataset, unpublished_dataset
    ):
        """`CustomSample` specifically, and not one of the generated types: it
        supplies its own `filterset_class`, which is the documented tier of the
        configuration API where the factory never runs at all. Swapping it for a
        type whose filter set the factory builds would still pass and would stop
        covering the case this test exists for."""
        assert registry.get_for_model(CustomSample).filterset_class is not None
        CustomSampleFactory(dataset=published_dataset)

        choices = self._page_filters(client, CustomSample)["dataset"].queryset

        assert published_dataset in choices
        assert unpublished_dataset not in choices

    def test_a_published_but_private_dataset_is_still_offered(
        self, client, unpublished_dataset
    ):
        """The scoping tests publication and nothing else. A private dataset
        whose data is published contributes rows, so it stays in the choice list
        beside them (D3, FR-003)."""
        private = DatasetFactory(published=True, visibility=Visibility.PRIVATE)
        CustomSampleFactory(dataset=private)

        choices = self._page_filters(client, CustomSample)["dataset"].queryset

        assert private in choices
        assert unpublished_dataset not in choices

    def test_the_record_type_filter_is_left_alone(self, client, published_dataset):
        """The measurement mixin scopes `polymorphic_ctype` to the registered
        types. The publication pass reads each filter's own queryset, so a
        relation publication says nothing about comes through untouched."""
        sample = RockSampleFactory(dataset=published_dataset)
        ExampleMeasurementFactory(sample=sample, dataset=published_dataset)

        choices = self._page_filters(client, ExampleMeasurement)[
            "polymorphic_ctype"
        ].queryset

        expected = ContentType.objects.get_for_models(*registry.measurements).values()
        assert set(choices) == set(expected)


@pytest.mark.django_db
class TestSwitcher:
    """T048-T052, FR-042-047, US5 Acceptance Scenarios 1-6: every listing carries a
    control offering every registered type's listing, grouped under Samples and
    Measurements, marking the one currently being viewed, opening its destination
    unnarrowed regardless of the origin's search/filter state (D6), and omitting
    itself entirely where only one type is registered - a control offering only the
    page you are on is a no-op (FR-047)."""

    def _all_listing_urls(self):
        return {
            reverse(f"{registry.get_for_model(model).get_slug()}-list")
            for model in registry.samples + registry.measurements
        }

    def test_the_switcher_lists_every_registered_types_listing(self, client):
        assert len(registry.samples) > 1
        assert registry.measurements
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        listed_urls = {
            entry["url"]
            for entry in response.context["sample_listings"]
            + response.context["measurement_listings"]
        }
        assert listed_urls == self._all_listing_urls()

    def test_the_switcher_control_is_rendered_with_a_link_to_every_other_listing(
        self, client
    ):
        slug = registry.get_for_model(RockSample).get_slug()
        current_url = reverse(f"{slug}-list")

        response = client.get(current_url)

        content = response.content.decode()
        assert 'id="listing-switcher"' in content
        switcher = content.split('id="listing-switcher"', 1)[1]
        for url in self._all_listing_urls() - {current_url}:
            assert f'href="{url}"' in switcher

    def test_entries_are_grouped_under_samples_and_measurements(self, client):
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        sample_urls = {entry["url"] for entry in response.context["sample_listings"]}
        measurement_urls = {
            entry["url"] for entry in response.context["measurement_listings"]
        }
        expected_sample_urls = {
            reverse(f"{registry.get_for_model(model).get_slug()}-list")
            for model in registry.samples
        }
        expected_measurement_urls = {
            reverse(f"{registry.get_for_model(model).get_slug()}-list")
            for model in registry.measurements
        }
        assert sample_urls == expected_sample_urls
        assert measurement_urls == expected_measurement_urls

    def test_the_currently_viewed_listing_is_marked_current(self, client):
        slug = registry.get_for_model(RockSample).get_slug()
        current_url = reverse(f"{slug}-list")

        response = client.get(current_url)

        all_entries = (
            response.context["sample_listings"]
            + response.context["measurement_listings"]
        )
        current_entries = [entry for entry in all_entries if entry["is_current"]]
        other_entries = [entry for entry in all_entries if not entry["is_current"]]
        assert [entry["url"] for entry in current_entries] == [current_url]
        assert all(entry["url"] != current_url for entry in other_entries)

    def test_choosing_a_measurement_listing_from_a_searched_sample_listing_opens_it_unfiltered(
        self, client
    ):
        rock_slug = registry.get_for_model(RockSample).get_slug()
        measurement_slug = registry.get_for_model(ExampleMeasurement).get_slug()
        expected_url = reverse(f"{measurement_slug}-list")

        response = client.get(
            reverse(f"{rock_slug}-list"), {"q": "Basalt", "rock_type": "Granite"}
        )

        measurement_entry = next(
            entry
            for entry in response.context["measurement_listings"]
            if entry["url"] == expected_url
        )
        assert measurement_entry["url"] == expected_url
        assert "?" not in measurement_entry["url"]

    def test_with_exactly_one_registered_type_no_switcher_control_is_rendered(
        self, client, monkeypatch
    ):
        monkeypatch.setattr(
            type(registry), "samples", property(lambda self: [RockSample])
        )
        monkeypatch.setattr(type(registry), "measurements", property(lambda self: []))
        slug = registry.get_for_model(RockSample).get_slug()
        current_url = reverse(f"{slug}-list")

        response = client.get(current_url)

        assert response.context["sample_listings"] == [
            {
                "name": registry.get_for_model(RockSample).get_verbose_name_plural(),
                "url": current_url,
                "is_current": True,
            }
        ]
        assert response.context["measurement_listings"] == []
        assert 'id="listing-switcher"' not in response.content.decode()


@pytest.mark.django_db
class TestSwitcherIsInlineWithTheTitle:
    """T084: the switcher control sits in the page title bar, directly next to
    and inline with the page title, as a small button labelled "Switch" - not
    "Switch listing", and not appended in a row of its own below the title.
    The switcher's own render gate (FR-047) is untouched and covered by
    `TestSwitcher`."""

    def test_the_switcher_and_the_breadcrumb_trail_share_one_flex_row(self, client):
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        soup = BeautifulSoup(response.content, "html.parser")
        switcher = soup.find(id="listing-switcher")
        breadcrumbs = soup.find("nav", class_="breadcrumbs")
        assert switcher is not None
        assert breadcrumbs is not None
        assert switcher.parent is breadcrumbs.parent
        # The shell's own title wrapper is itself a flex container (stacked
        # column, for the subtitle beneath it) - a bare "flex" check would
        # pass against that ancestor by coincidence. Row alignment is what
        # this task actually asks for, so pin the direction too.
        classes = switcher.parent.get("class", [])
        assert "flex" in classes
        assert "flex-col" not in classes
        assert "items-center" in classes

    def test_the_switcher_button_is_small_and_labelled_switch(self, client):
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        soup = BeautifulSoup(response.content, "html.parser")
        switcher = soup.find(id="listing-switcher")
        trigger = switcher.find("button")
        assert trigger is not None
        assert trigger.get_text(strip=True) == "Switch"
        assert "btn-sm" in trigger.get("class", [])
        assert "Switch listing" not in soup.get_text()


@pytest.mark.django_db
class TestNothingUnreachable:
    """T074, FR-052, SC-009, Acceptance Scenarios 1-2: deletions alone cannot
    demonstrate an absence, and the suite T061 runs cannot detect an unreached
    module. The reachability graph below is walked fresh from the real entry
    points Django itself uses - `INSTALLED_APPS` for `apps.py`, the resolved
    root URLconf for `urls.py` - plus any plain Python import, inside the
    package or from the rest of the repository, so a module nothing reaches
    any more fails here rather than sitting unused until the next reader
    notices it."""

    PACKAGE_DIR = Path(collections_pkg.__file__).parent
    PACKAGE_MODULE = "fairdm.contrib.collections"
    REPO_ROOT = Path(collections_pkg.__file__).resolve().parents[3]

    def _dotted_name(self, path):
        rel = path.relative_to(self.PACKAGE_DIR).with_suffix("")
        return ".".join([self.PACKAGE_MODULE, *rel.parts])

    def _package_modules(self):
        """Every `.py` file in the package with real content - `__init__.py`
        excluded, since a package marker has no reachability question of its
        own."""
        return {
            self._dotted_name(path): path
            for path in sorted(self.PACKAGE_DIR.rglob("*.py"))
            if path.name != "__init__.py" and "__pycache__" not in path.parts
        }

    def _own_package(self, path):
        rel_parent = path.relative_to(self.PACKAGE_DIR).parent.parts
        return ".".join([self.PACKAGE_MODULE, *rel_parent]).rstrip(".")

    def _package_imports(self, path):
        """The `fairdm.contrib.collections.*` dotted module names one file
        imports, resolving both absolute imports and, for a file inside the
        package, relative ones (`from .views import X`)."""
        is_internal = self.PACKAGE_DIR in path.parents
        own_package = self._own_package(path) if is_internal else None
        found = set()
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.level:
                    if not is_internal:
                        continue
                    target = f"{own_package}.{node.module}"
                else:
                    target = node.module
                if target == self.PACKAGE_MODULE or target.startswith(
                    f"{self.PACKAGE_MODULE}."
                ):
                    found.add(target)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == self.PACKAGE_MODULE or alias.name.startswith(
                        f"{self.PACKAGE_MODULE}."
                    ):
                        found.add(alias.name)
        return found

    def _external_importers(self):
        """Every module this package exposes that a `.py` file elsewhere in
        `fairdm/` or `fairdm_demo/` production code imports directly - an
        import in `registry/factories.py` counts as a real entry point exactly
        as much as a route does."""
        found = set()
        for top in ("fairdm", "fairdm_demo"):
            for path in (self.REPO_ROOT / top).rglob("*.py"):
                if self.PACKAGE_DIR in path.parents:
                    continue
                if "__pycache__" in path.parts or "migrations" in path.parts:
                    continue
                found |= self._package_imports(path)
        return found

    def test_every_remaining_module_is_reached_from_a_real_entry_point(self):
        modules = self._package_modules()

        assert self.PACKAGE_MODULE in settings.INSTALLED_APPS, (
            "apps.py's own entry point, INSTALLED_APPS, no longer names this "
            "package - the reachability graph below would be built on a false "
            "premise"
        )
        root_urlconf_source = Path(
            importlib.import_module(settings.ROOT_URLCONF).__file__
        ).read_text()
        assert f"{self.PACKAGE_MODULE}.urls" in root_urlconf_source, (
            "urls.py's own entry point, the resolved ROOT_URLCONF, no longer "
            "includes it - the reachability graph below would be built on a "
            "false premise"
        )

        reachable = {
            f"{self.PACKAGE_MODULE}.apps",
            f"{self.PACKAGE_MODULE}.urls",
        } | self._external_importers()
        reachable &= modules.keys()

        frontier = set(reachable)
        while frontier:
            next_frontier = set()
            for dotted in frontier:
                for imported in self._package_imports(modules[dotted]):
                    if imported in modules and imported not in reachable:
                        reachable.add(imported)
                        next_frontier.add(imported)
            frontier = next_frontier

        unreached = modules.keys() - reachable
        assert not unreached, (
            "unreachable modules remain in fairdm/contrib/collections/: "
            f"{sorted(unreached)}"
        )

    def test_a_listing_response_offers_no_download_control_in_any_format(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert "export_choices" not in response.context
        assert not hasattr(response.context["view"], "export_formats")
        content = response.content.decode()
        for term in (".csv", ".xlsx", ".json", ".yaml", ".latex", ".ods", ".tsv"):
            assert term not in content
