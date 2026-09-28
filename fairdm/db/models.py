"""Model base classes, managers and fields FairDM models build on."""

from django.db.models import *  # isort:skip

from auto_prefetch import (
    ForeignKey,
    Manager,
    OneToOneField,
    QuerySet,
)
from auto_prefetch import Model as PrefetchModel
from django.db import models
from django.db.models import __all__ as django_models_all
from django.utils.translation import gettext as _
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
    """Metaclass that makes every model use ``prefetch_manager`` as its base manager."""

    def __new__(cls, name, bases, attrs, **kwargs):
        """Create the model class and set its base manager to ``prefetch_manager``.

        django-auto-prefetch needs this base manager, and setting it here spares each model
        from declaring it.

        Args:
            name: The name of the new class.
            bases: Base classes of the new class.
            attrs: Attributes of the new class.
            **kwargs: Additional keyword arguments.

        Returns:
            The newly created model class.
        """
        new_class = super().__new__(cls, name, bases, attrs, **kwargs)

        # Forced even when a model sets its own, to satisfy django-auto-prefetch's system checks.
        new_class._meta.base_manager_name = "prefetch_manager"

        return new_class


class Model(LifecycleModelMixin, PrefetchModel, metaclass=PrefetchBase):  # type: ignore[no-redef]
    """An abstract base model that replaces ``django.db.models.Model`` across the application.

    It inherits from:
        - LifecycleModelMixin: Declarative hooks for model events such as pre_save and post_save
          (https://rsinger86.github.io/django-lifecycle/).
        - auto_prefetch.Model: Utilities for optimising queryset prefetching
          (https://github.com/adamchainz/django-auto-prefetch).

    Attributes:
        added: Set to the current date and time when the record is created.
        modified: Updated to the current date and time whenever the record is saved.
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
    """Metaclass combining auto-prefetch and polymorphic model behaviour."""

    pass


class PrefetchPolymorphicQuerySet(QuerySet, managers.PolymorphicQuerySet):  # type: ignore[misc,metaclass]
    """A polymorphic queryset that also supports auto-prefetching."""

    pass


class PrefetchPolymorphicManager(managers.PolymorphicManager):
    """A polymorphic manager whose querysets also support auto-prefetching."""

    queryset_class = PrefetchPolymorphicQuerySet  # type: ignore[assignment]


class PolymorphicQuerySet(managers.PolymorphicQuerySet):
    """A polymorphic queryset whose bulk delete removes the polymorphic objects correctly."""

    def delete(self):
        """Delete the queryset as base-class rows, so every polymorphic subclass row goes too."""
        base_qs = super().non_polymorphic()
        # Reverting to the base queryset class stops `delete()` recursing into this override.
        base_qs.__class__ = managers.PolymorphicQuerySet
        return base_qs.delete()


class PolymorphicManager(managers.PolymorphicManager):
    """A polymorphic manager that serves ``PolymorphicQuerySet``."""

    queryset_class = PolymorphicQuerySet  # type: ignore[assignment]


class PolymorphicModel(BasePolymorphicModel, metaclass=PrefetchPolymorphicBase):
    """An abstract base for polymorphic models with auto-prefetching managers.

    Attributes:
        objects: The default manager for polymorphic queries.
        prefetch_manager: The manager auto-prefetch uses for related lookups.
    """

    objects = PrefetchPolymorphicManager()  # type: ignore[misc]
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
    "PartialDateField",
]
