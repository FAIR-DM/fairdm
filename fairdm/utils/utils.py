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
# DOCUMENTATION_BASE_URL = "http://localhost:5000/user-guide/"


def user_guide(name: str) -> str:
    """
    Returns the documentation URL for a given name.

    Args:
        name: The name of the documentation section.

    Returns:
        The URL to the documentation section.
    """
    return f"{DOCUMENTATION_BASE_URL}{name}.html"


def get_setting(name: str, key: str):
    """
    Return a setting from the Django settings module.

    Args:
        name: The name of the FAIRDM setting (without FAIRDM_ prefix).
        key: The key within the setting dictionary.

    Returns:
        The setting value or None if not found.
    """
    settings_dict = getattr(settings, f"FAIRDM_{name}")
    return settings_dict.get(key)


def get_subclasses(model):
    """
    Retrieve all registered Django model subclasses of a given model.

    This function iterates through all models registered in the Django app registry
    and returns a list of models that are subclasses of the specified `model`,
    excluding the model itself.

    Args:
        model (type): The Django model class for which to find subclasses.

    Returns:
        list[type]: A list of model classes that are direct or indirect subclasses of `model`.

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
    models = apps.get_models()  # Get all registered Django models
    return [m for m in models if issubclass(m, model) and m != model]


def get_inheritance_chain(model, base_model):
    """
    Retrieve the inheritance chain of a given model up to a specified base model.

    This function traverses the method resolution order (MRO) of a Django model class
    and collects all classes in the hierarchy that are subclasses of `base_model`.

    Args:
        model (type): The Django model class for which to determine the inheritance chain.
        base_model (type): The base model class that serves as the stopping point for traversal.

    Returns:
        list[type]: A list of model classes in the inheritance chain, starting from `model`
                    and ending at `base_model`, inclusive.

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
    for base in model.__mro__:  # Traverse the Method Resolution Order (MRO)
        if hasattr(base, "_meta") and issubclass(base, base_model):
            chain.append(base)
    return chain


def get_model_class(uuid: str):
    """Return a model class from a given UUID."""
    return apps.get_model(CORE_MAPPING[uuid[0]])


def get_core_object_or_none(uuid: str) -> tuple:
    """
    Retrieves the model class and the object instance matching the given UUID. If no instance is found,
    it returns None.

    Args:
        uuid (str): The UUID of the object to retrieve.

    Returns:
        tuple: A tuple containing the model class and the first object instance with the specified UUID,
               or None if no such object exists.
    """
    model = get_model_class(uuid)
    return model, model.objects.filter(uuid=uuid).first()


def get_core_object_or_404(uuid: str):
    """Accepts a shortuuid primary key (as assigned to core data models) and returns the object or raises a 404."""
    model = get_model_class(uuid)
    return get_object_or_404(model, uuid=uuid)


def default_image_path(instance, filename: str) -> str:
    """
    Generates file paths for images.

    Args:
        instance: The model instance the image is being uploaded to.
        filename: The original filename of the uploaded image.

    Returns:
        A relative file path for storing the image.
    """
    model_name = slugify(instance._meta.verbose_name_plural)
    return f"{model_name}/{instance.uuid}/{filename}"


def fieldsets_to_crispy_layout(fieldsets):
    """
    Convert Django fieldsets into a crispy-forms Layout.

    This function takes a list of fieldsets (typically defined in Django's `admin.py`)
    and transforms them into a crispy-forms `Layout`. It supports grouping fields
    into `Fieldset` containers and organizing grouped fields into `Row` and `Column` structures.

    Args:
        fieldsets (list[tuple[str, dict]]): A list of tuples, where each tuple contains:
            - `legend` (str or None): The title of the fieldset.
            - `options` (dict): A dictionary containing the key `"fields"` which is a list
              of field names or tuples/lists of field names to be grouped.

    Returns:
        Layout: A crispy-forms `Layout` object representing the given fieldsets.

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
        layout = [legend]  # Stores fields formatted as Row/Column structures
        help_text = options.pop("help_text", None)
        if help_text:
            layout.append(HTML(f"<p class='help-text'>{help_text}</p>"))

        fields = options.pop("fields", [])
        # Convert fields to layout items and add them individually
        field_layout = fields_to_crispy_layout(fields)
        layout.extend(field_layout.fields)
        # for field in fields:
        #     if isinstance(field, (tuple, list)):  # If a tuple/list, group them in a Row
        #         inner_row = [Column(f) for f in field]  # Wrap each field in a Column
        #         layout.append(Row(*inner_row))  # Create a Row with the Columns
        #     else:
        #         layout.append(field)  # Add a standalone field

        # Wrap fields in a Fieldset (with or without a legend)
        crispy_layout.append(Fieldset(*layout, **options))

    return Layout(*crispy_layout)


def fields_to_crispy_layout(fields):
    """
    Convert a flat list of fields or tuples/lists of fields into crispy-forms layout.

    - Single field names are added directly.
    - Tuples/lists of field names are wrapped in Columns inside a Row.
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
    """Converts the FairDM style fieldsets to Django style fieldsets."""
    return tuple((key, value) for key, value in fieldsets.items())
