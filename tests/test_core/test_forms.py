"""Tests for fairdm/core/forms.py."""

import pytest

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.dataset.models import Dataset
from fairdm.core.forms import KeywordForm
from fairdm.core.project.models import Project
from fairdm.factories import DatasetFactory, ProjectFactory


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

    def test_a_configured_vocabulary_adds_no_field(self, settings):
        settings.FAIRDM_SAMPLE = {"keywords": ["fairdm.core.vocabularies.FairDMRoles"]}

        form = KeywordForm(instance=RockSampleFactory())

        assert list(form.fields) == ["tags"]

    def test_it_offers_the_free_keywords_alone(self):
        form = KeywordForm(
            instance=ExampleMeasurementFactory(sample=RockSampleFactory())
        )

        assert list(form.fields) == ["tags"]


@pytest.mark.django_db
class TestKeywordFormTags:
    def test_it_saves_an_existing_tag_and_a_new_one(self):
        ProjectFactory().tags.add("existing")
        project = ProjectFactory()

        form = KeywordForm(data={"tags": ["existing", "brand-new"]}, instance=project)

        assert form.is_valid(), form.errors
        form.save()
        assert sorted(project.tags.names()) == ["brand-new", "existing"]

    def test_it_strips_each_tag_and_drops_blank_ones(self):
        project = ProjectFactory()

        form = KeywordForm(data={"tags": ["  padded  ", "", "   "]}, instance=project)

        assert form.is_valid(), form.errors
        assert form.cleaned_data["tags"] == ["padded"]

    def test_it_removes_the_tags_that_are_no_longer_chosen(self):
        project = ProjectFactory()
        project.tags.add("old", "kept")

        form = KeywordForm(data={"tags": ["kept"]}, instance=project)

        assert form.is_valid(), form.errors
        form.save()
        assert list(project.tags.names()) == ["kept"]

    def test_it_clears_the_tags_when_none_are_chosen(self):
        project = ProjectFactory()
        project.tags.add("old")

        form = KeywordForm(data={}, instance=project)

        assert form.is_valid(), form.errors
        form.save()
        assert list(project.tags.names()) == []

    def test_it_shows_the_tags_chosen_when_reopened(self):
        project = ProjectFactory()
        project.tags.add("first", "second")

        form = KeywordForm(instance=project)

        widget = form.fields["tags"].widget
        context = widget.get_context("tags", form["tags"].value(), {})["widget"]
        assert sorted(o["value"] for o in context["selected_options"]) == [
            "first",
            "second",
        ]

    def test_the_field_lets_a_new_tag_be_added(self):
        form = KeywordForm(instance=ProjectFactory())

        assert form.fields["tags"].widget.create is True
