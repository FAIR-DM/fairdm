"""
FairDM Utilities Package

This package provides common utilities and helper functions used throughout
the FairDM framework, including view mixins, form helpers, permission utilities,
and data processing functions.

Import utilities as needed to avoid import cycles during Django startup.
"""


# Lazy imports to avoid Django import cycle issues
def __getattr__(name: str):
    """Lazy import for utils package to avoid Django startup issues."""
    if name == "DiscoveryTags":
        from .choices import DiscoveryTags

        return DiscoveryTags
    elif name == "SchemeChoices":
        from .choices import SchemeChoices

        return SchemeChoices
    elif name == "Visibility":
        from .choices import Visibility

        return Visibility
    elif name == "AutoGenerationFactories":
        from .factories import AutoGenerationFactories

        return AutoGenerationFactories
    elif name == "OBJECT_PERMS":
        from .permissions import OBJECT_PERMS

        return OBJECT_PERMS
    elif name == "assign_all_model_perms":
        from .permissions import assign_all_model_perms

        return assign_all_model_perms
    elif name == "remove_all_model_perms":
        from .permissions import remove_all_model_perms

        return remove_all_model_perms
    elif name == "default_image_path":
        from .utils import default_image_path

        return default_image_path
    elif name == "fairdm_fieldsets_to_django":
        from .utils import fairdm_fieldsets_to_django

        return fairdm_fieldsets_to_django
    elif name == "fields_to_crispy_layout":
        from .utils import fields_to_crispy_layout

        return fields_to_crispy_layout
    elif name == "fieldsets_to_crispy_layout":
        from .utils import fieldsets_to_crispy_layout

        return fieldsets_to_crispy_layout
    elif name == "get_core_object_or_404":
        from .utils import get_core_object_or_404

        return get_core_object_or_404
    elif name == "get_core_object_or_none":
        from .utils import get_core_object_or_none

        return get_core_object_or_none
    elif name == "get_inheritance_chain":
        from .utils import get_inheritance_chain

        return get_inheritance_chain
    elif name == "get_model_class":
        from .utils import get_model_class

        return get_model_class
    elif name == "get_setting":
        from .utils import get_setting

        return get_setting
    elif name == "get_subclasses":
        from .utils import get_subclasses

        return get_subclasses
    elif name == "user_guide":
        from .utils import user_guide

        return user_guide
    elif name == "CRUDView":
        from .view_mixins import CRUDView

        return CRUDView
    elif name == "FairDMBaseMixin":
        from .view_mixins import FairDMBaseMixin

        return FairDMBaseMixin
    elif name == "FairDMModelFormMixin":
        from .view_mixins import FairDMModelFormMixin

        return FairDMModelFormMixin
    elif name == "RelatedObjectMixin":
        from .view_mixins import RelatedObjectMixin

        return RelatedObjectMixin
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
