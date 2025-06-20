from django.db.models import *  # isort:skip

from auto_prefetch import ForeignKey, Manager, OneToOneField, QuerySet
from auto_prefetch import Model as PrefetchModel
from django.db import models
from django.db.models import __all__ as django_models_all

# from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _
from django_bleach.models import BleachField as TextField
from django_lifecycle import LifecycleModelMixin
from polymorphic import managers
from polymorphic.base import PolymorphicModelBase
from polymorphic.models import PolymorphicModel as BasePolymorphicModel

from .fields import (
    BigIntegerQuantityField,
    DecimalQuantityField,
    IntegerQuantityField,
    PartialDateField,
    PositiveIntegerQuantityField,
    QuantityField,
)


class PrefetchBase(models.base.ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        """
        Create a new class instance, injecting or overriding the 'base_manager_name' attribute
        in the inner Meta class with 'prefetch_manager' if it is not already set. (required for auto-prefetch to
        work correctly without asking the user to add it manually to their models)

        Args:
            cls (type): The metaclass.
            name (str): The name of the new class.
            bases (tuple): Base classes of the new class.
            attrs (dict): Attributes of the new class.
            **kwargs: Additional keyword arguments.
        Returns:
            type: The newly created class with the modified Meta attribute.
        """
        new_class = super().__new__(cls, name, bases, attrs, **kwargs)

        # Only inject if it's not already explicitly set
        # if not hasattr(new_class._meta, "base_manager_name"):
        if new_class._meta.base_manager_name is None:
            new_class._meta.base_manager_name = "prefetch_manager"

        return new_class


class Model(PrefetchModel, LifecycleModelMixin, models.Model, metaclass=PrefetchBase):
    # class Model(models.Model):
    """
    An abstract Django model designed to replace `django.db.models.Model`. It provides additional functionality
     to all inheriting models in the application.

    This class inherits from:
        - LifecycleModel: Declarative hooks for model events (e.g., pre_save, post_save).
        (https://rsinger86.github.io/django-lifecycle/)
        - auto_prefetch.hModel: Provides utilities for optimizing queryset prefetching.
        (https://github.com/adamchainz/django-auto-prefetch)
    It includes the following fields:
        - added (DateTimeField): Automatically set to the current date and time when the record is created.
        - modified (DateTimeField): Automatically updated to the current date and time whenever the record is saved.
    """

    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date added"),
        help_text=_("The date and time this record was added to the database."),
    )
    modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified"),
        help_text=_("The date and time this record was last modified."),
    )

    class Meta:
        abstract = True


class PrefetchPolymorphicBase(PrefetchBase, PolymorphicModelBase):
    pass


class PrefetchPolymorphicQuerySet(QuerySet, managers.PolymorphicQuerySet):
    pass


class PrefetchPolymorphicManager(managers.PolymorphicManager):
    """
    A custom Django model manager that combines the functionality of the `auto_prefetch.Manager`
    with a PolymorphicManager, enabling polymorphic queryset support along with any
    auto prefetching logic.

    Inherits from:
        - auto_prefetch.Manager
        - managers.PolymorphicManager
    """

    queryset_class = PrefetchPolymorphicQuerySet


class PolymorphicQuerySet(managers.PolymorphicQuerySet):
    def delete(self):
        """
        Override the delete method to ensure that polymorphic objects are deleted correctly.
        This method ensures that all related polymorphic objects are deleted when the queryset is deleted.
        """
        # Call the parent delete method to handle the actual deletion
        # qs = self.non_polymorphic()
        # return QuerySet.delete(qs)
        base_qs = super().non_polymorphic()
        # Prevent recursion by reverting to the parent class
        base_qs.__class__ = managers.PolymorphicQuerySet
        return base_qs.delete()


class PolymorphicManager(managers.PolymorphicManager):
    """
    A custom Django model manager that combines the functionality of the `auto_prefetch.Manager`
    with a PolymorphicManager, enabling polymorphic queryset support along with any
    auto prefetching logic.

    Inherits from:
        - auto_prefetch.Manager
        - managers.PolymorphicManager
    """

    queryset_class = PolymorphicQuerySet


class PolymorphicModel(BasePolymorphicModel, metaclass=PrefetchPolymorphicBase):
    # class PolymorphicModel(ShowFieldType, BasePolymorphicModel):
    """
    Abstract base model that supports polymorphic behavior for Django ORM models.
    This class combines functionality from `ShowFieldType`, `BasePolymorphicModel`, and uses
    the `PolymorphicBase` metaclass to enable polymorphic model inheritance. It provides
    custom managers (`objects` and `prefetch_manager`) for efficient querying and prefetching
    of related polymorphic objects.

    Attributes:
        objects (PrefetchPolymorphicManager): Default manager for polymorphic queries.
        prefetch_manager (PrefetchPolymorphicManager): Additional manager for optimized prefetching.
    """

    # objects = PolymorphicManager()
    objects = PrefetchPolymorphicManager()
    prefetch_manager = PrefetchPolymorphicManager()

    class Meta:
        abstract = True


__all__ = [
    *django_models_all,
    "BigIntegerQuantityField",
    "DecimalQuantityField",
    "ForeignKey",
    "IntegerQuantityField",
    "Manager",
    "Model",
    "OneToOneField",
    "PositiveIntegerQuantityField",
    "QuantityField",
    "QuerySet",
    "TextField",
    "FairDMBase",
    "PartialDateField",
]
