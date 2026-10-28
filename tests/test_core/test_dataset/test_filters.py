"""Tests for ``DatasetFilter`` in ``fairdm.core.dataset.filters``."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from licensing.models import License

from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.filters import DatasetFilter
from fairdm.core.dataset.models import Dataset
from fairdm.core.vocabularies import DATE_TYPES, DESCRIPTION_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

User = get_user_model()


def _anonymous_request():
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return request


@pytest.mark.django_db
class TestLicenseFilter:
    def test_filter_by_license_exact_match(self):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")

        ds1 = DatasetFactory(license=cc_by)
        ds2 = DatasetFactory(license=cc_by)
        DatasetFactory(license=cc0)

        # `DatasetFactory()` defaults to PRIVATE, which the default manager would
        # exclude before the filter runs, hence `all_objects` throughout.
        filterset = DatasetFilter(
            data={"license": cc_by.id}, queryset=Dataset.all_objects.all()
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert ds1 in filterset.qs
        assert ds2 in filterset.qs

    def test_filter_without_license_shows_all(self):
        DatasetFactory.create_batch(3)

        filterset = DatasetFilter(data={}, queryset=Dataset.all_objects.all())

        assert filterset.is_valid()
        assert filterset.qs.count() == 3


@pytest.mark.django_db
class TestProjectFilter:
    def request_for(self, user=None):
        request = RequestFactory().get("/")
        request.user = user or AnonymousUser()
        return request

    @pytest.fixture
    def public_projects(self):
        return [ProjectFactory(visibility=Visibility.PUBLIC) for _ in range(3)]

    def test_the_project_filter_is_a_record_filter_at_public_scope(self):
        project_filter = DatasetFilter().filters["project"]

        assert isinstance(project_filter, RecordMultipleFilter)
        assert project_filter.field.scope == "public"

    def test_filter_by_project(self, public_projects):
        project1, project2, _ = public_projects

        ds1 = DatasetFactory(project=project1)
        ds2 = DatasetFactory(project=project1)
        DatasetFactory(project=project2)

        filterset = DatasetFilter(
            data={"project": [project1.id]},
            queryset=Dataset.all_objects.all(),
            request=self.request_for(),
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert ds1 in filterset.qs
        assert ds2 in filterset.qs

    def test_two_ticked_projects_narrow_the_list_to_the_datasets_of_either(
        self, public_projects
    ):
        project1, project2, project3 = public_projects
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

    def test_filter_by_null_project(self):
        DatasetFactory(project=None)
        DatasetFactory(project=ProjectFactory())

        filterset = DatasetFilter(data={"project": ""}, queryset=Dataset.objects.all())

        assert filterset.is_valid()


@pytest.mark.django_db
class TestCrossRelationshipFilters:
    def test_filter_by_description_type(self):
        matching = DatasetFactory()
        DatasetDescriptionFactory(
            related=matching, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )
        other = DatasetFactory()

        filterset = DatasetFilter(
            data={"description_type": f"{DESCRIPTION_TYPES}/abstract"},
            queryset=Dataset.all_objects.all(),
        )

        assert filterset.is_valid()
        assert matching in filterset.qs
        assert other not in filterset.qs

    def test_filter_by_date_type(self):
        matching = DatasetFactory()
        DatasetDateFactory(related=matching, type_id=f"{DATE_TYPES}/available")
        other = DatasetFactory()

        filterset = DatasetFilter(
            data={"date_type": f"{DATE_TYPES}/available"},
            queryset=Dataset.all_objects.all(),
        )

        assert filterset.is_valid()
        assert matching in filterset.qs
        assert other not in filterset.qs


@pytest.mark.django_db
class TestMultipleFilterCombinations:
    def test_combine_license_and_project(self):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        project1 = ProjectFactory(visibility=Visibility.PUBLIC)
        project2 = ProjectFactory(visibility=Visibility.PUBLIC)

        ds_match = DatasetFactory(license=cc_by, project=project1)
        DatasetFactory(license=cc_by, project=project2)
        DatasetFactory(license=cc0, project=project1)

        filterset = DatasetFilter(
            data={"license": cc_by.id, "project": [project1.id]},
            queryset=Dataset.all_objects.all(),
            request=_anonymous_request(),
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_match in filterset.qs

    def test_combine_all_filters(self):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        other_project = ProjectFactory(visibility=Visibility.PUBLIC)

        ds_match = DatasetFactory(license=cc_by, project=project)
        DatasetDescriptionFactory(
            related=ds_match, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )

        wrong_project = DatasetFactory(license=cc_by, project=other_project)
        DatasetDescriptionFactory(
            related=wrong_project, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )
        wrong_license = DatasetFactory(license=cc0, project=project)
        DatasetDescriptionFactory(
            related=wrong_license, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )
        wrong_type = DatasetFactory(license=cc_by, project=project)
        DatasetDescriptionFactory(
            related=wrong_type, type_id=f"{DESCRIPTION_TYPES}/methods"
        )

        filterset = DatasetFilter(
            data={
                "license": cc_by.id,
                "project": [project.id],
                "description_type": f"{DESCRIPTION_TYPES}/abstract",
            },
            queryset=Dataset.all_objects.all(),
            request=_anonymous_request(),
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_match in filterset.qs


@pytest.mark.django_db
class TestFilterPerformance:
    def test_cross_relationship_filter_query_count(self, django_assert_num_queries):
        def count_matches():
            filterset = DatasetFilter(
                data={"description_type": f"{DESCRIPTION_TYPES}/abstract"},
                queryset=Dataset.all_objects.all(),
            )
            return filterset.qs.count()

        DatasetDescriptionFactory(
            related=DatasetFactory(), type_id=f"{DESCRIPTION_TYPES}/abstract"
        )
        with CaptureQueriesContext(connection) as one_record:
            assert count_matches() == 1

        for _ in range(24):
            DatasetDescriptionFactory(
                related=DatasetFactory(), type_id=f"{DESCRIPTION_TYPES}/abstract"
            )
        for _ in range(25):
            DatasetDescriptionFactory(
                related=DatasetFactory(), type_id=f"{DESCRIPTION_TYPES}/methods"
            )

        with django_assert_num_queries(len(one_record)):
            assert count_matches() == 25


@pytest.mark.django_db
class TestFilterFormRendering:
    def test_filter_form_has_all_fields(self):
        filterset = DatasetFilter(queryset=Dataset.objects.all())

        expected_fields = [
            "license",
            "project",
            "description_type",
            "date_type",
        ]
        for field_name in expected_fields:
            assert field_name in filterset.form.fields, f"Missing field: {field_name}"

    def test_filter_form_renders_without_errors(self):
        filterset = DatasetFilter(queryset=Dataset.objects.all())

        form_html = str(filterset.form)
        assert form_html
        assert "license" in form_html
        assert "project" in form_html

    def test_filter_form_with_data_is_valid(self):
        license_obj = License.objects.first()
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        filterset = DatasetFilter(
            data={
                "license": license_obj.id,
                "project": [project.id],
            },
            queryset=Dataset.objects.all(),
            request=request,
        )

        assert filterset.is_valid()
