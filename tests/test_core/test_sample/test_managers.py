"""Tests for the sample queryset's published() and visible_to() rules."""

import pytest
from django.contrib.auth.models import AnonymousUser

from demo.factories import RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.sample.models import Sample
from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestPublished:
    def test_published_includes_a_sample_whose_dataset_is_published(self):
        sample = RockSampleFactory(dataset=DatasetFactory(published=True))

        assert sample in Sample.objects.published()

    def test_published_excludes_a_sample_whose_dataset_is_unpublished(self):
        sample = RockSampleFactory(dataset=DatasetFactory(published=False))

        assert sample not in Sample.objects.published()


@pytest.mark.django_db
class TestVisibleTo:
    """FR-019: a sample follows its own dataset."""

    @pytest.fixture
    def samples(self):
        return {
            "released": RockSampleFactory(
                dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
            ),
            "unpublished": RockSampleFactory(
                dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=False)
            ),
            "private": RockSampleFactory(
                dataset=DatasetFactory(visibility=Visibility.PRIVATE, published=False)
            ),
        }

    def test_a_visitor_sees_only_samples_in_public_published_datasets(self, samples):
        visible = Sample.objects.visible_to(AnonymousUser())

        assert set(visible) == {samples["released"]}

    def test_a_signed_in_user_with_no_rights_sees_the_same_as_a_visitor(self, samples):
        visible = Sample.objects.visible_to(PersonFactory(is_active=True))

        assert set(visible) == {samples["released"]}

    def test_a_dataset_team_member_also_sees_that_datasets_samples(self, samples):
        user = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=samples["private"].dataset,
            contributor=user,
            level=ContributionLevel.VIEW,
        )

        visible = Sample.objects.visible_to(user)

        assert set(visible) == {samples["released"], samples["private"]}

    def test_a_person_who_may_edit_a_dataset_sees_its_samples(self, samples):
        user = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=samples["unpublished"].dataset,
            contributor=user,
            level=ContributionLevel.EDIT,
        )

        visible = Sample.objects.visible_to(user)

        assert set(visible) == {samples["released"], samples["unpublished"]}

    def test_no_user_at_all_is_treated_as_a_visitor(self, samples):
        assert set(Sample.objects.visible_to(None)) == {samples["released"]}
