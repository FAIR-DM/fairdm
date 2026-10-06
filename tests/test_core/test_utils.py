"""Tests for the permission helpers in fairdm.core.utils."""

import pytest

from fairdm.core.utils import assign_perm
from fairdm.factories import DatasetFactory, PersonFactory


@pytest.fixture
def user(db):
    # PersonFactory leaves about 1 in 5 users inactive, and guardian denies an
    # inactive user every object permission.
    return PersonFactory(is_active=True)


@pytest.fixture
def dataset(db):
    return DatasetFactory()


@pytest.mark.django_db
class TestPolymorphicGatingWithoutTypeOf:
    def test_get_permission_target_returns_the_object_unchanged(self, dataset):
        from fairdm.core.utils import get_permission_target

        dataset.polymorphic_model_marker = True

        assert get_permission_target(dataset, "dataset.view_dataset") is dataset

    def test_get_non_polymorphic_instance_returns_the_object_unchanged(self, dataset):
        from fairdm.core.utils import get_non_polymorphic_instance

        dataset.polymorphic_model_marker = True

        assert get_non_polymorphic_instance(dataset) is dataset

    def test_get_perms_does_not_raise(self, dataset, user):
        from fairdm.core.utils import get_perms

        dataset.polymorphic_model_marker = True

        assert get_perms(user, dataset) == []


@pytest.mark.django_db
class TestGetObjectsForUserNormalisesPolymorphicContentType:
    def test_a_grant_filed_under_the_base_content_type_is_found(self, dataset, user):
        from demo.factories import RockSampleFactory
        from demo.models import RockSample
        from fairdm.core.utils import get_objects_for_user

        granted = RockSampleFactory(dataset=dataset)
        ungranted = RockSampleFactory(dataset=dataset)
        assign_perm("view_sample", user, granted)

        naive_perm = f"{RockSample._meta.app_label}.view_{RockSample._meta.model_name}"
        results = get_objects_for_user(user, naive_perm, RockSample.objects.all())

        assert granted in results
        assert ungranted not in results
