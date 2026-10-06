"""The shared object-permission backend for stored guardian rows on polymorphic models.

``Sample``, ``Measurement`` and ``Contributor`` (``Person``/``Organization``) are all
django-polymorphic models. A permission declared on the polymorphic base, such as
``change_contributor``, is filed under the base's content type, but a subclass instance
(``Organization``) carries its own app label and its own content type.
``guardian.backends.ObjectPermissionBackend.has_perm`` compares the permission's app label
against the object's, and raises ``WrongAppError`` when neither matches.

``OrganizationPermissionBackend`` extends this one, and it is registered directly in
``AUTHENTICATION_BACKENDS`` in place of raw guardian, so that organisations and any model a
portal defines resolve through it. A project, dataset, sample or measurement never does: its
rights come from contribution levels (``RecordLevelBackend``), and a stored row grants nothing.
"""

from guardian.backends import ObjectPermissionBackend

from .utils import get_non_polymorphic_instance, get_permission_target


class PolymorphicObjectPermissionBackend(ObjectPermissionBackend):
    """Normalise a polymorphic instance to its base before the object-level check.

    A project, dataset, sample or measurement is refused outright: only a contribution level
    gives rights over those, so a stored row on one grants nothing.

    Gated on the object, not on the permission string: the underlying library only compares
    application labels when the permission carries one, so a gate keyed on that comparison never
    fires for an unqualified permission and the failure becomes a silent denial rather than an
    error. Normalisation only happens when the instance's real class differs from its
    polymorphic base and that base owns the permission being checked. A record whose
    permissions are declared on its own content type (``Organization``) is left alone.
    """

    def has_perm(self, user_obj, perm, obj=None):
        """Check the permission against the base instance, denying organisation management.

        Args:
            user_obj: The user.
            perm: The permission, with or without its app label.
            obj: The object the permission is asked on.

        Returns:
            False for a core record. Otherwise whether a stored row grants the permission.
        """
        from fairdm.contrib.contributors.access import RecordAccess

        if RecordAccess.is_core_record(obj):
            return False

        # Only OrganizationPermissionBackend may grant this. Django ORs every backend's answer,
        # so a stored guardian grant honoured here would override its decision.
        if obj is not None and perm in (
            "contributors.manage_organization",
            "manage_organization",
        ):
            from fairdm.contrib.contributors.models import Organization

            if isinstance(obj, Organization):
                return False

        return super().has_perm(user_obj, perm, get_permission_target(obj, perm))

    def get_all_permissions(self, user_obj, obj=None):
        """Merge the permissions filed under the subclass and its polymorphic base."""
        from fairdm.contrib.contributors.access import RecordAccess

        if RecordAccess.is_core_record(obj):
            return set()
        base_class = getattr(obj, "type_of", None) if obj is not None else None
        if base_class is None or type(obj) is base_class:
            return super().get_all_permissions(user_obj, obj)

        return super().get_all_permissions(user_obj, obj) | super().get_all_permissions(
            user_obj, get_non_polymorphic_instance(obj)
        )
