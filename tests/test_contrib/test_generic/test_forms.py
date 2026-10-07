"""Tests for fairdm/contrib/generic/forms.py."""

import pytest

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.generic.forms import DescriptionForm, KeywordForm
from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import DatasetFactory, ProjectFactory


@pytest.mark.django_db
class TestDescriptionForm:
    def test_value_at_the_ceiling_is_valid(self):
        form = DescriptionForm(
            data={"type": "SampleCollection", "value": "x" * DESCRIPTION_MAX_LENGTH}
        )

        assert form.is_valid(), form.errors

    def test_value_one_character_over_the_ceiling_is_rejected(self):
        form = DescriptionForm(
            data={
                "type": "SampleCollection",
                "value": "x" * (DESCRIPTION_MAX_LENGTH + 1),
            }
        )

        assert not form.is_valid()
        assert "value" in form.errors


@pytest.mark.django_db
class TestKeywordForm:
    def test_building_it_for_two_models_leaves_each_bound_to_its_own(self):
        project = ProjectFactory()
        dataset = DatasetFactory()

        first = KeywordForm(instance=project)
        second = KeywordForm(instance=dataset)

        assert first._meta.model is Project
        assert second._meta.model is Dataset
        assert KeywordForm._meta.model is None

    def test_a_registered_sample_type_reads_the_vocabularies_of_the_sample_setting(
        self, settings
    ):
        settings.FAIRDM_SAMPLE = {"keywords": ["fairdm.core.vocabularies.FairDMRoles"]}

        form = KeywordForm(instance=RockSampleFactory())

        assert "FairDMRoles" in form.fields

    def test_a_record_type_with_no_setting_gets_the_free_text_field_alone(
        self, settings
    ):
        if hasattr(settings, "FAIRDM_MEASUREMENT"):
            del settings.FAIRDM_MEASUREMENT

        form = KeywordForm(
            instance=ExampleMeasurementFactory(sample=RockSampleFactory())
        )

        assert list(form.fields) == ["tags"]
