"""Small helpers for models, settings, documentation URLs and crispy layouts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from crispy_forms.layout import HTML, Column, Fieldset, Layout, Row
from django.apps import apps
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from fairdm.contrib import CORE_MAPPING

if TYPE_CHECKING:
    pass

DOCUMENTATION_BASE_URL = "https://www.fairdm.org/en/latest/user-guide/"


def user_guide(name: str) -> str:
    """Return the documentation URL for a given name.

    Args:
        name: The name of the documentation section.

    Returns:
        The URL to the documentation section.
    """
    return f"{DOCUMENTATION_BASE_URL}{name}.html"


def get_setting(name: str, key: str):
    """Return a value from a FAIRDM dictionary setting.

    Args:
        name: The name of the FAIRDM setting (without FAIRDM_ prefix).
        key: The key within the setting dictionary.

    Returns:
        The setting value or None if the key is not found.
    """
    settings_dict = getattr(settings, f"FAIRDM_{name}")
    return settings_dict.get(key)


def get_subclasses(model):
    """Return the registered Django model subclasses of a given model.

    Iterates the app registry's models and keeps those that are subclasses of ``model``,
    excluding the model itself.

    Args:
        model: The Django model class for which to find subclasses.

    Returns:
        The direct and indirect subclasses of ``model``.

    Example:
        >>> class A(models.Model):
        ...     pass
        >>> class B(A):
        ...     pass
        >>> class C(B):
        ...     pass
        >>> get_subclasses(A)
        [B, C]
    """
    models = apps.get_models()
    return [m for m in models if issubclass(m, model) and m != model]


def get_inheritance_chain(model, base_model):
    """Return the inheritance chain of a model up to a base model.

    Walks the model's method resolution order and collects every model class that is a subclass
    of ``base_model``.

    Args:
        model: The Django model class for which to determine the inheritance chain.
        base_model: The base model class where the chain ends.

    Returns:
        The model classes in the chain, starting from ``model`` and ending at ``base_model``.

    Example:
        >>> class A(models.Model):
        ...     pass
        >>> class B(A):
        ...     pass
        >>> class C(B):
        ...     pass
        >>> get_inheritance_chain(C, A)
        [C, B, A]
    """
    chain = []
    for base in model.__mro__:
        if hasattr(base, "_meta") and issubclass(base, base_model):
            chain.append(base)
    return chain


def get_model_class(uuid: str):
    """Return the core model class a UUID belongs to.

    The UUID's first character identifies the model.

    Args:
        uuid: A core object's shortuuid primary key.

    Returns:
        The model class.
    """
    return apps.get_model(CORE_MAPPING[uuid[0]])


def get_core_object_or_none(uuid: str) -> tuple:
    """Return the model class and the object matching a UUID.

    Args:
        uuid: The UUID of the object to retrieve.

    Returns:
        A tuple of the model class and the first object with that UUID, or ``None`` in place of
        the object when none exists.
    """
    model = get_model_class(uuid)
    return model, model.objects.filter(uuid=uuid).first()


def get_core_object_or_404(uuid: str):
    """Return the core object with a shortuuid primary key, or raise a 404.

    Args:
        uuid: A core object's shortuuid primary key.

    Returns:
        The matching object. ``Http404`` is raised when no object has that UUID.
    """
    model = get_model_class(uuid)
    return get_object_or_404(model, uuid=uuid)


def default_image_path(instance, filename: str) -> str:
    """Generate the upload path for an image.

    Args:
        instance: The model instance the image is being uploaded to.
        filename: The original filename of the uploaded image.

    Returns:
        A relative file path for storing the image.
    """
    model_name = slugify(instance._meta.verbose_name_plural)
    return f"{model_name}/{instance.uuid}/{filename}"


def fieldsets_to_crispy_layout(fieldsets):
    """Convert Django fieldsets into a crispy-forms Layout.

    Takes fieldsets typically defined in Django's `admin.py` and transforms them into a
    crispy-forms `Layout`, grouping fields into `Fieldset` containers and organizing grouped
    fields into `Row` and `Column` structures. The ``fields`` and ``help_text`` entries are popped
    from each options dict, so the input is modified.

    Args:
        fieldsets: A list of tuples, each containing:
            - `legend` (str or None): The title of the fieldset.
            - `options` (dict): A dictionary holding `"fields"`, a list of field names or
              tuples/lists of field names to be grouped, and optionally `"help_text"`.

    Returns:
        A crispy-forms `Layout` representing the given fieldsets.

    Example:
        >>> fieldsets = [
        >>>     ("Personal Info", {"fields": ["first_name", "last_name"]}),
        >>>     ("Contact", {"fields": [("email", "phone")]}),
        >>> ]
        >>> fieldsets_to_crispy_layout(fieldsets)
        Layout(
            Fieldset("Personal Info", "first_name", "last_name"),
            Fieldset("Contact", Row(Column("email"), Column("phone")))
        )
    """
    crispy_layout = []

    for legend, options in fieldsets:
        layout = [legend]
        help_text = options.pop("help_text", None)
        if help_text:
            layout.append(HTML(f"<p class='help-text'>{help_text}</p>"))

        fields = options.pop("fields", [])
        field_layout = fields_to_crispy_layout(fields)
        layout.extend(field_layout.fields)
        crispy_layout.append(Fieldset(*layout, **options))

    return Layout(*crispy_layout)


def fields_to_crispy_layout(fields):
    """Convert a flat list of fields, or tuples and lists of fields, into a crispy-forms Layout.

    Single field names are added directly. Tuples and lists of field names are wrapped in Columns
    inside a Row.

    Args:
        fields: Field names, or tuples or lists of field names to place side by side.

    Returns:
        A crispy-forms `Layout`.
    """
    layout = []
    for field in fields:
        if isinstance(field, (tuple, list)):
            columns = [Column(f) for f in field]
            layout.append(Row(*columns))
        else:
            layout.append(field)
    return Layout(*layout)


def fairdm_fieldsets_to_django(fieldsets):
    """Convert FairDM-style fieldsets to Django-style fieldsets.

    Args:
        fieldsets: A dict mapping each legend to its options dict.

    Returns:
        A tuple of ``(legend, options)`` pairs.
    """
    return tuple((key, value) for key, value in fieldsets.items())
