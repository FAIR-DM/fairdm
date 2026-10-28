"""Tests for the vocabulary-driven descriptions form."""

import pytest

from fairdm.core.dataset.models import DatasetDescription
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.core.project.models import ProjectDescription
from fairdm.factories import DatasetFactory, ProjectFactory

DESCRIPTION_CASES = [
    (ProjectDescription, ProjectFactory),
    (DatasetDescription, DatasetFactory),
]


@pytest.mark.django_db
class TestVocabularyDescriptionsForm:
    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_field_set_matches_the_vocabulary_exactly_and_in_order(
        self, related_model, parent_factory
    ):
        instance = parent_factory()

        form = VocabularyDescriptionsForm(
            related_model=related_model, instance=instance
        )

        assert list(form.fields) == list(
            [concept.uri for concept in related_model.get_type_concepts()]
        )

    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_each_area_is_labelled_with_the_concepts_name_and_definition(
        self, related_model, parent_factory
    ):
        instance = parent_factory()
        concept = related_model.get_type_concepts()[0]
        first_type = concept.uri

        form = VocabularyDescriptionsForm(
            related_model=related_model, instance=instance
        )

        assert form.fields[first_type].label == concept.display_label()
        assert form.fields[first_type].help_text == concept.first_value(
            "skos:definition"
        )

    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_saving_text_into_one_area_writes_exactly_one_row_of_that_type(
        self, related_model, parent_factory
    ):
        instance = parent_factory()
        first_type = [concept.uri for concept in related_model.get_type_concepts()][0]

        form = VocabularyDescriptionsForm(
            related_model=related_model,
            instance=instance,
            data={first_type: "Some descriptive text."},
        )

        assert form.is_valid(), form.errors
        form.save()

        assert related_model._default_manager.filter(related=instance).count() == 1
        row = related_model._default_manager.get(related=instance)
        assert row.type_id == first_type
        assert row.value == "Some descriptive text."

    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_a_value_over_the_ceiling_is_rejected(self, related_model, parent_factory):
        # The form saves through the manager without full_clean(), so the model's length
        # ceiling never runs unless the form enforces it too (#329).
        from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH

        instance = parent_factory()
        first_type = [concept.uri for concept in related_model.get_type_concepts()][0]

        form = VocabularyDescriptionsForm(
            related_model=related_model,
            instance=instance,
            data={first_type: "x" * (DESCRIPTION_MAX_LENGTH + 1)},
        )

        assert not form.is_valid()
        assert first_type in form.errors
