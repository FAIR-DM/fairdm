"""Model mixins for FairDM models."""

from django.utils.decorators import classonlymethod

from fairdm.utils.utils import get_inheritance_chain


class PolymorphicMixin:
    """A mixin for polymorphic base models that know their own ``type_of`` root."""

    @classonlymethod
    def get_inheritance_chain(cls):
        """Return the model classes from this class up to ``type_of``, inclusive.

        Returns:
            The inheritance chain, most specific class first.
        """
        return get_inheritance_chain(cls, cls.type_of)
