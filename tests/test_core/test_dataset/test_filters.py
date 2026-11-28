"""Tests for ``DatasetFilter`` in ``fairdm.core.dataset.filters``."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from licensing.models import License

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.filters import DatasetFilter
from fairdm.core.dataset.models import Dataset, DatasetDate, DatasetDescription
from fairdm.core.project.models import ProjectDate
from fairdm.core.vocabularies import DESCRIPTION_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestLicenseFilter:
    def test_filter_by_license_exact_match(self):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")

        match = DatasetFactory(license=cc_by, project=None)
        DatasetFactory(license=cc0, project=None)

        # `DatasetFactory()` defaults to PRIVATE, which the default manager would
        # exclude before the filter runs, hence `all_objects` throughout.
        filterset = DatasetFilter(
            data={"license": cc_by.id}, queryset=Dataset.all_objects.all()
        )

        assert filterset.is_valid()
        assert list(filterset.qs) == [match]


@pytest.mark.django_db
class TestProjectFilter:
    def request_for(self, user=None):
        request = RequestFactory().get("/")
        request.user = user or AnonymousUser()
        return request

    def test_two_ticked_projects_narrow_the_list_to_the_datasets_of_either(self):
        project1, project2, project3 = (
            ProjectFactory(visibility=Visibility.PUBLIC) for _ in range(3)
        )
        wanted = [
            DatasetFactory(project=project1),
            DatasetFactory(project=project2),
        ]
        DatasetFactory(project=project3)

        filterset = DatasetFilter(
            data={"project": [project1.id, project2.id]},
            queryset=Dataset.all_objects.all(),
            request=self.request_for(),
        )

        assert filterset.is_valid(), filterset.errors
        assert set(filterset.qs) == set(wanted)

    def test_a_private_project_is_refused_even_to_a_member(self):
        member = UserFactory()
        private = ProjectFactory()
        ContributionFactory(
            content_object=private, contributor=member, level=ContributionLevel.EDIT
        )

        filterset = DatasetFilter(
            data={"project": [private.id]},
            queryset=Dataset.all_objects.all(),
            request=self.request_for(member),
        )

        assert not filterset.is_valid()
        assert "project" in filterset.errors


@pytest.mark.django_db
class TestCrossRelationshipFilters:
    def test_filter_by_description_type(self):
        matching = DatasetFactory(project=None)
        DatasetDescriptionFactory(
            related=matching, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )
        other = DatasetFactory(project=None)

        filterset = DatasetFilter(
            data={"description_type": f"{DESCRIPTION_TYPES}/abstract"},
            queryset=Dataset.all_objects.all(),
        )

        assert filterset.is_valid()
        assert matching in filterset.qs
        assert other not in filterset.qs


@pytest.mark.django_db
class TestTypeFilterChoices:
    def test_it_offers_the_collection_by_label_in_its_order(self):
        concepts = DatasetDescription.get_type_concepts()

        choices = list(DatasetFilter().form.fields["description_type"].choices)[1:]

        assert concepts
        assert choices == [(c.uri, c.display_label()) for c in concepts]

    def test_a_value_outside_the_collection_is_refused(self):
        filterset = DatasetFilter(
            data={"description_type": "ABSTRACT"}, queryset=Dataset.all_objects.all()
        )

        assert filterset.form.has_error("description_type", code="invalid_choice")

    def test_a_type_the_project_collection_holds_alone_is_not_offered(self):
        dataset_types = {c.uri for c in DatasetDate.get_type_concepts()}
        project_only = {c.uri for c in ProjectDate.get_type_concepts()} - dataset_types

        field = DatasetFilter().form.fields["date_type"]
        offered = {uri for uri, label in field.choices}

        assert project_only
        assert not project_only & offered
