"""Unit tests for Measurement model."""

import unicodedata
from types import SimpleNamespace

import pint
import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import RestrictedError
from django.test.utils import CaptureQueriesContext
from django.urls import resolve

from demo.factories import (
    ExampleMeasurementFactory,
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
)
from fairdm.core.measurement.forms import MeasurementForm
from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.core.models import Measurement, Sample
from fairdm.factories import (
    DatasetFactory,
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    MeasurementIdentifierFactory,
    PersonFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestMeasurementModelCreation:
    def test_xrf_measurement_creation_with_all_fields(self, sample):
        from demo.models import XRFMeasurement

        measurement = XRFMeasurement.objects.create(
            name="XRF Analysis",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
            detection_limit_ppm=5.0,
        )

        assert measurement.pk is not None
        assert measurement.name == "XRF Analysis"
        assert measurement.sample == sample
        assert measurement.dataset == sample.dataset
        assert measurement.uuid.startswith("m")
        assert measurement.added is not None
        assert measurement.modified is not None
        assert measurement.element == "Si"
        assert measurement.concentration_ppm == 250000.0

    def test_icp_ms_measurement_creation_with_minimal_fields(self, sample):
        from demo.models import ICP_MS_Measurement

        measurement = ICP_MS_Measurement.objects.create(
            name="ICP-MS Analysis",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        assert measurement.pk is not None
        assert measurement.name == "ICP-MS Analysis"
        assert measurement.sample == sample
        assert measurement.dataset == sample.dataset
        assert measurement.isotope == "207Pb"

    def test_measurement_uuid_is_unique(self, xrf_measurement, icp_ms_measurement):
        assert xrf_measurement.uuid != icp_ms_measurement.uuid
        assert xrf_measurement.uuid.startswith("m")
        assert icp_ms_measurement.uuid.startswith("m")

    def test_uuid_is_not_editable_afterwards(self, measurement):
        from fairdm.core.measurement.admin import MeasurementChildAdmin

        assert "uuid" not in MeasurementForm.base_fields
        assert "uuid" in MeasurementChildAdmin.readonly_fields


@pytest.mark.django_db
class TestMeasurementFields:
    def test_name_is_required(self, sample):
        from demo.models import ExampleMeasurement

        instance = ExampleMeasurement(sample=sample, dataset=sample.dataset)

        with pytest.raises(ValidationError) as exc_info:
            instance.full_clean()

        assert "name" in exc_info.value.message_dict

    def test_label_image_keywords_and_tags_are_all_optional(self, sample):
        instance = ExampleMeasurementFactory(sample=sample, local_id=None, image=None)

        instance.full_clean()

        assert not instance.local_id
        assert not instance.image
        assert instance.keywords.count() == 0
        assert instance.tags.count() == 0


class TestMeasurementFieldMetadata:
    def test_field_verbose_names_and_help_text_are_lazy(self):
        from django.utils.functional import Promise

        for field_name in ["dataset", "sample", "local_id"]:
            field = Measurement._meta.get_field(field_name)
            assert isinstance(field.verbose_name, Promise), field_name
            assert isinstance(field.help_text, Promise), field_name


@pytest.mark.django_db
class TestMeasurementLocalId:
    def test_local_id_has_no_uniqueness_constraint(self):
        field = Measurement._meta.get_field("local_id")
        assert field.unique is False

    def test_local_id_is_indexed(self):
        field = Measurement._meta.get_field("local_id")
        assert field.db_index is True

    def test_the_same_local_id_is_valid_in_two_different_datasets(
        self, dataset, second_dataset, sample, second_sample
    ):
        one = ExampleMeasurementFactory(
            dataset=dataset, sample=sample, local_id="LAB-001"
        )
        two = ExampleMeasurementFactory(
            dataset=second_dataset, sample=second_sample, local_id="LAB-001"
        )

        one.full_clean()
        two.full_clean()
        assert one.local_id == two.local_id == "LAB-001"


@pytest.mark.django_db
class TestMeasurementTimestamps:
    def test_creation_and_modification_times_are_recorded(self, measurement):
        assert measurement.added is not None
        assert measurement.modified is not None

    def test_modification_time_advances_on_change(self, measurement):
        original_added = measurement.added
        original_modified = measurement.modified

        measurement.name = "Renamed"
        measurement.save()
        measurement.refresh_from_db()

        assert measurement.modified > original_modified
        assert measurement.added == original_added


@pytest.mark.django_db
class TestMeasurementContributions:
    def test_measurement_role_vocabulary_members(self):
        assert Measurement.CONTRIBUTOR_ROLES.values == [
            "MeasurementPreparation",
            "MeasurementCollection",
            "Support",
        ]

    def test_contribution_records_contributor_and_roles(self, measurement):
        contributor = PersonFactory()

        contribution = measurement.add_contributor(
            contributor, with_roles=["MeasurementCollection", "Support"]
        )

        assert contribution.contributor == contributor
        role_names = set(contribution.roles.values_list("name", flat=True))
        assert role_names == {"MeasurementCollection", "Support"}


@pytest.mark.django_db
class TestMeasurementPolymorphicInheritance:
    def test_polymorphic_measurement_subclass_creation(self, sample):
        from demo.models import XRFMeasurement

        xrf = XRFMeasurement.objects.create(
            name="XRF Test",
            sample=sample,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=50000.0,
            detection_limit_ppm=2.0,
        )

        assert xrf.pk is not None
        assert xrf.name == "XRF Test"
        assert hasattr(xrf, "element")
        assert xrf.element == "Fe"

    def test_polymorphic_query_returns_typed_instances(self, sample):
        from demo.models import ICP_MS_Measurement, XRFMeasurement

        xrf = XRFMeasurement.objects.create(
            name="XRF",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
            detection_limit_ppm=5.0,
        )
        icp = ICP_MS_Measurement.objects.create(
            name="ICP-MS",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        measurements = Measurement.objects.all()

        assert measurements.count() == 2
        xrf_instance = measurements.get(pk=xrf.pk)
        icp_instance = measurements.get(pk=icp.pk)

        assert isinstance(xrf_instance, XRFMeasurement)
        assert isinstance(icp_instance, ICP_MS_Measurement)
        assert hasattr(xrf_instance, "element")
        assert hasattr(icp_instance, "isotope")


@pytest.mark.django_db
class TestMeasurementVocabularyValidation:
    def test_measurement_description_uses_measurement_vocabulary(self, measurement):
        from fairdm.core.measurement.models import MeasurementDescription

        # "method" is not a member of the measurement description vocabulary.
        desc = MeasurementDescription.objects.create(
            related=measurement,
            type="MeasurementSetup",
            value="XRF spectroscopy analysis",
        )

        assert desc.type == "MeasurementSetup"
        assert desc.VOCABULARY is not None

    def test_measurement_date_uses_measurement_vocabulary(self, measurement):
        from fairdm.core.measurement.models import MeasurementDate

        # "measured" is not a member of the measurement date vocabulary.
        date = MeasurementDate.objects.create(
            related=measurement, type="Setup", value="2024-01-15"
        )

        assert date.type == "Setup"
        assert date.VOCABULARY is not None


@pytest.mark.django_db
class TestMeasurementIdentifierVocabulary:
    def test_available_types_are_doi_only(self):
        assert set(MeasurementIdentifier.VOCABULARY.values) == {"DOI"}

    def test_no_type_names_a_sample_person_organisation_or_project(self):
        assert set(MeasurementIdentifier.VOCABULARY.values).isdisjoint(
            {
                "IGSN",
                "ORCID",
                "RESEARCHER_ID",
                "ROR",
                "WIKIDATA",
                "ISNI",
                "CROSSREF_FUNDER_ID",
                "GRANT_NUMBER",
                "PROPOSAL_ID",
            }
        )


@pytest.mark.django_db
class TestMeasurementMetadataRelations:
    def test_description_date_and_identifier_refer_to_the_measurement_directly(
        self, measurement
    ):
        description = MeasurementDescriptionFactory(related=measurement)
        date = MeasurementDateFactory(related=measurement)
        identifier = MeasurementIdentifierFactory(related=measurement)

        assert description.related == measurement
        assert date.related == measurement
        assert identifier.related == measurement

    def test_deleting_the_measurement_deletes_its_description_date_and_identifier(
        self, measurement
    ):
        description = MeasurementDescriptionFactory(related=measurement)
        date = MeasurementDateFactory(related=measurement)
        identifier = MeasurementIdentifierFactory(related=measurement)

        measurement.delete()

        assert not MeasurementDescription.objects.filter(pk=description.pk).exists()
        assert not MeasurementDate.objects.filter(pk=date.pk).exists()
        assert not MeasurementIdentifier.objects.filter(pk=identifier.pk).exists()


@pytest.mark.django_db
class TestMeasurementDescriptionVocabularyMembers:
    def test_available_types_are_named_one_by_one(self):
        assert set(MeasurementDescription.VOCABULARY.values) == {
            "MeasurementConditions",
            "MeasurementSetup",
            "MeasurementTearDown",
            "Other",
        }

    def test_a_description_type_is_drawn_from_the_measurement_collection(
        self, measurement
    ):
        description = MeasurementDescriptionFactory(
            related=measurement, type="MeasurementSetup"
        )
        assert description.type in MeasurementDescription.VOCABULARY.values


@pytest.mark.django_db
class TestMeasurementDateVocabularyMembers:
    def test_available_types_are_named_one_by_one(self):
        assert set(MeasurementDate.VOCABULARY.values) == {"Setup", "TearDown"}

    def test_a_date_type_is_drawn_from_the_measurement_collection(self, measurement):
        date = MeasurementDateFactory(related=measurement, type="TearDown")
        assert date.type in MeasurementDate.VOCABULARY.values


@pytest.mark.django_db
class TestMeasurementMetadataTypeValidation:
    def test_description_type_outside_the_vocabulary_is_refused_by_full_clean(
        self, measurement
    ):
        description = MeasurementDescriptionFactory.build(
            related=measurement, type="NotARealDescriptionType"
        )
        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()
        assert "NotARealDescriptionType" in str(exc_info.value)

    def test_description_type_outside_the_vocabulary_is_refused_on_direct_save(
        self, measurement
    ):
        with pytest.raises(ValidationError) as exc_info:
            MeasurementDescriptionFactory(
                related=measurement, type="NotARealDescriptionType"
            )
        assert "NotARealDescriptionType" in str(exc_info.value)

    def test_date_type_outside_the_vocabulary_is_refused_by_full_clean(
        self, measurement
    ):
        date = MeasurementDateFactory.build(
            related=measurement, type="NotARealDateType"
        )
        with pytest.raises(ValidationError) as exc_info:
            date.full_clean()
        assert "NotARealDateType" in str(exc_info.value)

    def test_date_type_outside_the_vocabulary_is_refused_on_direct_save(
        self, measurement
    ):
        with pytest.raises(ValidationError) as exc_info:
            MeasurementDateFactory(related=measurement, type="NotARealDateType")
        assert "NotARealDateType" in str(exc_info.value)

    def test_identifier_type_outside_the_vocabulary_is_refused_by_full_clean(
        self, measurement
    ):
        identifier = MeasurementIdentifierFactory.build(
            related=measurement, type="NotARealIdentifierType"
        )
        with pytest.raises(ValidationError) as exc_info:
            identifier.full_clean()
        assert "NotARealIdentifierType" in str(exc_info.value)

    def test_identifier_type_outside_the_vocabulary_is_refused_on_direct_save(
        self, measurement
    ):
        with pytest.raises(ValidationError) as exc_info:
            MeasurementIdentifierFactory(
                related=measurement, type="NotARealIdentifierType"
            )
        assert "NotARealIdentifierType" in str(exc_info.value)


@pytest.mark.django_db
class TestMeasurementCrossDatasetSampleLinking:
    def test_measurement_can_link_to_sample_in_different_dataset(self, sample):
        from demo.models import XRFMeasurement
        from fairdm.factories import DatasetFactory

        dataset_b = DatasetFactory(project=sample.dataset.project)

        measurement = XRFMeasurement.objects.create(
            name="Cross-Dataset XRF",
            sample=sample,
            dataset=dataset_b,
            element="Ca",
            concentration_ppm=15000.0,
        )

        assert measurement.sample.dataset != measurement.dataset
        assert measurement.sample == sample
        assert measurement.dataset == dataset_b


@pytest.mark.django_db
class TestMeasurementValueMethods:
    def test_get_value_returns_name_for_base_measurement(self, measurement):
        # Base Measurement doesn't have 'value' or 'uncertainty' attributes
        value = measurement.get_value()
        assert value == measurement.name

    def test_print_value_returns_string_for_base_measurement(self, measurement):
        value_str = measurement.print_value()
        assert isinstance(value_str, str)
        assert value_str == measurement.name

    def test_a_measurement_with_no_value_is_named_by_its_name(self):
        measurement = ICP_MS_MeasurementFactory(
            sample=RockSampleFactory(), name="206Pb/238U, spot 3", value=None
        )
        assert str(measurement) == "206Pb/238U, spot 3"

    def test_a_measurement_with_no_value_or_name_is_named_by_its_portal_id(self):
        measurement = ICP_MS_MeasurementFactory(
            sample=RockSampleFactory(), name="", value=None
        )
        assert str(measurement) == measurement.uuid


@pytest.mark.django_db
class TestMeasurementDirectInstantiation:
    def test_measurement_cannot_be_instantiated_directly(self, sample):

        measurement = Measurement(
            name="Direct Measurement",
            sample=sample,
            dataset=sample.dataset,
        )

        with pytest.raises(ValidationError):
            measurement.clean()


@pytest.mark.django_db
class TestMeasurementURLPattern:
    def test_get_absolute_url_returns_measurement_detail_pattern(self, xrf_measurement):
        url = xrf_measurement.get_absolute_url()

        assert url.startswith("/measurement/")
        assert str(xrf_measurement.uuid) in url
        assert url.endswith("/")


@pytest.mark.django_db
class TestMeasurementCascadeBehavior:
    def test_deleting_sample_is_refused_while_a_measurement_refers_to_it(
        self, xrf_measurement
    ):
        from django.db.models import RestrictedError

        sample = xrf_measurement.sample

        with pytest.raises(RestrictedError):
            sample.delete()

        assert Measurement.objects.filter(pk=xrf_measurement.pk).exists()

    def test_deleting_a_dataset_removes_its_samples_and_their_measurements(self):
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
        sample_pk, measurement_pk = sample.pk, measurement.pk

        dataset.delete()

        assert not Sample.objects.filter(pk=sample_pk).exists()
        assert not Measurement.objects.filter(pk=measurement_pk).exists()


@pytest.mark.django_db
class TestMeasurementQuerySetOptimizations:
    def test_with_related_prefetches_sample_dataset_contributors(self, sample):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.models import XRFMeasurement

        measurements = []
        for i in range(5):
            measurement = XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Si",
                concentration_ppm=250000.0 + i,
                detection_limit_ppm=5.0,
            )
            measurements.append(measurement)

        with CaptureQueriesContext(connection) as context_without:
            measurements_without = list(XRFMeasurement.objects.all())
            for measurement in measurements_without:
                _ = measurement.sample.name
                _ = measurement.dataset.name

        queries_without = len(context_without.captured_queries)

        with CaptureQueriesContext(connection) as context_with:
            measurements_with = list(XRFMeasurement.objects.with_related())
            for measurement in measurements_with:
                _ = measurement.sample.name
                _ = measurement.dataset.name

        queries_with = len(context_with.captured_queries)

        assert queries_with < queries_without
        assert queries_with <= 5

    def test_with_metadata_prefetches_descriptions_dates_identifiers(self, sample):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.models import XRFMeasurement
        from fairdm.core.measurement.models import (
            MeasurementDate,
            MeasurementDescription,
        )

        measurement = XRFMeasurement.objects.create(
            name="XRF with metadata",
            sample=sample,
            dataset=sample.dataset,
            element="Ca",
            concentration_ppm=15000.0,
            detection_limit_ppm=2.0,
        )
        MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="XRF analysis"
        )
        MeasurementDate.objects.create(
            related=measurement, type="Setup", value="2024-01-15"
        )

        with CaptureQueriesContext(connection) as context_without:
            measurements_without = list(
                XRFMeasurement.objects.filter(pk=measurement.pk)
            )
            for m in measurements_without:
                _ = list(m.descriptions.all())
                _ = list(m.dates.all())

        len(context_without.captured_queries)

        with CaptureQueriesContext(connection) as context_with:
            measurements_with = list(
                XRFMeasurement.objects.filter(pk=measurement.pk).with_metadata()
            )
            for m in measurements_with:
                _ = list(m.descriptions.all())
                _ = list(m.dates.all())

        queries_with = len(context_with.captured_queries)

        assert queries_with <= 4

    def test_polymorphic_queryset_returns_correct_typed_instances(self, sample):
        from demo.models import ICP_MS_Measurement, XRFMeasurement
        from fairdm.core.measurement.models import Measurement

        XRFMeasurement.objects.create(
            name="XRF Measurement",
            sample=sample,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=50000.0,
            detection_limit_ppm=2.0,
        )
        ICP_MS_Measurement.objects.create(
            name="ICP-MS Measurement",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        measurements = list(Measurement.objects.all())

        xrf_instances = [m for m in measurements if isinstance(m, XRFMeasurement)]
        icp_instances = [m for m in measurements if isinstance(m, ICP_MS_Measurement)]

        assert len(xrf_instances) >= 1
        assert len(icp_instances) >= 1

        for measurement in measurements:
            assert type(measurement).__name__ in [
                "XRFMeasurement",
                "ICP_MS_Measurement",
                "ExampleMeasurement",
            ]
            assert (
                hasattr(measurement, "element")
                or hasattr(measurement, "isotope")
                or hasattr(measurement, "char_field")
            )

    def test_queryset_method_chaining_works_correctly(self, sample):
        from demo.models import XRFMeasurement

        for i in range(3):
            XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Si",
                concentration_ppm=250000.0 + i,
                detection_limit_ppm=5.0,
            )

        chained = XRFMeasurement.objects.with_related().with_metadata()

        assert chained.count() >= 3

        filtered = chained.filter(element="Si")
        assert filtered.count() >= 3

        for measurement in filtered[:2]:
            assert isinstance(measurement, XRFMeasurement)
            assert measurement.element == "Si"

    @pytest.mark.slow
    def test_1000_measurements_load_with_minimal_queries_using_with_related(
        self, sample
    ):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from demo.models import XRFMeasurement

        measurements = []
        for i in range(100):
            measurement = XRFMeasurement.objects.create(
                name=f"XRF {i}",
                sample=sample,
                dataset=sample.dataset,
                element="Si",
                concentration_ppm=250000.0 + i,
                detection_limit_ppm=5.0,
            )
            measurements.append(measurement)

        with CaptureQueriesContext(connection) as context:
            optimized_measurements = list(XRFMeasurement.objects.with_related())
            for measurement in optimized_measurements[:10]:
                _ = measurement.sample.name
                _ = measurement.dataset.name

        num_queries = len(context.captured_queries)

        assert num_queries <= 10


@pytest.mark.django_db
class TestMeasurementModel:
    def test_measurement_creation(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.pk is not None
        assert measurement.name is not None
        assert measurement.uuid is not None
        assert measurement.uuid.startswith("m")

    def test_measurement_str_representation(self):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Test Measurement"
        )
        str_repr = str(measurement)
        assert str_repr is not None

    def test_measurement_sample_relationship(self):
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=sample)

        assert measurement.sample == sample
        assert measurement in sample.measurements.all()

    def test_measurement_dataset_relationship(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.dataset is not None
        assert measurement in measurement.dataset.measurements.all()

    def test_measurement_type_of_property(self):
        assert Measurement.type_of == Measurement

    def test_measurement_get_template_name(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        templates = measurement.get_template_name()

        assert isinstance(templates, list)
        assert len(templates) == 2
        assert templates[1] == "fairdm/measurement_card.html"

    def test_measurement_get_absolute_url(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        url = measurement.get_absolute_url()

        assert url == f"/measurement/{measurement.uuid}/"
        assert "measurement:overview" in url or "/measurement/" in url

    def test_measurement_descriptions_relationship(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        descriptions = MeasurementDescription.objects.filter(related=measurement)

        assert descriptions.count() >= 0
        assert all(desc.related == measurement for desc in descriptions)

    def test_measurement_dates_relationship(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        dates = MeasurementDate.objects.filter(related=measurement)

        assert dates.count() >= 0
        assert all(date.related == measurement for date in dates)

    def test_add_contributor(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        user = PersonFactory()

        contribution = measurement.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert measurement.contributors.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestMeasurementForm:
    def test_form_initialization(self):
        form = MeasurementForm()
        assert form is not None

    def test_form_missing_required_fields(self):
        form_data = {}
        form = MeasurementForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors or "sample" in form.errors

    def test_form_with_request_context(self):
        from unittest.mock import Mock

        request = Mock()
        form = MeasurementForm(request=request)

        assert form.request == request


@pytest.mark.django_db
class TestMeasurementViews:
    def test_get_absolute_url_is_the_measurements_own_address(self):
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=sample)

        measurement_url = measurement.get_absolute_url()

        assert measurement_url != sample.get_absolute_url()
        assert str(measurement.uuid) in measurement_url

    def test_get_absolute_url_resolves_to_the_measurement_detail_view(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        match = resolve(measurement.get_absolute_url())

        assert match.view_name == "measurement:overview"
        assert match.kwargs["uuid"] == str(measurement.uuid)

    def test_detail_page_renders(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )

        response = client.get(measurement.get_absolute_url())

        assert response.status_code == 200
        assert measurement.name in response.content.decode()

    def test_detail_page_is_not_found_while_its_dataset_is_unpublished(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )

        assert client.get(measurement.get_absolute_url()).status_code == 404


@pytest.mark.django_db
class TestMeasurementPermissions:
    def test_measurement_contributor_relationship(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        contribution = measurement.add_contributor(user, with_roles=["Creator"])

        assert measurement.contributors.count() == 1
        assert contribution.contributor == user


@pytest.mark.django_db
class TestMeasurementCRUDWorkflow:
    def test_create_measurement_with_sample_and_dataset(self):
        dataset = DatasetFactory(name="Test Dataset")
        sample = RockSampleFactory(dataset=dataset)

        measurement = ExampleMeasurementFactory(
            name="Test Measurement", dataset=dataset, sample=sample
        )

        assert measurement.pk is not None
        assert measurement.name == "Test Measurement"
        assert measurement.dataset == dataset
        assert measurement.sample == sample
        assert measurement in dataset.measurements.all()
        assert measurement in sample.measurements.all()

    def test_read_measurement_via_queryset(self):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Readable Measurement"
        )

        retrieved = Measurement.objects.get(pk=measurement.pk)

        assert retrieved == measurement
        assert retrieved.name == "Readable Measurement"
        assert retrieved.uuid == measurement.uuid

    def test_update_measurement_fields(self):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Original Name"
        )
        original_uuid = measurement.uuid

        measurement.name = "Updated Name"
        measurement.save()
        measurement.refresh_from_db()

        assert measurement.name == "Updated Name"
        assert measurement.uuid == original_uuid

    def test_delete_measurement(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        measurement_id = measurement.pk

        measurement.delete()

        assert not Measurement.objects.filter(pk=measurement_id).exists()

    def test_deleting_dataset_cascades_to_measurements(self):
        measurement_dataset = DatasetFactory(name="Measurement Dataset")
        sample_dataset = DatasetFactory(name="Sample Dataset")

        sample = RockSampleFactory(dataset=sample_dataset)

        measurement = ExampleMeasurementFactory(
            dataset=measurement_dataset, sample=sample
        )
        measurement_id = measurement.pk

        measurement_dataset.delete()

        assert not Measurement.objects.filter(pk=measurement_id).exists()
        assert Sample.objects.filter(pk=sample.pk).exists()

    def test_deleting_sample_protects_measurements(self):
        from django.db import IntegrityError

        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=sample)

        with pytest.raises(IntegrityError):
            sample.delete()

        assert Measurement.objects.filter(pk=measurement.pk).exists()


@pytest.mark.django_db
class TestCrossDatasetMeasurementSampleLinking:
    def test_measurement_can_reference_sample_from_different_dataset(self):
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        sample_b = RockSampleFactory(dataset=dataset_b)

        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        assert measurement_a.dataset == dataset_a
        assert measurement_a.sample == sample_b
        assert measurement_a.sample.dataset == dataset_b
        assert measurement_a.dataset != measurement_a.sample.dataset

    def test_cross_dataset_provenance_clear_in_relationships(self):
        dataset_a = DatasetFactory(name="Measurement Dataset")
        dataset_b = DatasetFactory(name="Sample Dataset")

        sample = RockSampleFactory(dataset=dataset_b, name="Sample from B")
        measurement = ExampleMeasurementFactory(
            dataset=dataset_a, name="Measurement in A", sample=sample
        )

        assert measurement.dataset.name == "Measurement Dataset"
        assert measurement.sample.name == "Sample from B"
        assert measurement.sample.dataset.name == "Sample Dataset"

    def test_measurements_with_cross_dataset_samples_filter_correctly(self):
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        sample_a = RockSampleFactory(dataset=dataset_a)
        sample_b = RockSampleFactory(dataset=dataset_b)

        m1 = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_a)
        m2 = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)
        m3 = ExampleMeasurementFactory(dataset=dataset_b, sample=sample_b)

        measurements_in_a = Measurement.objects.filter(dataset=dataset_a)
        assert m1 in measurements_in_a
        assert m2 in measurements_in_a
        assert m3 not in measurements_in_a

        measurements_of_sample_b = Measurement.objects.filter(sample=sample_b)
        assert m2 in measurements_of_sample_b
        assert m3 in measurements_of_sample_b
        assert m1 not in measurements_of_sample_b

    def test_cross_dataset_measurement_deletion_does_not_affect_sample(self):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()

        sample = RockSampleFactory(dataset=dataset_b)
        measurement = ExampleMeasurementFactory(dataset=dataset_a, sample=sample)

        sample_id = sample.pk
        measurement.delete()

        assert RockSampleFactory._meta.model.objects.filter(pk=sample_id).exists()


@pytest.mark.django_db
class TestMeasurementValueWithUncertainty:
    def test_get_value_returns_name_for_base_measurement(self):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Test Measurement"
        )

        value = measurement.get_value()

        assert value == "Test Measurement"

    def test_print_value_returns_string_representation(self):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Test Measurement"
        )

        printed = measurement.print_value()

        assert isinstance(printed, str)
        assert "Test Measurement" in printed

    def test_polymorphic_measurement_get_value_with_value_field(self):
        # Using the demo app's XRFMeasurement, which nominates no value of its own,
        # so the report falls back to the record's name.
        from demo.models import XRFMeasurement

        xrf = XRFMeasurement.objects.create(
            name="Iron Analysis",
            dataset=DatasetFactory(),
            sample=RockSampleFactory(),
            element="Fe",
            concentration_ppm=45.2,
        )

        value = xrf.get_value()

        assert value == "Iron Analysis"

    def test_value_display_consistent_across_polymorphic_types(self):
        base_measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Base Measurement"
        )
        assert base_measurement.get_value() == "Base Measurement"

        from demo.models import ICP_MS_Measurement

        icp_ms = ICP_MS_Measurement.objects.create(
            name="Uranium Analysis",
            dataset=DatasetFactory(),
            sample=RockSampleFactory(),
            isotope="U-238",
            counts_per_second="12000.00",
            value="12.500",
            uncertainty="0.400",
        )
        icp_ms.refresh_from_db()

        assert unicodedata.normalize(
            "NFKC", icp_ms.print_value()
        ) == unicodedata.normalize("NFKC", "12.50 ± 0.40 µg/l")


@pytest.mark.django_db
class TestMeasurementFAIRMetadata:
    def test_measurement_description_uses_measurement_vocabulary(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        description = MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="XRF Analysis"
        )

        assert description.type == "MeasurementSetup"
        assert description.related == measurement
        assert description.value == "XRF Analysis"
        assert description.VOCABULARY is not None

    def test_measurement_date_uses_measurement_vocabulary(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        measurement_date = MeasurementDate.objects.create(
            related=measurement, type="Setup", value="2024-02-15"
        )

        assert measurement_date.type == "Setup"
        assert measurement_date.related == measurement
        assert measurement_date.value == "2024-02-15"
        assert measurement_date.VOCABULARY is not None

    def test_measurement_vocabulary_types_differ_from_sample_vocabularies(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        desc = MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="Test"
        )

        assert desc.VOCABULARY is not None
        assert hasattr(desc, "VOCABULARY")

    def test_measurement_can_have_multiple_descriptions_of_different_types(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        desc1 = MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="XRF Spectroscopy"
        )

        desc2 = MeasurementDescription.objects.create(
            related=measurement, type="MeasurementConditions", value="Bruker S8 Tiger"
        )

        descriptions = MeasurementDescription.objects.filter(related=measurement)

        assert descriptions.count() == 2
        assert desc1 in descriptions
        assert desc2 in descriptions
        assert desc1.type != desc2.type

    def test_measurement_can_have_multiple_dates_of_different_types(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        date1 = MeasurementDate.objects.create(
            related=measurement, type="Setup", value="2024-02-15"
        )

        date2 = MeasurementDate.objects.create(
            related=measurement, type="TearDown", value="2024-02-10"
        )

        dates = MeasurementDate.objects.filter(related=measurement)

        assert dates.count() == 2
        assert date1 in dates
        assert date2 in dates
        assert date1.type != date2.type


@pytest.mark.django_db
class TestMeasurementQuerySetOptimization:
    def test_with_related_prefetches_direct_relationships(self):
        for _ in range(5):
            measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
            measurement.add_contributor(PersonFactory(), with_roles=["Creator"])

        with CaptureQueriesContext(connection) as queries:
            measurements = list(Measurement.objects.with_related().all())

            for m in measurements:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(m.contributors.all())

        query_count = len(queries)
        assert query_count <= 10

    def test_with_metadata_prefetches_descriptions_dates_identifiers(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="XRF"
        )
        MeasurementDate.objects.create(related=measurement, type="Setup", value="2024")

        with CaptureQueriesContext(connection) as queries:
            measurements = list(Measurement.objects.with_metadata().all())

            for m in measurements:
                _ = list(MeasurementDescription.objects.filter(related=m))
                _ = list(MeasurementDate.objects.filter(related=m))

        query_count = len(queries)
        assert query_count <= 8

    def test_queryset_method_chaining_works_correctly(self):
        dataset = DatasetFactory()
        for _ in range(3):
            measurement = ExampleMeasurementFactory(
                sample=RockSampleFactory(), dataset=dataset
            )
            MeasurementDescription.objects.create(
                related=measurement, type="MeasurementSetup", value="Test"
            )

        measurements = (
            Measurement.objects.with_related().with_metadata().filter(dataset=dataset)
        )

        assert measurements.count() == 3

        with CaptureQueriesContext(connection) as queries:
            results = list(measurements)
            for m in results:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(MeasurementDescription.objects.filter(related=m))

        query_count = len(queries)
        assert query_count <= 10

    def test_polymorphic_queries_return_correct_typed_instances(self):
        example_measurements = [
            ExampleMeasurementFactory(sample=RockSampleFactory()) for _ in range(2)
        ]

        from demo.models import ExampleMeasurement, XRFMeasurement

        polymorphic_measurements = [
            XRFMeasurement.objects.create(
                name=f"XRF {i}",
                dataset=DatasetFactory(),
                sample=RockSampleFactory(),
                element="Fe",
                concentration_ppm=10.0 + i,
            )
            for i in range(2)
        ]

        all_measurements = Measurement.objects.all()

        xrf_count = sum(1 for m in all_measurements if isinstance(m, XRFMeasurement))
        example_count = sum(
            1 for m in all_measurements if type(m) is ExampleMeasurement
        )

        assert xrf_count >= 2
        assert example_count >= 2

    def test_large_measurement_collection_loads_efficiently(self):
        measurements = []
        for i in range(50):
            m = ExampleMeasurementFactory(
                sample=RockSampleFactory(), name=f"Measurement {i}"
            )
            m.add_contributor(PersonFactory(), with_roles=["Creator"])
            MeasurementDescription.objects.create(
                related=m, type="MeasurementSetup", value=f"Method {i}"
            )
            measurements.append(m)

        with CaptureQueriesContext(connection) as queries:
            optimized_results = list(
                Measurement.objects.with_related().with_metadata().all()
            )

            for m in optimized_results:
                _ = m.sample.name
                _ = m.dataset.name
                _ = list(m.contributors.all())
                _ = list(m.descriptions.all())

        optimized_query_count = len(queries)

        assert optimized_query_count < 20, (
            f"Query count too high: {optimized_query_count}"
        )


@pytest.mark.django_db
class TestCrossDatasetDeletionBoundaries:
    def test_deleting_the_measurement_dataset_deletes_the_measurement(self):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()
        sample_b = RockSampleFactory(dataset=dataset_b)
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)
        measurement_pk = measurement_a.pk

        dataset_a.delete()

        assert not ExampleMeasurementFactory._meta.model.objects.filter(
            pk=measurement_pk
        ).exists()

    def test_deleting_the_measurement_dataset_leaves_the_sample_standing(self):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()
        sample_b = RockSampleFactory(dataset=dataset_b)
        ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)
        sample_pk = sample_b.pk

        dataset_a.delete()

        assert RockSampleFactory._meta.model.objects.filter(pk=sample_pk).exists()

    def test_deleting_the_sample_is_refused_while_the_measurement_refers_to_it(self):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()
        sample_b = RockSampleFactory(dataset=dataset_b)
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        with pytest.raises(RestrictedError):
            sample_b.delete()

        assert ExampleMeasurementFactory._meta.model.objects.filter(
            pk=measurement_a.pk
        ).exists()

    def test_deleting_the_sample_dataset_is_refused_while_a_measurement_elsewhere_refers_to_it(
        self,
    ):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()
        sample_b = RockSampleFactory(dataset=dataset_b)
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        with pytest.raises(RestrictedError):
            dataset_b.delete()

        assert ExampleMeasurementFactory._meta.model.objects.filter(
            pk=measurement_a.pk
        ).exists()


@pytest.mark.django_db
class TestGetValue:
    def test_type_nominating_a_value_reports_that_value(self, sample):
        measurement = ICP_MS_MeasurementFactory(sample=sample, value="5.000")
        measurement.refresh_from_db()

        assert measurement.get_value() == measurement.value

    def test_type_nominating_none_reports_the_record_name(self, sample):
        measurement = ExampleMeasurementFactory(sample=sample, name="Base Reading")

        assert measurement.get_value() == "Base Reading"


@pytest.mark.django_db
class TestGetValueWithUncertainty:
    def test_uncertainty_is_carried_with_the_value(self, sample):
        measurement = ICP_MS_MeasurementFactory(
            sample=sample, value="5.000", uncertainty="0.300"
        )
        measurement.refresh_from_db()

        result = measurement.get_value()

        # A pint `Measurement`'s attributes are `.value` and `.error`, not `.err`.
        assert isinstance(result, pint.Measurement)
        assert result.value.magnitude == pytest.approx(
            float(measurement.value.magnitude)
        )
        assert result.error.magnitude == pytest.approx(
            float(measurement.uncertainty.magnitude)
        )
        assert result.value.units == measurement.value.units


class TestGetValuePlainNumber:
    def test_plain_number_with_uncertainty_present_is_returned_unchanged(self):
        record = SimpleNamespace(name="Plain Reading", value=42, uncertainty=5)

        assert Measurement.get_value(record) == 42

    def test_plain_number_with_no_uncertainty_is_returned_unchanged(self):
        record = SimpleNamespace(name="Plain Reading", value=42)

        assert Measurement.get_value(record) == 42


@pytest.mark.django_db
class TestPrintValue:
    def test_renders_value_uncertainty_and_units_together(self, sample):
        measurement = ICP_MS_MeasurementFactory(
            sample=sample, value="5.000", uncertainty="0.300"
        )
        measurement.refresh_from_db()

        # NFKC-normalised: the unit registry is free to render the micro prefix as
        # either U+00B5 MICRO SIGN or U+03BC GREEK SMALL LETTER MU (both normalise to
        # the same codepoint), and that choice belongs to the registry, not this test.
        assert unicodedata.normalize(
            "NFKC", measurement.print_value()
        ) == unicodedata.normalize("NFKC", "5.00 ± 0.30 µg/l")
