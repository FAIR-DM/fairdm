"""Pages served without a plugin that was removed, opened through the test client."""

import pytest
from bs4 import BeautifulSoup
from django.template import Context, Template
from django.test import Client
from django.urls import NoReverseMatch

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution, Contributor
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.contrib.plugins.checks import is_overview
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
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

MODELS = {
    "project": Project,
    "dataset": Dataset,
    "sample": Sample,
    "measurement": Measurement,
    "person": Contributor,
    "organization": Contributor,
}


def removable():
    """Every plugin FairDM registers on a record type that has an overview page, as test parameters.

    Read from the registry when the tests are collected, so a plugin added later is covered
    without editing this file.
    """
    return [
        pytest.param(kind, mount.name, id=f"{kind}-{mount.name}")
        for kind, model in MODELS.items()
        for mount in plugins.registry.resolve(model)
        if not is_overview(mount)
    ]


def make_record(kind):
    """Create a record of one kind that every visitor may open."""
    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    if kind == "project":
        return ProjectFactory(visibility=Visibility.PUBLIC)
    if kind == "dataset":
        return dataset
    if kind == "sample":
        return RockSampleFactory(dataset=dataset)
    if kind == "measurement":
        sample = RockSampleFactory(dataset=dataset)
        return XRFMeasurementFactory(dataset=dataset, sample=sample)
    if kind == "person":
        return PersonFactory(is_active=True, is_claimed=True, password="testpass123")
    return OrganizationFactory()


def links_of(response):
    """Every address an anchor on the page leads to."""
    page = BeautifulSoup(response.content, "html.parser")
    return [anchor["href"] for anchor in page.select("a[href]")]


def assert_served_without(response, former):
    """The page was served and nothing on it leads to ``former`` or to no address at all."""
    assert response.status_code == 200
    links = links_of(response)
    assert not [href for href in links if href.startswith(former)]
    assert not [href for href in links if href.strip() in ("", "None")]


@pytest.fixture
def manager(db):
    """Someone who can manage every record."""
    client = Client()
    client.force_login(UserFactory(is_superuser=True, is_staff=True))
    return client


@pytest.mark.django_db
class TestARemovedPluginLeavesNoTraceOnTheOverview:
    @pytest.mark.parametrize(("kind", "name"), removable())
    def test_the_overview_is_served_to_a_visitor_and_to_a_manager_without_a_link_to_it(
        self, client, manager, plugin_sandbox, kind, name
    ):
        record = make_record(kind)
        former = plugin_reverse(record, name)

        with plugin_sandbox.declare():
            plugins.remove(MODELS[kind], name)

        for who in (client, manager):
            assert_served_without(who.get(record.get_absolute_url()), former)

    @pytest.mark.parametrize(("kind", "name"), removable())
    def test_the_former_address_answers_as_one_that_never_existed(
        self, client, manager, plugin_sandbox, kind, name
    ):
        record = make_record(kind)
        former = plugin_reverse(record, name)
        never = former.rstrip("/") + "-never-existed/"

        with plugin_sandbox.declare():
            plugins.remove(MODELS[kind], name)

        for who in (client, manager):
            assert who.get(former).status_code == who.get(never).status_code == 404


@pytest.mark.django_db
class TestTheNameOfARemovedPluginDoesNotResolve:
    @pytest.fixture
    def removed(self, plugin_sandbox):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        with plugin_sandbox.declare():
            plugins.remove(Project, "dataset-list")
        return project

    def test_reversing_it_raises(self, removed):
        with pytest.raises(NoReverseMatch):
            plugin_reverse(removed, "dataset-list")

    def test_reversing_it_with_a_default_returns_the_default(self, removed):
        assert plugin_reverse(removed, "dataset-list", default="") == ""
        assert plugin_reverse(removed, "dataset-list", default=None) is None

    def test_a_name_that_resolves_ignores_the_default(self, removed):
        assert plugin_reverse(removed, "contribution-list", default="")

    @pytest.mark.parametrize("library", ["plugin_tags", "fairdm"])
    def test_the_template_tag_gives_an_empty_string(self, removed, library):
        template = Template("{% load " + library + " %}[{% plugin_url 'dataset-list' %}]")

        assert template.render(Context({"object": removed})) == "[]"

    @pytest.mark.parametrize("library", ["plugin_tags", "fairdm"])
    def test_the_template_tag_still_gives_the_address_of_one_that_is_there(
        self, removed, library
    ):
        template = Template(
            "{% load " + library + " %}{% plugin_url 'contribution-list' %}"
        )

        assert template.render(Context({"object": removed})) == plugin_reverse(
            removed, "contribution-list"
        )


@pytest.mark.django_db
class TestPagesThatLinkToTheRecordAbove:
    def test_a_dataset_s_contributors_page_is_served_without_the_projects(
        self, client, manager, plugin_sandbox
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        ContributionFactory(
            content_object=project,
            contributor=PersonFactory(),
            level=ContributionLevel.VIEW,
        )
        above = plugin_reverse(project, "contribution-list")
        page = plugin_reverse(dataset, "contribution-list")
        assert above in links_of(manager.get(page))

        with plugin_sandbox.declare():
            plugins.remove(Project, "contribution-list")

        for who in (client, manager):
            assert_served_without(who.get(page), above)

    def test_a_sample_s_contributors_page_is_served_without_the_datasets(
        self, client, manager, plugin_sandbox
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = RockSampleFactory(dataset=dataset)
        ContributionFactory(
            content_object=dataset,
            contributor=PersonFactory(),
            level=ContributionLevel.VIEW,
        )
        above = plugin_reverse(dataset, "contribution-list")
        page = plugin_reverse(sample, "contribution-list")
        assert above in links_of(manager.get(page))

        with plugin_sandbox.declare():
            plugins.remove(Dataset, "contribution-list")

        for who in (client, manager):
            assert_served_without(who.get(page), above)


@pytest.mark.django_db
class TestRemovingTouchesNothingStored:
    def test_the_credits_a_removed_plugin_managed_are_still_there(self, plugin_sandbox):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        credit = ContributionFactory(content_object=project)

        with plugin_sandbox.declare():
            plugins.remove(Project, "contribution-list")

        assert Contribution.objects.filter(pk=credit.pk).exists()
        assert project.contributors.count() == 1
