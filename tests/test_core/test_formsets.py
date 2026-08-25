"""Tests for the shared, parameterised date-ordering formset (T003).

Source: ``fairdm/core/formsets.py``

Exercises ``date_ordering_formset`` against two record types whose date
vocabularies each carry an ordered pair - Project (Start/End) and Dataset
(CollectionStart/CollectionEnd) - and proves the rule is scoped to the pair
it is parameterised on, per plan P6: handing every record type the same
rule gives one with no ordered pair a rule that runs and validates nothing.
"""

import pytest
from django.forms import inlineformset_factory

from fairdm.core.dataset.models import Dataset, DatasetDate
from fairdm.core.formsets import date_ordering_formset
from fairdm.core.project.models import Project, ProjectDate
from fairdm.factories import DatasetFactory, ProjectFactory

DATE_ORDER_CASES = [
    (
        Project,
        ProjectDate,
        ProjectFactory,
        "Start",
        "End",
        "The project's end date (%(end)s) cannot be before its start date (%(start)s).",
    ),
    (
        Dataset,
        DatasetDate,
        DatasetFactory,
        "CollectionStart",
        "CollectionEnd",
        "The dataset's collection end date (%(end)s) cannot be "
        "before its collection start date (%(start)s).",
    ),
]


def _build_formset(parent_model, date_model, instance, start_type, end_type, message, data):
    formset_class = inlineformset_factory(
        parent_model,
        date_model,
        fields=("type", "value"),
        formset=date_ordering_formset(start_type, end_type, message),
        extra=0,
    )
    prefix = date_model._meta.default_related_name
    management_data = {
        f"{prefix}-TOTAL_FORMS": "2",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
        **data,
    }
    return formset_class(data=management_data, instance=instance, prefix=prefix)


@pytest.mark.django_db
class TestDateOrderingFormSet:
    """A backwards start/end pair submitted as two rows in one submission is
    refused, for both a project and a dataset."""

    @pytest.mark.parametrize(
        "parent_model, date_model, parent_factory, start_type, end_type, message",
        DATE_ORDER_CASES,
    )
    def test_a_backwards_pair_submitted_together_is_refused(
        self, parent_model, date_model, parent_factory, start_type, end_type, message
    ):
        instance = parent_factory()
        prefix = date_model._meta.default_related_name
        formset = _build_formset(
            parent_model,
            date_model,
            instance,
            start_type,
            end_type,
            message,
            {
                f"{prefix}-0-type": start_type,
                f"{prefix}-0-value": "2020-06-01",
                f"{prefix}-1-type": end_type,
                f"{prefix}-1-value": "2010-01-01",
            },
        )

        assert not formset.is_valid()
        assert formset.non_form_errors() == [
            message % {"start": "2020-06-01", "end": "2010-01-01"}
        ]

    @pytest.mark.parametrize(
        "parent_model, date_model, parent_factory, start_type, end_type, message",
        DATE_ORDER_CASES,
    )
    def test_a_forwards_pair_submitted_together_is_accepted(
        self, parent_model, date_model, parent_factory, start_type, end_type, message
    ):
        instance = parent_factory()
        prefix = date_model._meta.default_related_name
        formset = _build_formset(
            parent_model,
            date_model,
            instance,
            start_type,
            end_type,
            message,
            {
                f"{prefix}-0-type": start_type,
                f"{prefix}-0-value": "2010-01-01",
                f"{prefix}-1-type": end_type,
                f"{prefix}-1-value": "2020-06-01",
            },
        )

        assert formset.is_valid(), formset.errors

    @pytest.mark.parametrize(
        "parent_model, date_model, parent_factory, start_type, end_type, message",
        DATE_ORDER_CASES,
    )
    def test_an_equal_start_and_end_is_accepted(
        self, parent_model, date_model, parent_factory, start_type, end_type, message
    ):
        """A start and end on the same day is not "backwards" - the rule
        refuses an end strictly before the start, not one equal to it
        (T010)."""
        instance = parent_factory()
        prefix = date_model._meta.default_related_name
        formset = _build_formset(
            parent_model,
            date_model,
            instance,
            start_type,
            end_type,
            message,
            {
                f"{prefix}-0-type": start_type,
                f"{prefix}-0-value": "2020-06-01",
                f"{prefix}-1-type": end_type,
                f"{prefix}-1-value": "2020-06-01",
            },
        )

        assert formset.is_valid(), formset.errors

    def test_types_outside_the_parameterised_pair_are_unaffected(self):
        """The rule only compares the two types it was parameterised on.
        Dataset's vocabulary carries other, unordered date types alongside
        its CollectionStart/CollectionEnd pair (Submitted, Published, ...);
        submitting two of those - however 'backwards' their values look -
        is unaffected. This is the same reason a record type with no
        ordered pair at all is never parameterised onto this rule."""
        dataset = DatasetFactory()
        prefix = DatasetDate._meta.default_related_name
        formset = _build_formset(
            Dataset,
            DatasetDate,
            dataset,
            "CollectionStart",
            "CollectionEnd",
            "The dataset's collection end date (%(end)s) cannot be "
            "before its collection start date (%(start)s).",
            {
                f"{prefix}-0-type": "Submitted",
                f"{prefix}-0-value": "2020-06-01",
                f"{prefix}-1-type": "Published",
                f"{prefix}-1-value": "2010-01-01",
            },
        )

        assert formset.is_valid(), formset.errors
