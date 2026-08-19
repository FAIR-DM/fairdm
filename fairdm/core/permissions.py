"""The shared object-permission backend for FairDM's polymorphic core records.

``Sample``, ``Measurement`` and ``Contributor`` (``Person``/``Organization``) are all
django-polymorphic models. A permission declared on the polymorphic base - ``change_sample``,
say - is filed under the base's content type, but a subclass instance (``RockSample``) carries
its own app label and its own content type.
``guardian.backends.ObjectPermissionBackend.has_perm`` compares the permission's app label
against the object's, and raises ``WrongAppError`` when neither matches (``research.md`` R2).

Fixed once, here, rather than per record type: the sample, measurement and organisation backends
all re-parent onto this one (``decisions.md`` D-018), and it is registered directly in
``AUTHENTICATION_BACKENDS`` in place of raw guardian, so that datasets, projects and
organisations - none of which delegate to a record-specific backend - keep resolving through it
too, rather than through an unwritten delegation contract.
"""

from guardian.backends import ObjectPermissionBackend

from .utils import get_non_polymorphic_instance, get_permission_target


class PolymorphicObjectPermissionBackend(ObjectPermissionBackend):
    """Normalises a polymorphic instance to its base before the object-level check.

    Gated on the object, not on the permission string: the underlying library only compares
    application labels when the permission carries one, so a gate keyed on that comparison never
    fires for an unqualified permission and the failure becomes a silent denial rather than an
    error. Normalisation itself only happens when the instance's real class differs from its
    polymorphic base *and* that base owns the permission being checked - so a record whose
    permissions are declared on its own content type (``Organization``) is left alone, and no
    currently-passing check changes behaviour.
    """

    def has_perm(self, user_obj, perm, obj=None):
        return super().has_perm(user_obj, perm, get_permission_target(obj, perm))

    def get_all_permissions(self, user_obj, obj=None):
        """List every permission this backend grants on ``obj`` (F4).

        Left overriding only ``has_perm`` meant ``user.get_all_permissions(specimen)`` still read
        the subclass's own content type and never surfaced a grant filed under the polymorphic
        base. Unlike ``has_perm``, there is no single ``perm`` here to gate a base-owns-it check
        on (D-019's "no single perm" problem again), so this merges both content types' rows the
        same way :func:`fairdm.core.utils.get_perms` does, rather than picking one.
        """
        base_class = getattr(obj, "type_of", None) if obj is not None else None
        if base_class is None or type(obj) is base_class:
            return super().get_all_permissions(user_obj, obj)

        return super().get_all_permissions(user_obj, obj) | super().get_all_permissions(
            user_obj, get_non_polymorphic_instance(obj)
        )
