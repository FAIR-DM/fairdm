"""Tests for ``DatasetFilter`` in ``fairdm.core.dataset.filters``."""

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from licensing.models import License

from fairdm.core.dataset.filters import DatasetFilter
from fairdm.core.dataset.models import Dataset
from fairdm.factories import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    ProjectFactory,
)

User = get_user_model()


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
    def test_filter_by_project(self):
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        ds1 = DatasetFactory(project=project1)
        ds2 = DatasetFactory(project=project1)
        DatasetFactory(project=project2)

        filterset = DatasetFilter(
            data={"project": project1.id}, queryset=Dataset.all_objects.all()
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert ds1 in filterset.qs
        assert ds2 in filterset.qs

    def test_filter_by_null_project(self):
        DatasetFactory(project=None)
        DatasetFactory(project=ProjectFactory())

        filterset = DatasetFilter(data={"project": ""}, queryset=Dataset.objects.all())

        assert filterset.is_valid()


@pytest.mark.django_db
class TestCrossRelationshipFilters:
    def test_filter_by_description_type(self):
        matching = DatasetFactory()
        DatasetDescriptionFactory(related=matching, type="Abstract")
        other = DatasetFactory()

        filterset = DatasetFilter(
            data={"description_type": "Abstract"}, queryset=Dataset.all_objects.all()
        )

        assert filterset.is_valid()
        assert matching in filterset.qs
        assert other not in filterset.qs

    def test_filter_by_date_type(self):
        matching = DatasetFactory()
        DatasetDateFactory(related=matching, type="Available")
        other = DatasetFactory()

        filterset = DatasetFilter(
            data={"date_type": "Available"}, queryset=Dataset.all_objects.all()
        )

        assert filterset.is_valid()
        assert matching in filterset.qs
        assert other not in filterset.qs


@pytest.mark.django_db
class TestMultipleFilterCombinations:
    def test_combine_license_and_project(self):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        ds_match = DatasetFactory(license=cc_by, project=project1)
        DatasetFactory(license=cc_by, project=project2)
        DatasetFactory(license=cc0, project=project1)

        filterset = DatasetFilter(
            data={"license": cc_by.id, "project": project1.id},
            queryset=Dataset.all_objects.all(),
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_match in filterset.qs

    def test_combine_all_filters(self):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        project = ProjectFactory()
        other_project = ProjectFactory()

        ds_match = DatasetFactory(license=cc_by, project=project)
        DatasetDescriptionFactory(related=ds_match, type="Abstract")

        wrong_project = DatasetFactory(license=cc_by, project=other_project)
        DatasetDescriptionFactory(related=wrong_project, type="Abstract")
        wrong_license = DatasetFactory(license=cc0, project=project)
        DatasetDescriptionFactory(related=wrong_license, type="Abstract")
        wrong_type = DatasetFactory(license=cc_by, project=project)
        DatasetDescriptionFactory(related=wrong_type, type="Methods")

        filterset = DatasetFilter(
            data={
                "license": cc_by.id,
                "project": project.id,
                "description_type": "Abstract",
            },
            queryset=Dataset.all_objects.all(),
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_match in filterset.qs


@pytest.mark.django_db
class TestFilterPerformance:
    def test_cross_relationship_filter_query_count(self, django_assert_num_queries):
        def count_matches():
            filterset = DatasetFilter(
                data={"description_type": "Abstract"},
                queryset=Dataset.all_objects.all(),
            )
            return filterset.qs.count()

        DatasetDescriptionFactory(related=DatasetFactory(), type="Abstract")
        with CaptureQueriesContext(connection) as one_record:
            assert count_matches() == 1

        for _ in range(24):
            DatasetDescriptionFactory(related=DatasetFactory(), type="Abstract")
        for _ in range(25):
            DatasetDescriptionFactory(related=DatasetFactory(), type="Methods")

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
        project = ProjectFactory()

        filterset = DatasetFilter(
            data={
                "license": license_obj.id,
                "project": project.id,
            },
            queryset=Dataset.objects.all(),
        )

        assert filterset.is_valid()
