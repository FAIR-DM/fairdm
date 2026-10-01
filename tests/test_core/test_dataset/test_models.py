"""Tests for the ``Dataset`` model, its querysets and its related-record models."""

import time
from datetime import timedelta

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import Promise

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.dataset.models import (
    DATACITE_RELATIONSHIP_TYPES,
    Dataset,
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
    DatasetLiteratureRelation,
    DatasetQuerySet,
)
from fairdm.factories import (
    DatasetFactory,
    DatasetIdentifierFactory,
    LiteratureItemFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.factories.contributors import ContributionFactory
from fairdm.utils.choices import Visibility

# `DatasetFactory()` defaults to PRIVATE, so tests unrelated to visibility use
# `Dataset.all_objects`.


@pytest.mark.django_db
class TestDatasetCreation:
    def test_create_dataset_with_required_fields(self):
        project = ProjectFactory()
        dataset = Dataset.objects.create(name="Test Dataset", project=project)

        assert dataset.pk is not None
        assert dataset.name == "Test Dataset"
        assert dataset.project == project

    def test_create_dataset_with_factory(self):
        dataset = DatasetFactory()

        assert dataset.pk is not None
        assert dataset.name
        assert dataset.project is not None
        assert dataset.uuid is not None


@pytest.mark.django_db
class TestDatasetNameValidation:
    def test_name_is_required(self):
        project = ProjectFactory()
        dataset = Dataset(project=project)

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_max_length_enforced(self):
        project = ProjectFactory()
        long_name = "x" * 301
        dataset = Dataset(name=long_name, project=project)

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_accepts_valid_length(self):
        project = ProjectFactory()
        valid_name = "x" * 300
        dataset = Dataset(name=valid_name, project=project)

        dataset.full_clean()
        dataset.save()
        assert dataset.pk is not None


@pytest.mark.django_db
class TestDatasetVisibility:
    def test_visibility_default_is_private(self):
        dataset = DatasetFactory()

        assert dataset.visibility == Visibility.PRIVATE.value

    def test_visibility_accepts_valid_choices(self):
        valid_choices = [
            Visibility.PUBLIC,
            Visibility.PRIVATE,
        ]

        for choice in valid_choices:
            dataset = DatasetFactory(visibility=choice.value)
            assert dataset.visibility == choice.value

    def test_visibility_rejects_invalid_choice(self):
        project = ProjectFactory()
        dataset = Dataset(name="Test", project=project, visibility=999)

        with pytest.raises(ValidationError):
            dataset.full_clean()

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
class TestDatasetPublished:
    def test_published_defaults_to_false_when_unset(self):
        dataset = Dataset.objects.create(
            name="Unpublished by default", project=ProjectFactory()
        )

        dataset.refresh_from_db()

        assert dataset.published is False

    def test_every_existing_dataset_reads_back_unpublished(self):
        datasets = DatasetFactory.create_batch(3)

        reloaded = Dataset.all_objects.filter(pk__in=[d.pk for d in datasets])

        assert reloaded.count() == 3
        assert all(d.published is False for d in reloaded)


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

    def test_deleting_a_record_a_private_dataset_depends_on_still_cascades(self):
        project = ProjectFactory()
        private_dataset = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        dataset_pk = private_dataset.pk

        project.delete()

        assert not Dataset.all_objects.filter(pk=dataset_pk).exists()

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

        # The scan is the guard, so an empty scan is a broken guard, not a pass:
        # `referenced <= declared` is trivially true of the empty set.
        assert referenced, (
            "no permission references found - the scan has stopped working"
        )
        assert referenced <= declared
        assert "view_private" not in declared


@pytest.mark.django_db
class TestDatasetProjectRelationship:
    def test_project_delete_cascades_to_dataset(self):
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        dataset_id = dataset.pk

        project.delete()

        assert not Dataset.objects.filter(pk=dataset_id).exists()

    def test_project_delete_succeeds_without_datasets(self):
        project = ProjectFactory()
        project_id = project.pk

        project.delete()

        from fairdm.core.project.models import Project

        assert not Project.objects.filter(pk=project_id).exists()

    def test_multiple_datasets_deleted_with_project(self):
        project = ProjectFactory()
        datasets = DatasetFactory.create_batch(3, project=project)
        dataset_ids = [dataset.pk for dataset in datasets]

        project.delete()

        assert not Dataset.objects.filter(pk__in=dataset_ids).exists()


@pytest.mark.django_db
class TestOrphanedDatasets:
    def test_dataset_can_exist_without_project(self):
        dataset = Dataset.objects.create(name="Orphaned Dataset", project=None)

        assert dataset.pk is not None
        assert dataset.project is None

    def test_orphaned_dataset_queries(self):
        Dataset.objects.create(name="Orphaned", project=None)
        DatasetFactory()

        orphaned = Dataset.all_objects.filter(project__isnull=True)
        assert orphaned.count() == 1

    def test_setting_project_to_null_creates_orphan(self):
        dataset = DatasetFactory()
        dataset.project = None
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.project is None


@pytest.mark.django_db
class TestDatasetLicense:
    def test_license_defaults_to_cc_by_4(self):
        dataset = DatasetFactory()

        assert dataset.license is not None
        assert "CC BY 4.0" in dataset.license.name

    def test_license_can_be_changed(self):
        from licensing.models import License

        dataset = DatasetFactory()
        new_license, _ = License.objects.get_or_create(
            name="CC BY-SA 4.0",
            defaults={
                "slug": "cc-by-sa-4-0",
                "canonical_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
        )

        dataset.license = new_license
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.license == new_license

    def test_license_can_be_null(self):
        dataset = DatasetFactory()
        dataset.license = None
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.license is None


@pytest.mark.django_db
class TestDatasetUUID:
    def test_uuid_generated_automatically(self):
        dataset = DatasetFactory()

        assert dataset.uuid is not None
        assert str(dataset.uuid)

    def test_uuid_is_unique(self):
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()

        assert dataset1.uuid != dataset2.uuid

    def test_duplicate_uuid_raises_integrity_error(self):
        dataset1 = DatasetFactory()

        with pytest.raises(IntegrityError):
            Dataset.objects.create(
                name="Duplicate UUID",
                project=ProjectFactory(),
                uuid=dataset1.uuid,
            )

    def test_uuid_immutable_after_creation(self):
        DatasetFactory()
        uuid_field = Dataset._meta.get_field("uuid")

        assert uuid_field.editable is False


@pytest.mark.django_db
class TestDatasetFields:
    def test_name_is_required(self):
        dataset = Dataset(project=ProjectFactory())

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_length_is_bound(self):
        dataset = Dataset(name="x" * 301, project=ProjectFactory())

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_dataset_with_no_project_is_valid(self):
        dataset = Dataset(name="Orphaned Dataset", project=None)

        dataset.full_clean()

    def test_image_is_optional(self):
        dataset = Dataset(name="No Image", project=ProjectFactory())

        dataset.full_clean()

    def test_project_is_optional(self):
        dataset = Dataset.objects.create(name="No Project")

        assert dataset.project is None

    def test_data_publication_is_optional(self):
        dataset = Dataset(name="No Reference", project=ProjectFactory())

        dataset.full_clean()
        assert dataset.reference is None


@pytest.mark.django_db
class TestDatasetOrdering:
    def test_default_ordering_is_most_recently_modified_first(self):
        oldest = DatasetFactory()
        middle = DatasetFactory()
        newest = DatasetFactory()

        now = timezone.now()
        # `modified` is auto_now, so update() bypasses `pre_save()` to pin known values.
        Dataset.all_objects.filter(pk=oldest.pk).update(
            modified=now - timedelta(days=2)
        )
        Dataset.all_objects.filter(pk=middle.pk).update(
            modified=now - timedelta(days=1)
        )
        Dataset.all_objects.filter(pk=newest.pk).update(modified=now)

        assert list(Dataset.all_objects.all()) == [newest, middle, oldest]


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
class TestDatasetKeywords:
    def test_controlled_vocabulary_term_is_stored_as_a_reference(self):
        from research_vocabs.models import Concept

        dataset = DatasetFactory()
        # `Concept.preload()` runs once per session in tests/conftest.py.
        term = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        assert term is not None

        dataset.keywords.add(term)

        stored = dataset.keywords.get(pk=term.pk)
        assert isinstance(stored, Concept)
        assert stored.name == term.name

    def test_free_tags_are_distinguishable_from_controlled_keywords(self):
        from research_vocabs.models import Concept

        dataset = DatasetFactory()
        keyword = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        dataset.keywords.add(keyword)
        dataset.tags.add("erosion")

        assert "erosion" in dataset.tags.names()
        assert dataset.keywords.count() == 1
        assert all(isinstance(k, Concept) for k in dataset.keywords.all())
        assert not dataset.keywords.filter(name="erosion").exists()


@pytest.mark.django_db
class TestDatasetContributions:
    def test_contribution_records_contributor_and_roles(self):
        dataset = DatasetFactory()
        person = PersonFactory()

        contribution = dataset.add_contributor(
            person, with_roles=["Creator", "DataCollector"]
        )

        assert contribution.contributor == person
        assert set(contribution.roles.values_list("name", flat=True)) == {
            "Creator",
            "DataCollector",
        }
        assert dataset.contributors.filter(pk=contribution.pk).exists()

    def test_role_vocabulary_members(self):
        assert set(Dataset.CONTRIBUTOR_ROLES.values) == {
            "Creator",
            "ContactPerson",
            "DataCollector",
            "DataCurator",
            "DataManager",
            "Editor",
            "Producer",
            "RelatedPerson",
            "Researcher",
            "ProjectLeader",
            "ProjectManager",
            "ProjectMember",
            "Supervisor",
            "WorkPackageLeader",
            "RightsHolder",
            "Other",
        }


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

        for type_ in DatasetDescription.VOCABULARY.values[:count]:
            DatasetDescription.objects.create(related=dataset, type=type_, value="x")

        for type_ in DatasetDate.VOCABULARY.values[:count]:
            DatasetDate.objects.create(related=dataset, type=type_, value="2024-01-01")

        # One identifier per (related, type) is enforced, so each gets a distinct type.
        for i, type_ in enumerate(DatasetIdentifier.VOCABULARY.values[:count]):
            DatasetIdentifierFactory(
                related=dataset, type=type_, value=f"10.{9000 + i}/{dataset.pk}"
            )

        for _ in range(count):
            ContributionFactory(content_object=dataset)

        return dataset

    def test_query_count_does_not_grow_with_related_record_count(
        self, django_assert_num_queries
    ):
        small = self._dataset_with_metadata(1)
        large = self._dataset_with_metadata(3)

        def load_everything(pk):
            ds = Dataset.all_objects.with_metadata().get(pk=pk)
            list(ds.descriptions.all())
            list(ds.dates.all())
            list(ds.identifiers.all())
            list(ds.contributors.all())
            list(ds.keywords.all())

        with django_assert_num_queries(6):
            load_everything(small.pk)

        with django_assert_num_queries(6):
            load_everything(large.pk)


class TestDatasetTranslatable:
    def test_field_labels_and_help_text_are_lazy(self):
        for field_name in ["uuid", "license", "visibility"]:
            field = Dataset._meta.get_field(field_name)
            assert isinstance(field.verbose_name, Promise), field_name
            assert isinstance(field.help_text, Promise), field_name

    def test_vocabulary_terms_are_lazy(self):
        from fairdm.core.vocabularies import FairDMIdentifiers

        assert isinstance(FairDMIdentifiers.DOI["skos:prefLabel"], Promise)
        assert isinstance(FairDMIdentifiers.DOI["skos:definition"], Promise)


class TestDatasetVisibilityChoices:
    def test_visibility_vocabulary_members(self):
        assert {member.name for member in Visibility} == {"PRIVATE", "PUBLIC"}

    def test_visibility_field_defaults_to_private(self):
        field = Dataset._meta.get_field("visibility")
        assert field.get_default() == Visibility.PRIVATE


@pytest.mark.django_db
class TestDatasetSharedFixtures:
    def test_public_and_private_dataset_fixtures(self, public_dataset, private_dataset):
        assert public_dataset.visibility == Visibility.PUBLIC
        assert private_dataset.visibility == Visibility.PRIVATE

    def test_dataset_with_full_metadata_carries_one_of_each_related_record(
        self, dataset_with_full_metadata
    ):
        dataset = dataset_with_full_metadata
        assert dataset.descriptions.count() == 1
        assert dataset.dates.count() == 1
        assert dataset.identifiers.count() == 1
        assert dataset.literature_relations.count() == 1
        assert dataset.contributors.count() == 1


@pytest.mark.django_db
class TestDatasetDescription:
    def test_abstract_is_stored_under_its_type_and_retrievable_by_type(self):
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="A brief summary."
        )

        retrieved = dataset.descriptions.get(type="Abstract")
        assert retrieved.value == "A brief summary."

    def test_second_description_of_a_carried_type_is_refused_naming_the_type(self):
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="First abstract."
        )

        duplicate = DatasetDescription(
            related=dataset, type="Abstract", value="Second abstract."
        )
        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "Abstract" in str(exc_info.value)

    def test_methods_description_is_accepted(self):
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset, type="Methods", value="Samples were analysed by XRF."
        )

        description.full_clean()
        description.save()

        assert dataset.descriptions.get(type="Methods").value == (
            "Samples were analysed by XRF."
        )

    def test_two_descriptions_are_both_returned_each_under_its_own_type(self):
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="Abstract text."
        )
        DatasetDescription.objects.create(
            related=dataset, type="Methods", value="Methods text."
        )

        by_type = {d.type: d.value for d in dataset.descriptions.all()}
        assert by_type == {
            "Abstract": "Abstract text.",
            "Methods": "Methods text.",
        }

    def test_description_vocabulary_members(self):
        assert set(DatasetDescription.VOCABULARY.values) == {
            "Abstract",
            "Methods",
            "SeriesInformation",
            "TechnicalInfo",
            "Other",
        }


@pytest.mark.django_db
class TestDatasetDate:
    def test_collection_start_is_stored_under_its_type(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06-01"
        )

        stored = dataset.dates.get(type=DatasetDate.START_TYPE)
        assert str(stored.value) == "2020-06-01"

    def test_second_collection_start_is_refused(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-01-01"
        )

        duplicate = DatasetDate(
            related=dataset, type=DatasetDate.START_TYPE, value="2021-01-01"
        )
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_collection_end_before_start_is_refused_naming_both_dates(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06-01"
        )

        end = DatasetDate(
            related=dataset, type=DatasetDate.END_TYPE, value="2019-05-01"
        )
        with pytest.raises(ValidationError) as exc_info:
            end.full_clean()

        message = str(exc_info.value)
        assert "2020-06-01" in message
        assert "2019-05-01" in message

    def test_moving_start_after_existing_end_is_refused(self):
        dataset = DatasetFactory()
        start = DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-01-01"
        )
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.END_TYPE, value="2020-12-31"
        )

        start.value = "2021-01-01"
        with pytest.raises(ValidationError):
            start.full_clean()

    def test_collection_end_with_no_start_is_accepted(self):
        dataset = DatasetFactory()
        end = DatasetDate(
            related=dataset, type=DatasetDate.END_TYPE, value="2024-06-15"
        )

        end.full_clean()

    def test_year_only_end_in_same_year_as_month_precision_start_is_accepted(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06"
        )

        end = DatasetDate(related=dataset, type=DatasetDate.END_TYPE, value="2020")
        end.full_clean()

    def test_month_precision_end_before_month_precision_start_is_refused(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06"
        )

        end = DatasetDate(related=dataset, type=DatasetDate.END_TYPE, value="2020-03")
        with pytest.raises(ValidationError):
            end.full_clean()

    def test_date_with_no_value_is_refused(self):
        dataset = DatasetFactory()
        date = DatasetDate(related=dataset, type="Available")

        with pytest.raises(ValidationError) as exc_info:
            date.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_date_vocabulary_members(self):
        assert set(DatasetDate.VOCABULARY.values) == {
            "Available",
            "CollectionStart",
            "CollectionEnd",
            "Submitted",
            "Published",
            "Withdrawn",
        }


@pytest.mark.django_db
class TestDatasetIdentifier:
    def test_available_types_are_the_dataset_collection_only(self):
        assert set(DatasetIdentifier.VOCABULARY.values) == {"DOI"}
        assert set(DatasetIdentifier.VOCABULARY.values).isdisjoint(
            {
                "ORCID",
                "RESEARCHER_ID",
                "ROR",
                "WIKIDATA",
                "ISNI",
                "CROSSREF_FUNDER_ID",
            }
        )

    def test_identifier_value_is_refused_across_every_record_type(self):
        from fairdm.core.project.models import ProjectIdentifier

        project = ProjectFactory()
        ProjectIdentifier.objects.create(
            related=project, type="DOI", value="10.5555/shared-value"
        )

        dataset = DatasetFactory()
        clashing = DatasetIdentifier(
            related=dataset, type="DOI", value="10.5555/shared-value"
        )
        with pytest.raises(ValidationError) as exc_info:
            clashing.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_identifier_types_agrees_with_the_related_models_binding(self):
        assert DatasetIdentifier.VOCABULARY.choices == Dataset.IDENTIFIER_TYPES


@pytest.mark.django_db
class TestDatasetDateValidation:
    def test_create_date_with_valid_type(self):
        dataset = DatasetFactory()
        dataset_date = DatasetDate.objects.create(
            related=dataset, type="Available", value="2024-01-15"
        )

        assert dataset_date.pk is not None
        assert dataset_date.type == "Available"
        assert str(dataset_date.value) == "2024-01-15"
        assert dataset_date.related == dataset

    def test_date_type_vocabulary_validation(self):
        dataset = DatasetFactory()
        dataset_date = DatasetDate(
            related=dataset, type="InvalidType", value="2024-01-15"
        )

        with pytest.raises(ValidationError) as exc_info:
            dataset_date.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_date_types_accepted(self):
        from fairdm.core.dataset.models import Dataset

        dataset = DatasetFactory()

        for type_code, _type_label in Dataset.DATE_TYPES.choices:
            dataset_date = DatasetDate(
                related=dataset, type=type_code, value="2024-01-15"
            )
            dataset_date.full_clean()

    def test_date_field_required(self):
        dataset = DatasetFactory()
        dataset_date = DatasetDate(
            related=dataset,
            type="Available",
        )

        with pytest.raises(ValidationError) as exc_info:
            dataset_date.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        dataset_date = DatasetDate(
            type="Available",
            value="2024-01-15",
        )

        with pytest.raises(ValidationError):
            dataset_date.full_clean()

    def test_unique_together_constraint(self):
        dataset = DatasetFactory()

        DatasetDate.objects.create(
            related=dataset, type="Available", value="2024-01-15"
        )

        with pytest.raises(IntegrityError):
            DatasetDate.objects.create(
                related=dataset, type="Available", value="2024-02-20"
            )

    def test_multiple_date_types_allowed(self):
        dataset = DatasetFactory()

        DatasetDate.objects.create(
            related=dataset, type="Available", value="2024-01-15"
        )
        DatasetDate.objects.create(
            related=dataset, type="Submitted", value="2024-02-01"
        )

        assert dataset.dates.count() == 2

    def test_cascade_delete_with_dataset(self):
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type="Available", value="2024-01-15"
        )

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetDate.objects.filter(related_id=dataset_id).exists()


@pytest.mark.django_db
class TestDatasetDescriptionValidation:
    def test_create_description_with_valid_type(self):
        dataset = DatasetFactory()
        description = DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="This is an abstract"
        )

        assert description.pk is not None
        assert description.type == "Abstract"

    def test_description_type_vocabulary_validation(self):
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset, type="InvalidType", value="Test description"
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_description_types_accepted(self):
        from fairdm.core.dataset.models import Dataset

        dataset = DatasetFactory()

        for type_code, _type_label in Dataset.DESCRIPTION_TYPES.choices:
            description = DatasetDescription(
                related=dataset, type=type_code, value=f"Test {type_code}"
            )
            description.full_clean()

    def test_description_field_required(self):
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset,
            type="Abstract",
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        description = DatasetDescription(
            type="Abstract",
            value="Test",
        )

        with pytest.raises(ValidationError):
            description.full_clean()

    def test_unique_together_constraint(self):
        dataset = DatasetFactory()

        DatasetDescription.objects.create(
            related=dataset, type="Methods", value="Method 1"
        )

        with pytest.raises(IntegrityError):
            DatasetDescription.objects.create(
                related=dataset, type="Methods", value="Method 2"
            )

    def test_cascade_delete_with_dataset(self):
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="Test"
        )

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetDescription.objects.filter(related_id=dataset_id).exists()


@pytest.mark.django_db
class TestDatasetIdentifierValidation:
    def test_create_identifier_with_valid_type(self):
        dataset = DatasetFactory()
        identifier = DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        assert identifier.pk is not None
        assert identifier.type == "DOI"

    def test_identifier_type_vocabulary_validation(self):
        dataset = DatasetFactory()
        identifier = DatasetIdentifier(
            related=dataset, type="InvalidType", value="some-identifier"
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_identifier_types_accepted(self):
        dataset = DatasetFactory()

        for type_code, _type_label in Dataset.IDENTIFIER_TYPES:
            identifier = DatasetIdentifier(
                related=dataset, type=type_code, value=f"test-{type_code}"
            )
            identifier.full_clean()

    def test_identifier_field_required(self):
        dataset = DatasetFactory()
        identifier = DatasetIdentifier(
            related=dataset,
            type="DOI",
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        identifier = DatasetIdentifier(
            type="DOI",
            value="10.1000/xyz123",
        )

        with pytest.raises(ValidationError):
            identifier.full_clean()


@pytest.mark.django_db
class TestDOISupport:
    def test_create_doi_identifier(self):
        dataset = DatasetFactory()
        doi = DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        assert doi.type == "DOI"
        assert doi.value == "10.1000/xyz123"

    def test_query_datasets_with_doi(self):
        dataset_with_doi = DatasetFactory()
        DatasetIdentifier.objects.create(
            related=dataset_with_doi, type="DOI", value="10.1000/xyz123"
        )

        dataset_without_doi = DatasetFactory()

        datasets_with_doi = Dataset.all_objects.filter(
            identifiers__type="DOI"
        ).distinct()

        assert dataset_with_doi in datasets_with_doi
        assert dataset_without_doi not in datasets_with_doi

    def test_get_doi_helper(self):
        dataset = DatasetFactory()
        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        doi = dataset.identifiers.filter(type="DOI").first()
        assert doi is not None
        assert doi.value == "10.1000/xyz123"

    def test_cascade_delete_with_dataset(self):
        dataset = DatasetFactory()
        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetIdentifier.objects.filter(related_id=dataset_id).exists()

    def test_unique_together_constraint(self):
        dataset = DatasetFactory()

        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        with pytest.raises(IntegrityError):
            DatasetIdentifier.objects.create(
                related=dataset, type="DOI", value="10.1000/different"
            )


@pytest.mark.django_db
class TestDatasetLiterature:
    def test_a_data_publication_is_recorded_as_the_datasets_reference(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        dataset.reference = paper
        dataset.full_clean()
        dataset.save()
        dataset.refresh_from_db()

        assert dataset.reference == paper

    def test_the_same_publication_cannot_be_named_by_two_datasets(self):
        paper = LiteratureItemFactory()
        DatasetFactory(reference=paper)

        with pytest.raises(IntegrityError):
            DatasetFactory(reference=paper)

    def test_deleting_the_named_publication_leaves_the_dataset_with_none_named(self):
        paper = LiteratureItemFactory()
        dataset = DatasetFactory(reference=paper)

        paper.delete()
        dataset.refresh_from_db()

        assert dataset.pk is not None
        assert dataset.reference is None


@pytest.mark.django_db
class TestDatasetLiteratureRelationValidation:
    def test_create_relation_with_valid_type(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        assert relation.pk is not None
        assert relation.relationship_type == "IsCitedBy"

    def test_relationship_type_vocabulary_validation(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation(
            dataset=dataset, literature_item=paper, relationship_type="InvalidType"
        )

        with pytest.raises(ValidationError) as exc_info:
            relation.full_clean()

        assert "relationship_type" in exc_info.value.error_dict

    def test_relationship_types_match_the_datacite_schema_by_name(self):
        expected_codes = {
            "IsCitedBy", "Cites", "IsSupplementTo", "IsSupplementedBy",
            "IsContinuedBy", "Continues", "IsDescribedBy", "Describes",
            "HasMetadata", "IsMetadataFor", "HasVersion", "IsVersionOf",
            "IsNewVersionOf", "IsPreviousVersionOf", "IsPartOf", "HasPart",
            "IsPublishedIn", "IsReferencedBy", "References", "IsDocumentedBy",
            "Documents", "IsCompiledBy", "Compiles", "IsVariantFormOf",
            "IsOriginalFormOf", "IsIdenticalTo", "IsReviewedBy", "Reviews",
            "IsDerivedFrom", "IsSourceOf", "IsRequiredBy", "Requires",
            "Obsoletes", "IsObsoletedBy",
        }  # fmt: skip
        actual_codes = {code for code, _label in DATACITE_RELATIONSHIP_TYPES}

        assert actual_codes == expected_codes

        dataset = DatasetFactory()
        paper = LiteratureItemFactory()
        for type_code in expected_codes:
            relation = DatasetLiteratureRelation(
                dataset=dataset, literature_item=paper, relationship_type=type_code
            )
            relation.full_clean()

    def test_dataset_required(self):
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation(
            literature_item=paper,
            relationship_type="IsCitedBy",
        )

        with pytest.raises(ValidationError):
            relation.full_clean()

    def test_literature_item_required(self):
        dataset = DatasetFactory()

        relation = DatasetLiteratureRelation(
            dataset=dataset,
            relationship_type="IsCitedBy",
        )

        with pytest.raises(ValidationError):
            relation.full_clean()


@pytest.mark.django_db
class TestUniqueTogetherConstraint:
    def test_duplicate_relationship_raises_error(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        with pytest.raises(IntegrityError):
            DatasetLiteratureRelation.objects.create(
                dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
            )

    def test_different_types_allowed(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )
        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsDocumentedBy"
        )

        assert dataset.literature_relations.count() == 2


@pytest.mark.django_db
class TestCascadeBehavior:
    def test_cascade_on_dataset_delete(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        dataset.delete()

        assert DatasetLiteratureRelation.objects.count() == 0

    def test_cascade_on_literature_delete(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        paper.delete()

        assert DatasetLiteratureRelation.objects.count() == 0


@pytest.mark.django_db
class TestQueryingRelationships:
    def test_query_by_relationship_type(self):
        dataset = DatasetFactory()
        paper1 = LiteratureItemFactory()
        paper2 = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper1, relationship_type="IsCitedBy"
        )
        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper2, relationship_type="IsDocumentedBy"
        )

        citing = dataset.related_literature.filter(
            dataset_relations__relationship_type="IsCitedBy"
        )

        assert citing.count() == 1
        assert paper1 in citing

    def test_access_through_manytomany(self):
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        assert paper in dataset.related_literature.all()


@pytest.mark.django_db
class TestPrivacyFirstDefault:
    def test_default_manager_includes_public_datasets(self):
        ds_public = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)

        result = Dataset.objects.all()

        assert result.count() == 1
        assert ds_public in result


@pytest.mark.django_db
class TestWithRelatedOptimization:
    def test_with_related_prefetches_project(self, django_assert_max_num_queries):
        DatasetFactory.create_batch(5, project=ProjectFactory())

        with django_assert_max_num_queries(3):
            datasets = list(Dataset.all_objects.with_related())
            for ds in datasets:
                _ = ds.project.name if ds.project else None

    def test_with_related_prefetches_contributors(self, django_assert_max_num_queries):
        datasets = DatasetFactory.create_batch(5)
        for ds in datasets:
            for _ in range(3):
                ContributionFactory(content_object=ds)

        with django_assert_max_num_queries(3):
            datasets = list(Dataset.all_objects.with_related())
            for ds in datasets:
                _ = list(ds.contributors.all())

    def test_with_related_on_filtered_queryset(self):
        project = ProjectFactory()
        ds_match = DatasetFactory(project=project)
        DatasetFactory()

        result = Dataset.all_objects.filter(project=project).with_related()

        assert result.count() == 1
        assert ds_match in result

    def test_with_related_returns_queryset_for_chaining(self):
        DatasetFactory()

        result = Dataset.objects.with_related().filter(
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )

        assert isinstance(result, type(Dataset.objects.all()))


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
class TestWithContributorsOptimization:
    def test_with_contributors_prefetches_contributors(
        self, django_assert_max_num_queries
    ):
        datasets = DatasetFactory.create_batch(5)
        for ds in datasets:
            for _ in range(3):
                ContributionFactory(content_object=ds)

        with django_assert_max_num_queries(2):
            datasets = list(Dataset.all_objects.with_contributors())
            for ds in datasets:
                _ = list(ds.contributors.all())

    def test_with_contributors_does_not_prefetch_project(self):
        datasets = DatasetFactory.create_batch(5, project=ProjectFactory())

        result = Dataset.all_objects.with_contributors()

        datasets = list(result)
        assert len(datasets) == 5

    def test_with_contributors_on_filtered_queryset(self):
        project = ProjectFactory()
        ds_match = DatasetFactory(project=project)
        DatasetFactory()

        result = Dataset.all_objects.filter(project=project).with_contributors()

        assert result.count() == 1
        assert ds_match in result

    def test_with_contributors_returns_queryset_for_chaining(self):
        DatasetFactory()

        result = Dataset.objects.with_contributors().filter(
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )

        assert isinstance(result, type(Dataset.objects.all()))


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
        def load_with_related():
            for ds in Dataset.all_objects.with_related():
                _ = ds.project.name if ds.project else None
                _ = list(ds.contributors.all())

        ds = DatasetFactory(project=ProjectFactory())
        ContributionFactory(content_object=ds)
        with CaptureQueriesContext(connection) as one_record:
            load_with_related()

        for _ in range(9):
            ds = DatasetFactory(project=ProjectFactory())
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

        ContributionFactory(content_object=DatasetFactory())
        with CaptureQueriesContext(connection) as one_record:
            load_contributors()

        for _ in range(9):
            ds = DatasetFactory()
            for _ in range(3):
                ContributionFactory(content_object=ds)

        with django_assert_num_queries(len(one_record)):
            load_contributors()

    def test_chained_optimizations_compound_benefits(
        self, django_assert_max_num_queries
    ):
        datasets = []
        for _ in range(5):
            ds = DatasetFactory(project=ProjectFactory())
            for _ in range(2):
                ContributionFactory(content_object=ds)
            datasets.append(ds)

        with django_assert_max_num_queries(4):
            result = list(Dataset.all_objects.with_related().with_contributors())
            for ds in result:
                _ = ds.project.name if ds.project else None
                _ = list(ds.contributors.all())


@pytest.mark.django_db
class TestDatasetModel:
    def test_dataset_creation(self):
        dataset = DatasetFactory()

        assert dataset.pk is not None
        assert dataset.name is not None
        assert dataset.uuid is not None
        assert dataset.uuid.startswith("d")

    def test_dataset_visibility_default(self):
        dataset = DatasetFactory()
        # The factory may randomise visibility.
        assert dataset.visibility in Visibility.values

    def test_dataset_queryset_with_contributors(self):
        dataset = DatasetFactory()

        queryset = Dataset.all_objects.with_contributors()
        dataset_with_prefetch = queryset.get(pk=dataset.pk)

        assert dataset_with_prefetch.contributors is not None

    def test_dataset_queryset_with_related(self):
        dataset = DatasetFactory()

        queryset = Dataset.all_objects.with_related()
        dataset_with_prefetch = queryset.get(pk=dataset.pk)

        assert dataset_with_prefetch.project is not None

    def test_dataset_str_representation(self):
        dataset = DatasetFactory(name="Test Dataset")
        assert str(dataset) == "Test Dataset"

    def test_dataset_absolute_url(self):
        dataset = DatasetFactory()
        url = dataset.get_absolute_url()

        assert url == reverse("dataset:overview", kwargs={"uuid": dataset.uuid})

    def test_dataset_has_data_property(self):
        dataset = DatasetFactory()

        has_data = dataset.has_data
        assert isinstance(has_data, bool)

    def test_dataset_bbox_property(self):
        dataset = DatasetFactory()

        bbox = dataset.bbox
        assert bbox is None or isinstance(bbox, (dict, tuple, list))

    def test_dataset_descriptions_relationship(self):
        dataset = DatasetFactory()
        descriptions = DatasetDescription.objects.filter(related=dataset)

        assert descriptions.count() >= 0
        assert all(desc.related == dataset for desc in descriptions)

    def test_dataset_dates_relationship(self):
        dataset = DatasetFactory()
        dates = DatasetDate.objects.filter(related=dataset)

        assert dates.count() >= 0
        assert all(date.related == dataset for date in dates)

    def test_add_contributor(self):
        dataset = DatasetFactory()
        user = PersonFactory()

        contribution = dataset.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert dataset.contributors.filter(pk=contribution.pk).exists()

    def test_dataset_project_relationship(self):
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        assert dataset.project == project
        assert dataset in Dataset.all_objects.filter(project=project)


@pytest.mark.django_db
class TestDatasetCreationRecord:
    def test_dataset_created_by_a_known_user_names_that_user(self):
        creator = PersonFactory()
        dataset = DatasetFactory(created_by=creator)

        dataset.refresh_from_db()

        assert dataset.created_by == creator

    def test_changing_a_field_advances_modified_and_leaves_creator_unchanged(self):
        creator = PersonFactory()
        dataset = DatasetFactory(created_by=creator)
        original_modified = dataset.modified

        time.sleep(0.01)
        dataset.name = "Renamed Dataset"
        dataset.save()
        dataset.refresh_from_db()

        assert dataset.modified > original_modified
        assert dataset.created_by == creator

    def test_dataset_survives_creators_account_removal(self):
        creator = PersonFactory()
        dataset = DatasetFactory(created_by=creator)

        creator.delete()
        dataset.refresh_from_db()

        assert dataset.pk is not None
        assert dataset.created_by is None

    def test_created_by_field_is_not_editable(self):
        assert Dataset._meta.get_field("created_by").editable is False


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
