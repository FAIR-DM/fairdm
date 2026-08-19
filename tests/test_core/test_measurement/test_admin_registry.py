"""Tests that the measurement admin's type selection is driven by the registry.

T025, T032, T033. Lands in a new file rather than in
``tests/test_core/test_measurement/test_admin.py`` - that file is owned by a
concurrently running story for this feature and is out of this story's scope.

Covers:
    - T033: ``MeasurementParentAdmin.get_child_models()`` reads ``registry.measurements``,
      proven by monkeypatching the registry property rather than merely observing a
      non-empty list (``assert len(child_models) > 0`` establishes nothing about *where*
      the list came from).
    - T032: the administrative type selection offers exactly the registered measurement
      types - including one registered from outside the framework
      (``tests.registry_models.models.ConcreteMeasurement``) - and excludes records that
      are not measurements (``ConcreteSample``) and the unregistered base ``Measurement``.
    - T025: creating a bare ``Measurement`` is refused through the administrative
      interface - the parent admin's add view never offers the base type as a child,
      because ``Measurement`` is never a member of ``registry.measurements``.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from fairdm.core.measurement.admin import MeasurementParentAdmin
from fairdm.core.measurement.models import Measurement
from fairdm.registry import registry
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


@pytest.fixture
def measurement_parent_admin():
    """A ``MeasurementParentAdmin`` instance, the way Django admin builds one."""
    return MeasurementParentAdmin(Measurement, AdminSite())


class TestChildModelDiscoveryReadsTheRegistry:
    """T033: child-model discovery on the parent admin reads the registry."""

    def test_child_models_reads_the_registry(
        self, measurement_parent_admin, monkeypatch
    ):
        """Monkeypatching ``registry.measurements`` changes what the admin offers -
        proof the admin reads the registry rather than some other, coincidentally
        non-empty source."""
        sentinel = [ConcreteMeasurement]
        monkeypatch.setattr(
            type(registry), "measurements", property(lambda self: sentinel)
        )

        assert measurement_parent_admin.get_child_models() == sentinel

    def test_child_models_matches_registry_measurements(self, measurement_parent_admin):
        """Without patching, the admin's child models are exactly what the registry
        reports as registered measurement types."""
        assert measurement_parent_admin.get_child_models() == registry.measurements


@pytest.mark.django_db
class TestAdminOffersExactlyRegisteredMeasurementTypes:
    """T032: the type-selection interface offers exactly the registered types."""

    def test_offers_a_type_registered_from_outside_the_framework(
        self, clean_registry, measurement_parent_admin
    ):
        """``ConcreteMeasurement`` stands in for a type a portal defines and registers
        itself, outside the framework's own measurement types."""
        registry.register(ConcreteMeasurement)

        child_models = measurement_parent_admin.get_child_models()

        assert ConcreteMeasurement in child_models
        assert set(child_models) == set(registry.measurements)

    def test_excludes_a_registered_record_that_is_not_a_measurement(
        self, clean_registry, measurement_parent_admin
    ):
        """A registered ``Sample`` subclass never appears among the measurement
        choices, even though it shares the same registry."""
        registry.register(ConcreteMeasurement)
        registry.register(ConcreteSample)

        child_models = measurement_parent_admin.get_child_models()

        assert ConcreteMeasurement in child_models
        assert ConcreteSample not in child_models

    def test_excludes_the_unregistered_base_measurement(
        self, clean_registry, measurement_parent_admin
    ):
        """The base ``Measurement`` model is never registered (FR-010/FR-011), so it
        never appears as a type choice."""
        registry.register(ConcreteMeasurement)

        assert Measurement not in measurement_parent_admin.get_child_models()


@pytest.mark.django_db
class TestAdminRefusesTheBaseMeasurement:
    """T025: creating a bare measurement is refused through the administrative
    interface - the base type is never offered as a child to add."""

    def test_admin_refuses_the_base_content_type(self, admin_client):
        """The polymorphic parent admin's add view never offers the base type as a
        child. ``Measurement`` is never a member of ``registry.measurements`` (only
        registered measurement types are), so asking the add view to route to the
        base type's own content type is refused the same way an unregistered model
        would be - it is not among the child admins the parent knows how to
        delegate to."""
        ct = ContentType.objects.get_for_model(Measurement)
        response = admin_client.get(
            reverse("admin:measurement_measurement_add"), {"ct_id": ct.pk}
        )

        assert response.status_code == 403
