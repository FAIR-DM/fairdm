"""
Custom permission backends for Sample model.

Provides guardian integration with permission inheritance from Dataset.
"""

from guardian.backends import ObjectPermissionBackend


class SamplePermissionBackend(ObjectPermissionBackend):
    """
    Custom permission backend for Sample model that inherits permissions from parent Dataset.

    This backend extends django-guardian's ObjectPermissionBackend to support:
    1. Object-level permissions on Sample instances (FR-059)
    2. Permission inheritance from parent Dataset (FR-060)

    Permission Mapping:
    - view_dataset → view_sample
    - change_dataset → change_sample
    - delete_dataset → delete_sample

    Usage:
        Add to settings.AUTHENTICATION_BACKENDS:
        ```python
        AUTHENTICATION_BACKENDS = [
            "django.contrib.auth.backends.ModelBackend",
            "fairdm.core.sample.permissions.SamplePermissionBackend",
        ]
        ```

    Examples:
        ```python
        from guardian.shortcuts import assign_perm

        # Direct sample permission
        assign_perm("view_sample", user, sample)
        user.has_perm("view_sample", sample)  # True

        # Inherited from dataset
        assign_perm("view_dataset", user, dataset)
        user.has_perm("view_sample", sample)  # True (inherited)
        ```
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has permission on object.

        For Sample objects, checks:
        1. Direct sample-level permissions via guardian
        2. Inherited dataset-level permissions

        Args:
            user_obj: User instance
            perm: Permission string (e.g., 'sample.view_sample')
            obj: Optional Sample instance

        Returns:
            bool: True if user has permission
        """
        # Let parent backend handle non-Sample objects and global permissions
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        # Import here to avoid circular imports
        from fairdm.core.sample.models import Sample

        # Only handle Sample objects
        if not isinstance(obj, Sample):
            return super().has_perm(user_obj, perm, obj)

        # Check direct sample permission first
        if super().has_perm(user_obj, perm, obj):
            return True

        # Check inherited dataset permission
        if obj.dataset:
            # Map sample permissions to dataset permissions
            permission_map = {
                "sample.view_sample": "dataset.view_dataset",
                "sample.change_sample": "dataset.change_dataset",
                "sample.delete_sample": "dataset.delete_dataset",
                "sample.add_sample": "dataset.change_dataset",  # Adding samples requires dataset change permission
                "sample.import_data": "dataset.import_data",
            }

            # Get corresponding dataset permission
            dataset_perm = permission_map.get(perm)
            if dataset_perm:
                # Check if user has permission on parent dataset
                return super().has_perm(user_obj, dataset_perm, obj.dataset)

        return False
