from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm, get_perms, remove_perm

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
    perms = Permission.objects.filter(content_type=ctype).values_list("codename", flat=True)
    for perm in perms:
        assign_perm(perm, user, obj)


def remove_all_model_perms(user, obj):
    for perm in get_perms(user, obj):
        remove_perm(perm, user, obj)
