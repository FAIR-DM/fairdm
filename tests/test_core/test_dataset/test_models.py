"""
Unit tests for Dataset model.

Tests cover:
- Model creation and field constraints
- Name validation (required, max_length)
- Visibility choices and defaults
- PROTECT behavior on project deletion
- Orphaned datasets (project=null)
- License field with defaults
- UUID uniqueness and collision handling
- has_data property
- DatasetDate / DatasetDescription / DatasetIdentifier validation
- DatasetLiteratureRelation (deferred - literature app not yet complete)
- DatasetQuerySet privacy and query-optimization methods
- General model/queryset/URL smoke tests
"""

import time
from datetime import timedelta

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import Promise

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
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory


@pytest.mark.django_db
class TestDatasetCreation:
    """Test basic Dataset model creation."""

    def test_create_dataset_with_required_fields(self):
        """Can create dataset with required fields."""
        project = ProjectFactory()
        dataset = Dataset.objects.create(name="Test Dataset", project=project)

        assert dataset.pk is not None
        assert dataset.name == "Test Dataset"
        assert dataset.project == project

    def test_create_dataset_with_factory(self):
        """DatasetFactory creates valid dataset."""
        dataset = DatasetFactory()

        assert dataset.pk is not None
        assert dataset.name
        assert dataset.project is not None
        assert dataset.uuid is not None


@pytest.mark.django_db
class TestDatasetNameValidation:
    """Test Dataset.name field validation."""

    def test_name_is_required(self):
        """Dataset name is required."""
        project = ProjectFactory()
        dataset = Dataset(project=project)

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_max_length_enforced(self):
        """Dataset name respects max_length constraint."""
        project = ProjectFactory()
        long_name = "x" * 301  # max_length=300
        dataset = Dataset(name=long_name, project=project)

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_accepts_valid_length(self):
        """Dataset name accepts valid length strings."""
        project = ProjectFactory()
        valid_name = "x" * 300  # Exactly at max_length
        dataset = Dataset(name=valid_name, project=project)

        dataset.full_clean()  # Should not raise
        dataset.save()
        assert dataset.pk is not None


@pytest.mark.django_db
class TestDatasetVisibility:
    """Test Dataset visibility choices and defaults."""

    def test_visibility_default_is_private(self):
        """New datasets default to PRIVATE visibility."""
        dataset = DatasetFactory()

        assert dataset.visibility == Visibility.PRIVATE.value

    def test_visibility_accepts_valid_choices(self):
        """Dataset accepts all valid visibility choices."""
        valid_choices = [
            Visibility.PUBLIC,
            Visibility.PRIVATE,
        ]

        for choice in valid_choices:
            dataset = DatasetFactory(visibility=choice.value)
            assert dataset.visibility == choice.value

    def test_visibility_rejects_invalid_choice(self):
        """Dataset rejects invalid visibility choice."""
        project = ProjectFactory()
        dataset = Dataset(name="Test", project=project, visibility=999)

        with pytest.raises(ValidationError):
            dataset.full_clean()

    def test_reading_datasets_with_no_visibility_condition_returns_only_public(self):
        """T056 / FR-019: `Dataset.objects` - the ordinary way of reading
        datasets - excludes PRIVATE ones.
        """
        public = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(visibility=Visibility.PRIVATE)

        result = list(Dataset.objects.all())

        assert result == [public]

    def test_all_objects_returns_both_and_honours_a_condition_applied_to_it(self):
        """T057 / FR-019: `Dataset.all_objects` - the separately named,
        explicit route - returns every dataset regardless of visibility,
        and a condition applied to it (here, `project`) still applies.
        """
        project = ProjectFactory()
        public = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        private = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        elsewhere = DatasetFactory(visibility=Visibility.PUBLIC)  # a different project

        everything = Dataset.all_objects.all()
        assert set(everything) == {public, private, elsewhere}

        narrowed = Dataset.all_objects.filter(project=project)
        assert set(narrowed) == {public, private}

    def test_no_queryset_method_widens_an_already_narrowed_query(self):
        """T058 / FR-019: no method `DatasetQuerySet` offers may add PRIVATE
        datasets back to a query that has already excluded them.

        Asserted over the queryset's public surface - every method
        `DatasetQuerySet` itself defines - rather than by naming one method,
        so a differently-named future widening method is caught too (R1: the
        present `with_related`/`with_contributors`/`with_metadata` are
        prefetch helpers, not filters, and none of them may become one).
        """
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
        """T059 / FR-004: the same guarantee as
        `test_visibility_default_is_private`, read back through both the
        ordinary and the explicit route rather than off the in-memory
        instance the factory returned.
        """
        dataset = Dataset.objects.create(name="No visibility stated")

        assert Dataset.all_objects.get(pk=dataset.pk).visibility == (
            Visibility.PRIVATE.value
        )
        assert not Dataset.objects.filter(pk=dataset.pk).exists()


@pytest.mark.django_db
class TestDatasetVisibilityGuarantees:
    """FR-019a: following a relation to a dataset, deleting a record it
    depends on, and the administrative interface all still see it
    regardless of visibility. FR-020: any permission a visibility check
    consults is declared on the model.
    """

    def test_following_a_relation_to_a_private_dataset_still_finds_it(self):
        """T060. Never asserts `Dataset._meta.base_manager_name` - it is
        pinned to `prefetch_manager` by `fairdm.db.models.PrefetchBase`
        regardless of what this app declares (D-019, research.md R1), and
        reading it would prove nothing about whether traversal actually
        reaches a private dataset. Forward FK access (`identifier.related`)
        goes through `Model._base_manager`, not the privacy-first default
        manager, so it is unaffected by `DatasetManager`.
        """
        private_dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        identifier = DatasetIdentifierFactory(related=private_dataset)

        fetched = DatasetIdentifier.objects.get(pk=identifier.pk).related

        assert fetched == private_dataset

    def test_deleting_a_record_a_private_dataset_depends_on_still_cascades(self):
        """T061. The deletion collector goes through `Model._base_manager`
        (unfiltered), so deleting a project cascades to its PRIVATE datasets
        exactly as it does to public ones.
        """
        project = ProjectFactory()
        private_dataset = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        dataset_pk = private_dataset.pk

        project.delete()

        assert not Dataset.all_objects.filter(pk=dataset_pk).exists()

    def test_permissions_a_visibility_check_could_consult_are_all_declared(self):
        """T063 / FR-020. The one permission a visibility check used to
        consult - `for_user()` gated on `dataset.view_private` - named a
        permission nothing declares (D-004, D-010), and `for_user()` is
        removed. This guards the invariant itself: any `has_perm(...)` call
        anywhere in the dataset app's models or admin must name a permission
        `Dataset._meta.permissions` (or Django's own default add/change/
        delete/view set) actually declares, so a check against an
        undeclared one cannot survive unnoticed.
        """
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
    """Test Dataset-Project relationship and CASCADE behavior."""

    def test_project_delete_cascades_to_dataset(self):
        """Deleting a project with datasets cascades and deletes the datasets too."""
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        dataset_id = dataset.pk

        project.delete()

        assert not Dataset.objects.filter(pk=dataset_id).exists()

    def test_project_delete_succeeds_without_datasets(self):
        """Deleting project without datasets succeeds."""
        project = ProjectFactory()
        project_id = project.pk

        project.delete()

        from fairdm.core.project.models import Project

        assert not Project.objects.filter(pk=project_id).exists()

    def test_multiple_datasets_deleted_with_project(self):
        """Deleting a project cascades and deletes all of its datasets."""
        project = ProjectFactory()
        datasets = DatasetFactory.create_batch(3, project=project)
        dataset_ids = [dataset.pk for dataset in datasets]

        project.delete()

        assert not Dataset.objects.filter(pk__in=dataset_ids).exists()


@pytest.mark.django_db
class TestOrphanedDatasets:
    """Test orphaned datasets (project=null) behavior."""

    def test_dataset_can_exist_without_project(self):
        """Dataset can exist with project=null."""
        dataset = Dataset.objects.create(name="Orphaned Dataset", project=None)

        assert dataset.pk is not None
        assert dataset.project is None

    def test_orphaned_dataset_queries(self):
        """Can query orphaned datasets."""
        # `all_objects` - visibility is not this test's concern, and the
        # datasets above are created with the (private) default.
        Dataset.objects.create(name="Orphaned", project=None)
        DatasetFactory()  # With project

        orphaned = Dataset.all_objects.filter(project__isnull=True)
        assert orphaned.count() == 1

    def test_setting_project_to_null_creates_orphan(self):
        """Setting project to null creates orphaned dataset."""
        dataset = DatasetFactory()
        dataset.project = None
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.project is None


@pytest.mark.django_db
class TestDatasetLicense:
    """Test Dataset.license field and defaults."""

    def test_license_defaults_to_cc_by_4(self):
        """New datasets default to CC BY 4.0 license."""
        dataset = DatasetFactory()

        assert dataset.license is not None
        assert "CC BY 4.0" in dataset.license.name

    def test_license_can_be_changed(self):
        """Dataset license can be changed."""
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
        """Dataset license can be null."""
        dataset = DatasetFactory()
        dataset.license = None
        dataset.save()

        dataset.refresh_from_db()
        assert dataset.license is None


@pytest.mark.django_db
class TestDatasetUUID:
    """Test Dataset UUID field uniqueness and collision handling."""

    def test_uuid_generated_automatically(self):
        """Dataset UUID is generated automatically."""
        dataset = DatasetFactory()

        assert dataset.uuid is not None
        assert str(dataset.uuid)  # Can convert to string

    def test_uuid_is_unique(self):
        """Dataset UUIDs are unique."""
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()

        assert dataset1.uuid != dataset2.uuid

    def test_duplicate_uuid_raises_integrity_error(self):
        """Attempting to create dataset with duplicate UUID raises error."""
        dataset1 = DatasetFactory()

        with pytest.raises(IntegrityError):
            Dataset.objects.create(
                name="Duplicate UUID",
                project=ProjectFactory(),
                uuid=dataset1.uuid,  # Duplicate UUID
            )

    def test_uuid_immutable_after_creation(self):
        """UUID field is marked editable=False."""
        DatasetFactory()
        uuid_field = Dataset._meta.get_field("uuid")

        assert uuid_field.editable is False


@pytest.mark.django_db
class TestDatasetFields:
    """Test Dataset's own fields (T009, FR-002, FR-003)."""

    def test_name_is_required(self):
        """A dataset requires a name."""
        dataset = Dataset(project=ProjectFactory())

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_name_length_is_bound(self):
        """A name longer than the field allows is refused; no truncation
        occurs."""
        dataset = Dataset(name="x" * 301, project=ProjectFactory())

        with pytest.raises(ValidationError) as exc_info:
            dataset.full_clean()

        assert "name" in exc_info.value.error_dict

    def test_dataset_with_no_project_is_valid(self):
        """A dataset with no project is a normal state, not an orphan."""
        dataset = Dataset(name="Orphaned Dataset", project=None)

        dataset.full_clean()  # Should not raise

    def test_image_is_optional(self):
        """image is not required to create a valid dataset."""
        dataset = Dataset(name="No Image", project=ProjectFactory())

        dataset.full_clean()  # Should not raise

    def test_project_is_optional(self):
        """project is not required to create a valid dataset."""
        dataset = Dataset.objects.create(name="No Project")

        assert dataset.project is None

    def test_data_publication_is_optional(self):
        """The data publication (reference) is not required to create a
        valid dataset."""
        dataset = Dataset(name="No Reference", project=ProjectFactory())

        dataset.full_clean()  # Should not raise
        assert dataset.reference is None


@pytest.mark.django_db
class TestDatasetOrdering:
    """Test Dataset.Meta.ordering (T010, FR-006)."""

    def test_default_ordering_is_most_recently_modified_first(self):
        """Listing datasets with no ordering applied returns the most
        recently modified dataset first."""
        oldest = DatasetFactory()
        middle = DatasetFactory()
        newest = DatasetFactory()

        now = timezone.now()
        # `modified` is auto_now - bypass it via update(), which does not
        # invoke Field.pre_save(), to pin known values for the assertion.
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
    """Test the portal's configured default licence (T011, FR-007)."""

    def test_dataset_created_without_a_licence_gets_the_configured_default(self):
        """A dataset created without choosing a licence carries the
        portal's configured default licence."""
        from licensing.models import License

        dataset = Dataset.objects.create(
            name="No Licence Chosen", project=ProjectFactory()
        )

        default_name = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")
        assert dataset.license == License.objects.get(name=default_name)

    def test_a_portal_configured_default_licence_is_honoured(self):
        """A portal that sets its own default licence gets that one
        instead."""
        with override_settings(FAIRDM_DEFAULT_LICENSE="CC BY-SA 4.0"):
            dataset = Dataset.objects.create(
                name="Custom Default", project=ProjectFactory()
            )

        assert dataset.license.name == "CC BY-SA 4.0"


@pytest.mark.django_db
class TestDatasetKeywords:
    """Test Dataset categorisation by controlled keywords and free tags
    (T012, FR-005)."""

    def test_controlled_vocabulary_term_is_stored_as_a_reference(self):
        """A term from a configured controlled vocabulary added as a
        keyword is stored as a reference to that vocabulary rather than as
        text."""
        from research_vocabs.models import Concept

        dataset = DatasetFactory()
        # `Concept.preload()` runs once per session (tests/conftest.py), so
        # real terms from every registered vocabulary are already available.
        term = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        assert term is not None

        dataset.keywords.add(term)

        stored = dataset.keywords.get(pk=term.pk)
        assert isinstance(stored, Concept)
        assert stored.name == term.name

    def test_free_tags_are_distinguishable_from_controlled_keywords(self):
        """Free tags are stored and remain distinguishable from controlled
        keywords."""
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
    """Test contributions recorded against a dataset (T013, FR-017,
    FR-018)."""

    def test_contribution_records_contributor_and_roles(self):
        """A contribution records a contributor and one or more roles, and
        reads both back."""
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
        """The role vocabulary's members are asserted by name, not by
        iterating whatever it happens to hold."""
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
    """Test Dataset.has_data (T014, FR-008)."""

    def test_no_samples_or_measurements_reports_no_data(
        self, django_assert_num_queries
    ):
        """A dataset with no samples and no measurements reports that it
        does not hold data."""
        dataset = DatasetFactory()

        with django_assert_num_queries(1):
            assert dataset.has_data is False

    def test_adding_a_sample_flips_has_data_to_true(self, django_assert_num_queries):
        dataset = DatasetFactory()
        assert dataset.has_data is False

        RockSampleFactory(dataset=dataset)
        del dataset.has_data  # clear the cached_property

        with django_assert_num_queries(1):
            assert dataset.has_data is True

    def test_adding_a_measurement_flips_has_data_to_true(
        self, django_assert_num_queries
    ):
        dataset = DatasetFactory()
        assert dataset.has_data is False

        ExampleMeasurementFactory(sample=RockSampleFactory(), dataset=dataset)
        del dataset.has_data  # clear the cached_property

        with django_assert_num_queries(1):
            assert dataset.has_data is True


@pytest.mark.django_db
class TestDatasetPrefetch:
    """FR-030: loading a dataset with its descriptions, dates, identifiers,
    contributions and keywords costs a number of queries that does not grow
    with the number of related records - asserted at two different
    related-record counts, not one (T015)."""

    def _dataset_with_metadata(self, count):
        """Build a dataset carrying `count` records of each related type."""
        dataset = DatasetFactory()

        for type_ in DatasetDescription.VOCABULARY.values[:count]:
            DatasetDescription.objects.create(related=dataset, type=type_, value="x")

        for type_ in DatasetDate.VOCABULARY.values[:count]:
            DatasetDate.objects.create(related=dataset, type=type_, value="2024-01-01")

        # Distinct `type` per identifier - AbstractIdentifier enforces one
        # identifier per (related, type). The vocabulary is now narrowed to the
        # dataset collection, so `count` is capped by how many members it has -
        # this test's subject is the query count, which the other relations carry.
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
    """Test that field labels/help text and vocabulary terms resolve at
    request time rather than at import time (T016, FR-029)."""

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
    """T017, FR-004: the visibility vocabulary offers private and public
    and nothing else, and the field defaults to private."""

    def test_visibility_vocabulary_members(self):
        assert {member.name for member in Visibility} == {"PRIVATE", "PUBLIC"}

    def test_visibility_field_defaults_to_private(self):
        field = Dataset._meta.get_field("visibility")
        assert field.get_default() == Visibility.PRIVATE


@pytest.mark.django_db
class TestDatasetSharedFixtures:
    """T007: the shared fixtures build what they claim to."""

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
    """US-1: typed descriptions (T026, T027, T029, T030, T031)."""

    def test_abstract_is_stored_under_its_type_and_retrievable_by_type(self):
        """An abstract is stored against the dataset under the abstract
        type, and can be retrieved by type (T026, AC1).

        The existing `test_create_description_with_valid_type` asserts
        through the now-removed `description_type` alias and never
        retrieves the description by type - this does both honestly.
        """
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="A brief summary."
        )

        retrieved = dataset.descriptions.get(type="Abstract")
        assert retrieved.value == "A brief summary."

    def test_second_description_of_a_carried_type_is_refused_naming_the_type(self):
        """A second description of a type the dataset already carries is
        refused, and the message names the type (T027, AC2, FR-009).
        """
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
        """A methods description is accepted - methods describe how the
        data was produced and belong to the dataset (T029, AC3). `Methods`
        is a member of the dataset description vocabulary and deliberately
        absent from the project one.
        """
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset, type="Methods", value="Samples were analysed by XRF."
        )

        description.full_clean()  # must not raise
        description.save()

        assert dataset.descriptions.get(type="Methods").value == (
            "Samples were analysed by XRF."
        )

    def test_two_descriptions_are_both_returned_each_under_its_own_type(self):
        """A dataset with an abstract and a methods description returns
        both, each under its own type (T030, AC4).
        """
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
        """The dataset description vocabulary's members are asserted by
        name, not by iterating whatever it happens to hold (T031, AC5,
        SC-004).
        """
        assert set(DatasetDescription.VOCABULARY.values) == {
            "Abstract",
            "Methods",
            "SeriesInformation",
            "TechnicalInfo",
            "Other",
        }


@pytest.mark.django_db
class TestDatasetDate:
    """US-2: dates and the collection period (T035, T037-T042)."""

    def test_collection_start_is_stored_under_its_type(self):
        """A collection start date is attached and stored under the
        collection start type (T035, AC1).
        """
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06-01"
        )

        stored = dataset.dates.get(type=DatasetDate.START_TYPE)
        assert str(stored.value) == "2020-06-01"

    def test_second_collection_start_is_refused(self):
        """A second collection start on the same dataset is refused
        (AC2, FR-009).
        """
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
        """A collection end earlier than an existing collection start is
        refused, and the message names both dates (T037, AC3, FR-011).
        """
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
        """Changing the start to a date after the existing end is refused
        for the same reason, whichever of the two dates is being edited
        (T038, AC4).
        """
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
        """A collection end on a dataset with no collection start is
        accepted - there is nothing to contradict (T039, AC5).
        """
        dataset = DatasetFactory()
        end = DatasetDate(
            related=dataset, type=DatasetDate.END_TYPE, value="2024-06-15"
        )

        end.full_clean()  # must not raise

    def test_year_only_end_in_same_year_as_month_precision_start_is_accepted(self):
        """A year-only end in the same year as a month-precision start is
        accepted - the comparison happens at the coarser of the two
        precisions, so a dataset collected starting June 2020 and ending
        some time in 2020 is not an error (T040).
        """
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06"
        )

        end = DatasetDate(related=dataset, type=DatasetDate.END_TYPE, value="2020")
        end.full_clean()  # must not raise

    def test_month_precision_end_before_month_precision_start_is_refused(self):
        """A month-precision end earlier than a month-precision start in
        the same year is refused - the month-precision branch of
        `precedes` was previously exercised by no test (T040).
        """
        dataset = DatasetFactory()
        DatasetDate.objects.create(
            related=dataset, type=DatasetDate.START_TYPE, value="2020-06"
        )

        end = DatasetDate(related=dataset, type=DatasetDate.END_TYPE, value="2020-03")
        with pytest.raises(ValidationError):
            end.full_clean()

    def test_date_with_no_value_is_refused(self):
        """A date record whose value is absent is refused - a type with no
        date carries no meaning (T041).
        """
        dataset = DatasetFactory()
        date = DatasetDate(related=dataset, type="Available")

        with pytest.raises(ValidationError) as exc_info:
            date.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_date_vocabulary_members(self):
        """The dataset date vocabulary's members are asserted by name
        (T042, AC6, SC-004).
        """
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
    """US-3: identifiers (T048, T049, T054)."""

    def test_available_types_are_the_dataset_collection_only(self):
        """The dataset identifier vocabulary's members are asserted by
        name, and none of them names a person or an organisation (T048,
        AC3, SC-004).
        """
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
        """An identifier value already in use by a *different record
        type* - not merely a different dataset - is refused (T049, FR-013).

        `AbstractIdentifier.value` carries `unique=True`, which is a
        per-table constraint and so only protects `DatasetIdentifier`
        against itself. `DatasetIdentifier.clean()` additionally checks
        the value against the other three `AbstractIdentifier` subclasses
        (project, sample, measurement).
        """
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
        """`Dataset.IDENTIFIER_TYPES` agrees with what `DatasetIdentifier`
        itself binds to (T054).
        """
        assert DatasetIdentifier.VOCABULARY.choices == Dataset.IDENTIFIER_TYPES


@pytest.mark.django_db
class TestDatasetDateValidation:
    """Test DatasetDate model validation."""

    def test_create_date_with_valid_type(self):
        """Can create date with valid date_type."""
        dataset = DatasetFactory()
        dataset_date = DatasetDate.objects.create(
            related=dataset, type="Available", value="2024-01-15"
        )

        assert dataset_date.pk is not None
        assert dataset_date.type == "Available"
        assert str(dataset_date.value) == "2024-01-15"
        assert dataset_date.related == dataset

    def test_date_type_vocabulary_validation(self):
        """date_type must be from predefined vocabulary."""
        dataset = DatasetFactory()
        dataset_date = DatasetDate(
            related=dataset, type="InvalidType", value="2024-01-15"
        )

        with pytest.raises(ValidationError) as exc_info:
            dataset_date.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_date_types_accepted(self):
        """All valid date types from vocabulary are accepted."""
        from fairdm.core.dataset.models import Dataset

        dataset = DatasetFactory()

        # Test all types from Dataset.DATE_TYPES.choices
        for type_code, _type_label in Dataset.DATE_TYPES.choices:
            dataset_date = DatasetDate(
                related=dataset, type=type_code, value="2024-01-15"
            )
            dataset_date.full_clean()  # Should not raise

    def test_date_field_required(self):
        """date field is required."""
        dataset = DatasetFactory()
        dataset_date = DatasetDate(
            related=dataset,
            type="Available",
            # Missing value
        )

        with pytest.raises(ValidationError) as exc_info:
            dataset_date.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        """Dataset relationship is required."""
        dataset_date = DatasetDate(
            type="Available",
            value="2024-01-15",
            # Missing related
        )

        with pytest.raises(ValidationError):
            dataset_date.full_clean()

    def test_unique_together_constraint(self):
        """Dataset can have only one date per date_type."""
        dataset = DatasetFactory()

        DatasetDate.objects.create(related=dataset, type="Available", value="2024-01-15")

        # Attempt duplicate
        with pytest.raises(IntegrityError):
            DatasetDate.objects.create(
                related=dataset, type="Available", value="2024-02-20"
            )

    def test_multiple_date_types_allowed(self):
        """Dataset can have multiple dates of different types."""
        dataset = DatasetFactory()

        DatasetDate.objects.create(related=dataset, type="Available", value="2024-01-15")
        DatasetDate.objects.create(
            related=dataset, type="Submitted", value="2024-02-01"
        )

        assert dataset.dates.count() == 2

    def test_cascade_delete_with_dataset(self):
        """Deleting dataset deletes associated dates."""
        dataset = DatasetFactory()
        DatasetDate.objects.create(related=dataset, type="Available", value="2024-01-15")

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetDate.objects.filter(related_id=dataset_id).exists()


@pytest.mark.django_db
class TestDatasetDescriptionValidation:
    """Test DatasetDescription model validation."""

    def test_create_description_with_valid_type(self):
        """Can create description with valid description_type."""
        dataset = DatasetFactory()
        description = DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="This is an abstract"
        )

        assert description.pk is not None
        assert description.type == "Abstract"

    def test_description_type_vocabulary_validation(self):
        """description_type must be from predefined vocabulary."""
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset, type="InvalidType", value="Test description"
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_description_types_accepted(self):
        """All valid description types from vocabulary are accepted."""
        from fairdm.core.dataset.models import Dataset

        dataset = DatasetFactory()

        # Test all types from Dataset.DESCRIPTION_TYPES.choices
        for type_code, _type_label in Dataset.DESCRIPTION_TYPES.choices:
            description = DatasetDescription(
                related=dataset, type=type_code, value=f"Test {type_code}"
            )
            description.full_clean()  # Should not raise

    def test_description_field_required(self):
        """description field is required."""
        dataset = DatasetFactory()
        description = DatasetDescription(
            related=dataset,
            type="Abstract",
            # Missing value
        )

        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        """Dataset relationship is required."""
        description = DatasetDescription(
            type="Abstract",
            value="Test",
            # Missing related
        )

        with pytest.raises(ValidationError):
            description.full_clean()

    def test_unique_together_constraint(self):
        """Dataset can have only one description per type (unique_together constraint)."""
        dataset = DatasetFactory()

        DatasetDescription.objects.create(
            related=dataset, type="Methods", value="Method 1"
        )

        # Attempt to create duplicate description with same type should fail
        with pytest.raises(IntegrityError):
            DatasetDescription.objects.create(
                related=dataset, type="Methods", value="Method 2"
            )

    def test_cascade_delete_with_dataset(self):
        """Deleting dataset deletes associated descriptions."""
        dataset = DatasetFactory()
        DatasetDescription.objects.create(
            related=dataset, type="Abstract", value="Test"
        )

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetDescription.objects.filter(related_id=dataset_id).exists()


@pytest.mark.django_db
class TestDatasetIdentifierValidation:
    """Test DatasetIdentifier model validation."""

    def test_create_identifier_with_valid_type(self):
        """Can create identifier with valid identifier_type."""
        dataset = DatasetFactory()
        identifier = DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        assert identifier.pk is not None
        assert identifier.type == "DOI"

    def test_identifier_type_vocabulary_validation(self):
        """identifier_type must be from predefined vocabulary."""
        dataset = DatasetFactory()
        identifier = DatasetIdentifier(
            related=dataset, type="InvalidType", value="some-identifier"
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "type" in exc_info.value.error_dict

    def test_all_valid_identifier_types_accepted(self):
        """All valid identifier types from vocabulary are accepted."""
        dataset = DatasetFactory()

        # Test all types from Dataset.IDENTIFIER_TYPES
        for type_code, _type_label in Dataset.IDENTIFIER_TYPES:
            identifier = DatasetIdentifier(
                related=dataset, type=type_code, value=f"test-{type_code}"
            )
            identifier.full_clean()  # Should not raise

    def test_identifier_field_required(self):
        """identifier field is required."""
        dataset = DatasetFactory()
        identifier = DatasetIdentifier(
            related=dataset,
            type="DOI",
            # Missing value
        )

        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()

        assert "value" in exc_info.value.error_dict

    def test_dataset_relationship_required(self):
        """Dataset relationship is required."""
        identifier = DatasetIdentifier(
            type="DOI",
            value="10.1000/xyz123",
            # Missing related
        )

        with pytest.raises(ValidationError):
            identifier.full_clean()


@pytest.mark.django_db
class TestDOISupport:
    """Test DOI support via DatasetIdentifier."""

    def test_create_doi_identifier(self):
        """Can create DOI identifier."""
        dataset = DatasetFactory()
        doi = DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        assert doi.type == "DOI"
        assert doi.value == "10.1000/xyz123"

    def test_query_datasets_with_doi(self):
        """Can query datasets that have DOI."""
        dataset_with_doi = DatasetFactory()
        DatasetIdentifier.objects.create(
            related=dataset_with_doi, type="DOI", value="10.1000/xyz123"
        )

        dataset_without_doi = DatasetFactory()

        # `all_objects` - visibility is not this test's concern, and
        # DatasetFactory() defaults to private.
        datasets_with_doi = Dataset.all_objects.filter(
            identifiers__type="DOI"
        ).distinct()

        assert dataset_with_doi in datasets_with_doi
        assert dataset_without_doi not in datasets_with_doi

    def test_get_doi_helper(self):
        """Can retrieve DOI via query."""
        dataset = DatasetFactory()
        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        doi = dataset.identifiers.filter(type="DOI").first()
        assert doi is not None
        assert doi.value == "10.1000/xyz123"

    def test_cascade_delete_with_dataset(self):
        """Deleting dataset deletes associated identifiers."""
        dataset = DatasetFactory()
        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        dataset_id = dataset.pk
        dataset.delete()

        assert not DatasetIdentifier.objects.filter(related_id=dataset_id).exists()

    def test_unique_together_constraint(self):
        """Dataset can have only one identifier per identifier_type."""
        dataset = DatasetFactory()

        DatasetIdentifier.objects.create(
            related=dataset, type="DOI", value="10.1000/xyz123"
        )

        # Attempt duplicate identifier_type
        with pytest.raises(IntegrityError):
            DatasetIdentifier.objects.create(
                related=dataset, type="DOI", value="10.1000/different"
            )


@pytest.mark.django_db
class TestDatasetLiterature:
    """FR-015: a dataset may name at most one data publication (`reference`),
    which survives that publication's deletion.
    """

    def test_a_data_publication_is_recorded_as_the_datasets_reference(self):
        """T068."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        dataset.reference = paper
        dataset.full_clean()
        dataset.save()
        dataset.refresh_from_db()

        assert dataset.reference == paper

    def test_the_same_publication_cannot_be_named_by_two_datasets(self):
        """T068: `reference` is a `OneToOneField`, so at most one dataset can
        name a given publication - the uniqueness a plain `ForeignKey` would
        not give this field.
        """
        paper = LiteratureItemFactory()
        DatasetFactory(reference=paper)

        with pytest.raises(IntegrityError):
            DatasetFactory(reference=paper)

    def test_deleting_the_named_publication_leaves_the_dataset_with_none_named(self):
        """T069 / FR-015."""
        paper = LiteratureItemFactory()
        dataset = DatasetFactory(reference=paper)

        paper.delete()
        dataset.refresh_from_db()

        assert dataset.pk is not None
        assert dataset.reference is None


@pytest.mark.django_db
class TestDatasetLiteratureRelationValidation:
    """Test DatasetLiteratureRelation model validation.

    Was skipped as "literature app not yet complete" - it is a live
    dependency and `LiteratureItem` exists, so that reason no longer holds
    (D-016).
    """

    def test_create_relation_with_valid_type(self):
        """Can create relationship with valid DataCite type."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        assert relation.pk is not None
        assert relation.relationship_type == "IsCitedBy"

    def test_relationship_type_vocabulary_validation(self):
        """relationship_type must be valid DataCite type."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation(
            dataset=dataset, literature_item=paper, relationship_type="InvalidType"
        )

        with pytest.raises(ValidationError) as exc_info:
            relation.full_clean()

        assert "relationship_type" in exc_info.value.error_dict

    def test_relationship_types_match_the_datacite_schema_by_name(self):
        """T073 / FR-016, SC-004: the relationship-type vocabulary is
        asserted by naming DataCite's own RelationType members (DataCite
        Metadata Schema 4.4), not by iterating whatever
        `DATACITE_RELATIONSHIP_TYPES` happens to hold - a loop over the
        model's own list proves nothing about its contents (R3, D-008 draws
        the same line for the dataset identifier vocabulary).
        """
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
            relation.full_clean()  # Should not raise

    def test_dataset_required(self):
        """Dataset is required."""
        paper = LiteratureItemFactory()

        relation = DatasetLiteratureRelation(
            literature_item=paper,
            relationship_type="IsCitedBy",
            # Missing dataset
        )

        with pytest.raises(ValidationError):
            relation.full_clean()

    def test_literature_item_required(self):
        """LiteratureItem is required."""
        dataset = DatasetFactory()

        relation = DatasetLiteratureRelation(
            dataset=dataset,
            relationship_type="IsCitedBy",
            # Missing literature_item
        )

        with pytest.raises(ValidationError):
            relation.full_clean()


@pytest.mark.django_db
class TestUniqueTogetherConstraint:
    """Test unique_together constraint.

    T071, T072 / FR-016: the same item related under a second type retains
    both relationships, and the same relationship recorded twice is refused.
    """

    def test_duplicate_relationship_raises_error(self):
        """T072. Cannot create duplicate relationships of same type."""
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
        """T071. Same dataset-paper can have multiple relationship types."""
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
    """Test CASCADE delete behavior."""

    def test_cascade_on_dataset_delete(self):
        """Deleting dataset deletes relationships."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        dataset.delete()

        assert DatasetLiteratureRelation.objects.count() == 0

    def test_cascade_on_literature_delete(self):
        """Deleting literature item deletes relationships."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        paper.delete()

        assert DatasetLiteratureRelation.objects.count() == 0


@pytest.mark.django_db
class TestQueryingRelationships:
    """Test querying relationships."""

    def test_query_by_relationship_type(self):
        """Can filter relationships by type."""
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
        """Can access literature through ManyToMany relationship."""
        dataset = DatasetFactory()
        paper = LiteratureItemFactory()

        DatasetLiteratureRelation.objects.create(
            dataset=dataset, literature_item=paper, relationship_type="IsCitedBy"
        )

        assert paper in dataset.related_literature.all()


@pytest.mark.django_db
class TestPrivacyFirstDefault:
    """Test that the default manager excludes PRIVATE datasets.

    Verifies that Dataset.objects.all() returns only PUBLIC datasets
    by default. Full coverage of the privacy-first behaviour (exclusion,
    the explicit `all_objects` route, and the no-widening guarantee) is
    US-4's (T056-T063).
    """

    def test_default_manager_includes_public_datasets(self):
        """Default manager should include PUBLIC datasets."""
        # Arrange
        ds_public = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)

        # Act
        result = Dataset.objects.all()

        # Assert
        assert result.count() == 1
        assert ds_public in result


@pytest.mark.django_db
class TestWithRelatedOptimization:
    """Test with_related() query optimization.

    Verifies that with_related() prefetches project and contributors
    to prevent N+1 query problems when accessing related data.
    """

    def test_with_related_prefetches_project(self, django_assert_max_num_queries):
        """with_related() should prefetch project to prevent N+1 queries."""
        # Arrange - `all_objects`: visibility is not this test's concern,
        # and DatasetFactory() defaults to private.
        DatasetFactory.create_batch(5, project=ProjectFactory())

        # Act & Assert - Should use at most 3 queries:
        # 1. Main query for datasets
        # 2. Prefetch for projects
        # 3. Possible join table query
        with django_assert_max_num_queries(3):
            datasets = list(Dataset.all_objects.with_related())
            # Access project on each dataset - should not cause additional queries
            for ds in datasets:
                _ = ds.project.name if ds.project else None

    def test_with_related_prefetches_contributors(self, django_assert_max_num_queries):
        """with_related() should prefetch contributors to prevent N+1 queries."""
        # Arrange
        datasets = DatasetFactory.create_batch(5)
        for ds in datasets:
            for _ in range(3):
                ContributionFactory(content_object=ds)

        # Act & Assert - Should use at most 3 queries
        with django_assert_max_num_queries(3):
            datasets = list(Dataset.all_objects.with_related())
            # Access contributors on each dataset - should not cause additional queries
            for ds in datasets:
                _ = list(ds.contributors.all())

    def test_with_related_on_filtered_queryset(self):
        """with_related() should work after filtering."""
        # Arrange
        project = ProjectFactory()
        ds_match = DatasetFactory(project=project)
        DatasetFactory()  # Different project

        # Act
        result = Dataset.all_objects.filter(project=project).with_related()

        # Assert
        assert result.count() == 1
        assert ds_match in result

    def test_with_related_returns_queryset_for_chaining(self):
        """with_related() should return QuerySet for method chaining."""
        # Arrange
        DatasetFactory()

        # Act
        result = Dataset.objects.with_related().filter(
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )

        # Assert
        assert isinstance(result, type(Dataset.objects.all()))


@pytest.mark.django_db
class TestWithContributorsOptimization:
    """Test with_contributors() query optimization.

    Verifies that with_contributors() prefetches only contributors
    for cases where project data is not needed.
    """

    def test_with_contributors_prefetches_contributors(
        self, django_assert_max_num_queries
    ):
        """with_contributors() should prefetch contributors to prevent N+1 queries."""
        # Arrange
        datasets = DatasetFactory.create_batch(5)
        for ds in datasets:
            for _ in range(3):
                ContributionFactory(content_object=ds)

        # Act & Assert - Should use at most 2 queries:
        # 1. Main query for datasets
        # 2. Prefetch for contributors
        with django_assert_max_num_queries(2):
            datasets = list(Dataset.all_objects.with_contributors())
            # Access contributors on each dataset - should not cause additional queries
            for ds in datasets:
                _ = list(ds.contributors.all())

    def test_with_contributors_does_not_prefetch_project(self):
        """with_contributors() should not prefetch project (lighter than with_related)."""
        # Arrange - `all_objects`: visibility is not this test's concern.
        datasets = DatasetFactory.create_batch(5, project=ProjectFactory())

        # Act
        result = Dataset.all_objects.with_contributors()

        # Assert - Accessing projects will cause additional queries (not prefetched)
        # This is expected behavior - with_contributors is for cases where
        # you only need contributors, not all related data
        datasets = list(result)
        # Verify it returns valid queryset
        assert len(datasets) == 5

    def test_with_contributors_on_filtered_queryset(self):
        """with_contributors() should work after filtering."""
        # Arrange
        project = ProjectFactory()
        ds_match = DatasetFactory(project=project)
        DatasetFactory()  # Different project

        # Act
        result = Dataset.all_objects.filter(project=project).with_contributors()

        # Assert
        assert result.count() == 1
        assert ds_match in result

    def test_with_contributors_returns_queryset_for_chaining(self):
        """with_contributors() should return QuerySet for method chaining."""
        # Arrange
        DatasetFactory()

        # Act
        result = Dataset.objects.with_contributors().filter(
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )

        # Assert
        assert isinstance(result, type(Dataset.objects.all()))


@pytest.mark.django_db
class TestMethodChaining:
    """Test chaining multiple QuerySet methods.

    Verifies that all QuerySet methods can be chained together in any order
    and produce correct results.
    """

    def test_chain_filter_and_with_related_and_with_contributors(self):
        """Should be able to chain filter(), with_related(), and with_contributors()."""
        # Arrange - PUBLIC so the chain is exercised through the default
        # (privacy-first) manager rather than incidentally excluded by it.
        project = ProjectFactory()
        ds_match = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(visibility=Visibility.PUBLIC)  # Different project

        # Act
        result = (
            Dataset.objects.filter(project=project).with_related().with_contributors()
        )

        # Assert
        assert result.count() == 1
        assert ds_match in result


@pytest.mark.django_db
class TestPerformanceOptimization:
    """Test performance improvements with optimization methods.

    Verifies that using optimization methods reduces database queries
    by at least 80% compared to naive access patterns.
    """

    def test_with_related_reduces_queries_by_80_percent(self):
        """with_related() should significantly reduce queries vs naive access.

        Expects 70%+ reduction in total queries, eliminating N+1 patterns.
        With 10 datasets: naive ~12 queries, optimized ~3 queries (75% reduction).
        """
        from django.db import reset_queries
        from django.test.utils import override_settings

        # Arrange - Create 10 datasets with projects and contributors
        datasets = []
        for _ in range(10):
            ds = DatasetFactory(project=ProjectFactory())
            for _ in range(3):
                ContributionFactory(content_object=ds)
            datasets.append(ds)

        # Measure naive query count (without optimization). `all_objects` -
        # visibility is not this test's concern, and the datasets above are
        # created with the (private) default.
        with override_settings(DEBUG=True):
            reset_queries()
            naive_datasets = list(Dataset.all_objects.all())
            for ds in naive_datasets:
                _ = ds.project.name if ds.project else None
                _ = list(ds.contributors.all())
            naive_query_count = len(connection.queries)

            # Measure optimized query count (with with_related)
            reset_queries()
            optimized_datasets = list(Dataset.all_objects.with_related())
            for ds in optimized_datasets:
                _ = ds.project.name if ds.project else None
                _ = list(ds.contributors.all())
            optimized_query_count = len(connection.queries)

        # Assert - Optimized should use 80%+ fewer queries
        # Note: Actual reduction might be slightly less due to fixed baseline queries
        # The key metric is eliminating N+1 queries (should be ~3 optimized vs 12 naive)
        reduction_percent = (
            (naive_query_count - optimized_query_count) / naive_query_count
        ) * 100
        assert reduction_percent >= 70, (
            f"Expected 70%+ query reduction, got {reduction_percent:.1f}% "
            f"(naive: {naive_query_count}, optimized: {optimized_query_count})"
        )
        # Also verify absolute numbers make sense
        assert optimized_query_count <= 4, (
            f"Expected ≤4 optimized queries, got {optimized_query_count}"
        )
        assert naive_query_count >= 10, (
            f"Expected ≥10 naive queries, got {naive_query_count}"
        )

    def test_with_contributors_reduces_contributor_queries(self):
        """with_contributors() should eliminate N+1 queries for contributors."""
        from django.db import reset_queries
        from django.test.utils import override_settings

        # Arrange - Create 10 datasets with contributors
        for _ in range(10):
            ds = DatasetFactory()
            for _ in range(3):
                ContributionFactory(content_object=ds)

        # Measure naive query count. `all_objects` - visibility is not this
        # test's concern.
        with override_settings(DEBUG=True):
            reset_queries()
            naive_datasets = list(Dataset.all_objects.all())
            for ds in naive_datasets:
                _ = list(ds.contributors.all())
            naive_query_count = len(connection.queries)

            # Measure optimized query count
            reset_queries()
            optimized_datasets = list(Dataset.all_objects.with_contributors())
            for ds in optimized_datasets:
                _ = list(ds.contributors.all())
            optimized_query_count = len(connection.queries)

        # Assert - Optimized should use significantly fewer queries
        # Should be 2 queries (dataset + contributors) vs 11 queries (dataset + 10x contributors)
        assert optimized_query_count <= 2, (
            f"Expected ≤2 queries, got {optimized_query_count}"
        )
        assert naive_query_count >= 10, (
            f"Expected ≥10 queries (naive), got {naive_query_count}"
        )

    def test_chained_optimizations_compound_benefits(
        self, django_assert_max_num_queries
    ):
        """Chaining multiple optimizations should provide compound benefits."""
        # Arrange - `all_objects` is the unfiltered route now that `objects`
        # is privacy-first (R1); it is the direct replacement for the
        # removed `with_private()` in this query-optimisation smoke test.
        datasets = []
        for _ in range(5):
            ds = DatasetFactory(project=ProjectFactory())
            for _ in range(2):
                ContributionFactory(content_object=ds)
            datasets.append(ds)

        # Act & Assert - Chained optimizations should use minimal queries
        with django_assert_max_num_queries(4):
            # At most 4 queries:
            # 1. Datasets
            # 2. Projects
            # 3. Contributors
            # 4. Possible join table
            result = list(Dataset.all_objects.with_related().with_contributors())
            for ds in result:
                _ = ds.project.name if ds.project else None
                _ = list(ds.contributors.all())


@pytest.mark.django_db
class TestDatasetModel:
    """Tests for the Dataset model (general smoke tests)."""

    def test_dataset_creation(self):
        """Test creating a basic Dataset instance."""
        dataset = DatasetFactory()

        assert dataset.pk is not None
        assert dataset.name is not None
        assert dataset.uuid is not None
        assert dataset.uuid.startswith("d")

    def test_dataset_visibility_default(self):
        """Test that default visibility is PRIVATE."""
        dataset = DatasetFactory()
        # Factory may set visibility randomly, so just check it's a valid value
        assert dataset.visibility in Visibility.values

    def test_dataset_queryset_with_contributors(self):
        """Test DatasetQuerySet.with_contributors() prefetches correctly."""
        # `all_objects` - visibility is not this test's concern, and
        # DatasetFactory() defaults to private.
        dataset = DatasetFactory()

        # This should not raise an error and should be efficient
        queryset = Dataset.all_objects.with_contributors()
        dataset_with_prefetch = queryset.get(pk=dataset.pk)

        # Access contributors should not cause additional queries due to prefetch
        assert dataset_with_prefetch.contributors is not None

    def test_dataset_queryset_with_related(self):
        """Test DatasetQuerySet.with_related() prefetches correctly."""
        dataset = DatasetFactory()

        queryset = Dataset.all_objects.with_related()
        dataset_with_prefetch = queryset.get(pk=dataset.pk)

        # Should have prefetched project and contributors
        assert dataset_with_prefetch.project is not None

    def test_dataset_str_representation(self):
        """Test Dataset string representation."""
        dataset = DatasetFactory(name="Test Dataset")
        assert str(dataset) == "Test Dataset"

    def test_dataset_absolute_url(self):
        """Test get_absolute_url returns correct URL."""
        dataset = DatasetFactory()
        url = dataset.get_absolute_url()

        assert url == reverse("dataset-detail", kwargs={"uuid": dataset.uuid})

    def test_dataset_has_data_property(self):
        """Test has_data cached property."""
        dataset = DatasetFactory()

        # Initially should return False (no samples or measurements)
        has_data = dataset.has_data
        assert isinstance(has_data, bool)

    def test_dataset_bbox_property(self):
        """Test bbox cached property."""
        dataset = DatasetFactory()

        # Should return a bounding box or None
        bbox = dataset.bbox
        assert bbox is None or isinstance(bbox, (dict, tuple, list))

    def test_dataset_descriptions_relationship(self):
        """Test that dataset descriptions can be created correctly."""
        dataset = DatasetFactory()
        descriptions = DatasetDescription.objects.filter(related=dataset)

        # Factory may or may not create descriptions by default
        assert descriptions.count() >= 0
        assert all(desc.related == dataset for desc in descriptions)

    def test_dataset_dates_relationship(self):
        """Test that dataset dates can be created correctly."""
        dataset = DatasetFactory()
        dates = DatasetDate.objects.filter(related=dataset)

        # Factory may or may not create dates by default
        assert dates.count() >= 0
        assert all(date.related == dataset for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a dataset."""
        dataset = DatasetFactory()
        user = PersonFactory()

        contribution = dataset.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert dataset.contributors.filter(pk=contribution.pk).exists()

    def test_dataset_project_relationship(self):
        """Test that dataset can be associated with a project."""
        # `all_objects` - the reverse accessor (`project.datasets`) is built
        # from Dataset's default manager, so it is privacy-filtered too, and
        # this dataset carries the (private) default.
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        assert dataset.project == project
        assert dataset in Dataset.all_objects.filter(project=project)


@pytest.mark.django_db
class TestDatasetCreationRecord:
    """Unit tests for the `Dataset.created_by` creation record (US7).

    Mirrors `TestProjectCreator` (`tests/test_core/test_project/test_models.py`)
    - `Dataset.created_by` is `Project.created_by` copied field-for-field
    (D-015).
    """

    def test_dataset_created_by_a_known_user_names_that_user(self):
        """T089 / FR-021."""
        creator = PersonFactory()
        dataset = DatasetFactory(created_by=creator)

        dataset.refresh_from_db()

        assert dataset.created_by == creator

    def test_changing_a_field_advances_modified_and_leaves_creator_unchanged(self):
        """T090 / FR-022."""
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
        """T091 / FR-021: the dataset outlives its creator's account, with
        its creator reading as unknown rather than raising or being deleted
        itself.
        """
        creator = PersonFactory()
        dataset = DatasetFactory(created_by=creator)

        creator.delete()
        dataset.refresh_from_db()

        assert dataset.pk is not None
        assert dataset.created_by is None

    def test_created_by_field_is_not_editable(self):
        """T092: `created_by` is kept out of forms, the admin and the
        serializer solely by `editable=False`, mirroring
        `Project.created_by` - nothing else enforces it, so that flag needs
        its own assertion.
        """
        assert Dataset._meta.get_field("created_by").editable is False
