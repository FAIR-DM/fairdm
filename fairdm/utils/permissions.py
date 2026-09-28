"""Helpers that assign and remove object-level permissions."""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Not guardian's raw shortcuts: a grant on a polymorphic subclass instance is filed under the
# base's content type, which the raw functions never look under, so removal would find nothing.
from fairdm.core.utils import assign_perm, get_perms, remove_perm

OBJECT_PERMS = [
    "add_{model_name}",
    "change_{model_name}",
    "delete_{model_name}",
    "view_{model_name}",
    "add_contributor",
    "modify_contributor",
    "modify_metadata",
    "import",
]


def assign_all_model_perms(user, obj):
    """Grant a user every permission defined for the object's model.

    Args:
        user: The user to grant permissions to.
        obj: The object to grant them on.
    """
    ctype = ContentType.objects.get_for_model(obj)
    perms = Permission.objects.filter(content_type=ctype).values_list(
        "codename", flat=True
    )
    for perm in perms:
        assign_perm(perm, user, obj)


def remove_all_model_perms(user, obj):
    """Remove every object-level permission a user holds on the object.

    Args:
        user: The user whose permissions to remove.
        obj: The object to remove them from.
    """
    for perm in get_perms(user, obj):
        remove_perm(perm, user, obj)
