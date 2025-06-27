from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm

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
    ctype = ContentType.objects.get_for_model(obj)
    perms = Permission.objects.filter(content_type=ctype)
    for perm in perms:
        assign_perm(perm.codename, user, obj)


def user_has_object_permissions(user, obj, permissions):
    """
    Check if the user has the specified permissions on the object.

    :param user: The user to check permissions for.
    :param obj: The object to check permissions on.
    :param permissions: A list of permission names to check.
    :return: True if the user has all specified permissions, False otherwise.
    """
    for perm in permissions:
        if not user.has_perm(f"{obj._meta.app_label}.{perm}", obj):
            return False
    return True
