"""Tests for the rules the core FairDM factories keep for a portal that builds its records with them."""

import pytest

from fairdm.core.dataset.models import DatasetDescription
from fairdm.core.project.models import ProjectDescription
from fairdm.core.vocabularies import DESCRIPTION_TYPES
from fairdm.factories import DatasetFactory, ProjectFactory


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
class TestFactoryImages:
    def test_a_default_factory_sets_no_image(self):
        # Generating one on every call left files under MEDIA_ROOT (#323).
        assert not ProjectFactory().image
        assert not DatasetFactory().image

    def test_an_image_asked_for_is_generated_under_the_media_root(self, tmp_path):
        # MEDIA_ROOT was once a fixed path shared by every run, and nothing removed what landed there (#323).
        from pathlib import Path

        from django.conf import settings

        dataset = DatasetFactory(with_image=True)

        assert Path(settings.MEDIA_ROOT) == tmp_path / "media"
        assert tmp_path in Path(dataset.image.path).parents
