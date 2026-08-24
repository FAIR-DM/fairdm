"""Tests for the vocabulary-driven descriptions form (T004).

Source: ``fairdm/core/descriptions.py``

Exercises the form against two record types - ``ProjectDescription`` and
``DatasetDescription`` - per plan P6: a component built from one model's own
vocabulary proves nothing on its own, since it can only fail if a literal
name was left behind.
"""

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
    """One text area per concept in a related model's vocabulary, over both
    ProjectDescription and DatasetDescription."""

    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_field_set_matches_the_vocabulary_exactly_and_in_order(
        self, related_model, parent_factory
    ):
        instance = parent_factory()

        form = VocabularyDescriptionsForm(related_model=related_model, instance=instance)

        assert list(form.fields) == list(related_model.VOCABULARY.values)

    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_each_area_is_labelled_with_the_concepts_name_and_definition(
        self, related_model, parent_factory
    ):
        instance = parent_factory()
        vocabulary = related_model.VOCABULARY
        first_type = vocabulary.values[0]
        concept = vocabulary.get_concept(first_type)

        form = VocabularyDescriptionsForm(related_model=related_model, instance=instance)

        assert form.fields[first_type].label == concept.label()
        assert form.fields[first_type].help_text == concept.definition()

    @pytest.mark.parametrize("related_model, parent_factory", DESCRIPTION_CASES)
    def test_saving_text_into_one_area_writes_exactly_one_row_of_that_type(
        self, related_model, parent_factory
    ):
        instance = parent_factory()
        first_type = related_model.VOCABULARY.values[0]

        form = VocabularyDescriptionsForm(
            related_model=related_model,
            instance=instance,
            data={first_type: "Some descriptive text."},
        )

        assert form.is_valid(), form.errors
        form.save()

        assert related_model._default_manager.filter(related=instance).count() == 1
        row = related_model._default_manager.get(related=instance)
        assert row.type == first_type
        assert row.value == "Some descriptive text."
