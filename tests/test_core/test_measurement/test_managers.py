"""T026/T028: the bare-record refusal holds for routes ``clean()`` alone does not cover.

``Measurement.clean()`` (fairdm/core/measurement/models.py:111) only runs when something calls
``full_clean()`` or ``clean()`` explicitly - forms and the admin do, ``Measurement.objects.create()``
and a bare ``.save()`` do not. T028 closes that gap with a ``pre_save`` guard; these tests prove the
manager route and the framework's own fixture-loading route are both refused by it, not merely by
validation.

Landed as a new file (mirroring ``managers.py``, per ``craft-tdd``'s "mirror the source tree" rule)
rather than added to ``tests/test_core/test_measurement/test_models.py`` - that file is on this
story's prohibited list (owned by a concurrently running story).
"""

import pytest
from django.core.exceptions import ValidationError

from fairdm.core.measurement.models import Measurement


@pytest.mark.django_db
class TestManagerRefusesABareMeasurement:
    """T026/T028: ``Measurement.objects.create()`` cannot bypass the base-record refusal."""

    def test_manager_create_refuses_a_bare_measurement(self, dataset, sample):
        """``Measurement.objects.create()`` - the manager route - is refused even
        though it bypasses form and admin validation entirely."""
        with pytest.raises(ValidationError):
            Measurement.objects.create(name="Direct", dataset=dataset, sample=sample)

    def test_direct_save_refuses_a_bare_measurement(self, dataset, sample):
        """A bare ``Measurement().save()`` - the route ``clean()`` alone does not cover,
        since nothing calls it - is refused too."""
        measurement = Measurement(name="Direct", dataset=dataset, sample=sample)

        with pytest.raises(ValidationError):
            measurement.save()

    def test_fixture_loading_refuses_a_bare_measurement(self, dataset, sample):
        """T026: no fixture in the framework creates a bare measurement - proven here by
        showing that even the lowest-level route, deserializing a raw fixture row for the
        base model, is refused. Deserializing sends ``pre_save`` on every raw object
        (``django.core.serializers``), which is why this route is covered by the same
        guard as the manager and a direct save."""
        from django.core import serializers

        payload = (
            '[{"model": "measurement.measurement", "pk": null, '
            f'"fields": {{"name": "Direct", "dataset": {dataset.pk}, "sample": {sample.pk}}}}}]'
        )
        (deserialized,) = serializers.deserialize("json", payload)

        with pytest.raises(ValidationError):
            deserialized.save()
