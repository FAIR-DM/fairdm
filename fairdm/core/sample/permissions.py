"""Permission backend for samples, inheriting permissions from the parent dataset."""

from fairdm.core.permissions import PolymorphicObjectPermissionBackend


class SamplePermissionBackend(PolymorphicObjectPermissionBackend):
    """Permission backend that lets a sample inherit permissions from its dataset.

    A user without a direct permission on a sample is checked against the dataset:

    - ``view_dataset`` gives ``view_sample``
    - ``change_dataset`` gives ``change_sample``, ``delete_sample`` and ``add_sample``
    - ``import_data`` on the dataset gives ``import_data`` on the sample

    Changing a dataset confers deleting its samples, so a ``change_dataset``-only user can delete
    a sample they can freely edit. A specimen type such as ``RockSample`` works the same as
    ``Sample``, because ``assign_perm`` normalises it to the base instance that owns the
    permission.

    Attributes:
        supports_object_permissions: Object-level permissions are supported.
        supports_anonymous_user: Anonymous users are passed to the backend.

    Example:
        ```python
        from fairdm.core.utils import assign_perm

        assign_perm("view_dataset", user, dataset)
        user.has_perm("sample.view_sample", sample)  # True, inherited from the dataset
        ```
    """

    supports_object_permissions = True
    supports_anonymous_user = True

    def has_perm(self, user_obj, perm, obj=None):
        """Check the permission directly on the sample, then through its dataset.

        Args:
            user_obj: The user to check.
            perm: The permission, such as ``sample.view_sample``.
            obj: The object the permission is checked on. Non-samples go to the parent backend.

        Returns:
            True when the user holds the permission on the sample or its dataset.
        """
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        from fairdm.core.sample.models import Sample

        if not isinstance(obj, Sample):
            return super().has_perm(user_obj, perm, obj)

        if super().has_perm(user_obj, perm, obj):
            return True

        if obj.dataset:
            permission_map = {
                "sample.view_sample": "dataset.view_dataset",
                "sample.change_sample": "dataset.change_dataset",
                "sample.delete_sample": "dataset.change_dataset",
                "sample.add_sample": "dataset.change_dataset",
                "sample.import_data": "dataset.import_data",
            }

            dataset_perm = permission_map.get(perm)
            if dataset_perm:
                return super().has_perm(user_obj, dataset_perm, obj.dataset)

        return False
