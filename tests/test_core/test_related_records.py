"""Tests for the shared related-record row-set declarations."""

import pytest
from django.test import RequestFactory

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.abstract import AbstractDate
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.measurement.models import Measurement
from fairdm.core.related_records import (
    DatasetDateInline,
    DatasetIdentifierInline,
    MeasurementDateInline,
    MeasurementIdentifierInline,
    ProjectDateInline,
    ProjectIdentifierInline,
    RelatedRecordInline,
    SampleDateInline,
    SampleIdentifierInline,
)
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    DatasetDateFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    MeasurementDateFactory,
    MeasurementIdentifierFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleDateFactory,
    SampleIdentifierFactory,
)

ROW_SET_CASES = [
    (Project, ProjectDateInline, ProjectFactory, ProjectDateFactory, "Start"),
    (Dataset, DatasetDateInline, DatasetFactory, DatasetDateFactory, "CollectionStart"),
]

def make_measurement():
    """Make a measurement of a demo type on a sample in the same dataset."""
    sample = RockSampleFactory()
    return ExampleMeasurementFactory(sample=sample, dataset=sample.dataset)


ALL_FOUR_INLINE_CASES = [
    (Project, ProjectDateInline, ProjectFactory, ProjectDateFactory),
    (Project, ProjectIdentifierInline, ProjectFactory, ProjectIdentifierFactory),
    (Dataset, DatasetDateInline, DatasetFactory, DatasetDateFactory),
    (Dataset, DatasetIdentifierInline, DatasetFactory, DatasetIdentifierFactory),
    (Sample, SampleDateInline, RockSampleFactory, SampleDateFactory),
    (Sample, SampleIdentifierInline, RockSampleFactory, SampleIdentifierFactory),
    (Measurement, MeasurementDateInline, make_measurement, MeasurementDateFactory),
    (
        Measurement,
        MeasurementIdentifierInline,
        make_measurement,
        MeasurementIdentifierFactory,
    ),
]


def _row_value(model, index):
    """A valid, unique-enough ``value`` for a hand-built management form row."""
    if issubclass(model, AbstractDate):
        return "2020-01-01"
    return f"10.{9000 + index}/row-limit-test-{index}"


def _formset_for(declaration_cls, parent_model, instance, method="GET", data=None):
    request = (
        RequestFactory().post("/", data=data)
        if method == "POST"
        else RequestFactory().get("/")
    )
    declaration = declaration_cls(
        parent_model=parent_model, request=request, instance=instance, view=None
    )
    return declaration.construct_formset()


@pytest.mark.django_db
class TestRelatedRecordInline:
    @pytest.mark.parametrize(
        "parent_model, declaration_cls, parent_factory, row_factory, row_type",
        ROW_SET_CASES,
    )
    def test_existing_rows_are_presented_with_no_blank_rows_beyond_them(
        self, parent_model, declaration_cls, parent_factory, row_factory, row_type
    ):
        instance = parent_factory()
        row_factory(related=instance, type=row_type)

        formset = _formset_for(declaration_cls, parent_model, instance)

        assert formset.initial_form_count() == 1
        assert formset.extra == 0
        assert len(formset.forms) == 1

    @pytest.mark.parametrize(
        "parent_model, declaration_cls, parent_factory, row_factory, row_type",
        ROW_SET_CASES,
    )
    def test_a_submitted_new_row_is_written_against_that_record(
        self, parent_model, declaration_cls, parent_factory, row_factory, row_type
    ):
        instance = parent_factory()
        prefix = declaration_cls.model._meta.default_related_name
        data = {
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-type": row_type,
            f"{prefix}-0-value": "2020-01-01",
        }

        formset = _formset_for(
            declaration_cls, parent_model, instance, method="POST", data=data
        )

        assert formset.is_valid(), formset.errors
        formset.save()

        assert declaration_cls.model._default_manager.filter(
            related=instance, type=row_type
        ).exists()

    def test_each_subclass_names_only_its_model(self):
        assert ProjectIdentifierInline.model.__name__ == "ProjectIdentifier"
        assert DatasetIdentifierInline.model.__name__ == "DatasetIdentifier"
        for declaration_cls in (
            ProjectDateInline,
            ProjectIdentifierInline,
            DatasetDateInline,
            DatasetIdentifierInline,
        ):
            assert declaration_cls.fields == ("type", "value")
            assert declaration_cls.extra == 0

    @pytest.mark.parametrize(
        "parent_model, declaration_cls, parent_factory, row_factory",
        ALL_FOUR_INLINE_CASES,
    )
    def test_max_num_matches_the_parents_type_vocabulary(
        self, parent_model, declaration_cls, parent_factory, row_factory
    ):
        instance = parent_factory()

        formset = _formset_for(declaration_cls, parent_model, instance)

        assert formset.max_num == len(declaration_cls.model.VOCABULARY.choices)

    @pytest.mark.parametrize(
        "parent_model, declaration_cls, parent_factory, row_factory",
        ALL_FOUR_INLINE_CASES,
    )
    def test_a_record_already_at_the_maximum_refuses_one_more_row(
        self, parent_model, declaration_cls, parent_factory, row_factory
    ):
        instance = parent_factory()
        types = [choice for choice, _label in declaration_cls.model.VOCABULARY.choices]
        for row_type in types:
            row_factory(related=instance, type=row_type)
        max_num = len(types)

        prefix = declaration_cls.model._meta.default_related_name
        existing = list(getattr(instance, prefix).all())
        data = {
            f"{prefix}-TOTAL_FORMS": str(max_num + 1),
            f"{prefix}-INITIAL_FORMS": str(max_num),
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        for i, obj in enumerate(existing):
            data[f"{prefix}-{i}-id"] = str(obj.pk)
            data[f"{prefix}-{i}-type"] = obj.type
            data[f"{prefix}-{i}-value"] = str(obj.value)
        # One row beyond the maximum, hand-added to the management form as a
        # real submission would if a blank row were forced onto the page.
        data[f"{prefix}-{max_num}-type"] = types[0]
        data[f"{prefix}-{max_num}-value"] = _row_value(declaration_cls.model, max_num)

        formset = _formset_for(
            declaration_cls, parent_model, instance, method="POST", data=data
        )

        assert not formset.is_valid()
        assert any(
            error.code == "too_many_forms"
            for error in formset.non_form_errors().as_data()
        )

    def test_building_one_declarations_formset_does_not_mutate_the_shared_fields_tuple(
        self,
    ):
        # BaseInlineFormSet.__init__ appends the parent FK name to form._meta.fields in
        # place, so a shared list would leak that field into every sibling subclass.
        project = ProjectFactory()

        _formset_for(ProjectDateInline, Project, project)

        assert RelatedRecordInline.fields == ("type", "value")
        assert DatasetDateInline.fields == ("type", "value")
