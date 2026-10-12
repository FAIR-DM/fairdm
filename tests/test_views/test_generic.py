"""Tests for the portal home page in ``fairdm/views/generic.py``."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from demo.factories import RockSampleFactory, SoilSampleFactory, WaterSampleFactory
from demo.models import RockSample, SoilSample, WaterSample
from fairdm.contrib.identity.models import Identity
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from fairdm.views.generic import FairDMHomeView

pytestmark = pytest.mark.django_db

view = FairDMHomeView()


def limited(**limits):
    """Build a home view with some of its limits changed, as a portal's subclass would."""
    return type("LimitedHomeView", (FairDMHomeView,), limits)()


def public_dataset(**kwargs):
    """Build a public dataset in a public project."""
    project = ProjectFactory(visibility=Visibility.PUBLIC)
    return DatasetFactory(project=project, visibility=Visibility.PUBLIC, **kwargs)


class TestFairDMHomeView:
    def test_a_visitor_gets_the_landing_page(self, client):
        response = client.get(reverse("home"))

        assert response.status_code == 200
        assert "fairdm/landing.html" in [t.name for t in response.templates]

    def test_a_signed_in_user_gets_the_dashboard(self, authenticated_client):
        response = authenticated_client.get(reverse("home"))

        assert "fairdm/dashboard.html" in [t.name for t in response.templates]
        assert "latest_datasets" not in response.context

    def test_a_public_dataset_is_shown_and_links_to_its_page(self, client):
        dataset = public_dataset(name="Kaiserstuhl cores")

        content = client.get(reverse("home")).content.decode()

        assert "Kaiserstuhl cores" in content
        assert dataset.get_absolute_url() in content

    def test_a_private_dataset_is_not_shown(self, client):
        DatasetFactory(name="Embargoed cores", visibility=Visibility.PRIVATE)

        content = client.get(reverse("home")).content.decode()

        assert "Embargoed cores" not in content

    def test_a_public_project_is_shown(self, client):
        ProjectFactory(name="Graben survey", visibility=Visibility.PUBLIC)

        content = client.get(reverse("home")).content.decode()

        assert "Graben survey" in content

    def test_sections_with_nothing_to_show_are_left_out(self, client):
        content = client.get(reverse("home")).content.decode()

        for section in ("stats", "datasets", "projects"):
            assert f'id="landing-{section}"' not in content
        assert 'id="landing-hero"' in content

    def test_the_hero_carries_the_configured_title(self, client, settings):
        settings.SITE_NAME = "Rhine Portal"
        settings.HOME_PAGE_CONFIG = {"title": "Data from {site_name}"}

        content = client.get(reverse("home")).content.decode()

        assert "Data from Rhine Portal" in content

    def test_account_creation_is_offered_while_registration_is_open(
        self, client, settings
    ):
        settings.ACCOUNT_ALLOW_REGISTRATION = True

        content = client.get(reverse("home")).content.decode()

        assert reverse("account_signup") in content

    def test_account_creation_is_not_offered_when_registration_is_closed(
        self, client, settings
    ):
        settings.ACCOUNT_ALLOW_REGISTRATION = False

        content = client.get(reverse("home")).content.decode()

        assert reverse("account_signup") not in content

    def test_the_page_costs_no_more_queries_as_datasets_are_added(self, client):
        public_dataset()
        # The first request fills caches a later one reads, so it is not the one to compare.
        client.get(reverse("home"))
        with CaptureQueriesContext(connection) as one:
            client.get(reverse("home"))
        public_dataset()
        public_dataset()

        with CaptureQueriesContext(connection) as three:
            client.get(reverse("home"))

        assert len(three) == len(one)

    def test_the_page_costs_no_more_queries_as_projects_are_added(self, client):
        ProjectFactory(visibility=Visibility.PUBLIC)
        client.get(reverse("home"))
        with CaptureQueriesContext(connection) as one:
            client.get(reverse("home"))
        ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectFactory(visibility=Visibility.PUBLIC)

        with CaptureQueriesContext(connection) as three:
            client.get(reverse("home"))

        assert len(three) == len(one)

    def test_the_page_costs_no_more_queries_as_people_are_added(self, client):
        PersonFactory()
        client.get(reverse("home"))
        with CaptureQueriesContext(connection) as one:
            client.get(reverse("home"))
        PersonFactory()
        PersonFactory()

        with CaptureQueriesContext(connection) as three:
            client.get(reverse("home"))

        assert len(three) == len(one)

    def test_a_portal_template_adds_a_section_through_a_block(self, client):
        # The demo portal, installed in the test settings, extends the page with a notice.
        content = client.get(reverse("home")).content.decode()

        assert 'id="landing-demo"' in content


class TestFairDMHomeViewHero:
    def test_the_placeholder_is_filled_with_the_site_name(self, settings):
        settings.SITE_NAME = "Rhine Portal"
        settings.HOME_PAGE_CONFIG = {"title": "Welcome to {site_name}"}

        assert view.get_hero()["title"] == "Welcome to Rhine Portal"

    def test_the_saved_portal_name_replaces_the_site_name(self, settings):
        settings.SITE_NAME = "Rhine Portal"
        settings.HOME_PAGE_CONFIG = {"title": "{site_name}"}
        identity = Identity.get_solo()
        identity.set_current_language("en")
        identity.name = "Upper Rhine Data"
        identity.description = "About it."
        identity.save()

        assert view.get_hero()["title"] == "Upper Rhine Data"

    def test_false_hides_a_line(self, settings):
        settings.HOME_PAGE_CONFIG = {"lead": False, "eyebrow": False}

        content = view.get_hero()

        assert content["lead"] == ""
        assert content["eyebrow"] == ""

    def test_a_key_left_out_keeps_its_default(self, settings):
        settings.HOME_PAGE_CONFIG = {"title": "Only a title"}

        assert view.get_hero()["lead"]

    def test_a_static_path_becomes_a_static_address(self, settings):
        settings.HOME_PAGE_CONFIG = {"image": "portal/hero.jpg"}

        assert view.get_hero()["image"] == f"{settings.STATIC_URL}portal/hero.jpg"

    def test_a_full_address_is_left_as_given(self, settings):
        settings.HOME_PAGE_CONFIG = {"image": "https://example.org/hero.jpg"}

        assert view.get_hero()["image"] == "https://example.org/hero.jpg"

    def test_no_picture_is_the_default(self, settings):
        settings.HOME_PAGE_CONFIG = {}

        assert view.get_hero()["image"] == ""


class TestFairDMHomeViewAbout:
    def test_the_setting_describes_a_portal_with_no_saved_description(self, settings):
        settings.PORTAL_DESCRIPTION = "From the settings."

        assert view.get_about()["description"] == "From the settings."

    def test_the_saved_description_wins(self, settings):
        settings.PORTAL_DESCRIPTION = "From the settings."
        identity = Identity.get_solo()
        identity.set_current_language("en")
        identity.name = "Portal"
        identity.description = "From the administration."
        identity.save()

        assert view.get_about()["description"] == "From the administration."


class TestFairDMHomeViewCounts:
    def figures(self):
        return {str(figure["title"]): figure["value"] for figure in view.get_counts()}

    def test_an_empty_portal_has_no_figures(self):
        assert view.get_counts() == []

    def test_a_private_dataset_is_not_counted(self):
        public_dataset()
        DatasetFactory(visibility=Visibility.PRIVATE)

        assert self.figures()["Datasets"] == 1

    def test_samples_are_counted_only_in_public_published_datasets(self):
        RockSampleFactory(dataset=public_dataset(published=True))
        RockSampleFactory(dataset=public_dataset(published=False))
        RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PRIVATE, published=True)
        )

        assert self.figures()["Samples"] == 1

    def test_a_superuser_is_not_counted_among_the_people(self):
        PersonFactory()
        UserFactory(is_superuser=True)

        assert self.figures()["People"] == 1


class TestFairDMHomeViewLatestDatasets:
    def test_private_datasets_are_left_out(self):
        shown = public_dataset()
        DatasetFactory(visibility=Visibility.PRIVATE)

        assert list(view.get_latest_datasets()) == [shown]

    def test_a_public_dataset_in_a_private_project_is_left_out(self):
        DatasetFactory(
            project=ProjectFactory(visibility=Visibility.PRIVATE),
            visibility=Visibility.PUBLIC,
        )

        assert list(view.get_latest_datasets()) == []

    def test_the_most_recently_changed_come_first_up_to_the_limit(self):
        first, second, third = public_dataset(), public_dataset(), public_dataset()
        first.save()

        assert list(limited(latest_limit=2).get_latest_datasets()) == [first, third]


class TestFairDMHomeViewLatestProjects:
    def test_private_projects_are_left_out(self):
        shown = ProjectFactory(visibility=Visibility.PUBLIC)
        ProjectFactory(visibility=Visibility.PRIVATE)

        assert list(view.get_latest_projects()) == [shown]

    def test_the_newest_come_first_up_to_the_limit(self):
        ProjectFactory(visibility=Visibility.PUBLIC)
        second = ProjectFactory(visibility=Visibility.PUBLIC)
        third = ProjectFactory(visibility=Visibility.PUBLIC)

        assert list(limited(latest_limit=2).get_latest_projects()) == [third, second]


class TestFairDMHomeViewRecordTypes:
    models = [RockSample, SoilSample, WaterSample]

    def test_each_type_carries_its_public_count_and_its_table(self):
        dataset = public_dataset(published=True)
        RockSampleFactory.create_batch(2, dataset=dataset)

        types = view.get_record_types(Sample, self.models)

        rock = next(kind for kind in types["shown"] if kind["url"] == reverse("rocksample-list"))
        assert rock["count"] == 2

    def test_records_a_visitor_may_not_open_are_not_counted(self):
        RockSampleFactory(dataset=public_dataset(published=False))

        types = view.get_record_types(Sample, self.models)

        assert [kind["count"] for kind in types["shown"]] == [0, 0, 0]

    def test_the_types_with_the_most_records_come_first(self):
        dataset = public_dataset(published=True)
        WaterSampleFactory.create_batch(3, dataset=dataset)
        SoilSampleFactory.create_batch(2, dataset=dataset)
        RockSampleFactory(dataset=dataset)

        types = view.get_record_types(Sample, self.models)

        assert [kind["count"] for kind in types["shown"]] == [3, 2, 1]

    def test_types_past_the_limit_are_counted_and_not_listed(self):
        types = limited(record_type_limit=2).get_record_types(Sample, self.models)

        assert len(types["shown"]) == 2
        assert types["more"] == 1

    def test_nothing_is_left_over_within_the_limit(self):
        types = view.get_record_types(Sample, self.models)

        assert types["more"] == 0


class TestFairDMHomeViewPeople:
    def test_the_most_credited_person_comes_first(self):
        quiet = PersonFactory()
        busy = PersonFactory()
        ContributionFactory.create_batch(2, contributor=busy)

        assert list(view.get_people())[:2] == [busy, quiet]

    def test_a_superuser_is_left_out(self):
        UserFactory(is_superuser=True)

        assert list(view.get_people()) == []


class TestFairDMHomeViewOrganizations:
    def test_the_most_credited_organization_comes_first(self):
        OrganizationFactory()
        busy = OrganizationFactory()
        ContributionFactory(contributor=busy)

        assert view.get_organizations()[0] == busy
