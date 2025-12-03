"""Tests for contributor plugins."""

import pytest

from fairdm import plugins
from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.contributors.plugins import (
    ContributorOverview,
    ContributorProfile,
    ContributorsPlugin,
    DatasetContributors,
    MeasurementContributors,
    OrganizationOverview,
    OrganizationProfile,
    PersonOverview,
    PersonProfile,
    ProjectContributors,
    SampleContributors,
)
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.factories.contributors import (
    ContributionFactory,
    OrganizationFactory,
    PersonFactory,
)
from fairdm.factories.core import DatasetFactory, ProjectFactory


@pytest.mark.django_db
class TestPluginRegistration:
    """Test that plugins are properly registered to their models."""

    def test_person_overview_registered(self):
        """Test PersonOverview plugin is registered to Person model."""
        view_class = plugins.registry.get_view_for_model(Person)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "PersonOverview" in plugin_names

    def test_person_profile_registered(self):
        """Test PersonProfile plugin is registered to Person model."""
        view_class = plugins.registry.get_view_for_model(Person)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "PersonProfile" in plugin_names

    def test_organization_overview_registered(self):
        """Test OrganizationOverview plugin is registered to Organization model."""
        view_class = plugins.registry.get_view_for_model(Organization)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "OrganizationOverview" in plugin_names

    def test_organization_profile_registered(self):
        """Test OrganizationProfile plugin is registered to Organization model."""
        view_class = plugins.registry.get_view_for_model(Organization)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "OrganizationProfile" in plugin_names

    def test_project_contributors_registered(self):
        """Test ProjectContributors plugin is registered to Project model."""
        view_class = plugins.registry.get_view_for_model(Project)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "ProjectContributors" in plugin_names

    def test_dataset_contributors_registered(self):
        """Test DatasetContributors plugin is registered to Dataset model."""
        view_class = plugins.registry.get_view_for_model(Dataset)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "DatasetContributors" in plugin_names

    def test_sample_contributors_registered(self):
        """Test SampleContributors plugin is registered to Sample model."""
        view_class = plugins.registry.get_view_for_model(Sample)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "SampleContributors" in plugin_names

    def test_measurement_contributors_registered(self):
        """Test MeasurementContributors plugin is registered to Measurement model."""
        view_class = plugins.registry.get_view_for_model(Measurement)
        assert view_class is not None
        plugin_names = [p.__name__ for p in view_class.plugins]
        assert "MeasurementContributors" in plugin_names


@pytest.mark.django_db
class TestPluginInheritance:
    """Test that plugin inheritance structure works correctly."""

    def test_person_overview_inherits_contributor_overview(self):
        """Test PersonOverview inherits from ContributorOverview."""
        assert issubclass(PersonOverview, ContributorOverview)

    def test_organization_overview_inherits_contributor_overview(self):
        """Test OrganizationOverview inherits from ContributorOverview."""
        assert issubclass(OrganizationOverview, ContributorOverview)

    def test_person_profile_inherits_contributor_profile(self):
        """Test PersonProfile inherits from ContributorProfile."""
        assert issubclass(PersonProfile, ContributorProfile)

    def test_organization_profile_inherits_contributor_profile(self):
        """Test OrganizationProfile inherits from ContributorProfile."""
        assert issubclass(OrganizationProfile, ContributorProfile)

    def test_all_contributors_plugins_inherit_base(self):
        """Test all Contributors plugins inherit from ContributorsPlugin."""
        assert issubclass(ProjectContributors, ContributorsPlugin)
        assert issubclass(DatasetContributors, ContributorsPlugin)
        assert issubclass(SampleContributors, ContributorsPlugin)
        assert issubclass(MeasurementContributors, ContributorsPlugin)


@pytest.mark.django_db
class TestContributorOverviewPlugin:
    """Test ContributorOverview plugin functionality."""

    def test_get_contribution_counts_person(self):
        """Test contribution counts are calculated correctly for Person."""
        person = PersonFactory()
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        dataset = DatasetFactory()

        ContributionFactory(contributor=person, content_object=project1)
        ContributionFactory(contributor=person, content_object=project2)
        ContributionFactory(contributor=person, content_object=dataset)

        # Create plugin instance
        plugin = PersonOverview()
        plugin.base_object = person

        counts = plugin.get_contribution_counts()

        assert "Projects" in counts
        assert counts["Projects"] == 2
        assert "Datasets" in counts
        assert counts["Datasets"] == 1

    def test_get_contribution_counts_organization(self):
        """Test contribution counts are calculated correctly for Organization."""
        org = OrganizationFactory()
        project = ProjectFactory()

        ContributionFactory(contributor=org, content_object=project)

        # Create plugin instance
        plugin = OrganizationOverview()
        plugin.base_object = org

        counts = plugin.get_contribution_counts()

        assert "Projects" in counts
        assert counts["Projects"] == 1


@pytest.mark.django_db
class TestContributorsPlugin:
    """Test ContributorsPlugin functionality."""

    def test_get_queryset_filters_person_only(self):
        """Test that get_queryset returns only Person contributors."""
        project = ProjectFactory()
        person = PersonFactory()
        org = OrganizationFactory()

        # Add both person and organization contributions
        person_contribution = ContributionFactory(contributor=person, content_object=project)
        ContributionFactory(contributor=org, content_object=project)  # org contribution (filtered out)

        # Create plugin instance
        plugin = ProjectContributors()
        plugin.base_object = project

        queryset = plugin.get_queryset()

        # Should only return person contribution
        assert queryset.count() == 1
        assert queryset.first() == person_contribution

    def test_contributors_plugin_has_correct_attributes(self):
        """Test ContributorsPlugin has required attributes."""
        assert ContributorsPlugin.name == "contributors"
        assert ContributorsPlugin.title == "Contributors"
        assert ContributorsPlugin.menu_item is not None
        assert "contributor__name" in ContributorsPlugin.filterset_fields


@pytest.mark.django_db
class TestPluginDocstrings:
    """Test that all plugin classes have proper documentation."""

    def test_contributor_overview_has_docstring(self):
        """Test ContributorOverview has a docstring."""
        assert ContributorOverview.__doc__ is not None
        assert len(ContributorOverview.__doc__.strip()) > 0

    def test_contributor_profile_has_docstring(self):
        """Test ContributorProfile has a docstring."""
        assert ContributorProfile.__doc__ is not None
        assert len(ContributorProfile.__doc__.strip()) > 0

    def test_contributors_plugin_has_docstring(self):
        """Test ContributorsPlugin has a docstring."""
        assert ContributorsPlugin.__doc__ is not None
        assert len(ContributorsPlugin.__doc__.strip()) > 0
