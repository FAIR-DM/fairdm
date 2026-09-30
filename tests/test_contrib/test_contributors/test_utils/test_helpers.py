"""Tests for the contributor helpers."""

import pytest

from fairdm.contrib.contributors.utils.helpers import avatar_url
from fairdm.factories import OrganizationFactory, PersonFactory


@pytest.mark.django_db
class TestAvatarUrl:
    def test_a_contributor_without_an_image_has_no_avatar_url(self):
        assert avatar_url(PersonFactory(), "md") is None

    def test_nothing_has_no_avatar_url(self):
        assert avatar_url(None, "md") is None

    def test_small_sizes_get_the_small_thumbnail(self):
        person = PersonFactory(with_image=True)

        assert "150x150" in avatar_url(person, "sm")

    def test_large_sizes_get_the_medium_thumbnail(self):
        organization = OrganizationFactory(with_image=True)

        assert "600x600" in avatar_url(organization, "xl")

    def test_an_image_whose_file_is_missing_has_no_avatar_url(self):
        person = PersonFactory()
        person.image.name = "missing/nowhere.png"

        assert avatar_url(person, "md") is None
