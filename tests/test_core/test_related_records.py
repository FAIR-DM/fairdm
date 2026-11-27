"""Tests for the shared related-record row-set declarations.

Every declaration is the same base class naming a model, so each behaviour is checked on one
declaration, a project's dates.
"""

import pytest
from django.test import RequestFactory

from fairdm.core.project.models import Project, ProjectDate
from fairdm.core.related_records import ProjectDateInline
from fairdm.factories import ProjectDateFactory, ProjectFactory


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
    def test_existing_rows_are_presented_with_no_blank_rows_beyond_them(self):
        instance = ProjectFactory()
        ProjectDateFactory(related=instance, type=ProjectDate.START_TYPE)

        formset = _formset_for(ProjectDateInline, Project, instance)

        assert formset.initial_form_count() == 1
        assert formset.extra == 0
        assert len(formset.forms) == 1

    def test_a_submitted_new_row_is_written_against_that_record(self):
        instance = ProjectFactory()
        prefix = ProjectDateInline.model._meta.default_related_name
        data = {
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-type": ProjectDate.START_TYPE,
            f"{prefix}-0-value": "2020-01-01",
        }

        formset = _formset_for(
            ProjectDateInline, Project, instance, method="POST", data=data
        )

        assert formset.is_valid(), formset.errors
        formset.save()

        assert ProjectDate.objects.filter(
            related=instance, type=ProjectDate.START_TYPE
        ).exists()

    def test_max_num_matches_the_parents_type_vocabulary(self):
        formset = _formset_for(ProjectDateInline, Project, ProjectFactory())

        assert formset.max_num == len(ProjectDate.get_type_concepts())

    def test_a_record_already_at_the_maximum_refuses_one_more_row(self):
        instance = ProjectFactory()
        types = [concept.uri for concept in ProjectDate.get_type_concepts()]
        for row_type in types:
            ProjectDateFactory(related=instance, type=row_type)
        max_num = len(types)

        prefix = ProjectDateInline.model._meta.default_related_name
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
        data[f"{prefix}-{max_num}-value"] = "2020-01-01"

        formset = _formset_for(
            ProjectDateInline, Project, instance, method="POST", data=data
        )

        assert not formset.is_valid()
        assert any(
            error.code == "too_many_forms"
            for error in formset.non_form_errors().as_data()
        )
