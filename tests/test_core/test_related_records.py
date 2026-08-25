"""Tests for the shared related-record row-set declarations (T002).

Source: ``fairdm/core/related_records.py``

Exercises the row-set base against two record types - Project and Dataset -
per plan P6: a component built from one model's own relations proves
nothing on its own, since it can only fail if a literal name was left
behind.
"""

import pytest
from django.test import RequestFactory

from fairdm.core.abstract import AbstractDate
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.related_records import (
    DatasetDateInline,
    DatasetIdentifierInline,
    ProjectDateInline,
    ProjectIdentifierInline,
    RelatedRecordInline,
)
from fairdm.factories import (
    DatasetDateFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)

ROW_SET_CASES = [
    (Project, ProjectDateInline, ProjectFactory, ProjectDateFactory, "Start"),
    (Dataset, DatasetDateInline, DatasetFactory, DatasetDateFactory, "CollectionStart"),
]

ALL_FOUR_INLINE_CASES = [
    (Project, ProjectDateInline, ProjectFactory, ProjectDateFactory),
    (Project, ProjectIdentifierInline, ProjectFactory, ProjectIdentifierFactory),
    (Dataset, DatasetDateInline, DatasetFactory, DatasetDateFactory),
    (Dataset, DatasetIdentifierInline, DatasetFactory, DatasetIdentifierFactory),
]


def _row_value(model, index):
    """A valid, unique-enough ``value`` for a hand-built management form row.
    Dates take a plain ISO string; identifiers carry a table-wide unique
    constraint, so each needs its own value."""
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
    """The shared row-set base carries the two fields every related record
    has and offers no blank rows, over both Project and Dataset."""

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
        """T087/FR-024-style row cap, moved off the dataset's own admin
        (`fairdm/core/dataset/admin.py`'s ``IdentifierInline``/``DateInline``)
        onto the shared base so the project's update page gets it too."""
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
        """A record already holding one row per available type renders no
        blank row (``extra = 0``) and cannot be made to accept another by
        hand-editing the management form's ``TOTAL_FORMS``."""
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
            "Please submit at most" in str(error)
            for error in formset.non_form_errors()
        )

    def test_building_one_declarations_formset_does_not_mutate_the_shared_fields_tuple(
        self,
    ):
        """Regression: ``BaseInlineFormSet.__init__`` appends the parent FK's
        name to ``form._meta.fields`` in place. A list here would be the
        same object as the class attribute, so building a Project formset
        would leak a ``related`` field into every other subclass sharing
        this base - including Dataset's."""
        project = ProjectFactory()

        _formset_for(ProjectDateInline, Project, project)

        assert RelatedRecordInline.fields == ("type", "value")
        assert DatasetDateInline.fields == ("type", "value")
