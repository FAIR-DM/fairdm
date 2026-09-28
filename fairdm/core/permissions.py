"""The shared object-permission backend for FairDM's polymorphic core records.

``Sample``, ``Measurement`` and ``Contributor`` (``Person``/``Organization``) are all
django-polymorphic models. A permission declared on the polymorphic base, such as
``change_sample``, is filed under the base's content type, but a subclass instance
(``RockSample``) carries its own app label and its own content type.
``guardian.backends.ObjectPermissionBackend.has_perm`` compares the permission's app label
against the object's, and raises ``WrongAppError`` when neither matches.

The record-specific backends all extend this one, and it is registered directly in
``AUTHENTICATION_BACKENDS`` in place of raw guardian, so that datasets, projects and
organisations also resolve through it.
"""

from guardian.backends import ObjectPermissionBackend

from .utils import get_non_polymorphic_instance, get_permission_target


class PolymorphicObjectPermissionBackend(ObjectPermissionBackend):
    """Normalise a polymorphic instance to its base before the object-level check.

    Gated on the object, not on the permission string: the underlying library only compares
    application labels when the permission carries one, so a gate keyed on that comparison never
    fires for an unqualified permission and the failure becomes a silent denial rather than an
    error. Normalisation only happens when the instance's real class differs from its
    polymorphic base and that base owns the permission being checked. A record whose
    permissions are declared on its own content type (``Organization``) is left alone.
    """

    def has_perm(self, user_obj, perm, obj=None):
        """Check the permission against the base instance, denying organisation management."""
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
        base_class = getattr(obj, "type_of", None) if obj is not None else None
        if base_class is None or type(obj) is base_class:
            return super().get_all_permissions(user_obj, obj)

        return super().get_all_permissions(user_obj, obj) | super().get_all_permissions(
            user_obj, get_non_polymorphic_instance(obj)
        )
