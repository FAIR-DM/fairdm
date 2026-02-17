"""Custom permission backends for Measurement model.

Provides guardian integration with permission inheritance from Dataset.

Usage:
    Add to settings.AUTHENTICATION_BACKENDS:

    ```python
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
        "guardian.backends.ObjectPermissionBackend",
        "fairdm.core.sample.permissions.SamplePermissionBackend",
        "fairdm.core.measurement.permissions.MeasurementPermissionBackend",  # Add this
    ]
    ```
"""

from guardian.backends import ObjectPermissionBackend


class MeasurementPermissionBackend(ObjectPermissionBackend):
    """Custom permission backend for Measurement model with dataset inheritance.

    This backend extends django-guardian's ObjectPermissionBackend to support:
    1. Object-level permissions on Measurement instances
    2. Permission inheritance from parent Dataset

    Permission Mapping:
    - view_dataset → view_measurement
    - change_dataset → change_measurement
    - delete_dataset → delete_measurement
    - change_dataset → add_measurement (creating measurements requires dataset change permission)
    - import_data → import_data (bulk import inherits from dataset)

    Cross-Dataset Context:
    When a measurement in Dataset A references a sample from Dataset B:
    - Measurement edit permissions are controlled by Dataset A
    - Sample edit permissions are controlled by Dataset B (via SamplePermissionBackend)
    - This maintains clear permission boundaries for cross-dataset workflows

    Examples:
        ```python
        from guardian.shortcuts import assign_perm

        # Direct measurement permission
        assign_perm("view_measurement", user, measurement)
        user.has_perm("view_measurement", measurement)  # True

        # Inherited from dataset
        assign_perm("view_dataset", user, dataset)
        user.has_perm("view_measurement", measurement)  # True (inherited)

        # Cross-dataset scenario
        measurement_a = Measurement.objects.create(dataset=dataset_a, sample=sample_b)
        assign_perm("change_dataset", user, dataset_a)
        user.has_perm("change_measurement", measurement_a)  # True (can edit measurement)
        user.has_perm("change_sample", sample_b)  # False (requires Dataset B permission)
        ```
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """Check if user has permission on object.

        For Measurement objects, checks:
        1. Direct measurement-level permissions via guardian
        2. Inherited dataset-level permissions

        Args:
            user_obj: User instance
            perm: Permission string (e.g., 'measurement.view_measurement')
            obj: Optional Measurement instance

        Returns:
            bool: True if user has permission
        """
        # Let parent backend handle non-Measurement objects and global permissions
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        # Import here to avoid circular imports
        from fairdm.core.measurement.models import Measurement

        # Only handle Measurement objects
        if not isinstance(obj, Measurement):
            return super().has_perm(user_obj, perm, obj)

        # Check direct measurement permission first
        if super().has_perm(user_obj, perm, obj):
            return True

        # Check inherited dataset permission
        if obj.dataset:
            # Map measurement permissions to dataset permissions
            permission_map = {
                "measurement.view_measurement": "dataset.view_dataset",
                "measurement.change_measurement": "dataset.change_dataset",
                "measurement.delete_measurement": "dataset.delete_dataset",
                "measurement.add_measurement": "dataset.change_dataset",  # Creating requires change permission
                "measurement.import_data": "dataset.import_data",
            }

            # Get corresponding dataset permission
            dataset_perm = permission_map.get(perm)
            if dataset_perm:
                # Check if user has permission on parent dataset
                return super().has_perm(user_obj, dataset_perm, obj.dataset)

        return False
