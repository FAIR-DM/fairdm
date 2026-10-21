"""Tests for the form that chooses the person a merge keeps."""

import pytest

from fairdm.contrib.autocomplete.fields import PersonChoiceField
from fairdm.contrib.contributors.forms.person import MergePersonForm
from fairdm.factories import PersonFactory


@pytest.mark.django_db
class TestMergePersonForm:
    def test_the_target_is_chosen_with_the_person_field(self):
        form = MergePersonForm(exclude_pk=PersonFactory().pk)

        assert isinstance(form.fields["merge_into"], PersonChoiceField)

    def test_the_chosen_person_is_the_target(self, in_request):
        discarded = PersonFactory()
        kept = PersonFactory()
        in_request(PersonFactory())
        form = MergePersonForm({"merge_into": kept.pk}, exclude_pk=discarded.pk)

        assert form.is_valid(), form.errors
        assert form.cleaned_data["merge_into"] == kept

    def test_the_person_being_merged_is_refused_as_the_target(self, in_request):
        discarded = PersonFactory()
        in_request(PersonFactory())
        form = MergePersonForm({"merge_into": discarded.pk}, exclude_pk=discarded.pk)

        assert form.has_error("merge_into", code="same_person")
