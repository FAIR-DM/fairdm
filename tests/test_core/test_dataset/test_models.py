"""Tests for the ``Dataset`` model, its querysets and its related-record models."""

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
    DatasetQuerySet,
)
from fairdm.core.vocabularies import (
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
)
from fairdm.factories import (
    DatasetFactory,
    DatasetIdentifierFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.factories.contributors import ContributionFactory
from fairdm.utils.choices import Visibility
from fairdm.utils.location.coverage import Coverage

# `DatasetFactory()` defaults to PRIVATE, so tests unrelated to visibility use
# `Dataset.all_objects`.


@pytest.mark.django_db
class TestDatasetVisibility:
    def test_reading_datasets_with_no_visibility_condition_returns_only_public(self):
        public = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(visibility=Visibility.PRIVATE)

        result = list(Dataset.objects.all())

        assert result == [public]

    def test_all_objects_returns_both_and_honours_a_condition_applied_to_it(self):
        project = ProjectFactory()
        public = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        private = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        elsewhere = DatasetFactory(visibility=Visibility.PUBLIC)

        everything = Dataset.all_objects.all()
        assert set(everything) == {public, private, elsewhere}

        narrowed = Dataset.all_objects.filter(project=project)
        assert set(narrowed) == {public, private}

    def test_no_queryset_method_widens_an_already_narrowed_query(self):
        DatasetFactory(visibility=Visibility.PRIVATE)
        DatasetFactory(visibility=Visibility.PUBLIC)

        own_methods = [
            name
            for name, value in vars(DatasetQuerySet).items()
            if not name.startswith("_") and callable(value)
        ]
        assert own_methods, "expected DatasetQuerySet to define at least one method"

        for name in own_methods:
            widened = list(getattr(Dataset.objects.all(), name)())
            assert not any(ds.visibility == Visibility.PRIVATE for ds in widened), (
                f"DatasetQuerySet.{name}() added a PRIVATE dataset back to "
                "an already-narrowed query"
            )

    def test_a_dataset_created_with_no_visibility_stated_reads_back_private(self):
        dataset = Dataset.objects.create(name="No visibility stated")

        assert Dataset.all_objects.get(pk=dataset.pk).visibility == (
            Visibility.PRIVATE.value
        )
        assert not Dataset.objects.filter(pk=dataset.pk).exists()


@pytest.mark.django_db
class TestDatasetDataIsPublic:
    @pytest.mark.parametrize(
        ("visibility", "published", "expected"),
        [
            (Visibility.PUBLIC, True, True),
            (Visibility.PUBLIC, False, False),
            (Visibility.PRIVATE, True, False),
            (Visibility.PRIVATE, False, False),
        ],
    )
    def test_data_is_public_only_when_the_dataset_is_public_and_published(
        self, visibility, published, expected
    ):
        dataset = DatasetFactory(visibility=visibility, published=published)

        assert dataset.data_is_public is expected


@pytest.mark.django_db
class TestDatasetVisibilityGuarantees:
    def test_following_a_relation_to_a_private_dataset_still_finds_it(self):
        # Forward FK access uses `_base_manager`, not the privacy-first default manager.
        private_dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        identifier = DatasetIdentifierFactory(related=private_dataset)

        fetched = DatasetIdentifier.objects.get(pk=identifier.pk).related

        assert fetched == private_dataset

    def test_permissions_a_visibility_check_could_consult_are_all_declared(self):
        import inspect
        import re

        from fairdm.core.dataset import admin as dataset_admin_module
        from fairdm.core.dataset import models as dataset_models_module
        from fairdm.core.dataset import plugins as dataset_plugins_module
        from fairdm.core.dataset import views as dataset_views_module

        declared = {codename for codename, _label in Dataset._meta.permissions}
        declared |= {
            f"{action}_{Dataset._meta.model_name}"
            for action in Dataset._meta.default_permissions
        }

        source = "".join(
            inspect.getsource(module)
            for module in (
                dataset_models_module,
                dataset_admin_module,
                dataset_views_module,
                dataset_plugins_module,
            )
        )
        referenced = {
            codename.rsplit(".", 1)[-1]
            for codename in re.findall(r'has_perm\(\s*["\']([\w.]+)["\']', source)
        }
        referenced |= {
            codename.rsplit(".", 1)[-1]
            for codename in re.findall(
                r'^\s*permission\s*=\s*["\']([\w.]+)["\']', source, re.MULTILINE
            )
        }

        # The permissions a dataset's pages ask for now sit in the editing pages' table.
        from fairdm.core.editing import RecordEditingPage

        referenced |= {
            permission.rsplit(".", 1)[-1]
            for table in RecordEditingPage.PERMISSIONS.values()
            for model, permission in table.items()
            if model is Dataset
        }

        # The scan is the guard, so an empty scan is a broken guard, not a pass:
        # `referenced <= declared` is trivially true of the empty set.
        assert referenced, (
            "no permission references found - the scan has stopped working"
        )
        assert referenced <= declared
        assert "view_private" not in declared


@pytest.mark.django_db
class TestDatasetLicence:
    def test_dataset_created_without_a_licence_gets_the_configured_default(self):
        from licensing.models import License

        dataset = Dataset.objects.create(
            name="No Licence Chosen", project=ProjectFactory()
        )

        default_name = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")
        assert dataset.license == License.objects.get(name=default_name)

    def test_a_portal_configured_default_licence_is_honoured(self):
        with override_settings(FAIRDM_DEFAULT_LICENSE="CC BY-SA 4.0"):
            dataset = Dataset.objects.create(
                name="Custom Default", project=ProjectFactory()
            )

        assert dataset.license.name == "CC BY-SA 4.0"


@pytest.mark.django_db
class TestDatasetHasData:
    def test_no_samples_or_measurements_reports_no_data(
        self, django_assert_num_queries
    ):
        dataset = DatasetFactory()

        with django_assert_num_queries(1):
            assert dataset.has_data is False

    def test_adding_a_sample_flips_has_data_to_true(self, django_assert_num_queries):
        dataset = DatasetFactory()
        assert dataset.has_data is False

        RockSampleFactory(dataset=dataset)
        del dataset.has_data

        with django_assert_num_queries(1):
            assert dataset.has_data is True

    def test_adding_a_measurement_flips_has_data_to_true(
        self, django_assert_num_queries
    ):
        dataset = DatasetFactory()
        assert dataset.has_data is False

        ExampleMeasurementFactory(sample=RockSampleFactory(), dataset=dataset)
        del dataset.has_data

        with django_assert_num_queries(1):
            assert dataset.has_data is True


@pytest.mark.django_db
class TestDatasetPrefetch:
    def _dataset_with_metadata(self, count):
        """Build a dataset carrying `count` records of each related type."""
        dataset = DatasetFactory()

        for type_ in [
            concept.uri for concept in DatasetDescription.get_type_concepts()
        ][:count]:
            DatasetDescription.objects.create(related=dataset, type_id=type_, value="x")

        for type_ in [concept.uri for concept in DatasetDate.get_type_concepts()][
            :count
        ]:
            DatasetDate.objects.create(
                related=dataset, type_id=type_, value="2024-01-01"
            )

        # One identifier per (related, type) is enforced, so each gets a distinct type.
        for i, type_ in enumerate(
            [concept.uri for concept in DatasetIdentifier.get_type_concepts()][:count]
        ):
            DatasetIdentifierFactory(
                related=dataset, type_id=type_, value=f"10.{9000 + i}/{dataset.pk}"
            )

        for _ in range(count):
            ContributionFactory(content_object=dataset)

        return dataset

    def test_query_count_does_not_grow_with_related_record_count(self):
        small = self._dataset_with_metadata(1)
        large = self._dataset_with_metadata(3)

        def load_everything(pk):
            ds = Dataset.all_objects.with_metadata().get(pk=pk)
            list(ds.descriptions.all())
            list(ds.dates.all())
            list(ds.identifiers.all())
            list(ds.contributors.all())
            list(ds.keywords.all())

        load_everything(small.pk)  # warm content-type and vocabulary caches
        with CaptureQueriesContext(connection) as one:
            load_everything(small.pk)
        with CaptureQueriesContext(connection) as several:
            load_everything(large.pk)

        assert len(several) == len(one)


@pytest.mark.django_db
class TestDatasetDescription:
    def test_second_description_of_a_carried_type_is_refused_naming_the_type(self):
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="First abstract.",
        )

        duplicate = DatasetDescription(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Second abstract.",
        )
        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "Abstract" in str(exc_info.value)


@pytest.mark.django_db
class TestDatasetDate:
    def test_a_collection_end_before_the_start_is_refused_on_the_value(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type_id=DatasetDate.START_TYPE, value="2020-06-01"
        )

        end = DatasetDate(
            related=dataset, type_id=DatasetDate.END_TYPE, value="2019-05-01"
        )
        with pytest.raises(ValidationError) as exc_info:
            end.full_clean()

        assert "value" in exc_info.value.message_dict


@pytest.mark.django_db
class TestDatasetIdentifier:
    def test_identifier_value_is_refused_across_every_record_type(self):
        from fairdm.core.project.models import ProjectIdentifier

        project = ProjectFactory()
        ProjectIdentifier.objects.create(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.5555/shared-value",
        )

        dataset = DatasetFactory()
        clashing = DatasetIdentifier(
            related=dataset,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.5555/shared-value",
        )
        with pytest.raises(ValidationError) as exc_info:
            clashing.full_clean()

        assert "value" in exc_info.value.error_dict


@pytest.mark.django_db
class TestPublishedQuerySet:
    def test_published_returns_only_published_datasets_including_a_private_one(self):
        published_private = DatasetFactory(
            published=True, visibility=Visibility.PRIVATE
        )
        published_public = DatasetFactory(published=True, visibility=Visibility.PUBLIC)
        unpublished = DatasetFactory(published=False)

        result = Dataset.all_objects.published()

        assert published_private in result
        assert published_public in result
        assert unpublished not in result


@pytest.mark.django_db
class TestMethodChaining:
    def test_chain_filter_and_with_related_and_with_contributors(self):
        # PUBLIC, so the default (privacy-first) manager does not exclude the row.
        project = ProjectFactory()
        ds_match = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(visibility=Visibility.PUBLIC)

        result = (
            Dataset.objects.filter(project=project).with_related().with_contributors()
        )

        assert result.count() == 1
        assert ds_match in result


@pytest.mark.django_db
class TestPerformanceOptimization:
    def test_with_related_query_count_does_not_grow_with_rows(
        self, django_assert_num_queries
    ):
        project = ProjectFactory()

        def load_with_related():
            for ds in Dataset.all_objects.with_related():
                _ = ds.project.name if ds.project else None
                _ = list(ds.contributors.all())

        ds = DatasetFactory(project=project)
        ContributionFactory(content_object=ds)
        load_with_related()  # warm content-type caches
        with CaptureQueriesContext(connection) as one_record:
            load_with_related()

        for _ in range(2):
            ds = DatasetFactory(project=project)
            for _ in range(3):
                ContributionFactory(content_object=ds)

        with django_assert_num_queries(len(one_record)):
            load_with_related()

    def test_with_contributors_query_count_does_not_grow_with_rows(
        self, django_assert_num_queries
    ):
        def load_contributors():
            for ds in Dataset.all_objects.with_contributors():
                _ = list(ds.contributors.all())

        ContributionFactory(content_object=DatasetFactory(project=None))
        load_contributors()  # warm content-type caches
        with CaptureQueriesContext(connection) as one_record:
            load_contributors()

        for _ in range(2):
            ds = DatasetFactory(project=None)
            for _ in range(3):
                ContributionFactory(content_object=ds)

        with django_assert_num_queries(len(one_record)):
            load_contributors()


@pytest.mark.django_db
class TestDatasetQuerySetGetVisible:
    def test_a_public_dataset_in_a_public_project_is_visible(self):
        dataset = DatasetFactory(
            visibility=Visibility.PUBLIC,
            project=ProjectFactory(visibility=Visibility.PUBLIC),
        )

        assert dataset in Dataset.objects.get_visible()

    def test_a_private_dataset_is_left_out(self):
        dataset = DatasetFactory(
            visibility=Visibility.PRIVATE,
            project=ProjectFactory(visibility=Visibility.PUBLIC),
        )

        assert dataset not in Dataset.all_objects.get_visible()

    def test_a_public_dataset_in_a_private_project_is_left_out(self):
        dataset = DatasetFactory(
            visibility=Visibility.PUBLIC,
            project=ProjectFactory(visibility=Visibility.PRIVATE),
        )

        assert dataset not in Dataset.objects.get_visible()

    def test_a_public_dataset_with_no_project_is_visible(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, project=None)

        assert dataset in Dataset.objects.get_visible()


@pytest.mark.django_db
class TestMoveKeepsManager:
    """``RecordAccess`` tests the rule. This keeps the dataset's wiring of it."""

    def refusal_code(self, dataset):
        with pytest.raises(ValidationError) as refused:
            dataset.clean()
        return refused.value.error_dict["project"][0].code

    def test_a_move_to_a_project_that_gives_no_manager_is_refused(self, make_manager):
        project = ProjectFactory()
        make_manager(project)
        dataset = DatasetFactory(project=project)
        dataset.project = ProjectFactory()

        assert self.refusal_code(dataset) == "no_manager"


@pytest.mark.django_db
class TestDatasetSpatialCoverage:
    """AS 2.9 to 2.10 and FR-023: the box holds what the viewer may open, measurements included."""

    @pytest.fixture
    def dataset(self):
        return DatasetFactory(visibility=Visibility.PUBLIC, published=True)

    @staticmethod
    def at(longitude, latitude):
        return Point(longitude, latitude, srid=4326)

    def test_it_holds_every_location_of_the_samples_and_measurements(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=self.at(10.0, 10.0))
        RockSampleFactory(dataset=dataset, location=self.at(-5.0, 20.0))
        ExampleMeasurementFactory(
            sample=sample, dataset=dataset, location=self.at(40.0, -30.0)
        )

        found = dataset.spatial_coverage()

        assert found == Coverage(west=-5.0, south=-30.0, east=40.0, north=20.0)

    def test_a_measurement_with_none_is_placed_by_its_sample(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=self.at(10.0, 10.0))
        ExampleMeasurementFactory(sample=sample, dataset=dataset)

        assert dataset.spatial_coverage() == Coverage(10.0, 10.0, 10.0, 10.0)

    def test_a_measurement_placed_by_a_sample_in_another_dataset_widens_the_box(
        self, dataset
    ):
        RockSampleFactory(dataset=dataset, location=self.at(10.0, 10.0))
        elsewhere = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        distant = RockSampleFactory(dataset=elsewhere, location=self.at(50.0, 40.0))
        ExampleMeasurementFactory(sample=distant, dataset=dataset)

        assert dataset.spatial_coverage() == Coverage(10.0, 10.0, 50.0, 40.0)

    def test_it_is_none_when_nothing_is_located(self, dataset):
        RockSampleFactory(dataset=dataset)

        assert dataset.spatial_coverage() is None

    def test_it_is_none_for_a_dataset_with_no_records(self, dataset):
        assert dataset.spatial_coverage() is None

    def test_locations_either_side_of_the_180th_meridian_make_a_narrow_box(
        self, dataset
    ):
        RockSampleFactory(dataset=dataset, location=self.at(176.0, 0.0))
        RockSampleFactory(dataset=dataset, location=self.at(-176.0, 0.0))

        found = dataset.spatial_coverage()

        assert found.west > found.east
        assert (found.east - found.west) % 360 < 10

    def test_another_datasets_locations_are_not_counted(self, dataset):
        RockSampleFactory(dataset=dataset, location=self.at(10.0, 10.0))
        RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True),
            location=self.at(50.0, 50.0),
        )

        assert dataset.spatial_coverage() == Coverage(10.0, 10.0, 10.0, 10.0)

    def test_a_visitor_does_not_count_what_they_may_not_open(self):
        unpublished = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        RockSampleFactory(dataset=unpublished, location=self.at(10.0, 10.0))

        assert unpublished.spatial_coverage() is None
        assert unpublished.spatial_coverage(AnonymousUser()) is None
        assert unpublished.spatial_coverage(PersonFactory(is_active=True)) is None

    def test_a_member_of_the_team_counts_it(self):
        unpublished = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        RockSampleFactory(dataset=unpublished, location=self.at(10.0, 10.0))
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=unpublished,
            contributor=member,
            level=ContributionLevel.VIEW,
        )

        assert unpublished.spatial_coverage(member) == Coverage(10.0, 10.0, 10.0, 10.0)

    def test_a_person_holding_one_sample_counts_that_sample_and_nothing_else(self):
        unpublished = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        held = RockSampleFactory(dataset=unpublished, location=self.at(10.0, 10.0))
        RockSampleFactory(dataset=unpublished, location=self.at(50.0, 50.0))
        person = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=held, contributor=person, level=ContributionLevel.VIEW
        )

        found = unpublished.spatial_coverage(person)

        assert found == Coverage(10.0, 10.0, 10.0, 10.0)

    def test_a_measurement_placed_only_by_a_hidden_sample_adds_nothing(self):
        hidden = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        released = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = RockSampleFactory(dataset=hidden, location=self.at(10.0, 10.0))
        ExampleMeasurementFactory(sample=sample, dataset=released)

        assert released.spatial_coverage() is None

    def test_a_measurement_with_its_own_location_counts_whatever_its_sample(self):
        hidden = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        released = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = RockSampleFactory(dataset=hidden, location=self.at(10.0, 10.0))
        ExampleMeasurementFactory(
            sample=sample, dataset=released, location=self.at(20.0, 20.0)
        )

        assert released.spatial_coverage() == Coverage(20.0, 20.0, 20.0, 20.0)

    def test_a_measurement_in_a_hidden_dataset_is_not_counted(self):
        hidden = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        sample = RockSampleFactory(dataset=hidden)
        ExampleMeasurementFactory(
            sample=sample, dataset=hidden, location=self.at(20.0, 20.0)
        )

        assert hidden.spatial_coverage() is None
