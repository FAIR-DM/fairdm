"""Tests for the rules the core factories keep for the records a portal builds."""

import pytest

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.dataset.models import DatasetDescription
from fairdm.core.project.models import ProjectDescription
from fairdm.core.vocabularies import DESCRIPTION_TYPES
from fairdm.factories import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    ProjectDateFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
)


@pytest.mark.django_db
class TestFactoryVocabularyValidation:
    def test_project_factory_rejects_invalid_description_types(self):
        with pytest.raises(ValueError) as cm:
            ProjectFactory(descriptions=1, descriptions__types=["InvalidType"])

        assert "InvalidType" in str(cm.value)

    def test_project_factory_rejects_invalid_date_types(self):
        with pytest.raises(ValueError) as cm:
            ProjectFactory(dates=1, dates__types=["InvalidType"])

        assert "InvalidType" in str(cm.value)

    def test_factories_accept_valid_vocabulary_types(self):
        project = ProjectFactory(
            descriptions=2,
            descriptions__types=[
                f"{DESCRIPTION_TYPES}/abstract",
                f"{DESCRIPTION_TYPES}/introduction",
            ],
        )
        dataset = DatasetFactory(
            descriptions=2,
            descriptions__types=[
                f"{DESCRIPTION_TYPES}/abstract",
                f"{DESCRIPTION_TYPES}/methods",
            ],
        )

        assert ProjectDescription.objects.filter(related=project).count() == 2
        assert DatasetDescription.objects.filter(related=dataset).count() == 2

        desc_types = list(
            ProjectDescription.objects.filter(related=project).values_list(
                "type", flat=True
            )
        )
        assert f"{DESCRIPTION_TYPES}/abstract" in desc_types
        assert f"{DESCRIPTION_TYPES}/introduction" in desc_types

    def test_factories_use_vocabulary_defaults(self):
        project = ProjectFactory(descriptions=2)

        descriptions = ProjectDescription.objects.filter(related=project)
        assert descriptions.count() == 2

        desc_types = list(descriptions.values_list("type_id", flat=True))
        vocab_values = [
            concept.uri for concept in ProjectDescription.get_type_concepts()
        ]

        for dtype in desc_types:
            assert dtype in vocab_values


@pytest.mark.django_db
class TestEveryCoreFactoryBuildsItsVocabularyRecords:
    """Each core factory carries its own descriptions and dates hooks."""

    BUILDERS = {
        "project": (
            ProjectFactory,
            dict,
            {"descriptions": ProjectDescriptionFactory, "dates": ProjectDateFactory},
        ),
        "dataset": (
            DatasetFactory,
            dict,
            {"descriptions": DatasetDescriptionFactory, "dates": DatasetDateFactory},
        ),
        "sample": (
            RockSampleFactory,
            dict,
            {"descriptions": SampleDescriptionFactory, "dates": SampleDateFactory},
        ),
        "measurement": (
            ExampleMeasurementFactory,
            lambda: {"sample": RockSampleFactory()},
            {
                "descriptions": MeasurementDescriptionFactory,
                "dates": MeasurementDateFactory,
            },
        ),
    }

    def test_each_hook_creates_the_records_asked_for_and_refuses_an_unknown_type(self):
        failures = []
        for kind, (factory, extra, hooks) in self.BUILDERS.items():
            for hook, record_factory in hooks.items():
                model = record_factory._meta.model
                record = factory(**extra(), **{hook: 1})
                if model.objects.filter(related=record).count() != 1:
                    failures.append(f"{kind} {hook}: one record was not created")
                try:
                    factory(**extra(), **{hook: 1, f"{hook}__types": ["InvalidType"]})
                except ValueError as error:
                    if "InvalidType" not in str(error):
                        failures.append(f"{kind} {hook}: the error does not name it")
                else:
                    failures.append(f"{kind} {hook}: an unknown type was accepted")

        assert not failures, "\n".join(failures)


@pytest.mark.django_db
class TestFactoryImages:
    def test_a_default_factory_sets_no_image(self):
        # Generating one on every call left files under MEDIA_ROOT (#323).
        assert not ProjectFactory().image
        assert not DatasetFactory().image

    def test_an_image_asked_for_is_generated_under_the_media_root(self, tmp_path):
        # MEDIA_ROOT was once a fixed path shared by every run, and nothing removed
        # what landed there (#323).
        from pathlib import Path

        from django.conf import settings

        dataset = DatasetFactory(with_image=True)

        assert Path(settings.MEDIA_ROOT) == tmp_path / "media"
        assert tmp_path in Path(dataset.image.path).parents
