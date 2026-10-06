"""Unit tests for Sample model permissions."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from fairdm.core.sample.models import Sample
from fairdm.core.utils import assign_perm


@pytest.mark.django_db
class TestSampleDeclaredPermissions:
    def test_the_rights_the_level_table_names_are_declared(self):
        codenames = set(
            Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(Sample)
            ).values_list("codename", flat=True)
        )
        assert {
            "view_sample",
            "change_sample",
            "delete_sample",
            "add_sample",
            "import_data",
        } <= codenames


@pytest.mark.django_db
class TestSampleNoRights:
    # Must return False, not raise: guardian raises WrongAppError for a specimen
    # instance when the backend does not normalise the content type.
    def test_no_rights_anywhere_refuses_every_right(self, rock_sample, user):
        assert user.has_perm("sample.view_sample", rock_sample) is False
        assert user.has_perm("sample.change_sample", rock_sample) is False
        assert user.has_perm("sample.delete_sample", rock_sample) is False

    def test_a_right_on_a_different_dataset_does_not_leak(
        self, rock_sample, dataset, user
    ):
        from fairdm.factories import DatasetFactory

        other_dataset = DatasetFactory(project=dataset.project)
        assign_perm("change_dataset", user, other_dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is False


@pytest.mark.django_db
class TestObjectPermissionsSurvive:
    def test_organization_grant_still_resolves(self, user):
        from fairdm.factories import OrganizationFactory

        organization = OrganizationFactory()
        assign_perm("view_organization", user, organization)

        assert user.has_perm("contributors.view_organization", organization) is True


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
