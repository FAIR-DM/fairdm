"""Mixins for views nested behind the detail page of a core model."""

from __future__ import annotations

from functools import cached_property

from django.db.models import Model
from django.shortcuts import get_object_or_404

from fairdm.core.utils import get_non_polymorphic_instance
from fairdm.utils import get_model_class


class RelatedObjectMixin:
    """Fetch a related object from the URL and add it to the context.

    Meant for views behind the detail page of a core model, such as plugins. The
    object is looked up by the URL keyword named in ``base_object_url_kwarg``.

    Attributes:
        base_model: The model class the related object is fetched from.
        base_object_url_kwarg: Name of the URL keyword holding the object's uuid.

    Example:
        class SampleListView(RelatedObjectMixin, ListView):
            def get_queryset(self):
                return self.base_object.samples.all()
    """

    base_model: Model | None = None
    base_object_url_kwarg = "uuid"

    def get_related_model(self):
        """Resolve the related model class from the uuid in the URL.

        Returns:
            The model class the uuid belongs to.
        """
        return get_model_class(self.kwargs.get(self.base_object_url_kwarg))

    @cached_property
    def base_object(self):
        """Fetch the related object named by the uuid in the URL.

        Responds with a 404 when no such object exists.

        Returns:
            The instance of ``base_model`` with that uuid.
        """
        uuid = self.kwargs.get(self.base_object_url_kwarg)
        obj = get_object_or_404(self.base_model, uuid=uuid)
        if hasattr(obj, "polymorphic_model_marker"):
            self.non_polymorphic = get_non_polymorphic_instance(obj)
        return obj

    def get_context_data(self, **kwargs):
        """Add the related object, its model and the model name to the context."""
        context = super().get_context_data(**kwargs)
        context["base_object"] = self.base_object
        context["base_model"] = self.base_model
        context["base_model_name"] = self.base_model._meta.model_name
        context["non_polymorphic_object"] = get_non_polymorphic_instance(
            self.base_object
        )
        context[self.base_model._meta.model_name] = self.base_object
        return context
