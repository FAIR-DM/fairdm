"""
Custom permission backends for Sample model.

Provides guardian integration with permission inheritance from Dataset.
"""

from fairdm.core.permissions import PolymorphicObjectPermissionBackend


class SamplePermissionBackend(PolymorphicObjectPermissionBackend):
    """
    Custom permission backend for Sample model that inherits permissions from parent Dataset.

    This backend extends the shared ``PolymorphicObjectPermissionBackend`` (which normalises a
    specimen instance to its base ``Sample`` before the object-level check, see
    ``fairdm/core/permissions.py``) to support:
    1. Object-level permissions on Sample instances (FR-032)
    2. Permission inheritance from parent Dataset (FR-031)

    Permission Mapping:
    - view_dataset → view_sample
    - change_dataset → change_sample, delete_sample, add_sample

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
        from fairdm.core.utils import assign_perm

        # Direct sample permission - a specimen type such as ``RockSample`` works the same as
        # the base ``Sample``; ``assign_perm`` normalises it to the base instance that actually
        # owns the permission (FR-033b).
        assign_perm("view_sample", user, sample)
        user.has_perm("sample.view_sample", sample)  # True

        # Inherited from dataset
        assign_perm("view_dataset", user, dataset)
        user.has_perm("sample.view_sample", sample)  # True (inherited)
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
            # FR-031: changing a dataset confers changing AND deleting its samples, and adding
            # samples to it - not the dataset's own delete permission, which the specification
            # never mentions and which would otherwise leave a change_dataset-only user unable
            # to delete a sample they can freely edit.
            permission_map = {
                "sample.view_sample": "dataset.view_dataset",
                "sample.change_sample": "dataset.change_dataset",
                "sample.delete_sample": "dataset.change_dataset",
                "sample.add_sample": "dataset.change_dataset",  # Adding samples requires dataset change permission
                "sample.import_data": "dataset.import_data",
            }

            # Get corresponding dataset permission
            dataset_perm = permission_map.get(perm)
            if dataset_perm:
                # Check if user has permission on parent dataset
                return super().has_perm(user_obj, dataset_perm, obj.dataset)

        return False
