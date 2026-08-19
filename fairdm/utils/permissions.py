from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# `fairdm.core.utils`'s wrappers, not guardian's raw shortcuts (F3): a right granted through
# `fairdm.core.utils.assign_perm` on a polymorphic subclass instance (e.g. a specimen) is filed
# under the polymorphic base's content type, not the subclass's own. The raw guardian functions
# only ever look under the object's own content type, so `remove_all_model_perms` - fired from
# `Contribution.remove_user_perms` with a concrete specimen - found nothing there and silently
# left the grant in place.
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
    ctype = ContentType.objects.get_for_model(obj)
    perms = Permission.objects.filter(content_type=ctype).values_list(
        "codename", flat=True
    )
    for perm in perms:
        assign_perm(perm, user, obj)


def remove_all_model_perms(user, obj):
    for perm in get_perms(user, obj):
        remove_perm(perm, user, obj)
