"""Unit tests for Sample model permissions."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from fairdm.core.sample.models import Sample
from fairdm.core.utils import assign_perm, remove_perm


@pytest.mark.django_db
class TestSampleDeclaredPermissions:
    def test_the_rights_the_dataset_inheritance_map_consults_are_declared(self):
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
class TestSampleDirectPermissions:
    def test_direct_grant_holds_for_the_granted_specimen(self, rock_sample, user):
        assign_perm("change_sample", user, rock_sample)

        assert user.has_perm("sample.change_sample", rock_sample) is True

    def test_direct_grant_does_not_hold_for_another_specimen(
        self, rock_sample, water_sample, user
    ):
        assign_perm("view_sample", user, rock_sample)

        assert user.has_perm("sample.view_sample", water_sample) is False

    def test_direct_grant_can_be_removed(self, rock_sample, user):
        assign_perm("view_sample", user, rock_sample)
        assert user.has_perm("sample.view_sample", rock_sample) is True

        remove_perm("view_sample", user, rock_sample)
        assert user.has_perm("sample.view_sample", rock_sample) is False


@pytest.mark.django_db
class TestSamplePermissionInheritance:
    def test_view_dataset_confers_view_sample(self, rock_sample, user):
        assign_perm("view_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.view_sample", rock_sample) is True

    def test_change_dataset_confers_change_sample(self, rock_sample, user):
        assign_perm("change_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is True

    def test_change_dataset_confers_delete_sample(self, rock_sample, user):
        assign_perm("change_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.delete_sample", rock_sample) is True

    def test_change_dataset_confers_add_sample(self, rock_sample, user):
        assign_perm("change_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.add_sample", rock_sample) is True

    def test_view_dataset_alone_does_not_confer_change_sample(self, rock_sample, user):
        assign_perm("view_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is False

    def test_every_sample_in_the_dataset_inherits_the_same_grant(self, dataset, user):
        from demo.factories import RockSampleFactory, WaterSampleFactory

        sample1 = RockSampleFactory(dataset=dataset)
        sample2 = WaterSampleFactory(dataset=dataset)

        assign_perm("view_dataset", user, dataset)

        assert user.has_perm("sample.view_sample", sample1) is True
        assert user.has_perm("sample.view_sample", sample2) is True


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
    def test_dataset_grant_still_resolves(self, dataset, user):
        assign_perm("view_dataset", user, dataset)

        assert user.has_perm("dataset.view_dataset", dataset) is True

    def test_project_grant_still_resolves(self, project, user):
        assign_perm("view_project", user, project)

        assert user.has_perm("project.view_project", project) is True

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
class TestContributionRevocationIsNormalised:
    # Grants are filed under the Sample base content type, so revocation has to use
    # the same normalising wrappers or it silently removes nothing.
    def test_deleting_the_contribution_removes_the_grant(self, rock_sample, user):
        from fairdm.contrib.contributors.models import Contribution

        assign_perm("change_sample", user, rock_sample)
        assert user.has_perm("sample.change_sample", rock_sample) is True

        contribution = Contribution.add_to(user, rock_sample)

        contribution.delete()

        assert user.has_perm("sample.change_sample", rock_sample) is False


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


@pytest.mark.django_db
class TestGetAllPermissionsNormalisesPolymorphicContentType:
    # get_all_permissions must read the polymorphic base content type, not the
    # subclass's own, or a grant filed under the base never surfaces.
    def test_a_grant_filed_under_the_base_content_type_appears(self, rock_sample, user):
        assign_perm("view_sample", user, rock_sample)

        codenames = {p.split(".")[-1] for p in user.get_all_permissions(rock_sample)}

        assert "view_sample" in codenames
