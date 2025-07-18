from django.utils.translation import gettext as _

from fairdm.utils.utils import user_guide

# UUID_RE_PATTERN = r"^(?P<uuid>[[pdsme][a-zA-Z0-9_-]{22})/$"

UUID_RE_PATTERN = r"^(?P<uuid>[pdsmea-zA-Z0-9_-]{22})/$"
"""A regex the matches the uuid of a core data object (project, sample, measurement, etc.) and captures it in a named group 'uuid'."""

CORE_PERMISSIONS = [
    ("add_contributor", "Can add contributors"),
    ("modify_contributor", "Can modify contributors"),
    ("modify_metadata", "Can modify metadata"),
]


def documentation_link(path):
    """
    Returns a URL to the documentation for the given path.
    """
    return {
        "text": _("Learn more"),
        "href": user_guide(path),
        "icon": "fa-solid fa-book",
    }


def get_non_polymorphic_instance(obj):
    if not hasattr(obj, "polymorphic_model_marker"):
        return obj

    base_class = obj.type_of
    return base_class.objects.non_polymorphic().get(pk=obj.pk)


def model_class_inheritance_to_fieldsets(obj_or_class):
    from .models import Sample

    klass = obj_or_class if isinstance(obj_or_class, type) else obj_or_class.__class__
    declared_fields = {
        "id",
        "local_id",
        "sample_ptr",
        "polymorphic_ctype",
        "created",
        "modified",
        "options",
        "path",
        "depth",
        "numchild",
        "image",
    }
    result = []

    # Loop through the real model's MRO
    for base in reversed(klass.__mro__):
        # Only process Django models that are subclasses of models.Model
        if hasattr(base, "_meta") and issubclass(base, Sample):
            declared_in_base = []
            for field in base._meta.local_fields:
                # Check if field is already declared by a parent class
                if field.name not in declared_fields:
                    # Mark this field as declared
                    declared_fields.add(field.name)
                    declared_in_base.append(field.name)

            if declared_in_base:
                name = base._meta.verbose_name if base != Sample else None
                result.append((name, {"fields": declared_in_base}))

    # if len(result) == 1:
    # return {None: result["sample"]}
    # sample = result.pop("sample")
    # last_key = list(result.keys())[-1]

    first_group = result[0][1]
    last_group = result[-1][1]

    first_group["fields"] += last_group["fields"]
    del result[-1]

    return result
