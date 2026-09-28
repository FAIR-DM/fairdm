"""Permission backend for measurements, inheriting permissions from the parent dataset.

Add ``fairdm.core.measurement.permissions.MeasurementPermissionBackend`` to
``AUTHENTICATION_BACKENDS`` after ``fairdm.core.permissions.PolymorphicObjectPermissionBackend``.
"""

from fairdm.core.permissions import PolymorphicObjectPermissionBackend


class MeasurementPermissionBackend(PolymorphicObjectPermissionBackend):
    """Permission backend that lets a measurement inherit permissions from its dataset.

    A user without a direct permission on a measurement is checked against the dataset:

    - ``view_dataset`` gives ``view_measurement``
    - ``change_dataset`` gives ``change_measurement`` and ``add_measurement``
    - ``delete_dataset`` gives ``delete_measurement``
    - ``import_data`` on the dataset gives ``import_data`` on the measurement

    When a measurement in dataset A references a sample from dataset B, the measurement's
    permissions come from A and the sample's from B (through ``SamplePermissionBackend``).

    Attributes:
        supports_object_permissions: Object-level permissions are supported.
        supports_anonymous_user: Anonymous users are passed to the backend.
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """Check the permission directly on the measurement, then through its dataset.

        Args:
            user_obj: The user to check.
            perm: The permission, such as ``measurement.view_measurement``.
            obj: The object the permission is checked on. Non-measurements go to the parent backend.

        Returns:
            True when the user holds the permission on the measurement or its dataset.
        """
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        from fairdm.core.measurement.models import Measurement

        if not isinstance(obj, Measurement):
            return super().has_perm(user_obj, perm, obj)

        if super().has_perm(user_obj, perm, obj):
            return True

        if obj.dataset:
            permission_map = {
                "measurement.view_measurement": "dataset.view_dataset",
                "measurement.change_measurement": "dataset.change_dataset",
                "measurement.delete_measurement": "dataset.delete_dataset",
                "measurement.add_measurement": "dataset.change_dataset",
                "measurement.import_data": "dataset.import_data",
            }

            dataset_perm = permission_map.get(perm)
            if dataset_perm:
                return super().has_perm(user_obj, dataset_perm, obj.dataset)

        return False
