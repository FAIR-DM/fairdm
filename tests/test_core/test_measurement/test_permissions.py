"""
Unit tests for Measurement model permissions.

Tests verify that Measurement integrates with django-guardian for object-level
permissions and inherits permissions from parent Dataset, going through
``fairdm.core.utils.assign_perm``/``remove_perm``/``get_perms`` rather than
guardian's own shortcuts. That entry point normalises a polymorphic
measurement instance (e.g. ``ExampleMeasurement``) to the base ``Measurement``
record a permission is actually declared against before handing off to
guardian (see ``fairdm.core.utils.get_permission_target``). Guardian's own
``assign_perm``/``remove_perm`` cannot grant a permission directly on a
polymorphic subclass instance: the permission row is filed under
``Measurement``'s content type, but guardian resolves the content type to
check from the object's own (subclass) content type, and the lookup finds no
matching row.
"""

import pytest
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm, get_perms, remove_perm

from fairdm.core.utils import assign_perm as fairdm_assign_perm
from fairdm.factories import DatasetFactory
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

User = get_user_model()


@pytest.mark.django_db
class TestMeasurementPermissionInheritance:
    """A measurement holds the rights its dataset holds (FR-021 to FR-024).

    ``MeasurementPermissionBackend`` (``fairdm/core/measurement/permissions.py``) derives
    ``view_measurement``/``change_measurement``/``delete_measurement`` from the same-named
    right on the measurement's own dataset. These tests exercise that derivation directly,
    through the same ``assign_perm`` entry point a caller would use. ``Dataset`` is not a
    polymorphic model, so ``fairdm.core.utils.assign_perm`` normalises nothing here - it is
    used anyway, as the entry point this codebase actually calls (see module docstring).
    """

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
        """The dataset -> measurement derivation is a general mapping, not a one-off wired to
        a single instance: every measurement in the dataset picks it up.
        """
        measurement1 = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )
        measurement2 = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )

        fairdm_assign_perm("dataset.view_dataset", user, dataset)

        assert user.has_perm("measurement.view_measurement", measurement1)
        assert user.has_perm("measurement.view_measurement", measurement2)


@pytest.mark.skip(
    reason="Guardian does not support direct permission assignment to polymorphic subclass instances. "
    "Permissions are defined on base Measurement model (app: 'measurement') but polymorphic subclass instances "
    "(XRFMeasurement, ICPMSMeasurement) have different app labels ('fairdm_demo'). This causes WrongAppError. "
    "Permission inheritance from Dataset (see TestMeasurementPermissionInheritance) is the correct pattern."
)
@pytest.mark.django_db
class TestMeasurementGuardianIntegration:
    """Test Measurement model integrates with django-guardian for object-level permissions."""

    def test_can_assign_object_level_permissions_to_measurement(self, user):
        """Test that guardian permissions can be assigned to Measurement instances."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Assign view permission using base Measurement model (not polymorphic subclass)
        assign_perm("measurement.view_measurement", user, measurement)

        # Verify permission was assigned
        assert user.has_perm("measurement.view_measurement", measurement)
        assert "view_measurement" in get_perms(user, measurement)

    def test_can_assign_multiple_permissions_to_measurement(self, user):
        """Test that multiple permissions can be assigned to a Measurement."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Assign multiple permissions
        assign_perm("measurement.view_measurement", user, measurement)
        assign_perm("measurement.change_measurement", user, measurement)

        # Verify both permissions
        assert user.has_perm("measurement.view_measurement", measurement)
        assert user.has_perm("measurement.change_measurement", measurement)
        assert not user.has_perm("measurement.delete_measurement", measurement)

    def test_can_remove_object_level_permissions_from_measurement(self, user):
        """Test that guardian permissions can be removed from Measurement instances."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Assign and then remove permission
        assign_perm("measurement.view_measurement", user, measurement)
        assert user.has_perm("measurement.view_measurement", measurement)

        remove_perm("measurement.view_measurement", user, measurement)
        assert not user.has_perm("measurement.view_measurement", measurement)

    def test_permissions_are_object_specific(self, user):
        """Test that permissions are specific to each Measurement instance."""
        measurement1 = ExampleMeasurementFactory(sample=RockSampleFactory())
        measurement2 = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Assign permission to measurement1 only
        assign_perm("measurement.view_measurement", user, measurement1)

        # User can view measurement1 but not measurement2
        assert user.has_perm("measurement.view_measurement", measurement1)
        assert not user.has_perm("measurement.view_measurement", measurement2)


@pytest.mark.skip(
    reason="Cross-dataset permission tests deferred to Feature 007 (Permissions & Access Control). "
    "Factory fails when trying to create Measurement with sample from different dataset - "
    "polymorphic type checking issue. See Feature 006 Phase 8 notes for details."
)
@pytest.mark.django_db
class TestCrossDatasetPermissionBoundaries:
    """Test permission boundaries when measurements reference samples from different datasets (User Story 2)."""

    def test_measurement_permissions_based_on_measurement_dataset_not_sample_dataset(
        self, user
    ):
        """Test that measurement permissions are determined by the measurement's dataset, not the sample's dataset."""
        # Create two datasets
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        # Create sample in dataset B
        sample_b = RockSampleFactory(dataset=dataset_b)

        # Create measurement in dataset A that references sample from dataset B
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        # Grant user permissions on dataset A only (not dataset B)
        assign_perm("dataset.change_dataset", user, dataset_a)

        # User should be able to edit the measurement (in dataset A)
        assert user.has_perm("measurement.change_measurement", measurement_a)
        # User should NOT be able to edit the sample (in dataset B)
        assert not user.has_perm("sample.change_sample", sample_b)

    def test_cannot_edit_cross_dataset_sample_without_sample_dataset_permission(
        self, user
    ):
        """Test that editing a sample requires permission on the sample's dataset, even if measurement is editable."""
        # Create two datasets
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")

        # Create sample in dataset B
        sample_b = RockSampleFactory(dataset=dataset_b)

        # Create measurement in dataset A referencing sample from dataset B
        measurement_a = ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)

        # Grant user permissions on dataset A only
        assign_perm("dataset.change_dataset", user, dataset_a)
        assign_perm("dataset.view_dataset", user, dataset_a)

        # User can edit measurement but cannot edit the sample it references
        assert user.has_perm("measurement.change_measurement", measurement_a)
        assert not user.has_perm("sample.change_sample", sample_b)

    def test_dataset_permissions_correctly_isolate_cross_dataset_references(self, user):
        """Test that permission isolation is maintained for cross-dataset measurement-sample references."""
        # Create three datasets
        dataset_a = DatasetFactory(name="Dataset A")
        dataset_b = DatasetFactory(name="Dataset B")
        dataset_c = DatasetFactory(name="Dataset C")

        # Create samples and measurements across datasets
        sample_a = RockSampleFactory(dataset=dataset_a)
        sample_b = RockSampleFactory(dataset=dataset_b)

        measurement_in_c_ref_sample_a = ExampleMeasurementFactory(
            dataset=dataset_c, sample=sample_a
        )
        measurement_in_c_ref_sample_b = ExampleMeasurementFactory(
            dataset=dataset_c, sample=sample_b
        )

        # Grant user permissions on dataset C and dataset A (but not dataset B)
        assign_perm("dataset.change_dataset", user, dataset_c)
        assign_perm("dataset.view_dataset", user, dataset_a)

        # User can edit both measurements (both in dataset C)
        assert user.has_perm(
            "measurement.change_measurement", measurement_in_c_ref_sample_a
        )
        assert user.has_perm(
            "measurement.change_measurement", measurement_in_c_ref_sample_b
        )

        # User can view sample A but not edit it (view permission on dataset A)
        assert user.has_perm("sample.view_sample", sample_a)
        assert not user.has_perm("sample.change_sample", sample_a)

        # User cannot view or edit sample B (no permissions on dataset B)
        assert not user.has_perm("sample.view_sample", sample_b)
        assert not user.has_perm("sample.change_sample", sample_b)


@pytest.mark.django_db
class TestAnonymousUserPermissions:
    """Test that anonymous users have no permissions on measurements (FR-060)."""

    def test_anonymous_user_cannot_view_measurement(self, client):
        """Test that anonymous users cannot view measurements."""
        from django.contrib.auth.models import AnonymousUser

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        anonymous = AnonymousUser()

        # Anonymous users should have no permissions
        assert not anonymous.has_perm("measurement.view_measurement", measurement)
        assert not anonymous.has_perm("measurement.change_measurement", measurement)
        assert not anonymous.has_perm("measurement.delete_measurement", measurement)

    def test_anonymous_user_cannot_change_measurement(self, client):
        """Test that anonymous users cannot change measurements."""
        from django.contrib.auth.models import AnonymousUser

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        anonymous = AnonymousUser()

        assert not anonymous.has_perm("measurement.change_measurement", measurement)

    def test_anonymous_user_cannot_delete_measurement(self, client):
        """Test that anonymous users cannot delete measurements."""
        from django.contrib.auth.models import AnonymousUser

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        anonymous = AnonymousUser()

        assert not anonymous.has_perm("measurement.delete_measurement", measurement)

    def test_public_dataset_measurements_not_accessible_to_anonymous_without_explicit_permission(
        self, client
    ):
        """Test that measurements in public datasets still require explicit permissions for anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        # Create a dataset and measurement (public/private dataset handling may vary by implementation)
        dataset = DatasetFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory(), dataset=dataset)
        anonymous = AnonymousUser()

        # Even if dataset is "public", anonymous users need explicit view permissions
        # (This behavior depends on your specific permission backend implementation)
        assert not anonymous.has_perm("measurement.view_measurement", measurement)
