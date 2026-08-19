"""Tests for User Story 2 — recording a measurement against a sample from another dataset.

Covers FR-005 and FR-006: the sample a measurement names may belong to a different dataset
from the measurement itself, and neither record's attribution nor its permission boundary is
altered by the other (T040), and the two records' lifecycles stay independent — the
measurement's own dataset governs its deletion, and the sample it names cannot be deleted
while it exists (T041).

Grants go through ``fairdm.core.utils.assign_perm``, never guardian's own shortcut: guardian's
``assign_perm`` resolves the object's own (subclass) content type directly, and a permission
declared on the polymorphic ``Measurement`` base cannot be stored against a subclass instance
(e.g. ``ExampleMeasurement``) through that path — see ``fairdm.core.utils.get_permission_target``.
"""

import pytest

from fairdm.core.utils import assign_perm as fairdm_assign_perm
from fairdm.factories import DatasetFactory, PersonFactory
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory


@pytest.fixture
def user(db):
    """A user for permission checks.

    ``PersonFactory.is_active`` is ``Faker("boolean", chance_of_getting_true=80)`` — roughly
    one user in five is inactive by default, and django-guardian's
    ``ObjectPermissionChecker.has_perm`` denies every object-level permission to an inactive
    user without consulting any assignment. Passed explicitly here so a grant under test is
    never masked by an unlucky factory draw.
    """
    return PersonFactory(is_active=True)


@pytest.mark.django_db
class TestCrossDatasetEditingRights:
    """T040 — a user holding editing rights on the measurement's dataset alone may edit the
    measurement, and may not edit the sample, when the sample belongs to a different dataset."""

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
