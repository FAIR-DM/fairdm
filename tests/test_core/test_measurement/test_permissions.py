"""Unit tests for Measurement model permissions."""

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from guardian.shortcuts import assign_perm as guardian_assign_perm

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.measurement.models import Measurement
from fairdm.core.measurement.permissions import MeasurementPermissionBackend
from fairdm.core.utils import assign_perm as fairdm_assign_perm
from fairdm.core.utils import get_permission_target
from fairdm.core.utils import get_perms as fairdm_get_perms
from fairdm.core.utils import remove_perm as fairdm_remove_perm
from fairdm.factories import DatasetFactory, PersonFactory


@pytest.fixture
def user(db):
    # PersonFactory leaves about 1 in 5 users inactive, and guardian denies an inactive
    # user every object permission.
    return PersonFactory(is_active=True)


@pytest.mark.django_db
class TestMeasurementPermissionInheritance:
    def test_measurement_inherits_view_permission_from_dataset(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("dataset.view_dataset", user, measurement.dataset)

        assert user.has_perm("measurement.view_measurement", measurement)

    def test_measurement_inherits_change_permission_from_dataset(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("dataset.change_dataset", user, measurement.dataset)

        assert user.has_perm("measurement.change_measurement", measurement)

    def test_measurement_inherits_delete_permission_from_dataset(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("dataset.delete_dataset", user, measurement.dataset)

        assert user.has_perm("measurement.delete_measurement", measurement)

    def test_measurement_does_not_inherit_without_dataset_permission(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert not user.has_perm("measurement.view_measurement", measurement)
        assert not user.has_perm("measurement.change_measurement", measurement)
        assert not user.has_perm("measurement.delete_measurement", measurement)

    def test_multiple_measurements_inherit_from_same_dataset(self, dataset, user):
        measurement1 = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )
        measurement2 = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )

        fairdm_assign_perm("dataset.view_dataset", user, dataset)

        assert user.has_perm("measurement.view_measurement", measurement1)
        assert user.has_perm("measurement.view_measurement", measurement2)


@pytest.mark.django_db
class TestMeasurementGuardianIntegration:
    def test_can_assign_object_level_permissions_to_measurement(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("measurement.view_measurement", user, measurement)

        assert user.has_perm("measurement.view_measurement", measurement)
        assert "view_measurement" in fairdm_get_perms(user, measurement)

    def test_can_assign_multiple_permissions_to_measurement(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("measurement.view_measurement", user, measurement)
        fairdm_assign_perm("measurement.change_measurement", user, measurement)

        assert user.has_perm("measurement.view_measurement", measurement)
        assert user.has_perm("measurement.change_measurement", measurement)
        assert not user.has_perm("measurement.delete_measurement", measurement)

    def test_can_remove_object_level_permissions_from_measurement(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("measurement.view_measurement", user, measurement)
        assert user.has_perm("measurement.view_measurement", measurement)

        fairdm_remove_perm("measurement.view_measurement", user, measurement)
        assert not user.has_perm("measurement.view_measurement", measurement)

    def test_permissions_are_object_specific(self, user):
        measurement1 = ExampleMeasurementFactory(sample=RockSampleFactory())
        measurement2 = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("measurement.view_measurement", user, measurement1)

        assert user.has_perm("measurement.view_measurement", measurement1)
        assert not user.has_perm("measurement.view_measurement", measurement2)

    def test_direct_permission_coexists_with_inherited_dataset_permission(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("dataset.view_dataset", user, measurement.dataset)
        fairdm_assign_perm("measurement.change_measurement", user, measurement)

        assert user.has_perm("measurement.view_measurement", measurement)
        assert user.has_perm("measurement.change_measurement", measurement)
        assert not user.has_perm("measurement.delete_measurement", measurement)


@pytest.mark.django_db
class TestCrossDatasetPermissionBoundaries:
    def test_measurement_permissions_based_on_measurement_dataset_not_sample_dataset(
        self, user
    ):
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        sample_b = RockSampleFactory(dataset=dataset_b)

        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        fairdm_assign_perm("dataset.change_dataset", user, dataset_a)

        assert user.has_perm("measurement.change_measurement", measurement_a)
        assert not user.has_perm("sample.change_sample", sample_b)

    def test_cannot_edit_cross_dataset_sample_without_sample_dataset_permission(
        self, user
    ):
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        sample_b = RockSampleFactory(dataset=dataset_b)

        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        fairdm_assign_perm("dataset.change_dataset", user, dataset_a)
        fairdm_assign_perm("dataset.view_dataset", user, dataset_a)

        assert user.has_perm("measurement.change_measurement", measurement_a)
        assert not user.has_perm("sample.change_sample", sample_b)

    def test_dataset_permissions_correctly_isolate_cross_dataset_references(self, user):
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")
        dataset_c = DatasetFactory(name="Dataset C")

        sample_a = RockSampleFactory(dataset=dataset_a)
        sample_b = RockSampleFactory(dataset=dataset_b)

        measurement_in_c_ref_sample_a = ExampleMeasurementFactory(
            dataset=dataset_c, sample=sample_a
        )
        measurement_in_c_ref_sample_b = ExampleMeasurementFactory(
            dataset=dataset_c, sample=sample_b
        )

        fairdm_assign_perm("dataset.change_dataset", user, dataset_c)
        fairdm_assign_perm("dataset.view_dataset", user, dataset_a)

        assert user.has_perm(
            "measurement.change_measurement", measurement_in_c_ref_sample_a
        )
        assert user.has_perm(
            "measurement.change_measurement", measurement_in_c_ref_sample_b
        )

        assert user.has_perm("sample.view_sample", sample_a)
        assert not user.has_perm("sample.change_sample", sample_a)

        assert not user.has_perm("sample.view_sample", sample_b)
        assert not user.has_perm("sample.change_sample", sample_b)


@pytest.mark.django_db
class TestMeasurementRegisteredTypePermissions:
    def test_grant_on_registered_type_matches_the_bare_record(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        fairdm_assign_perm("measurement.change_measurement", user, measurement)

        bare_record = Measurement.objects.non_polymorphic().get(pk=measurement.pk)
        assert user.has_perm("measurement.change_measurement", measurement)
        assert user.has_perm("measurement.change_measurement", bare_record)
        assert fairdm_get_perms(user, measurement) == fairdm_get_perms(
            user, bare_record
        )

    def test_guardian_raw_assign_perm_cannot_grant_on_the_registered_type_directly(
        self, user
    ):
        # The permission is declared on Measurement's content type while the registered
        # type's instance carries its own.
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        with pytest.raises(Permission.DoesNotExist):
            guardian_assign_perm("measurement.change_measurement", user, measurement)

    def test_assign_perm_normalises_the_grant_target_to_the_base_record(self, user):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        target = get_permission_target(measurement, "measurement.change_measurement")

        assert type(measurement) is not Measurement
        assert type(target) is Measurement
        assert target.pk == measurement.pk


class TestMeasurementPermissionBackendRegistration:
    def test_measurement_permission_backend_is_registered(self):
        backend_path = (
            f"{MeasurementPermissionBackend.__module__}."
            f"{MeasurementPermissionBackend.__qualname__}"
        )
        assert backend_path in settings.AUTHENTICATION_BACKENDS


@pytest.mark.django_db
class TestAnonymousUserPermissions:
    def test_anonymous_user_cannot_view_measurement(self, client):
        from django.contrib.auth.models import AnonymousUser

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        anonymous = AnonymousUser()

        assert not anonymous.has_perm("measurement.view_measurement", measurement)
        assert not anonymous.has_perm("measurement.change_measurement", measurement)
        assert not anonymous.has_perm("measurement.delete_measurement", measurement)

    def test_anonymous_user_cannot_change_measurement(self, client):
        from django.contrib.auth.models import AnonymousUser

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        anonymous = AnonymousUser()

        assert not anonymous.has_perm("measurement.change_measurement", measurement)

    def test_anonymous_user_cannot_delete_measurement(self, client):
        from django.contrib.auth.models import AnonymousUser

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        anonymous = AnonymousUser()

        assert not anonymous.has_perm("measurement.delete_measurement", measurement)

    def test_public_dataset_measurements_not_accessible_to_anonymous_without_explicit_permission(
        self, client
    ):
        from django.contrib.auth.models import AnonymousUser

        dataset = DatasetFactory()
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), dataset=dataset
        )
        anonymous = AnonymousUser()

        # Even if dataset is "public", anonymous users need explicit view permissions
        assert not anonymous.has_perm("measurement.view_measurement", measurement)


@pytest.mark.django_db
class TestCrossDatasetEditingRights:
    def test_user_with_measurement_dataset_rights_can_edit_the_measurement(self, user):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()
        sample_b = RockSampleFactory(dataset=dataset_b)
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        fairdm_assign_perm("dataset.change_dataset", user, dataset_a)

        assert user.has_perm("measurement.change_measurement", measurement_a)

    def test_user_with_measurement_dataset_rights_cannot_edit_the_sample(self, user):
        dataset_a = DatasetFactory()
        dataset_b = DatasetFactory()
        sample_b = RockSampleFactory(dataset=dataset_b)
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        fairdm_assign_perm("dataset.change_dataset", user, dataset_a)

        assert not user.has_perm("sample.change_sample", sample_b)
